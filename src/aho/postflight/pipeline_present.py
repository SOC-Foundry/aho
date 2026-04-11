"""Post-flight check: pipeline validation for consumer projects."""


def check():
    """Returns (status, message). SKIP if project has no pipelines."""
    from aho.pipelines.registry import list_pipelines

    pipelines = list_pipelines()
    if not pipelines:
        return ("ok", "SKIP — no pipelines declared in .aho.json")

    from aho.pipelines.validate import validate_pipeline
    from aho.paths import find_project_root

    root = find_project_root()
    all_errors = []
    for name in pipelines:
        errors = validate_pipeline(name, root)
        all_errors.extend(errors)

    if all_errors:
        return ("fail", f"{len(all_errors)} errors: {'; '.join(all_errors[:3])}")
    return ("ok", f"{len(pipelines)} pipeline(s) valid")
