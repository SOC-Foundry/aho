#!/usr/bin/env fish
# aho-test-remote-intel-vram.fish
# Smoke test for Intel Arc iGPU / NPU offloading on Lunar Lake (Ultra 7 268V class)
# 
# Usage:
#   Local test (on the machine itself):
#     ./aho-test-remote-intel-vram.fish
#     ./aho-test-remote-intel-vram.fish localhost
# 
#   Remote test (from another machine):
#     ./aho-test-remote-intel-vram.fish user@hostname

set -l host $argv[1]

function _run_test_locally
    echo "=== Running LOCAL Intel Arc iGPU / NPU test on $(hostname) ==="
    echo "Date: $(date)"
    echo ""

    set -l models (ollama list 2>/dev/null | tail -n +2 | awk "{print \$1}" | string trim)

    if test (count $models) -eq 0
        echo "No models found via ollama list."
        return 1
    end

    echo "Models found:"
    for m in $models
        echo "  - $m"
    end
    echo ""

    # Try to get intel_gpu_top
    set -l gpu_tool ""
    if command -q intel_gpu_top
        set gpu_tool (command -v intel_gpu_top)
    else
        echo "intel_gpu_top not found. Trying to install intel-gpu-tools..."
        if sudo pacman -S --noconfirm intel-gpu-tools >/dev/null 2>&1
            or command -q yay; and yay -S --noconfirm intel-gpu-tools >/dev/null 2>&1
            echo "Installed intel-gpu-tools."
            hash -r 2>/dev/null; or true
            if command -q intel_gpu_top
                set gpu_tool (command -v intel_gpu_top)
            else if test -x /usr/bin/intel_gpu_top
                set gpu_tool /usr/bin/intel_gpu_top
            end
        else
            echo "Could not install intel-gpu-tools automatically."
        end
    end

    if test -n "$gpu_tool"
        echo "Using GPU monitor: $gpu_tool"
    else
        echo "WARNING: intel_gpu_top is not available. GPU utilization data will be limited."
    end

    echo ""
    echo "Note: This is a Lunar Lake machine (Intel Core Ultra 7 268V + Arc 140V)."
    echo "It uses unified on-package memory. There is no separate VRAM."
    echo "btop rarely shows useful GPU data here. intel_gpu_top is the right tool."
    echo ""

    for model in $models
        echo "=== Testing: $model ==="
        echo "Running short inference (GPU preference)..."
        env OLLAMA_INTEL_GPU=1 timeout 30 ollama run $model "Say exactly: PONG" 2>&1 | tail -4

        echo ""
        if test -n "$gpu_tool"
            echo "GPU activity (5s sample):"
            timeout 6 $gpu_tool -s 1000 -o - 2>/dev/null | head -12 || echo "intel_gpu_top returned no data (this can happen on some Lunar Lake configs)"
        else
            echo "Skipping detailed GPU sampling."
        end

        echo ""
        echo "Memory:"
        free -h | grep -E "Mem:|Swap:"

        echo ""
        echo "Currently loaded in Ollama:"
        ollama ps 2>/dev/null || echo "ollama ps unavailable"

        echo "---------------------------------------------"
        echo ""
    end

    echo "Local test complete."
end

function _run_test_remote
    set -l target $argv[1]
    echo "=== Remote test mode -> $target ==="

    if not ssh -o ConnectTimeout=8 $target "echo ok" >/dev/null 2>&1
        echo "ERROR: Cannot SSH to $target"
        exit 1
    end

    echo "SSH OK. Running remote test..."
    echo ""

    # Send the local test function to the remote and execute it
    ssh $target '
        # Inline the local test logic (kept in sync with _run_test_locally)
        echo "=== Running on $(hostname) ==="
        echo "Date: $(date)"
        echo ""

        set -l models (ollama list 2>/dev/null | tail -n +2 | awk "{print \$1}" | string trim)

        if test (count $models) -eq 0
            echo "No models found"
            exit 1
        end

        echo "Models: $models"
        echo ""

        set -l gpu_tool ""
        if command -q intel_gpu_top
            set gpu_tool (command -v intel_gpu_top)
        else
            echo "Trying to install intel-gpu-tools..."
            if sudo pacman -S --noconfirm intel-gpu-tools >/dev/null 2>&1 || yay -S --noconfirm intel-gpu-tools >/dev/null 2>&1
                echo "Installed"
                hash -r 2>/dev/null; or true
                if command -q intel_gpu_top
                    set gpu_tool (command -v intel_gpu_top)
                else if test -x /usr/bin/intel_gpu_top
                    set gpu_tool /usr/bin/intel_gpu_top
                end
            else
                echo "Install failed"
            end
        end

        if test -n "$gpu_tool"
            echo "GPU tool: $gpu_tool"
        else
            echo "No intel_gpu_top available"
        end

        echo ""
        echo "Note: Lunar Lake unified memory - no dedicated VRAM."
        echo ""

        for model in $models
            echo "=== $model ==="
            env OLLAMA_INTEL_GPU=1 timeout 30 ollama run $model "PONG" 2>&1 | tail -4
            echo ""
            if test -n "$gpu_tool"
                timeout 6 $gpu_tool -s 1000 -o - 2>/dev/null | head -12 || echo "GPU sampling gave no data"
            else
                echo "No GPU tool"
            end
            echo "Mem: $(free -h | grep Mem)"
            ollama ps 2>/dev/null
            echo "----"
        end
        echo "Done on $(hostname)"
    '
end

# --- Main logic ---

if test -z "$host"; or test "$host" = "localhost"; or test "$host" = "."
    _run_test_locally
else
    _run_test_remote $host
end
