# 0.2.9 Carry-Forwards

Items deferred from 0.2.8 to future iterations:

TO 0.2.10 (openclaw reliability + P3 hardening):
- Openclaw Errno 11 resource unavailable fix
- Repetition detector false positives on qwen3.5:9b
- Openclaw Errno 104 connection reset handling
- Protocol smoke column in mcp-readiness.md
- Post-reboot daemon verification (all 4 services survive cold boot)
- Whatever gaps 0.2.9 W8 P3 clone surfaces
- Extend mcp_sources_aligned gate to cover bin/aho-bootstrap npm list alongside bin/aho-mcp (drift found and fixed in 0.2.9 W1; gate should prevent recurrence)

TO 0.2.11 (remote agent executor + Phase 0 graduation):
- Full Telegram → dedicated agent executor routing
- Junior-dev remote operability beyond /ws notifications
- Phase 0 graduation ceremony

TO 0.4.x+ (post-Phase-0):
- Extracting secrets module as standalone package for external projects
- Multi-user Telegram
