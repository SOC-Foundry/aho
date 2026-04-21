"""R2 clean-state LRU eviction probe — W1 correction.

Runs against freshly restarted Ollama. Records VRAM and /api/ps after each step.
"""
import json
import subprocess
import time
import urllib.request
import urllib.error


def api_call(endpoint, payload=None, timeout=300):
    url = f"http://127.0.0.1:11434{endpoint}"
    if payload:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    else:
        req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"status": 200, "data": json.loads(resp.read())}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"status": e.code, "error": body}


def get_vram_mib():
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
        capture_output=True, text=True
    )
    return int(result.stdout.strip())


def get_ps():
    r = api_call("/api/ps")
    models = r.get("data", {}).get("models", [])
    return [
        {
            "name": m["name"],
            "size_vram_gb": round(m.get("size_vram", 0) / 1e9, 2),
            "context_length": m.get("context_length"),
        }
        for m in models
    ]


def load_model(name, keep_alive="5m"):
    t0 = time.monotonic()
    r = api_call("/api/chat", {
        "model": name,
        "messages": [{"role": "user", "content": "Say OK"}],
        "stream": False,
        "keep_alive": keep_alive,
        "options": {"num_ctx": 4096},
    })
    elapsed = round(time.monotonic() - t0, 2)
    if r["status"] == 200:
        content = r["data"].get("message", {}).get("content", "")[:100]
        return {"status": 200, "elapsed_s": elapsed, "response": content}
    return {"status": r["status"], "elapsed_s": elapsed, "error": r.get("error", "")[:200]}


def record_step(label, load_result=None):
    vram = get_vram_mib()
    ps = get_ps()
    step = {
        "label": label,
        "vram_mib": vram,
        "models_loaded": ps,
        "model_count": len(ps),
    }
    if load_result:
        step["load_result"] = load_result
    print(f"  {label}: VRAM={vram} MiB, models={[m['name'] for m in ps]}")
    if load_result:
        print(f"    load: status={load_result['status']}, elapsed={load_result.get('elapsed_s')}s")
    return step


steps = []

# Step 0: baseline (Nemotron auto-loaded from restart)
print("=== R2 Clean-State LRU Eviction Probe ===\n")
steps.append(record_step("Step 0: post-restart baseline"))

# Unload Nemotron for clean start
print("\nUnloading Nemotron...")
api_call("/api/chat", {
    "model": "nemotron-mini:4b",
    "messages": [{"role": "user", "content": "x"}],
    "stream": False,
    "keep_alive": 0,
})
time.sleep(5)
steps.append(record_step("Step 0b: after Nemotron unload"))

# Step 1: load Qwen (6.6GB)
print("\n--- Step 1: Load Qwen 3.5:9B ---")
r = load_model("qwen3.5:9b")
steps.append(record_step("Step 1: after Qwen load", r))

# Step 2: load Llama (2GB) — may force Qwen eviction
print("\n--- Step 2: Load Llama 3.2:3B ---")
r = load_model("llama3.2:3b")
steps.append(record_step("Step 2: after Llama load", r))

# Step 3: load GLM (8GB) — critical test
print("\n--- Step 3: Load GLM-4.6V-Flash-9B (CRITICAL) ---")
r = load_model("haervwe/GLM-4.6V-Flash-9B:latest")
steps.append(record_step("Step 3: after GLM load", r))

# Step 4: load Nemotron (2.7GB)
print("\n--- Step 4: Load Nemotron-mini:4b ---")
r = load_model("nemotron-mini:4b")
steps.append(record_step("Step 4: after Nemotron load", r))

# Step 5: request Qwen again — should reload
print("\n--- Step 5: Reload Qwen ---")
r = load_model("qwen3.5:9b")
steps.append(record_step("Step 5: after Qwen reload", r))

# Write results
output = {
    "probe_id": "R02-clean",
    "requirement": "R2 LRU eviction predictability (clean-state retest)",
    "context": "Post sudo systemctl restart ollama. Corrects W1 contaminated baseline.",
    "gpu": "NVIDIA GeForce RTX 2080 SUPER 8192 MiB",
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "steps": steps,
}

outpath = "/home/kthompson/dev/projects/aho/artifacts/iterations/0.2.15/ollama-probes/R02-clean.json"
with open(outpath, "w") as f:
    json.dump(output, f, indent=2)
print(f"\nWritten to {outpath}")
