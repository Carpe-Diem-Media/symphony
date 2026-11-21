# Research context and remaining gates

This is a non-authoritative summary of SYMPHONY_DEVVM_01 through SYMPHONY_DEVVM_04.
It records findings for review and grants no execution, integration or acceptance authority.

## What the evidence establishes

Checkpoint B establishes authenticated private release staging on the inspected workstation.
It does not establish that Devvm works as a VM backend on that host, disposable workload isolation,
multi-worker independence, exact guest toolchains, a passing Symphony suite inside a guest,
or a supported Symphony integration. Those runtime experiments were not performed.

Devvm is pinned to v0.1.0, source e9bd270398730bf0f7ffe44e8f78f5da323daeb7.
Lima is pinned to v2.2.1, source 27bc4c4b101e27994e01e36566a0f2091bbca507.

## Bootstrap containment remains blocked

Devvm supplies NetInternet directly to image construction, independently of a project's network tier.
On Linux that mode skips the wrapper used for NetNone and NetProxy. Lima constructs a user-network
backend without restrict=on. The build-proxy path retains direct internal-network reachability and
host-loopback access through Lima's host address. No runtime reachability probe was performed.

Sources:

- [Image construction specification](https://github.com/devvmhq/devvm/blob/e9bd270398730bf0f7ffe44e8f78f5da323daeb7/internal/build/build.go#L347).
- [Linux network-mode handling](https://github.com/devvmhq/devvm/blob/e9bd270398730bf0f7ffe44e8f78f5da323daeb7/internal/backend/lima/start.go#L209-L228).
- [Build proxy behavior](https://github.com/devvmhq/devvm/blob/e9bd270398730bf0f7ffe44e8f78f5da323daeb7/internal/backend/lima/buildproxy.go#L58-L87).
- [Pinned Lima QEMU network arguments](https://github.com/lima-vm/lima/blob/27bc4c4b101e27994e01e36566a0f2091bbca507/pkg/driver/qemu/qemu.go#L787-L804).

A future project VM's --network none setting does not close this first-build boundary.
No supported initial offline bootstrap was established. Package replay does not remove all downloads.
The --from path still creates an Ubuntu conversion VM with NetInternet and runs conversion/package
scripts. It is not a proven containment workaround.

Sources:

- [Base mise download](https://github.com/devvmhq/devvm/blob/e9bd270398730bf0f7ffe44e8f78f5da323daeb7/assets/layers/base.sh#L79).
- [Container-image conversion VM](https://github.com/devvmhq/devvm/blob/e9bd270398730bf0f7ffe44e8f78f5da323daeb7/internal/backend/lima/oci.go#L110-L151).
- [Guest conversion package installation](https://github.com/devvmhq/devvm/blob/e9bd270398730bf0f7ffe44e8f78f5da323daeb7/assets/oci/bootify.sh#L26-L31).

## Disk, identity and failure findings

The base request is 4 CPUs, 8 GiB RAM and 100 GiB virtual disk.
Project disks cannot shrink below the image. Linux project qcow2 overlays normally share an image,
but the implementation can retain a full copy. Configured virtual capacity is not allocated disk usage.
Build disks, package caches, downloaded images and project overlays need separate measurement.

Sources:

- [Base resource constants](https://github.com/devvmhq/devvm/blob/e9bd270398730bf0f7ffe44e8f78f5da323daeb7/internal/backend/fit.go#L6-L13).
- [Overlay implementation and fallback](https://github.com/devvmhq/devvm/blob/e9bd270398730bf0f7ffe44e8f78f5da323daeb7/internal/backend/lima/lima.go#L785-L803).

An image key identifies construction inputs, not finished disk bytes. No supported portable image
export/import contract was established. Absolute backing dependencies and machine-specific Lima state
prevent treating a copied Lima directory as a verified portable artifact.

Failure handling can delete unfinished state, stop errors are not always retained, and a fresh base
boot failure can trigger one automatic fallback to an older image. An outer evidence/termination
protocol would be required before any future bootstrap authorization.

Sources:

- [Image key](https://github.com/devvmhq/devvm/blob/e9bd270398730bf0f7ffe44e8f78f5da323daeb7/internal/image/key.go#L45-L68).
- [Unfinished build cleanup](https://github.com/devvmhq/devvm/blob/e9bd270398730bf0f7ffe44e8f78f5da323daeb7/internal/backend/lima/build.go#L344-L353).
- [Stop implementation](https://github.com/devvmhq/devvm/blob/e9bd270398730bf0f7ffe44e8f78f5da323daeb7/internal/backend/lima/lima.go#L516-L521).
- [Bounded boot fallback](https://github.com/devvmhq/devvm/blob/e9bd270398730bf0f7ffe44e8f78f5da323daeb7/internal/build/build.go#L156-L177).

A synthetic HOME, scoped XDG/Lima/cache/temp paths and a child-only system-QEMU PATH redirect normal
state access. They do not restrict a host process's filesystem rights or close bootstrap networking.
Changing LIMA_HOME alone is insufficient because Devvm resolves its own directories.

## Alternatives considered

Direct bootstrap on the daily driver remains HOLD until an outer, host-enforced network boundary is
demonstrated. Proxy variables and project policy are insufficient.

A distinct isolated provisioning environment could remove daily-driver exposure, but availability and
a supported authenticated image handoff remain unproven.

A direct KVM/libvirt design with no guest NIC from the first instruction offers a clearer next
containment design. Its image verification, filesystem/device confinement, process identity and
lifecycle still need independent design and authorization. No libvirt VM was started or configured.

## Symphony authority and decision separation

The current implementation rejects binary worker_host admission with remote_containment_unproven.
Staging success does not satisfy or replace that denial. No Devvm runtime adapter was implemented.

[Runtime admission at the inspected source baseline](https://github.com/Carpe-Diem-Media/symphony/blob/ea696d1453dfef81c869cdc4fbda77bfa135a416/elixir/lib/symphony_elixir/agent_runtime/runtime_isolation.ex#L39-L49).

The proposed project specification remains one disposable clone VM, 2 CPUs, 4 GiB RAM and 100 GiB
virtual disk, with agents/tools/layers disabled, network none, no ports, no devcontainer and no SSH-agent
forwarding. This is a proposal only. Fresh resource/pressure checks and approved synthetic endpoints
would be necessary before any later experiment.

B covers authenticated private file staging only.
C0 covers initial image construction under demonstrated acceptable containment and remains HOLD.
C1 covers the project VM experiment and remains HOLD unless C0 is satisfied and separately authorized.
Independent review of this PR cannot implicitly authorize C0, C1, remote-worker admission, F09, P08,
Master Gate acceptance, live-provider tests or cleanup.
