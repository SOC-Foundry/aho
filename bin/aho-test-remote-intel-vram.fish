#!/usr/bin/env fish
# aho-test-remote-intel-vram.fish
# Smoke test for Intel Arc iGPU / NPU offloading on Lunar Lake (Ultra 7 268V class)
# Run this from another machine via SSH to observe real GPU behavior on the target.

set -l host $argv[1]
if test -z "$host"
    set -l script_name (status filename | path basename)
    echo "Usage: $script_name [user@]hostname"
    echo "Example: $script_name kthompson@x9cos"
    exit 1
end

echo "=== Remote Intel Arc iGPU / NPU Smoke Test (Lunar Lake) ==="
echo "Target: $host"
echo ""
echo "Note: Lunar Lake (Ultra 7 268V) uses unified on-package LPDDR5X memory."
echo "There is no dedicated VRAM like on discrete NVIDIA GPUs."
echo "The Arc iGPU and NPU share memory with the CPU. btop often shows nothing."
echo "intel_gpu_top is the correct tool (the script will try to ensure it is available)."
echo ""

if not ssh -o ConnectTimeout=8 $host "echo ok" >/dev/null 2>&1
    echo "ERROR: Cannot SSH to $host"
    exit 1
end

echo "SSH connection OK"
echo ""

ssh $host '
    echo "=== Running on $(hostname) ==="
    echo "Date: $(date)"
    echo ""

    set -l models (ollama list 2>/dev/null | tail -n +2 | awk "{print \$1}" | string trim)

    if test (count $models) -eq 0
        echo "No models found via ollama list. Exiting."
        exit 1
    end

    echo "Models found on target:"
    for m in $models
        echo "  - $m"
    end
    echo ""

    # Robust detection/install of intel_gpu_top
    set -l gpu_top ""
    if command -q intel_gpu_top
        set gpu_top (command -v intel_gpu_top)
    else
        echo "intel_gpu_top not found in PATH. Attempting installation..."
        set -l installed 0
        if sudo pacman -S --noconfirm intel-gpu-tools >/dev/null 2>&1
            set installed 1
        else if command -q yay; and yay -S --noconfirm intel-gpu-tools >/dev/null 2>&1
            set installed 1
        end

        if test $installed -eq 1
            echo "Package installed. Refreshing command cache..."
            hash -r 2>/dev/null; or true
            # Some systems need this after pacman in non-interactive shells
            if test -x /usr/bin/intel_gpu_top
                set gpu_top /usr/bin/intel_gpu_top
            else if test -x /usr/local/bin/intel_gpu_top
                set gpu_top /usr/local/bin/intel_gpu_top
            else if command -q intel_gpu_top
                set gpu_top (command -v intel_gpu_top)
            end
        else
            echo "Automatic install of intel-gpu-tools failed."
        end
    end

    if test -n "$gpu_top"
        echo "GPU monitoring tool available: $gpu_top"
    else
        echo "WARNING: intel_gpu_top is NOT available. GPU utilization will not be shown."
        echo "You can try manually: sudo pacman -S intel-gpu-tools"
    end

    echo ""
    echo "Note on Lunar Lake (Ultra 7 268V + Arc 140V):"
    echo "This chip uses unified on-package memory (no dedicated VRAM like NVIDIA)."
    echo "The iGPU and NPU share the LPDDR5X with the CPU."
    echo "btop often shows nothing useful for this iGPU."
    echo "intel_gpu_top is the correct tool, but support on very new Arc parts can be limited."
    echo ""

    for model in $models
        echo "=== Testing model: $model ==="
        echo "Forcing load + short inference (preferring GPU/NPU)..."
        echo ""

        # Try to bias toward GPU. On Lunar Lake this may use iGPU or NPU depending on Ollama build.
        env OLLAMA_INTEL_GPU=1 timeout 30 ollama run $model "Respond with exactly the word PONG." 2>&1 | tail -5

        echo ""
        if test -n "$gpu_top"
            echo "GPU activity sample (5 seconds):"
            # -s 1000 = sample every 1s, -o - = output to stdout
            timeout 6 $gpu_top -s 1000 -o - 2>/dev/null | head -15 || echo "intel_gpu_top sampling returned no data (common on some Lunar Lake configs)"
        else
            echo "Skipping GPU sampling (tool not available)."
        end

        echo ""
        echo "System memory after load:"
        free -h | grep -E "Mem:|Swap:"

        echo ""
        echo "Ollama currently loaded models:"
        ollama ps 2>/dev/null || echo "ollama ps failed"

        echo "---------------------------------------------"
        echo ""
    end

    echo "Test finished on $(hostname)"
'
