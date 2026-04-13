# Kyle's Notes — 0.2.13 (W10 Rescope Close)

## Questions for Sign-off

1. **Does W2.5's substrate finding change how you think about the council architecture?** The dispatch layer is honest now but the models behind it are non-functional. Is local LLM evaluation still the right architecture, or should the council pivot to API-backed evaluation (Claude/Gemini for review) with local models limited to classification/routing?

2. **Was Pattern C worth the audit overhead given W0 friction?** 4 audits × ~13min avg = ~52min total audit time, plus ~4 hygiene sessions for terminal events. Audits caught one real finding (W0 role-crossing) and confirmed substance on three others. Continue, modify (e.g., batch audits with explicit timestamp semantics), or revert to single-agent for 0.2.14?

3. **Casing-variant Gotcha/gotch — what's the parser policy?** Current behavior: case-insensitive substring match for close variants ("Gotcha"→"gotcha"), NemotronParseError for distant mismatches ("gotch"). Options: (a) soft-match to nearest category, (b) strict exact-match only, (c) new diagnostic category for model quality monitoring. This affects how aggressively the classifier rejects non-deterministic model output.

4. **Should 0.2.14 attempt heavier quantization (Q8_0?), different model entirely (Qwen-as-evaluator?), or abandon GLM-as-evaluator?** GLM-4.6V-Flash-9B at Q4_K_M has real evaluation capability (W2.5 input #1 raw text identified the defect) but cannot deliver structured output. Heavier quantization may help at the cost of VRAM/latency. Qwen-3.5:9B is already operational for dispatch — could it serve dual duty? Or is local evaluation a dead end at this hardware tier?

5. **Any process changes from this iteration to bake into the harness?** Candidates: automated checkpoint lifecycle (emit workstream_start/complete from harness, not manually), one-audit-per-session protocol, audit archive naming convention to prevent batch-timestamp overwrite risk.

6. **Is the council health score formula still appropriate?** Health remained 35.3/100 despite W1 and W2 parser fixes. The score reflects member status data (operational/gap/unknown), which didn't change because the parsers fixed code behavior, not model capability. Should the formula weight code-level fixes, or is it correct that health only moves when member status actually changes?
