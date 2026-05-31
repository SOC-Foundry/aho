#!/usr/bin/env fish

function _vram
    nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader
end

function _load_model
    set -l model $argv[1]
    echo "Loading $model..."
    curl -s -X POST http://127.0.0.1:11434/api/generate \
        -H "Content-Type: application/json" \
        -d '{"model":"'$model'","prompt":"hello","stream":false,"keep_alive":"30m"}' > /dev/null
end

function _timed_prompt
    set -l model $argv[1]
    set -l prompt $argv[2]
    set -l start (date +%s%N)

    set -l resp (curl -s --max-time 45 -X POST http://127.0.0.1:11434/api/generate \
        -H "Content-Type: application/json" \
        -d '{"model":"'$model'","prompt":"'$prompt'","stream":false,"keep_alive":"30m"}' | jq -r '.response' 2>/dev/null | string shorten -m 120)

    set -l end (date +%s%N)
    set -l ms (math "($end - $start) / 1000000")

    echo "[$model] {$ms}ms : $resp"
end

function _offload_all
    echo "Offloading all models..."
    for m in (ollama ps 2>/dev/null | tail -n +2 | awk '{print $1}')
        curl -s -X POST http://127.0.0.1:11434/api/generate \
            -H "Content-Type: application/json" \
            -d '{"model":"'$m'","prompt":"","keep_alive":0,"stream":false}' > /dev/null 2>&1
    end
    sleep 3
end

echo "=== Council Simultaneous Stress Test ==="
echo "Baseline VRAM: " (_vram)

echo ""
echo "=== Test 1: Light simultaneous council (llama3.2 + nemotron + qwen3:8b + phi4 + llava) ==="

_offload_all

_load_model llama3.2:3b
_load_model nemotron-mini:4b
_load_model qwen3:8b
_load_model phi4:14b
_load_model llava:13b

echo "Loaded models:"
ollama ps
echo "VRAM after load: " (_vram)

echo ""
echo "Firing concurrent short tasks..."

_timed_prompt llama3.2:3b "Classify this as triage or ignore: User reports login issue" &
_timed_prompt nemotron-mini:4b "Is this a bug or feature request? missing button" &
_timed_prompt qwen3:8b "Write a one-sentence commit message for fixing a Safari login bug" &
_timed_prompt phi4:14b "As an auditor, is this change safe? Added input sanitization" &
_timed_prompt llava:13b "Describe what you would look for in a screenshot of a broken login form" &

wait

echo ""
echo "After concurrent tasks:"
ollama ps
echo "VRAM: " (_vram)

_offload_all

echo ""
echo "=== Test 1 complete ==="
