#!/usr/bin/env fish

echo "=== Cleaning slate ==="
ollama ps
echo "Forcing offload of everything..."
for m in (ollama ps 2>/dev/null | tail -n +2 | awk '{print $1}')
    curl -s -X POST http://127.0.0.1:11434/api/generate \
        -H "Content-Type: application/json" \
        -d '{"model":"'$m'","prompt":"","keep_alive":0,"stream":false}' > /dev/null 2>&1
end
sleep 6
echo "After cleanup:"
ollama ps
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader
