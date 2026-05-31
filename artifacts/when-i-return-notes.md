# When I Return - Notes for aho Machine Bootstrap Testing

**Date:** 2026-05-31

## What Was Done Before You Left

- New `install.fish` + thin wrappers delivered (by Claude via the handoff prompt)
- All fish scripts in the repo have been sanitized (zero heredocs)
- Light integration added to `bin/aho-council-preflight.fish` so it calls the new installer\'s `--check` mode
- Testing report template created: `artifacts/aho-install-testing-report.md`

## While You\'re Testing on the Other PC

Useful commands to have ready:

```fish
# On the target machine (after cloning aho)
cd ~/Development/Projects/socfoundry/aho

# 1. See what would change
./install.fish --dry-run

# 2. Generate state for aho-doctor
./install.fish --check
cat ~/.local/share/aho/install-state.jsonl

# 3. Actual bootstrap
./install.fish
```

After testing, fill out:
`artifacts/aho-install-testing-report.md`

## When You Get Back

Priorities we can tackle:

1. Review test results + any issues found
2. Decide on integration depth (how tightly preflight should depend on install.fish)
3. Documentation (README update, man-page style help, etc.)
4. Prepare for git push / review

## Quick Links

- Main implementation: `./install.fish`
- Wrappers: `bin/aho-machine-bootstrap.fish` and `bin/aho-deploy`
- Manifests: `manifests/packages/` and `manifests/ollama/`
- Test artifacts: `tests/council-stress/`
- This note: `artifacts/when-i-return-notes.md`

