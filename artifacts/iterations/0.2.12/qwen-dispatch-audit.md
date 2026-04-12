# Qwen and Nemoclaw Operational Audit - 0.2.12 W2

**Date**: 2026-04-12
**Executor**: gemini-cli
**Goal**: Characterize whether W13 real Qwen dispatch is feasible.

---

## §1 Qwen model availability
The primary artifact model `qwen3.5:9b` is successfully pulled, available locally, and healthy.
- **Name**: `qwen3.5:9b`
- **ID**: `6488c96fa5fa`
- **Size**: 6.6 GB
- **Last Modified**: 22 hours ago

## §2 Direct Ollama invocation
Bypassing Nemoclaw completely to interrogate the model server:
- **Command**: `curl -s http://localhost:11434/api/generate -d '{"model": "qwen3.5:9b", "prompt": "Say exactly: hello", "stream": false}' | jq -r .response`
- **Response**: `hello`
- **Status**: Responsive, synchronous execution operates as intended.

## §3 Nemoclaw daemon status
The NemoClaw Orchestrator Daemon (`aho-nemoclaw.service`) is running correctly.
- **State**: `active (running)`
- **PID**: `3740811` (Python)
- **Memory Footprint**: 78.2M
- **Tasks**: 22 running
- **Socket Allocation**: Bound successfully on UNIX domain socket `/home/kthompson/.local/share/aho/nemoclaw.sock`. Confirmed via `ss -lxp`.

## §4 Nemoclaw dispatch contract
A review of `src/aho/agents/nemoclaw.py` confirms the operational protocol between caller and Nemoclaw.
- **Protocol**: Raw JSON strings framed over UNIX domain socket (`\n` terminated).
- **Request Shape**: `{"cmd": "dispatch", "task": "<prompt>"}`
- **Execution Model**: Synchronous. The caller blocks on the socket `recv()` until the routed agent completes the task.
- **Routing Phase**: Uses Nemotron (`nemotron-mini:4b`) to classify the task intent (`assistant` vs `code_runner` vs `reviewer`).
- **Response Shape**: `{"ok": true, "response": "<generated_artifact_content>"}` (or `{"error": "<reason>"}` on failure).

## §5 Round-trip attempt
A trivial echo task was dispatched to the Nemoclaw socket using a Python test script (`{"cmd": "dispatch", "task": "Say exactly 'ping-ack'."}`).
- **Outcome**: Success.
- **Latency**: 23.74s (this reflects Nemotron classification time + OpenClaw environment scaffolding + Qwen generation time).
- **Returned Data**: `{"ok": true, "response": "ping-ack"}`

## §6 Operational status per member
Both `qwen` and `nemoclaw` demonstrate working dispatch paths from API invocation through socket integration to model inference.
- **Qwen-3.5:9B**: Operational
- **NemoClaw**: Operational

## §7 W13 readiness assessment
W13 dispatching via Nemoclaw is fully feasible and ready for execution. The schema mapping handles tasking, and the synchronous socket model matches expected workflow primitives. No structural gaps or blockers were identified that would prohibit real task routing. 
