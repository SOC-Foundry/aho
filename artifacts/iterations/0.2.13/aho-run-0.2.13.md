# aho Run Report — 0.2.13
**Iteration:** 0.2.13
**Theme:** Dispatch-layer repair
**Primary executor:** claude-code (drafter) | **Auditor:** gemini-cli | **Execution model:** Pattern C
**Status:** Rescoped at W2.5 (Path A). Closed pending Kyle sign-off.
---
## Workstreams
| WS | Surface | Session | Role | Status | Notes |
|---|---|---|---|---|---|
| W0 | Bumps + schema v3 + Pattern C protocol | 1 | Setup | pass_with_findings | 6 canonicals bumped, postflight ValueError patched, AgentInvolvement model added, protocol doc created, Qwen cameo site scoped (workstream_gate.py:24), baseline 13 known / 0 new |
| W1 | GLM parser fix | 1 | Repair | pass | GLMParseError added, _strip_markdown_fences helper, hardcoded {score:8, ship} removed, 3 new tests + 2 updated |
| W2 | Nemotron classifier fix | 1 | Repair | pass | NemotronParseError + NemotronConnectionError added, both categories[-1] removed, blanket except replaced with specific requests exceptions, 3 new tests |
| W2.5 | Model-quality gate (HARD GATE) | 1 | Gate | pass_with_findings | GLM: 5/5 parse errors (4 timeout, 1 wrong schema). Nemotron: 8/10 "feature" bias. Parsers honest, models non-functional. Path A rescope triggered. |
| W3 | Nemoclaw benchmark | — | Measurement | skipped_per_rescope | Deferred to 0.2.14 — premise depends on model viability |
| W4 | ADR-047 Nemoclaw decision | — | Decision | skipped_per_rescope | Deferred to 0.2.14 — depends on W3 + model viability |
| W5 | OpenClaw audit | — | Discovery | skipped_per_rescope | Deferred to 0.2.14 — independent of model viability but below priority line |
| W6 | G083 Tier 1: agents/ | — | Bulk Repair | skipped_per_rescope | Deferred to 0.2.14 — fixing exception handlers around non-functional models |
| W7 | G083 Tier 2: council/ | — | Bulk Repair | skipped_per_rescope | Deferred to 0.2.14 |
| W8 | G083 Tier 3: remainder | — | Bulk Repair | skipped_per_rescope | Deferred to 0.2.14 |
| W8.5 | Qwen cameo | — | Forensics | skipped_per_rescope | Deferred to 0.2.14 — site scoped but execution requires viable models |
| W9 | G083 ambiguous triage | — | Classification | skipped_per_rescope | Deferred to 0.2.14 |
| W10 | Rescope close | 2 | Close | pending_audit | Council health 35.3/100 (unchanged from 0.2.12). Retrospective, carry-forwards, bundle, Kyle's notes, sign-off sheet. |

**Delivered:** 4 workstreams (W0, W1, W2, W2.5) + 1 close (W10)
**Skipped:** 8 workstreams (W3-W9, W8.5) per Path A rescope
**Success criterion:** Council health ≥50/100. **Not met.** Health unchanged at 35.3/100. Parser fixes (W1, W2) repaired code behavior but did not change member operational status.

---
## Rescope Decision Record

**Trigger:** W2.5 substrate findings
**Decision:** Path A — close iteration at W2.5, defer W3-W9 to 0.2.14
**Rationale:** Models behind honest parsers cannot produce usable output. Running bulk repair (W6-W9) or architecture decisions (W3-W4) on non-functional substrate produces meaningless data.
**Auditor confirmation:** Gemini W2.5 audit (pass_with_findings) independently confirmed substrate quality findings.

---
## Agent Questions & Capability Gaps
- [ ] Model viability: GLM and Nemotron non-functional at current quantization/model tier. 0.2.14 must resolve.
- [ ] Council health formula: does it correctly weight code-level fixes vs member operational status?

---
## Kyle's Notes

See `kyle-notes-stub.md` for 6 questions.

1. Does W2.5's substrate finding change council architecture direction?
2. Was Pattern C worth the audit overhead?
3. Casing-variant Gotcha/gotch parser policy?
4. GLM replacement/requantization strategy for 0.2.14?
5. Process changes to bake into harness?
6. Council health formula appropriateness?

---
## Sign-off

- [x] Session 1 (W0-W2.5) Surgical Fixes + Gate
- [x] Session 2 (W10) Rescope Close
