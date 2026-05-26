#!/usr/bin/env fish
# aho-ssh-diagnose.fish — diagnose the libcrypto-unsupported error blocking
# git push to github.com-socfoundry.
#
# Runs read-only probes:
#   - SSH + OpenSSL versions
#   - Can ssh-keygen parse the .pub (different code path than ssh client)
#   - Can openssl recognize ED25519 in its algorithm list
#   - Does ssh-add -l show the matching key in the agent
#   - Verbose connection attempt to github.com-socfoundry (auth flow trace)
#
# No mutations. Outputs go to stdout for operator review.

set -l script_name "aho-ssh-diagnose"
set -l pub_file "$HOME/.ssh/socfoundry_a8cos.pub"

function _hdr
    set_color --bold magenta; echo ""; echo "─── $argv ───"; set_color normal
end

_hdr "1. SSH client version"
ssh -V 2>&1

_hdr "2. OpenSSL version"
openssl version 2>&1
openssl version -a 2>&1 | grep -iE 'platform|options' | head -3

_hdr "3. ssh-keygen parses .pub (independent of ssh client load path)"
ssh-keygen -lf $pub_file 2>&1

_hdr "4. .pub file shape (cat-A surfaces hidden chars; wc -c shows size)"
echo "size:"
wc -c $pub_file 2>&1
echo "content (cat -A — shows tabs, line endings, NULs):"
cat -A $pub_file 2>&1

_hdr "5. OpenSSL algorithm list — verify ED25519 in the public-key algorithms"
openssl list -public-key-algorithms 2>&1 | grep -iE 'ed25519|ED25519' | head -5
if test $status -ne 0
    echo "(no ED25519 hits — that may be the root cause)"
end

_hdr "6. OpenSSL providers (3.x architecture; need default at minimum)"
openssl list -providers 2>&1

_hdr "7. 1Password SSH agent — is it serving identities?"
echo "SSH_AUTH_SOCK = $SSH_AUTH_SOCK"
if test -S "$HOME/.1password/agent.sock"
    echo "1Password agent socket present at ~/.1password/agent.sock"
else
    set_color yellow; echo "WARN: ~/.1password/agent.sock not present"; set_color normal
end

_hdr "8. ssh-add -l — identities currently in the agent"
ssh-add -l 2>&1

_hdr "9. SSH config block for github.com-socfoundry"
ssh -G github.com-socfoundry 2>&1 | grep -iE 'identityagent|identityfile|identitiesonly|hostname|user' | head -10

_hdr "10. Verbose connection attempt (dry — pubkey auth flow, no commit)"
echo "running: ssh -vv -o BatchMode=yes -T git@github.com-socfoundry 2>&1 | tail -40"
ssh -vv -o BatchMode=yes -T git@github.com-socfoundry 2>&1 | tail -40

set_color cyan; echo ""; echo "[$script_name] done. Surface output above for analysis."; set_color normal
