# W3 Audit Dispositions - 0.2.16

Audit archive: `artifacts/iterations/0.2.16/audit/W3.json`
Audit result: `pass_with_findings`
Auditor: `gemini-cli`
Workstream scope: reduced under Option 4 - rule files + Telegram bridge + W2-only
calibration shipped; live engine evaluation, secrets verification, and synthetic
delivery test deferred (see `acceptance/W3.json` → `scope_notes.reduced_scope_disposition`).

The sealed acceptance archive `acceptance/W3.json` is not edited post-audit. This
note carries Kyle's dispositions on each AF finding verbatim, co-located with the
sealed archive so the record is self-describing at W3 close.

**Note on AF001 expr repair:** the recommended `rate(...) > 1` → `increase(...) > 5`
edit is targeted for the same iteration as the engine-selection ADR + bridge live
wire-up (W3-CF2 / W3-CF3). It is **deliberately not** retroactively applied to
either `artifacts/iterations/0.2.16/alerts/anomaly-rules.yaml` or
`artifacts/iterations/0.2.16/export/claude-otel-reference-pack/alerts/anomaly-rules.yaml`
in this close-out session - the sealed acceptance archive does not get
retroactive code changes, and neither file is wired to a live engine today, so
the rule fires no differently regardless.

## Dispositions (verbatim)

- **AF001** (Rule 3 interpretation ruling - Gemini ruled for prose interpretation
  `increase(claude_code_api_error[5m]) > 5`) - accepted. Recommended future
  repair: change `expr: rate(claude_code_api_error[5m]) > 1` to
  `expr: increase(claude_code_api_error[5m]) > 5` in BOTH
  artifacts/iterations/0.2.16/alerts/anomaly-rules.yaml AND
  artifacts/iterations/0.2.16/export/claude-otel-reference-pack/alerts/anomaly-rules.yaml.
  Do NOT make this edit in this close-out session - sealed acceptance archive
  does not get retroactive code changes. Carry-forward target: same iteration as
  engine-selection ADR (live wire-up workstream). Severity: cosmetic (rule fires
  no differently today since neither file is wired to a live engine).

- **AF002** (Calibration sample-size sensitivity n=21) - accepted as
  carry-forward. Already documented in pillar-11-monitoring-notes.md §Baseline
  calibration as "starting threshold only" with re-runnable probe. No new
  action; continued accumulation of W2/W3/future workstream metrics.jsonl gives
  larger n on next calibration. Carry-forward target: paired with
  engine-selection ADR + live wire-up. Severity: info.

- **AF003** (Rule 5 metric-source gap) - accepted as already-documented. The
  drafter's W3-F003 finding + the three resolution options in monitoring notes
  already disposition this. Gemini's audit confirms the gap independently. No
  new action in this close. Carry-forward target: paired with engine-selection
  ADR (the resolution choice IS part of engine selection - engine-side
  log-to-metric vs OTel processor conversion vs rule rewrite). Severity: info.
