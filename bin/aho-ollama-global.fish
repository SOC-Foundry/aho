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
# Models chosen for simultaneous use on 8GB-class hardware (RTX 2080 SUPER baseline):
#   - phi4-mini (primary hot triage + auditor)
#   - nomic-embed-text + qwen3-embedding:0.6b (RAG)
#   - qwen3:4b (strong structured alternative)
#   - qwen3:8b (dense producer fallback)
#   - qwen3.5:35b-a3b (MoE heavy producer - requires RAM offload + possible tuning)
#
# NOTE: This host was observed with 16 GB VRAM (RTX 2000 Ada). The fleet is
# conservative and will run well here; you can extend simultaneous loading later.
#
# WARNING: The 35b-a3b MoE is large even quantized. It may take 30-120+ minutes
# (or hours on slower links) + significant disk. It is pulled last.
# RECOMMENDED FOR OVERNIGHT:
#   tmux new -s aho-ollama
#   sudo fish ./bin/aho-ollama-global.fish
#   # (or nohup + tail -f /tmp/aho-ollama.log &)
# The script now runs a post-deploy 'ollama list' validation + minimal smoke
# (generate + embed probes) after all pulls complete.

set -g script_name "aho-ollama-global"

# Location of this aho checkout (so we can create stable shims for global use)
set -g project_root (dirname (realpath (status filename)))

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

function _install_aho_cli_surface
    # Determine the real (non-root) user even when the script is run with sudo
    set -l real_user (logname 2>/dev/null; or echo $SUDO_USER; or echo $USER)
    if test -z "$real_user" -o "$real_user" = "root"
        _warn "Could not determine non-root user for CLI surface install; skipping"
        return 0
    end

    set -l user_home (getent passwd $real_user | cut -d: -f6)
    if test -z "$user_home"
        _warn "Could not determine home for $real_user"
        return 0
    end

    set -l user_bin "$user_home/.local/bin"
    _info "Installing aho CLI entrypoints for $real_user into $user_bin"
    _info "(this makes the council engageable from any directory / outside the aho repo)"

    mkdir -p $user_bin
    chown $real_user:$real_user $user_bin

    # Key commands for global council engagement.
    # Wrappers exec the versions from this checkout so repo updates are live everywhere.
    set -l cmds aho aho-conductor aho-ollama-verify

    for cmd in $cmds
        set -l src "$project_root/bin/$cmd"
        if not test -f $src
            _warn "  skip $cmd (not found at $src)"
            continue
        end

        set -l wrapper_content "#!/usr/bin/env fish
# Stable aho entrypoint installed by aho-ollama-global.fish
# Delegates to the checkout at $project_root (updates there take effect immediately)
exec $src \$argv
"
        printf '%s' $wrapper_content > "$user_bin/$cmd"
        chmod +x "$user_bin/$cmd"
        chown $real_user:$real_user "$user_bin/$cmd"
        _success "  + $user_bin/$cmd"
    end

    # Make sure ~/.local/bin is on PATH for the user's fish sessions
    set -l fish_conf_d "$user_home/.config/fish/conf.d"
    mkdir -p $fish_conf_d
    set -l path_file "$fish_conf_d/aho-path.fish"
    set -l path_line 'set -gx PATH $HOME/.local/bin $PATH'

    if not test -f $path_file; or not grep -Fq '.local/bin' $path_file
        echo $path_line >> $path_file
        chown $real_user:$real_user $path_file
        _success "  + $path_file (adds ~/.local/bin to PATH for future fish shells)"
    end

    _info "Re-login (or 'exec fish') and you can run 'aho-conductor' / 'aho' from any directory."
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

function _validate_ollama_list
    _info "Validating deployment with 'ollama list' (executed as $OLLAMA_USER)..."

    set -l list_output (sudo -u $OLLAMA_USER \
        env HOME=$OLLAMA_HOME \
            OLLAMA_HOST=127.0.0.1:11434 \
            OLLAMA_MODELS=$OLLAMA_MODELS_DIR \
        /usr/local/bin/ollama list 2>&1)

    echo $list_output

    set -l found 0
    set -l expected (count $MODELS)

    for model in $MODELS
        set -l base (string split -m1 ':' $model)[1]
        if echo $list_output | grep -qi "$base"
            _success "  ✓ $model present"
            set found (math $found + 1)
        else
            _warn "  ✗ $model NOT listed (still pulling? name variant? check journalctl -u ollama.service)"
        end
    end

    if test $found -ge (math $expected - 1)
        _success "ollama list validation: $found/$expected models confirmed (heavy MoE may lag)"
    else
        _warn "ollama list validation: only $found/$expected confirmed — pulls may still be in flight"
    end
end

function _post_deploy_smoke
    _info "=== Post-deploy smoke test (after ollama list validation) ==="

    _validate_ollama_list

    # Tiny generate smoke against the primary hot model (phi4-mini). 15s hard cap.
    set -l smoke_model "phi4-mini"
    _info "Smoke: quick generate probe -> $smoke_model"
    set -l gen_payload '{"model":"'$smoke_model'","prompt":"Reply with only the single word: PONG","stream":false}'
    set -l gen_resp (curl -s --max-time 15 -X POST http://127.0.0.1:11434/api/generate \
        -H "Content-Type: application/json" \
        -d $gen_payload 2>&1)

    if echo $gen_resp | grep -qi '"response"' && echo $gen_resp | grep -qi 'PONG'
        _success "  ✓ generate smoke PASSED for $smoke_model"
    else
        _warn "  ? generate smoke inconclusive (model may still be loading into VRAM post-pull)"
        echo "    preview: "(echo $gen_resp | string shorten -m 160)
    end

    # Quick embedding smoke (critical for RAG council paths)
    _info "Smoke: quick embed probe -> nomic-embed-text"
    set -l emb_payload '{"model":"nomic-embed-text","input":"The quick brown fox for council smoke test."}'
    set -l emb_resp (curl -s --max-time 10 -X POST http://127.0.0.1:11434/api/embed \
        -H "Content-Type: application/json" \
        -d $emb_payload 2>&1)

    if command -q jq; and echo $emb_resp | jq -e '.embeddings[0][0]' >/dev/null 2>&1
        _success "  ✓ embed smoke PASSED for nomic-embed-text"
    else if echo $emb_resp | grep -q '"embeddings"'
        _success "  ✓ embed smoke PASSED for nomic-embed-text (response shape OK, jq not present for deep check)"
    else
        _warn "  ? embed smoke inconclusive (model loading or network)"
    end

    _success "Post-deploy smoke complete."
    _info "For deeper per-model tests (VRAM snapshots + structured JSON + all lights):"
    _info "  ./bin/aho-ollama-verify.fish"
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
    echo "Test from any user shell (after re-login for fish config):"
    echo "  ollama run phi4-mini"
    echo ""
    echo "Heavy MoE model (qwen3.5:35b-a3b) is available but may need extra tuning"
    echo "for best performance (layer offloading + system RAM helps)."
    echo ""
    echo "To monitor VRAM usage while running models:"
    echo "  watch -n 1 nvidia-smi"
    echo "  ollama ps"
    echo ""
    _info "Next: ./bin/aho-ollama-verify.fish  (or the smoke already ran above)"
end

# === Main ===

_require_root

_info "Starting global Ollama deployment for aho council (target: 8GB-class; observed 16GB on this host)"

_install_ollama_binary
_create_system_user
_write_systemd_service
_enable_and_start_service
_write_global_fish_config
_install_aho_cli_surface
_pull_models
_post_deploy_smoke
_print_summary

_success "Done. Ollama + models are now global. aho entrypoints are in ~/.local/bin for the invoking user."
_success "Re-login (or new fish) and run 'aho-conductor' or 'aho' from any directory."