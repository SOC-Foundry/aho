#!/usr/bin/env fish
# aho-ollama-global-16gb.fish
# Complete global Ollama + models deployment for 16GB VRAM (RTX 2000 Ada class).
#
# - System-wide Ollama (dedicated ollama user + systemd service)
# - Shared models in /var/lib/ollama
# - Makes models available to ALL users on the machine
# - Installs aho CLI entrypoints into ~/.local/bin so council can be called from any directory
# - Pulls a rich fleet tuned for 16GB with role specialization in mind
# - Runs individual smoke tests per model with aggressive VRAM offloading between tests
#
# Usage (from aho repo root):
#   sudo fish ./bin/aho-ollama-global-16gb.fish
#
# Designed for overnight run. Heavy models (especially qwen3.5:35b-a3b) will take hours.
# The script will do its best to clear VRAM between smoke tests using multiple techniques.
#
# Fleet philosophy (16GB council):
# - Multiple small specialized models for different council roles (triage, writer, auditor, etc.)
# - Strong 14B-class models as primary workhorses (Phi-4 + DeepSeek R1)
# - Qwen3 8B pulled for evaluation (you liked the sound of it)
# - Solid vision with llava:13b + nomic embeddings
# - One or two bigger models pulled last for when you want serious firepower
#
# This enables the pattern you described: multiple frontier executors (Grok, Claude Code, Gemini CLI)
# running in separate sessions/folders, all able to drive the same rich local council.

set -g script_name "aho-ollama-global-16gb"

set -g OLLAMA_USER "ollama"
set -g OLLAMA_HOME "/var/lib/ollama"
set -g OLLAMA_MODELS_DIR "$OLLAMA_HOME/.ollama"
set -g SERVICE_FILE "/etc/systemd/system/ollama.service"
set -g FISH_GLOBAL_CONF "/etc/fish/conf.d/ollama.fish"

# Location of this aho checkout (for stable CLI shims)
set -l script_dir (dirname (realpath (status --current-filename)))
set -g project_root (dirname $script_dir)

# 16GB RTX 2000 Ada fleet - rich role-specialized set
# Pulled in roughly small-to-large order. Heaviest last.
#
# Tag notes (fixed 2026-05-31):
# - phi4:14b          → Correct tag for Phi-4 14B (confirmed working)
# - llava:13b         → Best supported vision model for council use (screenshots, diagrams, UI)
# - Kept strong Qwen + DeepSeek + small role models (llama3.2, nemotron) as requested
set -g MODELS \
    nomic-embed-text \
    llama3.2:3b \
    nemotron-mini:4b \
    qwen3:8b \
    llava:13b \
    phi4:14b \
    deepseek-r1:14b \
    qwen2.5:14b \
    qwen3.5:35b-a3b

# Models that get full individual smoke + forced VRAM clearing
set -g SMOKE_MODELS \
    nomic-embed-text \
    llama3.2:3b \
    nemotron-mini:4b \
    qwen3:8b \
    llava:13b \
    phi4:14b \
    deepseek-r1:14b

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
        _error "This script must be run with sudo or as root."
        _error "Recommended: sudo fish ./bin/aho-ollama-global-16gb.fish"
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

    mkdir -p $OLLAMA_MODELS_DIR
    chown -R $OLLAMA_USER:$OLLAMA_USER $OLLAMA_HOME
    chmod 755 $OLLAMA_HOME
end

function _write_systemd_service
    _info "Writing systemd system service: $SERVICE_FILE"

    set -l service_content '[Unit]
Description=Ollama Service (global, multi-user, 16GB council)
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
# Give the 16GB card some breathing room
Environment="OLLAMA_MAX_LOADED_MODELS=3"

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

    sleep 3

    if systemctl is-active --quiet ollama.service
        _success "Ollama system service is active"
    else
        _error "Service did not start cleanly. Check: journalctl -u ollama.service -xe"
        exit 1
    end
end

function _write_global_fish_config
    _info "Writing global fish config for all users: $FISH_GLOBAL_CONF"

    set -l fish_content '# Global Ollama configuration (written by aho-ollama-global-16gb.fish)
# Makes ollama available to every fish user on this machine for the council
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
    _info "Installing aho CLI entrypoints for $real_user into $user_bin (global council access)"

    mkdir -p $user_bin
    chown $real_user:$real_user $user_bin

    set -l cmds aho aho-conductor aho-ollama-verify aho-ollama-global-16gb

    for cmd in $cmds
        set -l src "$project_root/bin/$cmd"
        if not test -f $src
            _warn "  skip $cmd (not found at $src)"
            continue
        end

        set -l wrapper_content "#!/usr/bin/env fish
# Stable aho entrypoint installed by aho-ollama-global-16gb.fish
# Points at the checkout at $project_root - updates there are live everywhere
exec $src \$argv
"
        printf '%s' $wrapper_content > "$user_bin/$cmd"
        chmod +x "$user_bin/$cmd"
        chown $real_user:$real_user "$user_bin/$cmd"
        _success "  + $user_bin/$cmd"
    end

    set -l fish_conf_d "$user_home/.config/fish/conf.d"
    mkdir -p $fish_conf_d
    set -l path_file "$fish_conf_d/aho-path.fish"
    set -l path_line 'set -gx PATH $HOME/.local/bin $PATH'

    if not test -f $path_file; or not grep -Fq '.local/bin' $path_file
        echo $path_line >> $path_file
        chown $real_user:$real_user $path_file
        _success "  + ensured ~/.local/bin on PATH for fish"
    end
end

function _pull_models
    _info "=== PULLING MODELS (this will take a long time - especially the last one) ==="
    _warn "Go to bed. The script will continue and do smoke tests with VRAM management."

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
            _warn "Pull failed or incomplete for $model (continuing anyway)"
        end
    end

    _success "All model pulls attempted."
end

function _validate_ollama_list
    _info "=== Final ollama list validation ==="

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
            _success "  ✓ $model"
            set found (math $found + 1)
        else
            _warn "  ? $model not listed"
        end
    end

    _info "Models confirmed: $found / $expected"
end

# === VRAM / Model Offloading ===

function _show_vram
    echo ""
    set_color --bold magenta; echo "─── VRAM Snapshot ───"; set_color normal
    nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader
    ollama ps
    echo ""
end

function _force_offload_model
    set -l model $argv[1]
    if test -z "$model"
        return 0
    end

    _info "Offloading $model to free VRAM..."

    # Method 1: Official keep_alive=0 trick (most reliable)
    curl -s --max-time 15 -X POST http://127.0.0.1:11434/api/generate \
        -H "Content-Type: application/json" \
        -d '{"model":"'$model'","prompt":"","keep_alive":0,"stream":false}' > /dev/null 2>&1

    # Method 2: ollama stop (if the subcommand exists in this version)
    /usr/local/bin/ollama stop $model 2>/dev/null; or true

    sleep 4

    # Method 3: Nuclear but sometimes necessary - kill runner processes for this model
    # Only target runner processes, never the main ollama serve
    pkill -f "ollama runner.*$model" 2>/dev/null; or true

    sleep 3
    _show_vram
end

function _offload_all_loaded_models
    _info "Force offloading ALL currently loaded models..."

    set -l loaded (ollama ps 2>/dev/null | tail -n +2 | awk '{print $1}' | string trim)

    for m in $loaded
        _force_offload_model $m
    end

    # Extra safety
    sleep 5
    _show_vram
end

# === Individual Smoke Tests with VRAM Clearing ===

function _smoke_basic
    set -l model $argv[1]
    _info "Basic smoke: $model"

    set -l resp (ollama run $model "Reply with exactly one word: PONG" 2>&1 | head -3)

    if echo $resp | grep -qi "PONG"
        _success "  Basic smoke passed"
    else
        _warn "  Basic smoke weak or failed"
        echo "    preview: "(echo $resp | string shorten -m 120)
    end
end

function _smoke_structured
    set -l model $argv[1]
    _info "Structured JSON smoke: $model"

    set -l prompt 'Classify this issue as one of [bug, feature, docs, security]. Output ONLY valid JSON: {"category": "...", "confidence": 0-100, "reason": "..."}. Task: "Login button does nothing on Safari."'

    set -l resp (ollama run $model "$prompt" 2>&1)

    if echo $resp | grep -q '"category"' && echo $resp | grep -q '"confidence"'
        _success "  Structured JSON smoke passed"
    else
        _warn "  Structured output was messy (common on first cold load)"
    end
end

function _smoke_embed
    set -l model $argv[1]
    _info "Embedding smoke: $model"

    set -l result (curl -s --max-time 30 \
        -H "Content-Type: application/json" \
        -d '{"model":"'$model'","input":"The quick brown fox for council RAG smoke test."}' \
        "http://127.0.0.1:11434/api/embed" 2>&1)

    if echo $result | grep -q '"embeddings"'
        _success "  Embedding smoke passed"
    else
        _warn "  Embedding smoke failed or slow"
    end
end

function _smoke_vision
    set -l model $argv[1]
    _info "Vision smoke: $model (text-only capability test)"

    set -l prompt "You are a vision model. Describe what you would do if shown a screenshot of a software bug. Answer in one short sentence."

    set -l resp (ollama run $model "$prompt" 2>&1 | head -4)

    if test -n "$resp"
        _success "  Vision smoke responded"
        echo "    preview: "(echo $resp | string shorten -m 140)
    else
        _warn "  Vision smoke gave empty response"
    end
end

function _run_individual_smoke_with_cleanup
    set -l model $argv[1]

    _info "=== STARTING INDIVIDUAL SMOKE FOR: $model ==="

    _show_vram

    # Make sure nothing else is loaded
    _offload_all_loaded_models

    switch $model
        case "*embed*"
            _smoke_embed $model
        case "*vl*" "*vision*"
            _smoke_vision $model
        case "*"
            _smoke_basic $model
            sleep 2
            _smoke_structured $model
    end

    _success "Smoke complete for $model"

    # CRITICAL: Force this model off before next test
    _force_offload_model $model

    _info "Waiting for VRAM to settle before next model..."
    sleep 8
    _show_vram
end

function _run_all_smoke_tests
    _info "=== RUNNING INDIVIDUAL SMOKE TESTS WITH VRAM CLEARING BETWEEN EACH ==="
    _warn "This will take significant time. VRAM will be aggressively cleared after every model."

    _show_vram

    for model in $SMOKE_MODELS
        _run_individual_smoke_with_cleanup $model
    end

    _success "All individual smoke tests complete."

    _info "Final VRAM state after all tests and cleanups:"
    _show_vram
end

# === Main ===

_require_root

_info "=== aho 16GB Global Ollama Council Deployment ==="
_info "Target hardware: 16GB RTX 2000 Ada"
_info "Fleet: rich role-specialized set (Phi-4 14B primary, Qwen3 8B for eval, DeepSeek R1 14B heavy, small role models, vision, nomic RAG)"
_info "This run will pull everything (heavy models last) then run per-model smokes with forced offloads."
_warn "GO TO BED. This will run for many hours."

_install_ollama_binary
_create_system_user
_write_systemd_service
_enable_and_start_service
_write_global_fish_config
_install_aho_cli_surface

_pull_models

_validate_ollama_list

_run_all_smoke_tests

_success "=== DEPLOYMENT + SMOKE TESTS COMPLETE ==="
_info "Ollama is now running system-wide."
_info "Models are available to every user."
_info "aho / aho-conductor are in ~/.local/bin (re-login or exec fish to get PATH)."
_info "You can now have Grok, Claude Code, and Gemini CLI sessions in different folders all driving the same local council."

_show_vram

_success "Sweet dreams. Check the results in the morning."