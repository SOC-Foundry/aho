#!/usr/bin/env fish
# aho-ollama-verify.fish
# Functional smoke tests for the global Ollama council fleet on 8GB hardware.
#
# Usage:
#   ./bin/aho-ollama-verify.fish                 # Test the practical light core
#   ./bin/aho-ollama-verify.fish --all           # Test every model (including heavy ones)
#   ./bin/aho-ollama-verify.fish --model phi4-mini
#   ./bin/aho-ollama-verify.fish --quick         # Faster, lighter prompts only
#
# Features:
# - VRAM snapshots before/after each test using nvidia-smi
# - Basic response test + structured JSON test (critical for council)
# - Embedding vector test for embed models
# - Timing and clear pass/fail reporting
# - Safe for 8GB VRAM — warns on heavy models

set -g script_name "aho-ollama-verify"

set -g LIGHT_MODELS \
    phi4-mini \
    nomic-embed-text \
    qwen3-embedding:0.6b \
    qwen3:4b

set -g HEAVY_MODELS \
    qwen3:8b \
    qwen3.5:35b-a3b

set -g ALL_MODELS $LIGHT_MODELS $HEAVY_MODELS

set -g OLLAMA_HOST "http://localhost:11434"

# Defaults
set -g test_all 0
set -g quick_mode 0
set -g specific_model ""

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

function _vram_snapshot
    echo ""
    set_color --bold magenta; echo "─── VRAM Snapshot ───"; set_color normal
    nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader
    echo ""
    ollama ps
    echo ""
end

function _test_basic
    set -l model $argv[1]
    _info "Basic response test: $model"

    set -l start_time (date +%s)

    set -l response (ollama run $model "Hello. In one short sentence, what kind of model are you and what are you good at?" 2>&1 | head -5)

    set -l end_time (date +%s)
    set -l duration (math $end_time - $start_time)

    if test -n "$response"
        _success "Basic test passed in {$duration}s"
        echo "  Response preview: "(echo $response | string shorten -m 120)
    else
        _error "Basic test failed or empty response for $model"
        return 1
    end
end

function _test_structured
    set -l model $argv[1]
    _info "Structured JSON test: $model"

    set -l prompt 'Classify this as one of [bug, feature, docs, security]: "User reports login button does nothing on Safari". Output ONLY valid JSON with keys: category, confidence (0-100), brief_reason'

    set -l start_time (date +%s)

    set -l response (ollama run $model "$prompt" 2>&1)

    set -l end_time (date +%s)
    set -l duration (math $end_time - $start_time)

    # Basic validation: does it look like JSON and contain expected keys?
    if echo $response | grep -q '"category"' && echo $response | grep -q '"confidence"' && echo $response | grep -q '"brief_reason"'
        _success "Structured JSON test passed in {$duration}s"
        echo "  JSON preview: "(echo $response | string shorten -m 160)
    else
        _warn "Structured output may be malformed or incomplete for $model"
        echo "  Raw response: "(echo $response | string shorten -m 200)
        return 1
    end
end

function _test_embedding
    set -l model $argv[1]
    _info "Embedding test: $model"

    set -l start_time (date +%s)

    set -l result (curl -s --max-time 30 \
        -H "Content-Type: application/json" \
        -d '{"model": "'$model'", "input": "The quick brown fox jumps over the lazy dog for retrieval testing."}' \
        "$OLLAMA_HOST/api/embed" 2>&1)

    set -l end_time (date +%s)
    set -l duration (math $end_time - $start_time)

    if echo $result | jq -e '.embeddings[0][0]' >/dev/null 2>&1
        set -l first_five (echo $result | jq -c '.embeddings[0][0:5]')
        _success "Embedding test passed in {$duration}s"
        echo "  First 5 dims: $first_five"
    else
        _error "Embedding test failed for $model"
        echo "  Response: "(echo $result | string shorten -m 200)
        return 1
    end
end

function _test_model
    set -l model $argv[1]

    _info "=== Testing $model ==="

    _vram_snapshot

    set -l failed 0

    switch $model
        case "*embed*"
            # Embedding models
            _test_embedding $model; or set failed 1

        case "*"
            # Generative models
            _test_basic $model; or set failed 1

            if test $quick_mode -eq 0
                _test_structured $model; or set failed 1
            end
    end

    _vram_snapshot

    if test $failed -eq 0
        _success "All tests passed for $model"
    else
        _error "One or more tests failed for $model"
    end

    # Give Ollama a chance to unload if it wants
    sleep 2
end

function _parse_args
    for arg in $argv
        switch $arg
            case --all
                set test_all 1
            case --quick
                set quick_mode 1
            case '--model=*'
                set specific_model (string replace -- '--model=' '' $arg)
            case --model
                # next arg
                set -g _expect_model 1
            case '*'
                if set -q _expect_model
                    set specific_model $arg
                    set -e _expect_model
                end
        end
    end
end

# === Main ===

_parse_args $argv

_info "Starting Ollama council model verification"
_info "Target hardware: 8GB VRAM (RTX 2080 SUPER)"

_vram_snapshot

if test -n "$specific_model"
    _info "Testing single model: $specific_model"
    _test_model $specific_model
else if test $test_all -eq 1
    _info "Testing ALL models (light + heavy)"
    for model in $ALL_MODELS
        _test_model $model
    end
else
    _info "Testing practical light council core (recommended for 8GB)"
    for model in $LIGHT_MODELS
        _test_model $model
    end

    _warn "Heavy models (qwen3:8b + qwen3.5:35b-a3b) were skipped."
    _warn "Run with --all if you want to test them (expect high RAM usage and slow performance on 8GB)."
end

set_color --bold green
echo ""
echo "=== Verification run complete ==="
set_color normal

_vram_snapshot

_info "Tip: Keep your nvidia-smi + ollama ps watch running in another terminal while testing."