# W2 Audit Dispositions — 0.2.16

Audit archive: `artifacts/iterations/0.2.16/audit/W2.json`
Audit result: `pass_with_findings`
Auditor: `gemini-cli`

The sealed acceptance archive `acceptance/W2.json` is not edited post-audit. This
note carries Kyle's dispositions on each AF finding verbatim, co-located with the
sealed archive so the record is self-describing at W2 close.

## Dispositions (verbatim)

- **AF003** (Baseline count-coherence drift — 421 vs 427 collection set) —
  accepted as-is. Gemini's action_required is already correct: "None for W2
  close; update test-baseline.json counts in the next workstream or iteration
  close-out to reflect the 427 total." Disposition: fold into iteration
  close-out drift repair alongside any other cosmetic drift. Severity:
  important-but-cosmetic. Do NOT edit the sealed W2 acceptance archive. Related
  auditor-quality note: the W2 baseline_regression block reported
  `tests_collected: 421` without listing the ignore-set that produced 421.
  Future workstreams should include the explicit ignore list in
  baseline_regression reporting to prevent this class of count drift. Add that
  as a carry-forward item under the next-workstream harness-hygiene bucket.

- **AF004** (dispatch.duration_ms measurement-site gap on error paths) —
  accepted as carry-forward. Target: 0.2.17 test coverage for error-path
  duration consistency. Severity: info. No action in W2 close beyond recording
  in carry-forwards-0.2.16.md.
