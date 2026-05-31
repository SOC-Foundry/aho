#!/usr/bin/env fish
# aho-ollama-global.fish
# One-shot global Ollama deployment for multi-user use on this machine.
# - Installs Ollama system-wide via official script
# - Runs Ollama as a dedicated system user + systemd system service
# - Stores models in shared location (/var/lib/ollama)
# - Makes models available to all users via localhost:11434
# - Pulls the recommended council fleet for 8GB VRAM + 64GB RAM hardware
#
# Usage (from aho repo root):
#   ./bin/aho-ollama-global.fish
#
# After running, any user on this machine can do:
#   ollama list
#   ollama run phi4-mini
#
# All users inherit OLLAMA_HOST via /etc/fish/conf.d/ollama.fish
#
# Models chosen for simultaneous use on RTX 2080 SUPER 8GB:
#   - phi4-mini (primary hot triage + auditor)
#   - nomic-embed-text + qwen3-embedding:0.6b (RAG)
#   - qwen3:4b (strong structured alternative)
#   - qwen3:8b (dense producer fallback)
#   - qwen3.5:35b-a3b (MoE heavy producer - requires RAM offload + possible tuning)
#
# WARNING: The 35b-a3b MoE is large even quantized. It may take 30-90+ minutes
# and significant disk. It is pulled last and can be skipped if desired.

set -g script_name "aho-ollama-global"

set -g OLLAMA_USER "ollama"
set -g OLLAMA_HOME "/var/lib/ollama"
set -g OLLAMA_MODELS_DIR "$OLLAMA_HOME/.ollama"
set -g SERVICE_FILE "/etc/systemd/system/ollama.service"
set -g FISH_GLOBAL_CONF "/etc/fish/conf.d/ollama.fish"

# Recommended fleet for this hardware (simultaneous-friendly core + on-demand)
set -g MODELS \
    phi4-mini \
    nomic-embed-text \
    qwen3-embedding:0.6b \
    qwen3:4b \
    qwen3:8b \
    qwen3.5:35b-a3b

function _info
    set_color cyan; echo "[$script_name] $argv"; set_color normal
end

function _warn
    set_color yellow; echo "[$script_name WARN] $argv"; set_color normal
end

function _error
    set_color red; echo "[$script_name ERROR] $argv"; set_color normal
end

function _success
    set_color green; echo "[$script_name] $argv"; set_color normal
end

function _require_root
    if test (id -u) -ne 0
        _error "This script must be run with sudo or as root for system-wide installation."
        _error "Recommended: sudo fish ./bin/aho-ollama-global.fish"
        exit 1
    end
end

function _install_ollama_binary
    if command -q ollama
        _info "Ollama binary already present: "(command -v ollama)
        return 0
    end

    _info "Installing Ollama via official script..."
    curl -fsSL https://ollama.com/install.sh | sh
    if test $status -ne 0
        _error "Official Ollama install script failed"
        exit 1
    end
    _success "Ollama binary installed to /usr/local/bin/ollama"
end

function _create_system_user
    if id -u $OLLAMA_USER >/dev/null 2>&1
        _info "System user '$OLLAMA_USER' already exists"
    else
        _info "Creating system user '$OLLAMA_USER'..."
        useradd -r -s /bin/false -m -d $OLLAMA_HOME $OLLAMA_USER
        if test $status -ne 0
            _error "Failed to create $OLLAMA_USER system user"
            exit 1
        end
    end

    # Ensure home and models dir exist with correct ownership
    mkdir -p $OLLAMA_MODELS_DIR
    chown -R $OLLAMA_USER:$OLLAMA_USER $OLLAMA_HOME
    chmod 755 $OLLAMA_HOME
end

function _write_systemd_service
    _info "Writing systemd system service: $SERVICE_FILE"

    # Using printf to avoid heredoc
    set -l service_content '[Unit]
Description=Ollama Service (global, multi-user)
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/ollama serve
User='$OLLAMA_USER'
Group='$OLLAMA_USER'
Restart=always
RestartSec=3
Environment="HOME='$OLLAMA_HOME'"
Environment="OLLAMA_HOST=127.0.0.1:11434"
Environment="OLLAMA_MODELS='$OLLAMA_MODELS_DIR'"
# Optional: limit context if needed on 8GB
# Environment="OLLAMA_MAX_LOADED_MODELS=2"

[Install]
WantedBy=multi-user.target
'

    printf '%s\n' $service_content | tee $SERVICE_FILE > /dev/null
    if test $status -ne 0
        _error "Failed to write $SERVICE_FILE"
        exit 1
    end

    systemctl daemon-reload
    _success "Systemd service written and daemon-reloaded"
end

function _enable_and_start_service
    _info "Enabling and starting ollama system service..."

    # Stop any existing user-level ollama service for the current user (common conflict)
    set -l current_user (logname 2>/dev/null; or echo $USER)
    if test -n "$current_user"
        sudo -u $current_user systemctl --user stop ollama.service 2>/dev/null; or true
        sudo -u $current_user systemctl --user disable ollama.service 2>/dev/null; or true
    end

    systemctl enable --now ollama.service
    if test $status -ne 0
        _error "Failed to enable/start ollama.service"
        exit 1
    end

    # Give it a moment
    sleep 2

    if systemctl is-active --quiet ollama.service
        _success "Ollama system service is active"
    else
        _error "Service did not start cleanly. Check: journalctl -u ollama.service -xe"
        exit 1
    end
end

function _write_global_fish_config
    _info "Writing global fish config for all users: $FISH_GLOBAL_CONF"

    set -l fish_content '# Global Ollama configuration (written by aho-ollama-global.fish)
# Makes ollama available to every fish user on this machine
set -gx OLLAMA_HOST http://localhost:11434
'

    printf '%s\n' $fish_content | tee $FISH_GLOBAL_CONF > /dev/null
    if test $status -ne 0
        _warn "Failed to write global fish config (non-fatal)"
    else
        _success "Global fish users will now inherit OLLAMA_HOST"
    end
end

function _pull_models
    _info "Pulling recommended models as $OLLAMA_USER user..."
    _warn "This will take a long time (especially qwen3.5:35b-a3b)."

    for model in $MODELS
        _info "Pulling $model ..."
        sudo -u $OLLAMA_USER \
            env HOME=$OLLAMA_HOME \
                OLLAMA_HOST=127.0.0.1:11434 \
                OLLAMA_MODELS=$OLLAMA_MODELS_DIR \
            /usr/local/bin/ollama pull $model

        if test $status -eq 0
            _success "Pulled: $model"
        else
            _warn "Pull failed or incomplete for $model (continuing)"
        end
    end
end

function _print_summary
    echo ""
    _success "=== Global Ollama deployment complete ==="
    echo ""
    echo "Service status:"
    systemctl status ollama.service --no-pager | head -6
    echo ""
    echo "Models available to ALL users on this machine:"
    echo "  ollama list"
    echo ""
    echo "Test from any user shell:"
    echo "  ollama run phi4-mini"
    echo ""
    echo "Heavy MoE model (qwen3.5:35b-a3b) is available but may need extra tuning"
    echo "for best performance on 8GB VRAM (layer offloading + your 64GB RAM helps)."
    echo ""
    echo "To monitor VRAM usage while running models:"
    echo "  watch -n 1 nvidia-smi"
    echo "  ollama ps"
    echo ""
    _info "Next: run the simultaneous loading tests we discussed."
end

# === Main ===

_require_root

_info "Starting global Ollama deployment for aho council (8GB VRAM target)"

_install_ollama_binary
_create_system_user
_write_systemd_service
_enable_and_start_service
_write_global_fish_config
_pull_models
_print_summary

_success "Done. You can now log in as any user and use the council models."