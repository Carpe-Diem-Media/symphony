defmodule SymphonyElixir.PathSafety do
  @moduledoc false

  @doc "Captures a canonical trusted executable path and its SHA-256 bytes."
  @spec trusted_executable_identity(Path.t()) ::
          {:ok, %{path: Path.t(), sha256: String.t()}} | {:error, :untrusted_path}
  def trusted_executable_identity(path) do
    with true <- Path.type(path) == :absolute,
         {:ok, ^path} <- canonicalize(path),
         :ok <- validate_trusted_executable(path),
         {:ok, bytes} <- File.read(path) do
      {:ok, %{path: path, sha256: Base.encode16(:crypto.hash(:sha256, bytes), case: :lower)}}
    else
      _ -> {:error, :untrusted_path}
    end
  rescue
    _ -> {:error, :untrusted_path}
  end

  @doc "Requires a root-owned executable and root-owned, non-writable ancestry."
  @spec validate_trusted_executable(Path.t()) :: :ok | {:error, :untrusted_path}
  def validate_trusted_executable(path) do
    if Enum.all?(trusted_path_ancestors(path), &trusted_path_component?/1),
      do: :ok,
      else: {:error, :untrusted_path}
  rescue
    _ -> {:error, :untrusted_path}
  end

  defp trusted_path_component?({candidate, is_executable}) do
    with {:ok, %File.Stat{} = stat} <- File.lstat(candidate),
         true <- stat.uid == 0,
         true <- Bitwise.band(stat.mode, 0o022) == 0,
         true <- Bitwise.band(stat.mode, 0o6000) == 0 do
      trusted_path_type?(stat, is_executable)
    else
      _failure -> false
    end
  end

  defp trusted_path_type?(%File.Stat{type: :regular, mode: mode}, true),
    do: Bitwise.band(mode, 0o111) != 0

  defp trusted_path_type?(%File.Stat{type: :directory}, false), do: true
  defp trusted_path_type?(_stat, _is_executable), do: false

  defp trusted_path_ancestors(path) do
    trusted_path_ancestors(Path.dirname(path), [{path, true}])
  end

  defp trusted_path_ancestors(path, acc) do
    if path == "/" do
      [{"/", false} | acc]
    else
      trusted_path_ancestors(Path.dirname(path), [{path, false} | acc])
    end
  end

  @spec canonicalize(Path.t()) :: {:ok, Path.t()} | {:error, term()}
  def canonicalize(path) when is_binary(path) do
    expanded_path = Path.expand(path)
    {root, segments} = split_absolute_path(expanded_path)

    case resolve_segments(root, [], segments, []) do
      {:ok, canonical_path} ->
        {:ok, canonical_path}

      {:error, reason} ->
        {:error, {:path_canonicalize_failed, expanded_path, reason}}
    end
  end

  defp split_absolute_path(path) when is_binary(path) do
    [root | segments] = Path.split(path)
    {root, segments}
  end

  @spec resolve_segments(String.t(), [String.t()], [String.t()], [String.t()]) ::
          {:ok, String.t()} | {:error, term()}
  defp resolve_segments(root, resolved_segments, [], _visited_symlinks),
    do: {:ok, join_path(root, resolved_segments)}

  defp resolve_segments(root, resolved_segments, [segment | rest], visited_symlinks) do
    candidate_path = join_path(root, resolved_segments ++ [segment])

    case File.lstat(candidate_path) do
      {:ok, %File.Stat{type: :symlink}} ->
        follow_symlink(candidate_path, root, resolved_segments, rest, visited_symlinks)

      {:ok, _stat} ->
        resolve_segments(root, resolved_segments ++ [segment], rest, visited_symlinks)

      {:error, :enoent} ->
        {:ok, join_path(root, resolved_segments ++ [segment | rest])}

      {:error, reason} ->
        {:error, reason}
    end
  end

  @spec follow_symlink(String.t(), String.t(), [String.t()], [String.t()], [String.t()]) ::
          {:ok, String.t()} | {:error, term()}
  defp follow_symlink(candidate_path, root, resolved_segments, rest, visited_symlinks) do
    if candidate_path in visited_symlinks do
      {:error, :eloop}
    else
      case File.read_link(candidate_path) do
        {:ok, target} ->
          resolved_target = Path.expand(target, join_path(root, resolved_segments))
          {target_root, target_segments} = split_absolute_path(resolved_target)

          resolve_segments(
            target_root,
            [],
            target_segments ++ rest,
            [candidate_path | visited_symlinks]
          )

        {:error, reason} ->
          {:error, reason}
      end
    end
  end

  defp join_path(root, segments) when is_list(segments) do
    Enum.reduce(segments, root, fn segment, acc -> Path.join(acc, segment) end)
  end
end
