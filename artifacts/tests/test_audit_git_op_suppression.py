"""0.2.18 W0 - Pillar 11 git-op pre-check enforcement-narration suppression.

The deterministic git-op regex (`_GIT_OP_PATTERNS` in `aho.council.audit`)
auto-injects an `AUDIT-PILLAR11` finding whenever it matches `git
commit|push|merge|add|...` in the audit target. In 0.2.18 W0, the
acceptance archive narrated the Pillar 11 invariant by *negating* exactly
those ops ("No `git commit`, `git push`, ... from this session") and the
pre-check fired on its own enforcement language - a known false-positive
shape.

Closure: a sentinel-based ±150-char context window suppresses hits when
the local context contains canonical aho enforcement vocabulary
(operator-only, operator-side, agent surfaces, never executes, OPR-,
"No git", etc.).

These tests lock in:
1. Plain unmarked hits remain hits (the safety property is preserved).
2. Each canonical enforcement sentinel suppresses adjacent hits.
3. The literal 0.2.18 W0 acceptance-archive shape is suppressed.
4. Multiple hits in one sentinel-window are all suppressed.
"""
from __future__ import annotations

from aho.council.audit import _scan_git_ops


def test_plain_hit_preserved_without_sentinel():
    text = "Then I ran git commit -m 'wip' on the executor session."
    assert _scan_git_ops(text) == ["git commit"]


def test_operator_only_sentinel_suppresses():
    text = "operator-only operations: git commit, git push, git merge"
    assert _scan_git_ops(text) == []


def test_operator_side_sentinel_suppresses():
    text = "git push to ghcr.io is operator-side per Pillar 11"
    assert _scan_git_ops(text) == []


def test_operator_executed_sentinel_suppresses():
    text = "git rebase is operator-executed; agent never invokes it"
    assert _scan_git_ops(text) == []


def test_agent_surfaces_sentinel_suppresses():
    text = "agent surfaces these for operator: git commit, git push"
    assert _scan_git_ops(text) == []


def test_never_executes_sentinel_suppresses():
    text = "executor never executes git commit in any session"
    assert _scan_git_ops(text) == []


def test_no_git_negation_sentinel_suppresses():
    text = "No `git commit`, `git push`, `git merge`, `git add` were invoked."
    assert _scan_git_ops(text) == []


def test_opr_action_id_sentinel_suppresses():
    text = "OPR-W0-003 - operator runs git push to ghcr.io at W1 close"
    assert _scan_git_ops(text) == []


def test_actual_w0_acceptance_archive_shape_suppressed():
    """The literal 0.2.18 W0 false-positive shape - four ops in one
    negation, expected to suppress every match.
    """
    text = (
        '"evidence": "No `git commit`, `git push`, `git merge`, `git add`, '
        '`git rm`, secret read, or wrapper-bypass invocations from this session."'
    )
    assert _scan_git_ops(text) == []


def test_multiple_hits_in_sentinel_window_all_suppressed():
    text = (
        "operator-only ops list: git commit, git push, git merge, git add, "
        "git reset, git rebase - all routed to operator."
    )
    assert _scan_git_ops(text) == []


def test_hit_outside_sentinel_window_still_fires():
    """A real violation later in the doc must still surface even if an
    earlier sentence used enforcement vocabulary. Window is ±150 chars."""
    prefix = "operator-only ops are surfaced not executed."
    padding = " filler text " * 30  # ~390 chars, > window
    real_violation = "I ran git commit on the executor session."
    text = prefix + padding + real_violation
    assert _scan_git_ops(text) == ["git commit"]


def test_gh_pr_pattern_also_subject_to_suppression():
    text = "operator-only github ops: gh pr create, gh pr merge"
    assert _scan_git_ops(text) == []


def test_gh_pr_pattern_unmarked_still_hits():
    text = "Then I executed gh pr merge on the branch."
    assert _scan_git_ops(text) == ["gh pr merge"]
