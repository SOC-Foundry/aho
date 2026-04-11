# aho 0.2.2 — Build Log

## W0 — Carryover hygiene
Version bumps to 0.2.2 across 8 canonical artifacts. components.yaml next_iteration bumped for openclaw/nemoclaw/telegram. build_log_complete multi-candidate path fix. report_builder wall clock per-workstream from event log. Evaluator AHO_EVAL_DEBUG logging added. CLI version bumped. 87 tests pass.

## W1 — OpenClaw global daemon
Real --serve mode with Unix socket server at ~/.local/share/aho/openclaw.sock. Session pool (5 max), JSON protocol (chat/execute/status/close). Error handling for Qwen degenerate output. Systemd user service aho-openclaw.service. bin/aho-openclaw wrapper using Python socket client. templates/systemd/ directory created. 7 new tests. Status flipped stub -> active.

## W2 — NemoClaw global daemon
Real --serve mode with Unix socket at ~/.local/share/aho/nemoclaw.sock. Global NemoClawOrchestrator with 3-role session pool (assistant/code_runner/reviewer). Nemotron classification for task routing. JSON protocol (dispatch/route/status). Systemd user service aho-nemoclaw.service. bin/aho-nemoclaw wrapper. 6 new tests. Status flipped stub -> active.

## W3 — Telegram bridge real implementation
Rewrote notifications.py with project-scoped secrets via get_secret(PROJECT, name). send/send_capability_gap/send_close_complete functions. 429 rate limit retry with backoff. Unix socket daemon mode. Systemd user service aho-telegram.service. bin/aho-telegram wrapper (send/test/status/gap). Live smoke test delivered. 8 new tests. Status flipped stub -> active.

## W4 — Doctor + install integration
Added _check_aho_daemons() to doctor.py — checks aho-openclaw, aho-nemoclaw, aho-telegram systemd user services. Updated bin/aho-install to copy templates/systemd/*.template and enable --now all 3 services. bin/aho-uninstall already handles aho-* glob. Doctor preflight: all 15 checks green.

## W5 — Dogfood + close
End-to-end smoke: nemoclaw dispatch -> route -> openclaw chat -> qwen generate -> telegram send. Trace count +5 (26->31). All 5 span names verified in traces.jsonl. 108 tests pass (target 87+). 0 stubs in components.yaml. Close artifacts generated. Telegram close-complete notification sent.
