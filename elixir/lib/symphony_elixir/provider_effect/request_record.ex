defmodule SymphonyElixir.ProviderEffect.RequestRecord do
  @moduledoc "A nonsecret, append-only record of one synthetic provider request."

  @enforce_keys [:request_id, :ordinal, :revision, :state, :send_may_have_occurred]
  defstruct [
    :request_id,
    :ordinal,
    :revision,
    :state,
    :send_may_have_occurred,
    :runtime_attempt_id,
    :grant_id,
    :context_digest,
    :thread_id,
    :turn_id,
    :prior_request_id,
    :tool_operation_id,
    :method,
    :url,
    :model,
    :body_digest,
    :body_bytes,
    :deadline_monotonic_ms,
    :response_id,
    :descriptor,
    evidence_scope: "SYNTHETIC_PIPE",
    authenticated: false,
    operationally_qualified: false
  ]

  @type t :: %__MODULE__{}
end
