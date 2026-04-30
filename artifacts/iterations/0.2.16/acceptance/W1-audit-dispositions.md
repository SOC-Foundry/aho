# W1 Audit Dispositions — 0.2.16

Audit archive: `artifacts/iterations/0.2.16/audit/W1.json`
Audit result: `pass_with_findings`
Auditor: `gemini-cli`

The sealed acceptance archive `acceptance/W1.json` is not edited post-audit. This
note carries Kyle's dispositions on each AF finding verbatim, co-located with the
sealed archive so the record is self-describing at W1 close.

## Dispositions (verbatim)

- **AF001, AF002** — non-W1 noise (these are W0-material Gemini recycled).
  Acknowledge in the workstream_complete payload but do not act on them.

- **AF003** — accepted as typo. `baseline_reference_failed_count: 14` in W1.json
  should be 13. Do NOT edit the sealed acceptance archive. Fold into iteration
  close-out drift repair (alongside any other cosmetic drift found at close).

- **AF004** (api_error_count is an alias for internal_error_count) — carry-forward
  candidate for 0.2.17. Intentional vs. missing-event-mapping vs. dead field is a
  design decision, not a W1-close decision.

- **AF005** (api_retries_exhausted_count is a dead field) — same as AF004,
  carry-forward to 0.2.17.
