# Kyle's Decisions — 0.2.10

**Date:** 2026-04-11
**Context:** Pre-W0 decisions for install surface implementation iteration

---

## Q1. OpenClaw agent routing policy

Size-based threshold + explicit agent-hint flag. Default: Qwen local for tasks under 2000 tokens, Claude API above. No Gemini CLI routing for 0.2.10.

## Q2. Dashboard systemd auto-start

Auto-start on login via systemd --user. Dashboard always up.

## Q3. OTEL collector config

OTLP gRPC receiver on 4317, file exporter to ~/.local/share/aho/traces/, batch processor, 24h retention. Jaeger consumes from same OTLP receiver.

## Q4. Fernet store location

Move to ~/.local/share/aho/secrets/ at install time with migration path. Copy old file to new path, update config to read new path, delete old file only after successful read.

## Q5. CLI unification transition

Keep old aho-* wrappers as shims forwarding to aho <subcommand> for 0.2.10. Delete in 0.2.11.
