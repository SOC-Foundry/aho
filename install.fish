#!/usr/bin/env fish
# install.fish — Clone-to-deploy orchestrator for aho.
# 0.2.5 — Thin orchestrator. Every step delegates to a bin/aho-* wrapper.
# Pillar 4: wrappers are the tool surface.
#
# Usage: ./install.fish
# Resumes from last successful step via ~/.local/state/aho/install.state

set -g script_name "aho-install"
set -g project_root (dirname (realpath (status filename)))
set -g state_dir "$HOME/.local/state/aho"
set -g state_file "$state_dir/install.state"
set -g log_file "$state_dir/install.log"

function _info
    set_color cyan; echo "[$script_name] $argv"; set_color normal
end

function _error
    set_color red; echo "[$script_name ERROR] $argv"; set_color normal
end

function _step_header
    echo ""
    set_color --bold magenta
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  Step $argv"
    echo "═══════════════════════════════════════════════════════════════════"
    set_color normal
end

function _log
    mkdir -p $state_dir
    printf '%s %s\n' (date '+%Y-%m-%dT%H:%M:%S') "$argv" >> $log_file
end

function _mark_step
    set -l step $argv[1]
    set -l status_val $argv[2]
    mkdir -p $state_dir
    # Read existing state, update step, write back
    if test -f $state_file
        # Remove existing line for this step
        grep -v "^$step=" $state_file > "$state_file.tmp"; or true
        mv "$state_file.tmp" $state_file
    end
    printf '%s=%s\n' $step $status_val >> $state_file
end

function _step_done
    set -l step $argv[1]
    if test -f $state_file
        grep -q "^$step=pass" $state_file
        return $status
    end
    return 1
end

function _run_step
    set -l step_num $argv[1]
    set -l step_name $argv[2]
    set -l step_cmd $argv[3..-1]

    if _step_done $step_name
        _info "Step $step_num ($step_name): already complete, skipping."
        return 0
    end

    _step_header "$step_num: $step_name"
    _log "START $step_name"

    eval $step_cmd 2>&1
    set -l result $status

    if test $result -ne 0
        _mark_step $step_name fail
        _log "FAIL $step_name (exit $result)"
        _error "Step $step_num ($step_name) failed. Fix the issue and re-run install.fish."
        return 1
    end

    _mark_step $step_name pass
    _log "PASS $step_name"
    _info "Step $step_num ($step_name): done."
    return 0
end

# ─────────────────────────────────────────────────────────────────────────
# Platform check (not a resumable step — always runs)
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
_log "START install.fish"

# ─────────────────────────────────────────────────────────────────────────
# Steps 1–9
# ─────────────────────────────────────────────────────────────────────────

_run_step 1 pacman "$project_root/bin/aho-pacman install"; or exit 1
_run_step 2 aur "$project_root/bin/aho-aur install"; or exit 1
_run_step 3 python "$project_root/bin/aho-python install"; or exit 1
_run_step 4 models "$project_root/bin/aho-models install"; or exit 1
_run_step 5 secrets "$project_root/bin/aho-secrets-init"; or exit 1
_run_step 6 mcp "$project_root/bin/aho-mcp install"; or exit 1
_run_step 7 systemd "$project_root/bin/aho-systemd install"; or exit 1

# Step 8: Symlink bin wrappers
_run_step 8 symlinks "
    mkdir -p $HOME/.local/bin
    for wrapper in (command ls $project_root/bin/)
        if test \"\$wrapper\" = aho-bootstrap; or test \"\$wrapper\" = aho-uninstall
            continue
        end
        ln -sf \"$project_root/bin/\$wrapper\" \"$HOME/.local/bin/\$wrapper\"
    end
"; or exit 1

# Step 9: aho doctor
_run_step 9 doctor "aho doctor"; or exit 1

# ─────────────────────────────────────────────────────────────────────────
# Done
# ─────────────────────────────────────────────────────────────────────────

_log "COMPLETE install.fish"
_info "───────────────────────────────────────────"
_info "aho install complete. All 9 steps passed."
_info "───────────────────────────────────────────"
