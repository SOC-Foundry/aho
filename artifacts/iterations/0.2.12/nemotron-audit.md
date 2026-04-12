# Nemotron Classifier Operational Audit - 0.2.12 W4

**Date**: 2026-04-12
**Executor**: gemini-cli
**Goal**: Characterize Nemotron operationally and audit for silent-fallback bugs (aho-G083 anti-pattern).

---

## §1 Nemotron model availability
The `nemotron-mini:4b` model is locally pulled via Ollama and is structurally available.
- **Name**: `nemotron-mini:4b`
- **ID**: `ed76ab18784f`
- **Size**: 2.7 GB
- **Access Method**: Local Ollama server

## §2 Direct invocation test
Direct command-line testing via `curl` to Ollama validates base model responsiveness:
- **Command**: `curl -s http://localhost:11434/api/generate -d '{"model": "nemotron-mini:4b", "prompt": "Say exactly: nemotron-ready", "stream": false}'`
- **Response**: `Sure, I'm ready to assist you. How can I help today?`
- **Status**: Responsive, but displays a notable lack of adherence to exact instructions in unstructured prompts (conversational padding instead of exact matching).

## §3 Daemon/CLI/module surface status
Nemotron does not operate its own standalone orchestrator daemon; it acts as the routing brain integrated into `aho-nemoclaw` operations.
- **Surface**: Nemotron is encapsulated via a synchronous Python client (`src/aho/artifacts/nemotron_client.py`).
- **Invocation**: Triggered dynamically during NemoClaw task routing (`classify(task, DEFAULT_ROLES, bias)`). 

## §4 Classification/routing protocol
The classification schema specifies exactly one role per input task based on the `DEFAULT_ROLES` mapping (`assistant`, `code_runner`, `reviewer`).
- **Input Shape**: A rigid zero-shot prompt prepended to the user's task requesting "EXACTLY ONE" category with an optional bias injected.
- **Evaluation Mechanism**: The module uses `requests.post()` synchronously to Ollama. It iterates through the valid categories and searches for a substring match (`cat.lower() in result.lower()`).
- **Fallback Logic**: If the resulting output does not contain any of the categories, or if an `Exception` (e.g. `requests.exceptions.ConnectionError`) occurs, the client silently returns `categories[-1]`.

## §5 Round-trip attempt
A basic classification task ("Write a Python script that calculates the Fibonacci sequence.") was routed using the `classify()` client.
- **Expected Outcome**: `code_runner`
- **Latency**: 0.13s.
- **Actual LLM Output (Logged)**: `"feature"`
- **Result Output**: Because `"feature"` wasn't inside `["assistant", "code_runner", "reviewer"]`, the agent hit its hardcoded fallback and returned `reviewer`.

## §6 Operational status + silent-fallback audit
Nemotron is physically operational but critically flawed at the integration layer. The implementation explicitly exhibits the `aho-G083` anti-pattern:
- **Finding (aho-G083)**: The exception handler in `_classify_impl` (`src/aho/artifacts/nemotron_client.py`) silently returns `categories[-1]` (`reviewer`) when an error occurs or the model's output cannot be parsed.
- **Systemic Risk**: This creates a cascading failure. If Nemotron is confused or unreachable, tasks are incorrectly routed to `reviewer`. As documented in W3, the `reviewer` (GLM Evaluator) is *also* a rubber-stamp on malformed input. Thus, failed classifications silently become rubber-stamped approvals.
- **Status**: `gap: classification logic silences errors and defaults to reviewer`

## §7 Routing-layer readiness
Nemotron **cannot** safely participate in W13 dispatch without structural modification.
If W13 attempts dispatch using NemoClaw, tasks will likely face unstable classification from Nemotron, silently defaulting to the `reviewer` fallback rather than the intended execution queue (`code_runner` or `assistant`). To enable true dispatch, the `classify()` exception layer must fail-open (throw explicitly) or request clarificatory re-prompting, rather than defaulting blindly to `categories[-1]`.
