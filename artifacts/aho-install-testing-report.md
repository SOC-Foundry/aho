# aho Machine Bootstrap - Testing Report

**Tester:**  
**Date:**  
**Target Machine:** (distro, hardware, fresh install vs existing?)  
**Branch / Commit:** main (as of 2026-05-31)

---

## 1. Dry Run

```bash
./install.fish --dry-run
```

**Result:**
- [ ] Completed without error
- [ ] Output was clear and actionable

**Notes / Surprises:**

---

## 2. Check Mode

```bash
./install.fish --check
```

**Result:**
- [ ] `~/.local/share/aho/install-state.jsonl` was created
- [ ] `aho-doctor` can read it without crashing
- List any `fail` statuses:

**Notes:**

---

## 3. Full Run

```bash
./install.fish
```

**Observations:**

| Phase              | Success? | Time Taken | Notes |
|--------------------|----------|------------|-------|
| pacman sync        |          |            |       |
| AUR sync (yay)     |          |            |       |
| Ollama model pulls |          |            |       |

**Issues Encountered:**

---

## 4. Post-Run Validation

- [ ] All packages from `pacman-native.txt` are installed (`pacman -Qqe`)
- [ ] All AUR packages from `aur-foreign.txt` are installed
- [ ] All models from `manifests/ollama/models.txt` appear in `ollama list`
- [ ] `ollama service` is running (if using global setup)
- [ ] No unexpected breakage to existing system

**Performance / UX Feedback:**

---

## 5. Idempotency Test

Run `./install.fish` a second time immediately after the first.

- [ ] Second run was fast (mostly no-ops)
- [ ] No unnecessary package reinstalls or model re-pulls
- [ ] Output was appropriately quiet about things already present

---

## 6. Edge Cases Tested (optional but valuable)

- [ ] Running on a machine without `yay` installed
- [ ] Running with `--dry-run` then real run
- [ ] Interrupting mid-run and resuming
- [ ] Machine with very different package base

**Results:**

---

## Overall Assessment

**Would you trust this on a new daily driver?**  
[ ] Yes  
[ ] Yes, with caveats  
[ ] Not yet

**Biggest Wins:**

**Biggest Concerns / Improvements Needed:**

---

**Raw Output / Logs Attached?** (paste or link here)
