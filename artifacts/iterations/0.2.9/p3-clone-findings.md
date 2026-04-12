# Persona 3 Validation Findings — aho 0.2.9 W8

**Date:** 2026-04-11
**Scope:** Validate aho's persona 3 (impromptu assistant — pwd-scoped work against arbitrary files)
**Result:** Persona 3 entry point does not exist. All 4 test tasks failed at the same point.

---

## Finding 1: No Persona 3 Entry Point

Searched all CLI commands, bin/ wrappers, and daemon dispatch paths for any mechanism that accepts "do this task against these files" outside the iteration/workstream framework.

**Entry points examined:**

| Path | Works for persona 3? | Why not |
|---|---|---|
| `bin/aho-openclaw chat "msg"` | No | Chat-only, no filesystem access. LLM responds "I can't access files." |
| `bin/aho-openclaw execute "code"` | Partial | Can run code that reads files, but no LLM reasoning about content. Disconnected from chat. |
| `bin/aho-nemoclaw dispatch "task"` | No | Daemon-dependent, iteration-scoped routing. No file awareness. |
| `bin/aho-conductor dispatch "task"` | No | Full pipeline (nemoclaw → workstream → evaluator → telegram). Iteration-scoped. No file input. |
| Telegram free-text → openclaw | No | Same as openclaw chat — no filesystem access on the receiving end. |
| `aho rag query "question"` | No | Queries the ChromaDB archive of aho's own artifacts. Not a general-purpose tool. |
| Claude Code / Gemini CLI | Yes (external) | These ARE persona 3 tools, but they're not aho — they're the agent runtimes aho orchestrates. |

**Verdict:** aho has zero persona 3 implementation surface. The gap is structural, not a missing flag.

---

## Finding 2: Chat and Execute Are Disconnected

OpenClaw has two capabilities that persona 3 would need:
1. **chat** — LLM reasoning (Qwen via Ollama). Cannot read files.
2. **execute** — subprocess code execution. Can read files. Cannot reason.

These two capabilities are not connected. There is no "read this file then reason about its contents" dispatch path. A persona 3 entry point would need to:
1. Accept a task description + file/directory references
2. Read the files (execute path or direct I/O)
3. Feed file contents to the LLM as context (chat path)
4. Write output to a specified location (execute path or direct I/O)

None of these four steps are wired together today.

---

## Finding 3: Test Environment and Task Results

**Test environment:** `/tmp/aho-persona-3-test/`
- `sample-contract.pdf` — 1-page professional services agreement (generated via reportlab)
- `sample-emails.txt` — 8 emails with 7 unique email addresses
- `sow-template.md` — empty file for SOW output

**Task results:**

| Task | Command | Result | Failure mode |
|---|---|---|---|
| A: Summarize PDF | `aho-openclaw chat "Summarize the PDF at..."` | "I can't access files" | No filesystem access in chat path |
| B: Generate SOW | `aho-openclaw chat "Generate a SOW..."` | Generated SOW content in response but could not write to disk | Chat generates but cannot write files |
| C: Risk review | `aho-openclaw chat "Review the contract PDF..."` | "I don't have access to local file paths" | Same as A |
| D: Extract emails | `aho-openclaw chat "Extract email addresses from..."` | "I don't have access to local file paths" | Same as A |

**Execute path test (supplementary):**
```fish
aho-openclaw execute "with open('/tmp/aho-persona-3-test/sample-emails.txt') as f: print(f.read())"
```
Result: **Success** — file contents returned. But this is raw code execution with no LLM reasoning. A user would need to write the Python themselves, defeating the purpose of an LLM assistant.

---

## Finding 4: What Persona 3 Would Require

Minimum viable persona 3 entry point needs:

1. **CLI command:** `aho do "task description" [--files file1 file2 ...] [--output dir]`
   - Accepts natural language task + file references
   - Works from any pwd, no iteration required
   - No daemon dependency (or graceful fallback to direct Ollama call)

2. **File bridge:** Read specified files, inject contents into LLM prompt context
   - Text files: direct injection
   - PDF: extract text (PyPDF2 or similar), inject
   - Directories: list + selective read based on task

3. **Output writer:** LLM response → file on disk
   - If task says "write to X", write to X
   - If no output specified, print to stdout
   - Markdown, JSON, plain text output formats

4. **No iteration coupling:** Works without `.aho.json`, `.aho-checkpoint.json`, or any iteration state. Reads from pwd or explicit paths.

---

## Finding 5: Architectural Gap Classification

This is NOT a bug or a missing feature in existing code. It's an entire capability surface that was never built because aho's architecture assumed all work happens within the iteration/workstream framework (persona 1 and 2).

The gap sits at the intersection of:
- OpenClaw's chat capability (has LLM, no files)
- OpenClaw's execute capability (has files, no LLM)
- The CLI surface (has neither a "do" command nor file-passing conventions)

**Effort estimate:** Small module (~150 lines) + CLI integration (~30 lines) + tests (~100 lines). Not a large workstream. The primitives (QwenClient, file I/O, CLI argparse) all exist — they just aren't composed for this use case.

---

## Carry-Forward

- Persona 3 entry point (`aho do`) → 0.2.10 or 0.2.11 scope depending on priority
- Chat+execute bridge in openclaw → prerequisite for persona 3
- PDF text extraction dependency → new pip dependency if persona 3 handles PDFs
