#!/usr/bin/env fish
# aho-council-preflight.fish
# Idempotent pre-flight checks for healthy council operation.
# Run this before starting significant council work.

set -g script_name "aho-council-preflight"

function _info
    set_color cyan; echo "[$script_name] $argv"; set_color normal
end

function _warn
    set_color yellow; echo "[$script_name WARN] $argv"; set_color normal
end

function _success
    set_color green; echo "[$script_name] $argv"; set_color normal
end

function _error
    set_color red; echo "[$script_name ERROR] $argv"; set_color normal
end

function _vram
    nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader 2>/dev/null || echo "nvidia-smi unavailable"
end

_info "Running pre-flight checks for council..."

# 0. Machine bootstrap state (new fresh-start installer)
set -l root_install "$HOME/Development/Projects/socfoundry/aho/install.fish"
if test -x "$root_install"
    _info "Checking machine bootstrap state via install.fish --check..."
    "$root_install" --check >/dev/null 2>&1
    if test -f "$HOME/.local/share/aho/install-state.jsonl"
        set -l fails (grep -c '"status": "fail"' "$HOME/.local/share/aho/install-state.jsonl" 2>/dev/null || echo 0)
        if test $fails -gt 0
            _warn "install.fish reports $fails failing checks. Run ./install.fish or ./install.fish --step <id> to remediate."
        else
            _success "Machine bootstrap state healthy (per install.fish)"
        end
    end
else
    _warn "Root install.fish not found. Consider running it for full machine bootstrap."
end

# 1. Ollama service
if not systemctl is-active --quiet ollama.service 2>/dev/null
    _error "Ollama service is not active"
    exit 1
end
_success "Ollama service is active"

# 2. Clean loaded models (we want a known state)
set -l loaded (ollama ps 2>/dev/null | tail -n +2 | awk '{print $1}' | string trim)
if test (count $loaded) -gt 0
    _warn "Models currently loaded: $loaded"
    _info "Forcing offload for clean pre-flight state..."
    for m in $loaded
        curl -s -X POST http://127.0.0.1:11434/api/generate \
            -H "Content-Type: application/json" \
            -d '{"model":"'$m'","prompt":"","keep_alive":0,"stream":false}' > /dev/null 2>&1
    end
    sleep 3
end
_success "No models left resident"

# 3. VRAM check (16GB card)
set -l vram (nvidia-smi --query-gpu=memory.used --format=csv,noheader 2>/dev/null | string replace " MiB" "" | string trim)
if test -n "$vram"
    if test $vram -gt 4000
        _warn "VRAM usage is high: {$vram} MiB. Consider investigating before heavy council work."
    else
        _success "VRAM usage looks reasonable: {$vram} MiB"
    end
end

# 4. Quick health ping on core small models
for model in llama3.2:3b nemotron-mini:4b
    if not ollama run $model "ping" --keep-alive 1m > /dev/null 2>&1
        _warn "$model did not respond quickly"
    else
        _success "$model responsive"
    end
end

_success "Pre-flight checks passed"
