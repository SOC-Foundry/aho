# a8geekomCos - 0.2.18 W0 baseline probe

**Probe origin host:** NZXTcos (10.0.x.x via Tailscale 100.x)
**Probe target host:** a8geekomCos (Tailscale 100.74.161.116)
**Probe time:** 0.2.18 W0 (2026-05-09)
**Probe agent:** claude-code (drafter+executor) via Tailscale SSH
**Plan-doc reference:** `artifacts/iterations/0.2.18/aho-plan-0.2.18.md` §W0 Bucket 3

## Tailscale reachability

| Field | Value |
|---|---|
| Tailscale IPv4 | `100.74.161.116` |
| MagicDNS short | `a8geekomcos` |
| MagicDNS FQDN | `a8geekomcos.tail78a311.ts.net` |
| Tailnet status | active; **direct** connection (not relayed) |
| RTT (NZXTcos → a8geekomCos) | **1ms** via `172.31.255.247:41641` |
| Owner | `kthompson@` |
| Tailscale SSH | enabled at probe time (operator ran `sudo tailscale up --ssh --accept-risk=lose-ssh`) |
| Auth mode at probe | "check" (browser-approval required per session); ACL refinement may relax to "accept" if W2 install.fish needs frequent SSH |
| NZXTcos MagicDNS FQDN (for W1 bake) | **`nzxtcos.tail78a311.ts.net`** ← bake into `aho:0.2.18` image as `OTEL_EXPORTER_OTLP_ENDPOINT=http://nzxtcos.tail78a311.ts.net:4317` |

## OS family + kernel

| Field | Value |
|---|---|
| Distribution | **CachyOS Linux** (Arch derivative - `ID=cachyos`, `ID_LIKE=arch`) |
| Build channel | rolling |
| Kernel | `7.0.5-2-cachyos` x86_64 (PREEMPT_DYNAMIC, build 2026-05-09) |

**Decision gate (per plan-doc §W0.8):** ✅ Arch/CachyOS confirmed. install.fish portability assumptions from 0.2.17 hold. **Not** an ADR-0006 scope-amendment trigger. W2 proceeds without amendment.

## Tools / package presence

| Tool | Path | Status |
|---|---|---|
| podman | `/usr/bin/podman` (5.8.2) | ✅ present, container runtime ready |
| fish | `/usr/bin/fish` | ✅ present (canonical install.fish shell) |
| ollama | - | ❌ **not installed** - W2 install.fish must install or base bundle path must include |
| git | `/usr/bin/git` | ✅ |
| python3 | `/usr/bin/python3` | ✅ |
| jq | `/usr/bin/jq` | ✅ |
| age | `/usr/bin/age` | ✅ (broker bundle decryption ready) |
| curl | `/usr/bin/curl` | ✅ |
| tailscale | `/usr/bin/tailscale` (1.x - version not pinned; Tailscale SSH active) | ✅ |
| ssh, sudo | `/usr/bin/{ssh,sudo}` | ✅ |

## CPU / iGPU profile (base-tier classification)

| Field | Value |
|---|---|
| CPU model | **AMD Ryzen 9 8945HS w/ Radeon 780M Graphics** |
| Architecture | x86_64 |
| Cores × threads | 8 cores × 2 threads = **16 logical CPUs** |
| Family/Model | 25 / 117 (AMD Zen 4 / Phoenix2) |
| Max boost | 5.26 GHz |
| Microcode | `0xa705208` |
| Discrete GPU | **none** |
| iGPU | **AMD Radeon 780M** (HawkPoint1, PCI `c6:00.0`) - RDNA3 integrated |
| `nvidia-smi` binary | **present** (`/usr/bin/nvidia-smi`) but driver fails (`couldn't communicate with the NVIDIA driver`) - there is no NVIDIA hardware |

**Tier-detect verdict:** `base` (correctly).

The `nvidia-smi` binary is on PATH as a stub (likely from a passive package install - perhaps `cuda` or `nvidia-utils` was preinstalled), but the subprocess query fails. `src/aho/tier_detect.py:28-49` handles this exact case: `shutil.which()` returns the path, subprocess runs with `check=True`, `CalledProcessError` is caught, function returns `None`, `classify(None)` returns `"base"`. **No code change required.** Edge-case noted for future probes - a binary-present, driver-absent host should never appear as partial/full.

## Disk capacity

| Mount | Size | Used | Avail | %Used |
|---|---|---|---|---|
| `/dev/nvme0n1p2` (`/`, `/home` shared) | 950G | 32G | **918G** | 4% |

Far above the ~5GB minimum (image ~1.5GB + llama3.2:3b ~2GB + nomic-embed-text ~270MB + working state). No disk pressure.

## Memory

| Field | Value |
|---|---|
| RAM total | **30 GiB** |
| RAM available | 28 GiB (1.6 GiB used at probe time) |
| Swap | 30 GiB (0 B used) |

Sufficient headroom for in-container `llama3.2:3b` (≈2.5 GiB working set) plus `nomic-embed-text` (≈350 MiB) plus container overhead - all CPU-bound on iGPU/CPU only, no VRAM pressure path.

## W1 / W2 implications

1. **W1 image bake - `OTEL_EXPORTER_OTLP_ENDPOINT` default value:** `http://nzxtcos.tail78a311.ts.net:4317`. This is the canonical value.
2. **W2 install.fish - ollama install path:** ollama is absent on a8geekomCos. install.fish must invoke `pacman -S ollama-bin` (or equivalent CachyOS path) OR the base bundle delivers ollama in-container with no host-side install. Confirm which pattern at W2 design.
3. **W2 secrets broker - host-local provisioning:** broker socket at `~/.local/share/aho/broker/broker.sock` per ADR-0009. Kyle creates per-host secrets on a8geekomCos directly; no cross-host tunneling.
4. **W2 Tailscale ACL - relaxation if needed:** current Tailscale SSH is in "check" mode (browser approval per session). If W2 install.fish makes repeated SSH calls (unlikely - typical install.fish is one-shot), the operator may want to update the tailnet ACL to `accept` (no per-session check) for the NZXTcos→a8geekomCos `kthompson` path. Not a 0.2.18 W0 deliverable; flagged for W2 visibility.
5. **W2 firewall pattern carry from 0.2.17:** `pasta-NAT` + `iif lo` rule pattern from 0.2.17 W1 may apply if a8geekomCos's host firewall blocks container→Ollama on loopback. Test at W2 D? - install.fish or smoke run will surface the symptom if present.

## Probe completeness

- ✅ Tailscale reachability + MagicDNS resolution
- ✅ OS family + kernel
- ✅ Package presence (podman, fish, ollama, git, python3, jq, age, curl, tailscale, ssh, sudo)
- ✅ CPU / iGPU profile + tier-detect verdict path
- ✅ Disk capacity
- ✅ Memory + swap
- ✅ NZXTcos MagicDNS FQDN captured (W1 bake input)

No probe items deferred or blocked at W0 close.
