#!/usr/bin/env fish

set -g LOGFILE /tmp/council-stress-results-$(date +%Y%m%d-%H%M).log

function log
    echo $argv | tee -a $LOGFILE
end

function vram
    nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader
end

function timed_prompt
    set -l model $argv[1]
    set -l prompt $argv[2]
    set -l start (date +%s%N)
    set -l resp (curl -s --max-time 45 -X POST http://127.0.0.1:11434/api/generate \
        -H "Content-Type: application/json" \
        -d '{"model":"'$model'","prompt":"'$prompt'","stream":false,"keep_alive":"5m"}' | jq -r '.response' 2>/dev/null | string shorten -m 100)
    set -l end (date +%s%N)
    set -l ms (math "($end - $start) / 1000000")
    echo "[$model] {$ms}ms"
    echo "    $resp"
end

function force_load
    set -l model $argv[1]
    echo "Loading $model..."
    curl -s -X POST http://127.0.0.1:11434/api/generate \
        -H "Content-Type: application/json" \
        -d '{"model":"'$model'","prompt":"warmup","stream":false,"keep_alive":"10m"}' > /dev/null
end

function offload_all
    for m in (ollama ps 2>/dev/null | tail -n +2 | awk '{print $1}')
        curl -s -X POST http://127.0.0.1:11434/api/generate \
            -H "Content-Type: application/json" \
            -d '{"model":"'$m'","prompt":"","keep_alive":0,"stream":false}' > /dev/null 2>&1
    end
    sleep 4
end

echo "=== Council Roster Discovery Stress Tests ===" | tee $LOGFILE
date | tee -a $LOGFILE
echo "Hardware: RTX 2000 Ada 16GB" | tee -a $LOGFILE
echo "" | tee -a $LOGFILE

offload_all
echo "Baseline VRAM: "(vram) | tee -a $LOGFILE

echo ""
echo "=== Scenario A: Fast Trio + qwen3:8b fallback (llama3.2 + nemotron + qwen3:8b) ===" | tee -a $LOGFILE
force_load llama3.2:3b
force_load nemotron-mini:4b
force_load qwen3:8b
echo "Loaded:" | tee -a $LOGFILE
ollama ps | tee -a $LOGFILE
echo "VRAM: "(vram) | tee -a $LOGFILE

echo "Concurrent quick tasks:" | tee -a $LOGFILE
timed_prompt llama3.2:3b "Triage: login broken on Safari?" | tee -a $LOGFILE
timed_prompt nemotron-mini:4b "Bug or feature: missing button?" | tee -a $LOGFILE
timed_prompt qwen3:8b "One sentence commit message for Safari login fix" | tee -a $LOGFILE

offload_all

echo ""
echo "=== Scenario B: Fast trio + deepseek-r1:14b (primary reasoner) ===" | tee -a $LOGFILE
force_load llama3.2:3b
force_load nemotron-mini:4b
force_load qwen3:8b
force_load deepseek-r1:14b
echo "Loaded:" | tee -a $LOGFILE
ollama ps | tee -a $LOGFILE
echo "VRAM: "(vram) | tee -a $LOGFILE

echo "Concurrent tasks under pressure:" | tee -a $LOGFILE
timed_prompt llama3.2:3b "Quick triage" | tee -a $LOGFILE
timed_prompt nemotron-mini:4b "Bug or feature?" | tee -a $LOGFILE
timed_prompt qwen3:8b "Short commit message" | tee -a $LOGFILE
timed_prompt deepseek-r1:14b "Is adding input sanitization safe? one sentence" | tee -a $LOGFILE

offload_all

echo ""
echo "=== Results logged to $LOGFILE ===" | tee -a $LOGFILE
cat $LOGFILE
