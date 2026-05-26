#!/usr/bin/env fish
# install.fish — Idempotent clone-to-deploy orchestrator for aho.
# 0.3.1 W1 — Check-first / remediate-on-fail / re-check / report-final-status.
# Pillar 4: wrappers are the tool surface.
#
# Usage:
#   ./install.fish                    Run all steps (idempotent on healthy host)
#   ./install.fish --check            Read-only: probe every step, no remediation
#   ./install.fish --step <step_id>   Run only the named step
#
# State:
#   ~/.local/state/aho/install.state             Legacy key=value step status (backward-compat)
#   ~/.local/share/aho/install-state.jsonl       Append-only structured per-step JSON
#   ~/.local/state/aho/install.log               Human-readable log
#
# JSONL schema (per line, one per step invocation):
#   {
#     "step_id":              str,
#     "step_name":            str,
#     "check_command":        str,
#     "expected_state":       str,
#     "observed_state":       str,
#     "action_taken":         str,                 # "none" | "remediated" | "remediation_failed" | "skipped_check_only"
#     "final_status":         str,                 # "satisfied" | "remediated" | "remediation_failed" | "check_only_pass" | "check_only_fail"
#     "started_at_utc":       str (ISO-8601),
#     "completed_at_utc":     str (ISO-8601),
#     "duration_ms":          int,
#     "remediation_command_if_any": str | null,
#     "mode":                 str                  # "full" | "check" | "step"
#   }

set -g script_name "aho-install"
set -g project_root (dirname (realpath (status filename)))
set -g state_dir "$HOME/.local/state/aho"
set -g state_file "$state_dir/install.state"
set -g log_file "$state_dir/install.log"
set -g jsonl_dir "$HOME/.local/share/aho"
set -g jsonl_file "$jsonl_dir/install-state.jsonl"

# Mode flags
set -g mode_check 0
set -g mode_step ""
set -g mode_label "full"

# Parse args
set -l argv_remaining
for arg in $argv
    switch $arg
        case --check
            set mode_check 1
            set mode_label "check"
        case '--step=*'
            set mode_step (string replace -- '--step=' '' $arg)
            set mode_label "step"
        case --step
            # next arg is the step id — handled by loop below
            set -g _expect_step_arg 1
        case '*'
            if set -q _expect_step_arg
                set mode_step $arg
                set mode_label "step"
                set -e _expect_step_arg
            else
                set argv_remaining $argv_remaining $arg
            end
    end
end

function _info
    set_color cyan; echo "[$script_name] $argv"; set_color normal
end

function _warn
    set_color yellow; echo "[$script_name WARN] $argv"; set_color normal
end

function _error
    set_color red; echo "[$script_name ERROR] $argv"; set_color normal
end

function _step_header
    echo ""
    set_color --bold magenta
    echo "─── $argv ───"
    set_color normal
end

function _log
    mkdir -p $state_dir
    printf '%s %s\n' (date '+%Y-%m-%dT%H:%M:%S') "$argv" >> $log_file
end

function _mark_step
    # Legacy state-file write: step=status. Backward-compat with 0.2.x install.state schema.
    set -l step $argv[1]
    set -l status_val $argv[2]
    mkdir -p $state_dir
    if test -f $state_file
        grep -v "^$step=" $state_file > "$state_file.tmp"; or true
        mv "$state_file.tmp" $state_file
    end
    printf '%s=%s\n' $step $status_val >> $state_file
end

function _utc_now
    # ISO-8601 UTC timestamp
    date -u '+%Y-%m-%dT%H:%M:%SZ'
end

function _epoch_ms
    # Milliseconds since epoch (10-digit seconds * 1000 + ms)
    date '+%s%3N'
end

function _emit_jsonl
    # Emit one JSONL line to install-state.jsonl. Args:
    #   $1 step_id, $2 step_name, $3 check_command, $4 expected_state,
    #   $5 observed_state, $6 action_taken, $7 final_status,
    #   $8 started_at_utc, $9 completed_at_utc, $10 duration_ms,
    #   $11 remediation_command_if_any (may be empty)
    mkdir -p $jsonl_dir
    set -l step_id $argv[1]
    set -l step_name $argv[2]
    set -l check_command $argv[3]
    set -l expected_state $argv[4]
    set -l observed_state $argv[5]
    set -l action_taken $argv[6]
    set -l final_status $argv[7]
    set -l started_at $argv[8]
    set -l completed_at $argv[9]
    set -l duration_ms $argv[10]
    set -l remediation_cmd $argv[11]
    set -l mode $mode_label

    # Emit via python to handle JSON escaping correctly.
    python3 -c '
import json, sys
fields = sys.argv[1:]
keys = ["step_id","step_name","check_command","expected_state","observed_state",
        "action_taken","final_status","started_at_utc","completed_at_utc",
        "duration_ms","remediation_command_if_any","mode"]
d = dict(zip(keys, fields))
d["duration_ms"] = int(d["duration_ms"])
if d["remediation_command_if_any"] == "":
    d["remediation_command_if_any"] = None
print(json.dumps(d))
' "$step_id" "$step_name" "$check_command" "$expected_state" "$observed_state" "$action_taken" "$final_status" "$started_at" "$completed_at" "$duration_ms" "$remediation_cmd" "$mode" >> $jsonl_file
end

function _run_check_remediate
    # Args:
    #   $1 step_id (also used as legacy step_name for backward-compat)
    #   $2 step_human_name
    #   $3 expected_state (short prose)
    #   $4 check_command (fish snippet)
    #   $5 remediation_command (fish snippet, may be empty for probe-only)
    set -l step_id $argv[1]
    set -l step_name $argv[2]
    set -l expected $argv[3]
    set -l check_cmd $argv[4]
    set -l remediate_cmd $argv[5]

    # --step <id> mode: skip everything except the named step
    if test "$mode_label" = "step"
        if test "$step_id" != "$mode_step"
            return 0
        end
    end

    _step_header "$step_id — $step_name"

    set -l started_at (_utc_now)
    set -l t0 (_epoch_ms)

    # 1. Check phase
    eval $check_cmd > /dev/null 2>&1
    set -l check_status $status

    if test $check_status -eq 0
        # Already satisfied
        set -l t1 (_epoch_ms)
        set -l completed_at (_utc_now)
        set -l dur (math $t1 - $t0)
        _emit_jsonl $step_id $step_name "$check_cmd" "$expected" "satisfied" "none" "satisfied" "$started_at" "$completed_at" "$dur" ""
        _mark_step $step_id pass
        _log "SATISFIED $step_id"
        _info "  satisfied (check passed)"
        return 0
    end

    # 2. Check failed
    if test "$mode_check" -eq 1
        # --check mode: never remediate
        set -l t1 (_epoch_ms)
        set -l completed_at (_utc_now)
        set -l dur (math $t1 - $t0)
        _emit_jsonl $step_id $step_name "$check_cmd" "$expected" "missing_or_drifted" "skipped_check_only" "check_only_fail" "$started_at" "$completed_at" "$dur" ""
        _log "CHECK_FAIL $step_id (check-only mode; no remediation)"
        _warn "  check failed (check-only mode; not remediating)"
        return 1
    end

    # 3. Remediation phase
    if test -z "$remediate_cmd"
        # Probe-only step with no remediation
        set -l t1 (_epoch_ms)
        set -l completed_at (_utc_now)
        set -l dur (math $t1 - $t0)
        _emit_jsonl $step_id $step_name "$check_cmd" "$expected" "missing_no_remediation" "none" "remediation_failed" "$started_at" "$completed_at" "$dur" ""
        _mark_step $step_id fail
        _log "PROBE_FAIL $step_id (no remediation defined)"
        _warn "  probe-only step failed; no remediation defined"
        return 1
    end

    _info "  check failed; remediating via: $remediate_cmd"
    eval $remediate_cmd 2>&1
    set -l remediate_status $status

    # 4. Re-check phase
    eval $check_cmd > /dev/null 2>&1
    set -l recheck_status $status

    set -l t1 (_epoch_ms)
    set -l completed_at (_utc_now)
    set -l dur (math $t1 - $t0)

    if test $recheck_status -eq 0
        _emit_jsonl $step_id $step_name "$check_cmd" "$expected" "remediated" "remediated" "remediated" "$started_at" "$completed_at" "$dur" "$remediate_cmd"
        _mark_step $step_id pass
        _log "REMEDIATED $step_id"
        _info "  remediated (re-check passed)"
        return 0
    end

    _emit_jsonl $step_id $step_name "$check_cmd" "$expected" "still_drifted_after_remediation" "remediation_failed" "remediation_failed" "$started_at" "$completed_at" "$dur" "$remediate_cmd"
    _mark_step $step_id fail
    _log "REMEDIATION_FAILED $step_id (re-check still fails after remediate exit $remediate_status)"
    _error "  remediation failed (re-check still fails)"
    return 1
end

# ─────────────────────────────────────────────────────────────────────────
# Platform check (always runs; not a resumable step)
# ─────────────────────────────────────────────────────────────────────────

if not test -f /etc/arch-release
    _error "Arch Linux required (/etc/arch-release not found). Halt."
    exit 1
end

if not type -q fish
    _error "fish shell required. Halt."
    exit 1
end

if test (uname -m) != "x86_64"
    _error "x86_64 required. Halt."
    exit 1
end

_info "Platform: Arch Linux + fish + x86_64. OK."
_info "Project root: $project_root"
_info "Mode: $mode_label"
if test "$mode_label" = "step"
    _info "Step filter: $mode_step"
end
_log "START install.fish (mode=$mode_label)"

# ─────────────────────────────────────────────────────────────────────────
# Step definitions
#
# Per amendment §D1: check_command runs first; if non-zero exit, remediate
# (existing wrapper install path) and re-check. JSONL line written per step.
# ─────────────────────────────────────────────────────────────────────────

set -l fail_count 0

# 1. pacman packages
_run_check_remediate \
    pacman "Pacman packages declared in artifacts/harness/pacman-packages.txt" \
    "all declared packages installed" \
    "$project_root/bin/aho-pacman status" \
    "$project_root/bin/aho-pacman install"
or set fail_count (math $fail_count + 1)

# 2. AUR packages
_run_check_remediate \
    aur "AUR packages declared in artifacts/harness/aur-packages.txt" \
    "all declared AUR packages installed" \
    "$project_root/bin/aho-aur status" \
    "$project_root/bin/aho-aur install"
or set fail_count (math $fail_count + 1)

# 3. Python (aho package editable install)
_run_check_remediate \
    python "aho Python package importable (editable install)" \
    "python3 -c 'import aho' succeeds" \
    "python3 -c 'import aho' 2>/dev/null" \
    "$project_root/bin/aho-python install"
or set fail_count (math $fail_count + 1)

# 4. Ollama models
_run_check_remediate \
    models "Ollama models per artifacts/harness/model-fleet.txt for tier" \
    "tier-appropriate models loaded" \
    "$project_root/bin/aho-models status" \
    "$project_root/bin/aho-models install"
or set fail_count (math $fail_count + 1)

# 4a. Ollama service running (fine-grained probe so aho-doctor can verify
#     independently of the models step's remediation cascade)
_run_check_remediate \
    ollama_running "Ollama service responds on http://localhost:11434" \
    "ollama API reachable" \
    "curl -sf -m 5 http://localhost:11434/api/tags > /dev/null" \
    "systemctl is-active ollama.service > /dev/null 2>&1; or sudo systemctl start ollama.service"
or set fail_count (math $fail_count + 1)

# 4b. llama3.2:3b model present
_run_check_remediate \
    llama_3_2_3b_present "Ollama has llama3.2:3b loaded (base-tier auditor seat)" \
    "ollama list shows llama3.2:3b" \
    "curl -sf -m 5 http://localhost:11434/api/tags 2>/dev/null | grep -q '\"llama3.2:3b\"'" \
    "ollama pull llama3.2:3b"
or set fail_count (math $fail_count + 1)

# 4c. nomic-embed-text present
_run_check_remediate \
    nomic_embed_present "Ollama has nomic-embed-text loaded (council embed seat)" \
    "ollama list shows nomic-embed-text" \
    "curl -sf -m 5 http://localhost:11434/api/tags 2>/dev/null | grep -q '\"nomic-embed-text'" \
    "ollama pull nomic-embed-text"
or set fail_count (math $fail_count + 1)

# 5. Secrets broker init
_run_check_remediate \
    secrets "aho-secrets-broker.service exists + active" \
    "systemctl --user is-active aho-secrets-broker.service == active" \
    "systemctl --user is-active aho-secrets-broker.service 2>/dev/null | grep -q '^active\$'" \
    "$project_root/bin/aho-secrets-init"
or set fail_count (math $fail_count + 1)

# 5a. Broker socket present (independent fine-grained probe)
_run_check_remediate \
    broker_socket_present "broker unix socket present at canonical XDG path" \
    "\$XDG_RUNTIME_DIR/aho-secrets.sock exists as a socket" \
    "test -S \"\$XDG_RUNTIME_DIR/aho-secrets.sock\"" \
    "systemctl --user start aho-secrets-broker.service"
or set fail_count (math $fail_count + 1)

# 6. MCP servers
_run_check_remediate \
    mcp "MCP server config + binaries present" \
    "aho-mcp status returns clean" \
    "$project_root/bin/aho-mcp status" \
    "$project_root/bin/aho-mcp install"
or set fail_count (math $fail_count + 1)

# 7. systemd user services
_run_check_remediate \
    systemd "aho-managed systemd user units installed" \
    "aho-systemd status returns clean" \
    "$project_root/bin/aho-systemd status" \
    "$project_root/bin/aho-systemd install"
or set fail_count (math $fail_count + 1)

# 8. Symlinks of bin/aho-* into ~/.local/bin
_run_check_remediate \
    symlinks "bin/aho-* wrappers symlinked into ~/.local/bin" \
    "every non-bootstrap wrapper present as ~/.local/bin/<wrapper>" \
    "test -L $HOME/.local/bin/aho-pacman; and test -L $HOME/.local/bin/aho-models; and test -L $HOME/.local/bin/aho-doctor" \
    "
mkdir -p $HOME/.local/bin
for wrapper in (command ls $project_root/bin/)
    if test \"\$wrapper\" = aho-bootstrap; or test \"\$wrapper\" = aho-uninstall
        continue
    end
    ln -sf \"$project_root/bin/\$wrapper\" \"$HOME/.local/bin/\$wrapper\"
end
"
or set fail_count (math $fail_count + 1)

# 9. tier.json present (D1 amendment add — was implicit in 0.2.18 W2 carry-forward)
#    W1 remediation = minimal viable tier-detect-and-write (W2 expands per
#    F-0.2.18-W2-003 closure into `aho install tier-manifest` subcommand).
_run_check_remediate \
    tier_json_present "~/.config/aho/tier.json exists with required keys" \
    "tier.json present with host_id + tier + bundle keys" \
    "test -f $HOME/.config/aho/tier.json; and python3 -c 'import json; d=json.load(open(\"$HOME/.config/aho/tier.json\")); assert all(k in d for k in [\"host_id\",\"tier\",\"bundle\"])' 2>/dev/null" \
    "
mkdir -p $HOME/.config/aho
python3 -c '
import json, os, subprocess, socket
host = socket.gethostname().split(\".\")[0]
# Probe for NVIDIA GPU
try:
    out = subprocess.run([\"nvidia-smi\", \"--query-gpu=memory.total\", \"--format=csv,noheader,nounits\"], capture_output=True, text=True, timeout=5)
    vram_mb = int(out.stdout.strip().split(\"\\n\")[0]) if out.returncode == 0 else 0
except Exception:
    vram_mb = 0
vram_gb = vram_mb // 1024 if vram_mb else 0
if vram_gb >= 32: tier, bundle = \"full\", [\"qwen3.5:9b\",\"glm-4.6v:flash\",\"nomic-embed-text\"]
elif vram_gb >= 12: tier, bundle = \"partial\", [\"qwen3.5:9b\",\"nomic-embed-text\"]
else: tier, bundle = \"base\", [\"llama3.2:3b\",\"nomic-embed-text\"]
d = {
    \"host_id\": host,
    \"tier\": tier,
    \"deployment_mode\": \"production\",
    \"families\": [\"llama3\" if tier == \"base\" else \"qwen3\", \"nomic\"],
    \"bundle\": bundle,
    \"rationale\": f\"auto-detected by install.fish (vram_gb={vram_gb}); W2 expands per F-0.2.18-W2-003 closure\",
    \"vram_gb\": vram_gb,
}
p = os.path.expanduser(\"~/.config/aho/tier.json\")
with open(p, \"w\") as f: json.dump(d, f, indent=2)
print(f\"wrote {p}: tier={tier}\")
'
"
or set fail_count (math $fail_count + 1)

# 10. chromadb importable (W0 D9 substrate-prerequisite gap)
_run_check_remediate \
    chromadb_importable "chromadb Python module importable in host Python" \
    "python3 -c 'import chromadb' succeeds" \
    "python3 -c 'import chromadb' 2>/dev/null" \
    "python3 -m pip install --user --break-system-packages chromadb"
or set fail_count (math $fail_count + 1)

# 11. canonical-root checkpoint present (closes F-0.3.1-W0-004)
_run_check_remediate \
    canonical_checkpoint_present "~/.aho-checkpoint.json present at canonical project root" \
    ".aho-checkpoint.json exists at $project_root with current_iteration set" \
    "test -f $project_root/.aho-checkpoint.json" \
    "
python3 -c '
import json, os, datetime
p = os.path.expanduser(\"$project_root/.aho-checkpoint.json\")
iteration = os.environ.get(\"AHO_ITERATION\", \"0.3.1\")
workstream = os.environ.get(\"AHO_WORKSTREAM\", \"W1\")
ckpt = {
    \"iteration\": iteration,
    \"phase\": 0,
    \"run_type\": \"adversarial-authorship\",
    \"current_workstream\": workstream,
    \"workstreams\": {},
    \"executor\": \"claude-code\",
    \"auditor\": \"llama3.2:3b\",
    \"started_at\": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    \"last_event\": None,
    \"status\": \"active\",
    \"proceed_awaited\": False
}
with open(p, \"w\") as f:
    json.dump(ckpt, f, indent=2)
    f.write(\"\\n\")
print(f\"wrote {p}\")
'
"
or set fail_count (math $fail_count + 1)

# 12. python sys.path clean (W1 probe; W2 remediates) — closes F-0.3.1-W0-005 partially
_run_check_remediate \
    python_sys_path_clean "Python sys.path has no legacy pre-migration aho/src entry (configurable via \$AHO_SYS_PATH_LEGACY_MARKER)" \
    "sys.path does not include legacy pre-migration path" \
    "python3 -c 'import sys; assert not any(\"/dev/projects/aho/src\" in p for p in sys.path), \"legacy path in sys.path\"' 2>/dev/null" \
    ""
or set fail_count (math $fail_count + 1)

# 13. chromadb collection populated (closes F-0.3.1-W0-002)
_run_check_remediate \
    chromadb_collection_populated "Per-project ChromaDB iteration-context collection has non-zero docs" \
    "aho.rag.collection_count(project) > 0 for active project (\$AHO_PROJECT or ahomw default)" \
    "PYTHONPATH=$project_root/src python3 -c '
import os, sys
from aho.rag import collection_count
project = os.environ.get(\"AHO_PROJECT\", \"ahomw\")
n = collection_count(project)
print(f\"collection_count({project})={n}\")
assert n > 0, f\"collection empty (count={n})\"
' 2>/dev/null" \
    "$project_root/bin/aho-rag-bootstrap --quiet"
or set fail_count (math $fail_count + 1)

# 13a. Substrate-freshness probe set ran in the recent past (W1 D4 step
#      so the doctor + dashboard have fresh-enough data).
_run_check_remediate \
    substrate_facts_probed_recently "Substrate-freshness probes ran within last 24h" \
    "observables.jsonl mtime within 24h" \
    "test -f $HOME/.local/share/aho/observables.jsonl; and python3 -c 'import os,time,pathlib; assert (time.time() - pathlib.Path(os.path.expanduser(\"~/.local/share/aho/observables.jsonl\")).stat().st_mtime) < 86400' 2>/dev/null" \
    "$project_root/bin/aho-probe-substrate --summary > /dev/null 2>&1"
or set fail_count (math $fail_count + 1)

# 14. doctor (aho doctor — gateway probe; preserves backward-compat with 0.2.x final step)
_run_check_remediate \
    doctor "aho doctor passes (gateway probe)" \
    "aho doctor exits 0" \
    "$HOME/.local/bin/aho doctor 2>/dev/null" \
    "$HOME/.local/bin/aho doctor"
or set fail_count (math $fail_count + 1)

# ─────────────────────────────────────────────────────────────────────────
# Done
# ─────────────────────────────────────────────────────────────────────────

_log "COMPLETE install.fish (mode=$mode_label, fail_count=$fail_count)"
_info "─────────────────────────────────────────────"
if test $fail_count -eq 0
    _info "aho install complete. all steps satisfied or remediated."
    exit 0
end
_warn "$fail_count step(s) failed. See $jsonl_file for structured output."
exit 1
