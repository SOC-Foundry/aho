#!/usr/bin/env fish
# aho-web-publish-prep.fish - assemble ./public/ for firebase hosting deploy.
#
# Layout produced:
#   public/
#   ├── index.html             (quantum-posture mockup - public landing)
#   └── campus/index.html      (same mockup at canonical /campus/ URL)
#
# 2026-05-17 architectural simplification: aho.run is PUBLIC eye-candy only
# (campus posture mockup). claw3d and the otel/jaeger UIs live behind
# Tailscale Serve on nzxtcos.tail8492.ts.net, tailnet-only - never on
# Firebase. Previous claw3d + /web/ Flutter copies removed; /app/ skeleton
# in repo is a 5-page Flutter stub with no wired data and will likely be
# absorbed into claw3d's future routes.
#
# Usage: bin/aho-web-publish-prep.fish
# Then:  firebase deploy --only hosting

set -g _NAME "aho-web-publish-prep"
set -g _ROOT (dirname (dirname (realpath (status filename))))

function _info; set_color cyan; echo "[$_NAME] $argv"; set_color normal; end
function _err;  set_color red;  echo "[$_NAME ERROR] $argv"; set_color normal; end
function _step; echo ""; set_color --bold magenta; echo "── $argv ──"; set_color normal; end

cd $_ROOT

# ── pre-flight ──
if not test -f artifacts/observability/mockup-quantum-campus.html
    _err "missing artifacts/observability/mockup-quantum-campus.html"
    exit 1
end

# ── step 1: clean + scaffold public/ ──
_step "1. scaffold public/"
rm -rf public
mkdir -p public/campus
_info "public/ scaffolded"

# ── step 2: copy quantum-posture mockup (root + /campus/ - same content, two URLs) ──
_step "2. campus/ + root (quantum-posture mockup)"
cp artifacts/observability/mockup-quantum-campus.html public/campus/index.html
cp artifacts/observability/mockup-quantum-campus.html public/index.html
_info "→ public/index.html (mockup is the root landing)"
_info "→ public/campus/index.html (mockup also at canonical /campus/ URL)"

# ── summary ──
_step "summary"
echo ""
_info "public/ ready for `firebase deploy --only hosting`:"
echo ""
find public -maxdepth 2 -type f | sort | sed 's|^|    |'
echo ""
_info "total size:"
du -sh public/ | sed 's|^|    |'
echo ""
_info "Next:"
_info "    firebase deploy --only hosting"
_info ""
_info "After deploy, URLs will be:"
_info "    https://aho.run/                    (quantum posture mockup - default landing)"
_info "    https://aho.run/campus/index.html   (same mockup at canonical URL)"
_info ""
_info "claw3d + Jaeger live on the tailnet (NOT on aho.run):"
_info "    https://nzxtcos.tail8492.ts.net/    (Jaeger UI - current Tailscale Serve mapping)"
_info "    claw3d Tailscale Serve mapping TBD (see Tailscale Serve setup notes)"
