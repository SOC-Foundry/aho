# ghcr push runbook - aho:0.2.18

**Status:** image built locally on NZXTcos in W1, rebuilt for substrate-drift fix (sha256 below), loaded on a8cos in W2. **Not yet pushed to ghcr.io.** This closes OPR-W1-001 / OPR-W2-002.

**Commit reference:** `e8c7c2e` (`KT completed 0.2.18 and updated README`) - the state that produced this image.

---

## What you're pushing

| Field | Value |
|---|---|
| Local tag | `aho:0.2.18` |
| Image ID | `3139b675dd425405ef739b44d958ba5ec8a0f49f0d5a945a2555aaaa90504703` |
| Local manifest digest | `sha256:9f6b5844d365aaaebf4a4c558bc5857643482a786fb734b634a3bac7b0569d79` |
| Target registry tag | `ghcr.io/soc-foundry/aho:0.2.18` |
| Size | 357 MB |
| Source commit | `e8c7c2e` (main) |
| Labels (from Dockerfile) | `io.aho.iteration=0.2.18`, `io.aho.workstream=W1`, description ref to W1 cross-host OTLP endpoint + W0 embed-timeout fix |

Note: digest above is from the local build. The **registry-side digest will differ** because `podman push` re-serializes the manifest. Both are valid; treat the registry digest as the canonical published reference.

---

## Pre-flight verification

```fish
# Confirm the image is local on NZXTcos
podman image inspect aho:0.2.18 --format '{{.Id}}'
# expected: 3139b675dd425405ef739b44d958ba5ec8a0f49f0d5a945a2555aaaa90504703

# Confirm Dockerfile labels match expectations
podman image inspect aho:0.2.18 --format '{{json .Config.Labels}}' | jq .
```

---

## Authentication (one of)

**Option A - gh CLI** (uses the GitHub token gh manages - preferred if you already have `gh auth status` healthy):

```fish
gh auth token | podman login ghcr.io -u <your-github-username> --password-stdin
```

**Option B - interactive podman login** (prompts for a personal access token with `write:packages` scope):

```fish
podman login ghcr.io
```

A token created at github.com/settings/tokens with at minimum `write:packages` works for option B.

---

## Tag + push

```fish
podman tag aho:0.2.18 ghcr.io/soc-foundry/aho:0.2.18
podman push ghcr.io/soc-foundry/aho:0.2.18
```

Push surfaces blob upload progress and ends with `Writing manifest to image destination` + a final digest line.

---

## Post-push verification

```fish
# Capture the registry-side digest (paste into acceptance amendment)
podman image inspect ghcr.io/soc-foundry/aho:0.2.18 --format '{{.Digest}}'

# Verify the registry sees it (this hits ghcr's API)
gh api repos/soc-foundry/aho/packages 2>/dev/null | jq '.[] | select(.name == "aho")'
# OR a direct manifest fetch:
curl -sS -H "Authorization: Bearer $(gh auth token)" \
  https://ghcr.io/v2/soc-foundry/aho/manifests/0.2.18 | jq .
```

---

## Followup actions after push

1. **Update acceptance archives with the registry-side digest.** Two files reference the digest expectation:
   - `artifacts/iterations/0.2.18/acceptance/W1.json` → `deliverable_evidence.image_digest`
   - `artifacts/iterations/0.2.18/acceptance/W2.json` → no explicit digest field (uses image_id which is unchanged)

   Pattern: add a `pushed_manifest_digest` field next to the existing local digest. Don't overwrite the local digest - both are accurate at their respective layers.

2. **Optional: also tag and push a `0.2.18-rc1` alias** if you want to mirror the 0.2.17-rc1/rc2 convention from the registry inventory.

3. **Cross-host pull validation** (proves the push is reachable from another host): on a8cos, after Kyle removes the locally-loaded image,
   ```fish
   ssh a8cos 'podman rmi aho:0.2.18 && podman pull ghcr.io/soc-foundry/aho:0.2.18'
   ```
   Skip if you want to preserve the current a8 state.

4. **Mark OPR-W1-001 + OPR-W2-002 closed.** Both reference this push as the gate.

5. **Decide whether to commit the registry-digest amendment** as part of the 0.2.18-close commit (with W3+W4 work) or as a small interim commit now.

---

*Generated 2026-05-17 during 0.2.18 W2 close. Author: claude-code as drafter, executed by Kyle per Pillar 11 (operator-only ghcr push).*
