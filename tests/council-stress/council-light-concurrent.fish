#!/usr/bin/env fish

function _vram
    nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader
end

function _timed_prompt
    set -l model $argv[1]
    set -l prompt $argv[2]
    set -l start (date +%s%N)

    set -l resp (curl -s --max-time 30 -X POST http://127.0.0.1:11434/api/generate \
        -H "Content-Type: application/json" \
        -d '{"model":"'$model'","prompt":"'$prompt'","stream":false,"keep_alive":"5m"}' | jq -r '.response' 2>/dev/null | string shorten -m 80)

    set -l end (date +%s%N)
    set -l ms (math "($end - $start) / 1000000")

    echo "[$model] {$ms}ms : $resp"
end

echo "=== Lighter Concurrent Test ==="
echo "Baseline: " (_vram)

echo ""
echo "Loading light set: llama3.2:3b + nemotron-mini:4b + qwen3:8b + phi4:14b"
ollama run llama3.2:3b "hi" --keep-alive 5m > /dev/null 2>&1
ollama run nemotron-mini:4b "hi" --keep-alive 5m > /dev/null 2>&1
ollama run qwen3:8b "hi" --keep-alive 5m > /dev/null 2>&1
ollama run phi4:14b "hi" --keep-alive 5m > /dev/null 2>&1
sleep 2

echo "Loaded:"
ollama ps
echo "VRAM: " (_vram)

echo ""
echo "Concurrent short tasks on 4 models..."

_timed_prompt llama3.2:3b "Quick triage: login bug?"
_timed_prompt nemotron-mini:4b "Bug or feature: missing button"
_timed_prompt qwen3:8b "One sentence commit message for Safari fix"
_timed_prompt phi4:14b "Is adding sanitization safe? yes/no + one reason"

echo ""
echo "After concurrent:"
ollama ps
echo "VRAM: " (_vram)
