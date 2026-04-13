#!/usr/bin/env fish
# iao install script - Linux + fish (Phase A, v10.66)
#
# Self-locates via (status filename). Walks up to find parent .iao.json.
# Copies components to ~/iao/. Writes idempotent fish config entries.

set -l SCRIPT_DIR (dirname (realpath (status filename)))
set -l cur $SCRIPT_DIR/..
while not test -f $cur/.iao.json
    if test "$cur" = "/"
        echo "ERROR: cannot find .iao.json walking up from $SCRIPT_DIR"
        exit 1
    end
    set cur (realpath $cur/..)
end
set -l PROJECT_ROOT $cur

echo "iao install"
echo "  source project: $PROJECT_ROOT"
echo "  source middleware: $SCRIPT_DIR"
echo "  destination: ~/iao/"
echo ""

# Compatibility check (if checker present)
if test -f $SCRIPT_DIR/iao/compatibility.py
    echo "Running compatibility check..."
    python3 $SCRIPT_DIR/iao/compatibility.py
    or begin
        echo "ERROR: compatibility check failed"
        exit 1
    end
else
    echo "(compatibility check deferred)"
end

# Copy components
mkdir -p ~/iao
cp -r $SCRIPT_DIR/bin ~/iao/
cp -r $SCRIPT_DIR/iao ~/iao/
cp -r $SCRIPT_DIR/prompts ~/iao/
cp -r $SCRIPT_DIR/templates ~/iao/
test -f $SCRIPT_DIR/MANIFEST.json; and cp $SCRIPT_DIR/MANIFEST.json ~/iao/
test -f $SCRIPT_DIR/COMPATIBILITY.md; and cp $SCRIPT_DIR/COMPATIBILITY.md ~/iao/
chmod +x ~/iao/bin/iao

# Idempotent fish config write
mkdir -p ~/.config/fish ~/.config/iao
touch ~/.config/fish/config.fish
set -l MARKER_BEGIN "# >>> iao >>>"
set -l MARKER_END "# <<< iao <<<"
if not grep -q "$MARKER_BEGIN" ~/.config/fish/config.fish
    printf "\n%s\n%s\n%s\n%s\n" \
        "$MARKER_BEGIN" \
        "set -gx PATH \$HOME/iao/bin \$PATH" \
        "test -f \$HOME/.config/iao/active.fish; and source \$HOME/.config/iao/active.fish" \
        "$MARKER_END" >> ~/.config/fish/config.fish
    echo "fish config: added iao block"
else
    echo "fish config: iao block already present (idempotent)"
end

echo ""
echo "Install complete. Open a new shell or:"
echo "  set -gx PATH ~/iao/bin \$PATH"
echo "  iao --version"
echo ""
echo "Next: iao project add <name> --gcp-project <gcp_project> --prefix <PREFIX> --path $PROJECT_ROOT"
