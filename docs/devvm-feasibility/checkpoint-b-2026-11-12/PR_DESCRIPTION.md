#### Context

Checkpoint B evidence needs a durable, inspectable PR so an independent reviewer can assess staging without treating it as runtime containment or programme acceptance.

#### TL;DR

*Publish authenticated Devvm/Lima staging evidence; keep bootstrap and project-VM gates on HOLD.*

#### Summary

- Record the single staging run, signatures, actual archive inventories and payload verification.
- Include exact scripts, retained manifests, source mappings and corrected audit failures.
- Explain bootstrap blockers and preserve C0/C1, remote admission, F09 and P08 boundaries.
- Publish text evidence only; retain binary assets locally and preserve a durable review packet.

#### Alternatives

- Keeping all results local would prevent independent review of the recorded evidence.
- Runtime integration and VM experiments require separate design and authorization.

#### Test Plan

- [x] Revalidate retained inventory, copied-source hashes, JSON, script syntax and packet checksums.
- [x] Include observed eight-case synthetic results and successful staging verification.
- [x] Run the existing PR-body checker directly with installed pinned Elixir.
- [ ] make -C elixir all: not run; dependencies are absent and acquisition remains outside authorization.
- [ ] Exact-candidate CI and independent acceptance.
