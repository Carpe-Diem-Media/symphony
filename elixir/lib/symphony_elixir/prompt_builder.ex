defmodule SymphonyElixir.PromptBuilder do
  @moduledoc """
  Builds agent prompts from normalized tracker work item data.
  """

  alias SymphonyElixir.AgentRuntime.{Profile, Route}
  alias SymphonyElixir.{Config, PathSafety, Workflow}
  alias SymphonyElixir.WorkControl.WorkflowLifecycle

  @render_opts [strict_variables: true, strict_filters: true]
  @role_prompt_root Path.expand("../../prompts", __DIR__)
  @planner_prompt_path Path.join(@role_prompt_root, "planner.md")
  @builder_prompt_path Path.join(@role_prompt_root, "builder.md")
  @reviewer_prompt_path Path.join(@role_prompt_root, "reviewer.md")
  @fixer_prompt_path Path.join(@role_prompt_root, "fixer.md")

  @external_resource @planner_prompt_path
  @external_resource @builder_prompt_path
  @external_resource @reviewer_prompt_path
  @external_resource @fixer_prompt_path

  @embedded_role_prompts %{
    "planner" => File.read!(@planner_prompt_path),
    "builder" => File.read!(@builder_prompt_path),
    "reviewer" => File.read!(@reviewer_prompt_path),
    "fixer" => File.read!(@fixer_prompt_path)
  }

  @spec build_prompt(SymphonyElixir.Tracker.Issue.t(), keyword()) :: String.t()
  def build_prompt(issue, opts \\ []) do
    template =
      Keyword.get_lazy(opts, :pilot_workflow, &Workflow.current/0)
      |> prompt_template!()
      |> parse_template!()

    rendered_prompt =
      template
      |> Solid.render!(
        %{
          "attempt" => Keyword.get(opts, :attempt),
          "issue" => issue |> Map.from_struct() |> to_solid_map()
        },
        @render_opts
      )
      |> IO.iodata_to_binary()

    case {Keyword.get(opts, :pilot_authority), Keyword.fetch(opts, :role_prompt)} do
      {%{role_policy: %{bytes: bytes}}, _} ->
        bytes <> "\n\n--- Workflow task ---\n" <> rendered_prompt

      {nil, {:ok, captured_role_prompt}} ->
        with_role_prompt(rendered_prompt, Keyword.get(opts, :route), captured_role_prompt)

      {nil, :error} ->
        with_role_prompt(rendered_prompt, Keyword.get(opts, :route))
    end
  end

  @spec with_role_prompt(String.t(), Route.t() | nil) :: String.t()
  def with_role_prompt(prompt, %Route{} = route) when is_binary(prompt) do
    with_role_prompt(prompt, route, role_prompt(route))
  end

  def with_role_prompt(prompt, _route), do: prompt

  @spec with_role_prompt(String.t(), Route.t() | nil, String.t() | nil) :: String.t()
  def with_role_prompt(prompt, %Route{}, captured_role_prompt) when is_binary(prompt) do
    append_role_prompt(prompt, captured_role_prompt)
  end

  def with_role_prompt(prompt, _route, _captured_role_prompt), do: prompt

  @spec role_prompt(Route.t() | nil) :: String.t() | nil
  def role_prompt(%Route{profile: %Profile{} = profile, profile_name: profile_name}) do
    prompt_name = profile.prompt || profile_name

    case role_prompt_file(prompt_name) do
      {:ok, prompt} -> prompt
      :error -> inline_role_prompt(prompt_name, profile_name)
    end
  end

  def role_prompt(_route), do: nil

  @doc "Captures the selected file-backed Planner policy for a pilot without fallback."
  @spec pilot_role_policy(Config.Schema.t()) :: {:ok, map()} | {:error, :pilot_policy_unavailable}
  def pilot_role_policy(settings) do
    profile_name =
      Enum.find_value(settings.agent.routes, "planner", fn {state, name} ->
        if WorkflowLifecycle.parse(to_string(state)) == {:ok, :planning}, do: Profile.normalize_name(name)
      end)

    with %Profile{responsibility: "planning"} = profile <- Map.get(settings.agent.profiles, profile_name),
         {:ok, name} <- normalize_role_prompt_name(profile.prompt || profile_name),
         root <- Path.expand(role_prompt_root()),
         {:ok, canonical_root} <- PathSafety.canonicalize(root),
         path <- role_prompt_path(name, root),
         {:ok, canonical_path} <- PathSafety.canonicalize(path),
         {:ok, bytes} when byte_size(bytes) > 0 <- File.read(canonical_path) do
      {:ok, %{profile_name: profile_name, prompt_name: profile.prompt || profile_name, root: root, canonical_root: canonical_root, path: canonical_path, bytes: bytes}}
    else
      _ -> {:error, :pilot_policy_unavailable}
    end
  rescue
    _ -> {:error, :pilot_policy_unavailable}
  end

  defp prompt_template!({:ok, %{prompt_template: prompt}}), do: default_prompt(prompt)

  defp prompt_template!({:error, reason}) do
    raise RuntimeError, "workflow_unavailable: #{inspect(reason)}"
  end

  defp parse_template!(prompt) when is_binary(prompt) do
    Solid.parse!(prompt)
  rescue
    error ->
      reraise %RuntimeError{
                message: "template_parse_error: #{Exception.message(error)} template=#{inspect(prompt)}"
              },
              __STACKTRACE__
  end

  defp to_solid_map(map) when is_map(map) do
    Map.new(map, fn {key, value} -> {to_string(key), to_solid_value(value)} end)
  end

  defp to_solid_value(%DateTime{} = value), do: DateTime.to_iso8601(value)
  defp to_solid_value(%NaiveDateTime{} = value), do: NaiveDateTime.to_iso8601(value)
  defp to_solid_value(%Date{} = value), do: Date.to_iso8601(value)
  defp to_solid_value(%Time{} = value), do: Time.to_iso8601(value)
  defp to_solid_value(%_{} = value), do: value |> Map.from_struct() |> to_solid_map()
  defp to_solid_value(value) when is_map(value), do: to_solid_map(value)
  defp to_solid_value(value) when is_list(value), do: Enum.map(value, &to_solid_value/1)
  defp to_solid_value(value), do: value

  defp default_prompt(prompt) when is_binary(prompt) do
    if String.trim(prompt) == "" do
      Config.workflow_prompt()
    else
      prompt
    end
  end

  defp role_prompt_file(prompt_name) when is_binary(prompt_name) do
    case normalize_role_prompt_name(prompt_name) do
      {:ok, normalized_name} -> fetch_role_prompt(normalized_name)
      :error -> :error
    end
  end

  defp role_prompt_file(_prompt_name), do: :error

  defp normalize_role_prompt_name(prompt_name) when is_binary(prompt_name) do
    normalized_name = String.trim(prompt_name)

    if normalized_name == "" or String.contains?(normalized_name, ["/", "\\", ".."]) or
         not String.match?(normalized_name, ~r/^[A-Za-z0-9_-]+(?:\.md)?$/) do
      :error
    else
      {:ok, normalized_name}
    end
  end

  defp fetch_role_prompt(normalized_name) do
    case read_role_prompt_file(normalized_name) do
      {:ok, prompt} -> {:ok, prompt}
      :error -> Map.fetch(@embedded_role_prompts, Path.rootname(normalized_name))
    end
  end

  defp read_role_prompt_file(normalized_name) do
    normalized_name
    |> role_prompt_path()
    |> File.read()
    |> case do
      {:ok, prompt} when is_binary(prompt) and byte_size(prompt) > 0 -> {:ok, prompt}
      _ -> :error
    end
  end

  defp role_prompt_path(normalized_name, root \\ role_prompt_root()) do
    filename =
      case Path.extname(normalized_name) do
        ".md" -> normalized_name
        _ -> normalized_name <> ".md"
      end

    Path.join(root, filename)
  end

  defp role_prompt_root do
    Application.get_env(:symphony_elixir, :role_prompt_root, @role_prompt_root)
  end

  defp append_role_prompt(prompt, role_prompt) when is_binary(prompt) and is_binary(role_prompt) do
    String.trim(role_prompt) <> "\n\n--- Workflow task ---\n" <> prompt
  end

  defp append_role_prompt(prompt, _role_prompt), do: prompt

  defp inline_role_prompt(prompt_name, profile_name) when is_binary(prompt_name) do
    prompt_name = String.trim(prompt_name)

    if prompt_name == "" or prompt_name == profile_name do
      nil
    else
      "Role policy: #{profile_name}\n\n#{prompt_name}"
    end
  end

  defp inline_role_prompt(_prompt_name, _profile_name), do: nil
end
