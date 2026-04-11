"""Unit tests for aho.harness alignment rules (10.68.1 W4)."""
import pathlib
import tempfile
from aho.harness import check_alignment, parse_base_harness, parse_project_harness


def write(path, text):
    path.write_text(text)


def test_clean():
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        base = d / "base.md"
        proj = d / "project.md"
        write(base, "### ahomw-ADR-001\nbody\n### ahomw-Pattern-01\nbody\n")
        write(proj, "**Project code:** kjtco\n**Base imports (acknowledged):**\n- ahomw-ADR-001..001\n- ahomw-Pattern-01..01\n\n### kjtco-ADR-001\nbody\n")
        v = check_alignment(base, proj)
        assert all(x.severity != "fail" for x in v), v
        assert all(x.severity != "warn" for x in v), v


def test_rule_a_collision():
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        base = d / "base.md"
        proj = d / "project.md"
        write(base, "### ahomw-ADR-001\nx\n")
        write(proj, "**Project code:** kjtco\n**Base imports (acknowledged):**\n- ahomw-ADR-001..001\n\n### foo01-ADR-001\nbody\n")
        v = check_alignment(base, proj)
        assert any(x.rule == "A" and x.severity == "fail" for x in v)


def test_rule_b_base_definition_in_project():
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        base = d / "base.md"
        proj = d / "project.md"
        write(base, "### ahomw-ADR-001\nx\n")
        write(proj, "**Project code:** kjtco\n**Base imports (acknowledged):**\n- ahomw-ADR-001..001\n\n### ahomw-ADR-002\nbad\n")
        v = check_alignment(base, proj)
        assert any(x.rule == "B" and x.severity == "fail" for x in v)


def test_rule_c_warn_unacknowledged():
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        base = d / "base.md"
        proj = d / "project.md"
        write(base, "### ahomw-ADR-001\nx\n### ahomw-ADR-002\ny\n")
        write(proj, "**Project code:** kjtco\n**Base imports (acknowledged):**\n- ahomw-ADR-001..001\n\n")
        v = check_alignment(base, proj)
        assert any(x.rule == "C" and x.severity == "warn" for x in v)


if __name__ == "__main__":
    test_clean()
    test_rule_a_collision()
    test_rule_b_base_definition_in_project()
    test_rule_c_warn_unacknowledged()
    print("all harness tests passed")
