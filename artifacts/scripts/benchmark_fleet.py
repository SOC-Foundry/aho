"""Benchmark the IAO model fleet (Qwen, Nemotron, GLM)."""
import time
from aho.artifacts.qwen_client import QwenClient
from aho.artifacts.nemotron_client import classify
from aho.artifacts.glm_client import generate as glm_generate


def benchmark():
    print("Benchmarking IAO Model Fleet...")
    print("──────────────────────────────")

    # 1. Qwen (9B)
    print("1. Qwen-3.5:9B (Artifacts)")
    client = QwenClient()
    start = time.time()
    resp = client.generate("You are a helpful assistant.", "Write a 50-word summary of aho.")
    duration = time.time() - start
    words = len(resp.text.split())
    print(f"   Status: {'OK' if resp.ok else 'FAIL'}")
    print(f"   Latency: {duration:.2f}s")
    print(f"   Throughput: {words/duration:.2f} words/s")
    print()

    # 2. Nemotron (4B)
    print("2. Nemotron-mini:4B (Classification)")
    start = time.time()
    res = classify("This iteration is performing well.", ["positive", "negative", "neutral"])
    duration = time.time() - start
    print(f"   Result: {res}")
    print(f"   Latency: {duration:.2f}s")
    print()

    # 3. GLM (9B)
    print("3. GLM-4.6V-Flash-9B (Vision/Reasoning)")
    start = time.time()
    res = glm_generate("Explain the 'trident of constraints' in aho.")
    duration = time.time() - start
    print(f"   Status: {'OK' if 'Error' not in res else 'FAIL'}")
    print(f"   Latency: {duration:.2f}s")
    print()


if __name__ == "__main__":
    benchmark()
