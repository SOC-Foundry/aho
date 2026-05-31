# council/

New implementation for the Ollama-based multi-model council.

This directory will contain:
- Model fleet configuration and loading logic
- Dispatcher / router for role specialization
- Simultaneous model management helpers
- Verification and health primitives

Designed around real hardware constraints (starting with 8GB → 16GB+ GPUs).
