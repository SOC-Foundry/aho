# G083 Anti-Pattern Repository Scan - 0.2.12 W5

**Date**: 2026-04-12
**Executor**: gemini-cli
**Goal**: Characterize the class size of the `aho-G083` silent-fallback anti-pattern across the codebase.

---

## Scan Methodology
- **Target**: `src/aho/`
- **Pattern**: Blanket `except Exception:` (or `except Exception as e:`) catch blocks.
- **Classification**:
  - `Safe`: The exception returns an explicit error sentinel, raises a new exception, or is correctly formatted for downstream error handlers.
  - `G083-class`: The exception silently swallows errors (via `pass`) or returns a hardcoded positive/success fallback value that masks the execution failure.
  - `Ambiguous`: Requires human judgment or context-specific evaluation (e.g., returning `None`, `[]`, or `False`).

## Scan Results
- **Total `except Exception` Occurrences**: 155
- **Safe**: 3
- **G083-class**: 35
- **Ambiguous**: 117

## Top G083-Class Hits
The following critical instances actively conceal pipeline health issues and must be addressed:

1. **`src/aho/artifacts/nemotron_client.py:71`**
   - **Pattern**: `return categories[-1]`
   - **Impact**: Any connection timeout or invalid Ollama parsing forces the classification silently to `reviewer`, misrouting tasks directly into the GLM rubber-stamp evaluator without alerting orchestrators.

2. **`src/aho/artifacts/evaluator.py:183`**
   - **Pattern**: `except Exception: pass` followed by returning the unmodified or defaulted dictionary.
   - **Impact**: Swallows metric and review tracking validation exceptions completely, hiding logging failures from standard observability.

3. **`src/aho/pipelines/registry.py:28`**
   - **Pattern**: `except Exception: pass` followed by `return {"pipeline": name, "phases": {}, "status": "not found"}`
   - **Impact**: Silently swallows file reading or JSON decoding errors in the pipeline schema registry, failing open with a "not found" object rather than explicitly raising configuration corruption.

4. **`src/aho/rag/archive.py:46`** & **`src/aho/rag/archive.py:74`**
   - **Pattern**: `except Exception: pass` when handling `client.delete_collection` or similar vector DB manipulations.
   - **Impact**: Masking ChromaDB connectivity issues, potentially resulting in downstream chunking logic failing mysteriously.

5. **`src/aho/postflight/artifacts_present.py:23`**
   - **Pattern**: `except Exception: pass` when attempting to load `.aho.json`.
   - **Impact**: Obscures iteration data load failures, returning a defaulted `iteration = "unknown"` which compromises postflight file validation.

## Recommendation for 0.2.13 Scope
**Recommendation**: **Bulk Fix Strategy**
The size of the anti-pattern (35 definitive hits, 117 ambiguous hits requiring structural review) indicates that fixing these per-hit organically is unfeasible and unsafe. It represents a systemic resilience deficit. 

For 0.2.13, a dedicated tech-debt workstream should be orchestrated to:
1. Ban blanket `except Exception:` blocks project-wide unless explicitly logging/re-raising.
2. Refactor all 35 definitive G083-class occurrences to return a structured failure type (`{"status": "error", "message": "..."}`) or use an explicit failure sentinel instead of `pass`.
3. Introduce an `AcceptanceCheck` verifying zero `except Exception: pass` constructs in core pipeline and artifact modules.
