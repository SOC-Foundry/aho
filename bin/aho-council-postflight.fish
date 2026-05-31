#!/usr/bin/env fish
# aho-council-postflight.fish
# Idempotent post-flight cleanup for healthy council operation.
# Run this after council sessions to leave the machine in a good state for others.

set -g script_name "aho-council-postflight"

function _info
    set_color cyan; echo "[$script_name] $argv"; set_color normal
end

function _warn
    set_color yellow; echo "[$script_name WARN] $argv"; set_color normal
end

function _success
    set_color green; echo "[$script_name] $argv"; set_color normal
end

_info "Running post-flight cleanup..."

# Offload everything
set -l loaded (ollama ps 2>/dev/null | tail -n +2 | awk '{print $1}' | string trim)
if test (count $loaded) -gt 0
    _info "Offloading models: $loaded"
    for m in $loaded
        curl -s -X POST http://127.0.0.1:11434/api/generate \
            -H "Content-Type: application/json" \
            -d '{"model":"'$m'","prompt":"","keep_alive":0,"stream":false}' > /dev/null 2>&1
    end
    sleep 4
end

_success "All models offloaded"

# Final VRAM report
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader 2>/dev/null | head -1

_success "Post-flight complete. System should be in a clean state for other users/executors."
