# GLM Evaluator Operational Audit - 0.2.12 W3

**Date**: 2026-04-12
**Executor**: gemini-cli
**Goal**: Characterize GLM as an actual operational component and assess W14 readiness.

---

## §1 GLM model availability
The specified GLM model is successfully pulled, available locally via Ollama, and healthy.
- **Name**: `haervwe/GLM-4.6V-Flash-9B:latest`
- **ID**: `ad2e2e374c6b`
- **Size**: 8.0 GB
- **Access Method**: Local Ollama server

## §2 Direct invocation test
Bypassing all aho Python harnesses to interrogate the model server directly using `curl`:
- **Command**: `curl -s http://localhost:11434/api/generate -d '{"model": "haervwe/GLM-4.6V-Flash-9B:latest", "prompt": "Say exactly: glm-ready", "stream": false}'`
- **Response**: `glm-ready`
- **Status**: The model responds synchronously and accurately to direct API requests.

## §3 Daemon/CLI/module surface status
Unlike OpenClaw and NemoClaw, the GLM evaluator **does not** have a dedicated systemd daemon, socket, or CLI wrapper.
- **Surface**: It exists purely as a synchronous Python class (`EvaluatorAgent` in `src/aho/agents/roles/evaluator_agent.py`) and a stateless integration client (`src/aho/artifacts/glm_client.py`).
- **Lifecycle**: It is instantiated dynamically inside existing Python processes when a review is requested. It relies on a base `OpenClawSession` context wrapper under the hood but bypasses standard daemon routing.

## §4 Review protocol
The review protocol is structured but fragile.
- **Input Shape**: Plaintext compilation of `Design`, `Plan`, and stringified `Output` dictionaries appended to a rigid prompt requesting JSON (`{score, issues, recommendation}`).
- **Output Expectations**: The module attempts a naive `json.loads(response)`. 
- **Failure Mode**: If `json.loads` fails (e.g., due to markdown fences like ````json`), the system silently swallows the error and defaults to a hardcoded response (`{"score": 8, "recommendation": "ship"}`).

## §5 Round-trip attempt
A trivial artifact ("print('hello world')") was submitted to `EvaluatorAgent().review()` via a test script.
- **Latency**: 54.06s.
- **Raw LLM Output**: Markdown-fenced JSON containing actual review feedback (score 5, Mandarin recommendation text).
- **Result Output**: The naive `json.loads` failed on the markdown fences. The agent silently swallowed the error and returned the hardcoded fallback: Score `8`, Recommendation `ship`.
- **Finding**: The evaluator agent is currently a rubber stamp. Any response containing markdown formatting bypasses the actual evaluation and defaults to passing the workstream.

## §6 Operational status
While the GLM model itself is healthy and responsive, the `evaluator-agent` implementation is critically flawed at the parsing layer.
- **Status**: `gap: parsing logic converts real reviews to rubber stamps`
- **Inventory update**: The `evaluator-agent` row in `council-inventory.md` has been updated to reflect this gap.

## §7 W14 readiness assessment
W14 is **not ready** for meaningful execution in its current state.
While the Python calls will complete without crashing, the metric value of a W14 "real GLM review dispatch" is zero because the parsing defect guarantees a hardcoded `ship` response for any cleanly markdown-formatted LLM reply.
To make W14 a legitimate dispatch test, the `EvaluatorAgent.review` JSON parsing logic must be patched (e.g., using a regex to strip markdown fences) prior to or as part of W14. This is a newly surfaced tech debt item.
