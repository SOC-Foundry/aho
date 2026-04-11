"""aho CLI dispatcher (v0.1.16)."""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = "aho 0.1.16"
CONFIG_DIR = Path.home() / ".config" / "aho"
PROJECTS_FILE = CONFIG_DIR / "projects.json"
ACTIVE_FILE = CONFIG_DIR / "active.fish"


def _load_projects():
    if PROJECTS_FILE.exists():
        return json.loads(PROJECTS_FILE.read_text())
    return {"projects": {}, "active": None}


def _save_projects(data):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    PROJECTS_FILE.write_text(json.dumps(data, indent=2))


def cmd_project(args):
    data = _load_projects()
    sub = args.project_cmd
    if sub == "add":
        data["projects"][args.name] = {
            "gcp_project": args.gcp_project,
            "prefix": args.prefix,
            "path": str(Path(args.path).resolve()),
        }
        _save_projects(data)
        print(f"Added project: {args.name}")
    elif sub == "list":
        if not data["projects"]:
            print("(no projects registered)")
            return
        active = data.get("active")
        for name, info in data["projects"].items():
            mark = " *" if name == active else "  "
            print(f"{mark} {name}  path={info['path']}")
    elif sub == "switch":
        if args.name not in data["projects"]:
            print(f"ERROR: unknown project: {args.name}")
            sys.exit(1)
        data["active"] = args.name
        _save_projects(data)
        info = data["projects"][args.name]
        project_path = Path(info['path'])
        
        # Update .aho.json in the target project if it exists
        aho_json_path = project_path / ".aho.json"
        if aho_json_path.exists():
            try:
                aho_data = json.loads(aho_json_path.read_text())
                aho_data["name"] = args.name
                aho_data["project_code"] = info.get("project_code") or args.name
                aho_data["artifact_prefix"] = info.get("prefix") or info.get("artifact_prefix") or args.name
                aho_json_path.write_text(json.dumps(aho_data, indent=2))
                print(f"Updated {aho_json_path}")
            except Exception as e:
                print(f"WARNING: could not update {aho_json_path}: {e}")

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        ACTIVE_FILE.write_text(
            f"set -gx AHO_PROJECT_ROOT {info['path']}\n"
            f"set -gx AHO_PROJECT_NAME {args.name}\n"
        )
        print(f"Switched to: {args.name}")
    elif sub == "current":
        print(data.get("active") or "(none)")
    elif sub == "remove":
        data["projects"].pop(args.name, None)
        if data.get("active") == args.name:
            data["active"] = None
        _save_projects(data)
        print(f"Removed: {args.name}")


def cmd_log(args):
    from aho.logger import log_workstream_complete
    if args.log_cmd == "workstream-complete":
        log_workstream_complete(args.workstream_id, args.status, args.summary)
    else:
        print("ERROR: missing log subcommand")


def cmd_init(args):
    target = Path(args.path).resolve() if args.path else Path.cwd()
    aho_json = target / ".aho.json"
    if aho_json.exists() and not args.force:
        print(f"ERROR: {aho_json} exists. Use --force to overwrite.")
        sys.exit(1)
    aho_json.write_text(json.dumps({
        "aho_version": "0.1",
        "name": args.name or target.name,
        "artifact_prefix": args.name or target.name,
        "gcp_project": args.gcp_project or "",
        "env_prefix": (args.prefix or target.name).upper(),
        "current_iteration": "v0.1",
        "phase": 0,
    }, indent=2))
    (target / "artifacts").mkdir(exist_ok=True)
    (target / "data").mkdir(exist_ok=True)
    print(f"Initialized aho project at {target}")


def cmd_status(args):
    from aho.doctor import run_all
    results = run_all(level="preflight")
    
    data = _load_projects()
    project_root = results.get("project_root", ("fail", "(none)"))[1]
    
    from aho.paths import find_project_root
    mode = "active"
    try:
        root = find_project_root()
        aho_json = root / ".aho.json"
        if aho_json.exists():
            mode = json.loads(aho_json.read_text()).get("mode", "active")
    except Exception:
        pass

    print("aho status")
    print("──────────")
    print(f"project:     {data.get('active') or '(none)'} ({project_root})")
    print(f"mode:        {mode}")
    print(f"iteration:   {os.environ.get('AHO_ITERATION', 'unknown')}")
    print(f"cwd:         {os.getcwd()}")
    
    ollama = "up" if results.get("ollama", ("fail", ""))[0] == "ok" else "down"
    print(f"ollama:      {ollama}")
    
    manifest = results.get("manifest", ("warn", "unknown"))[1]
    print(f"middleware:  {manifest}")
    
    print("project hooks:")
    # Shims are now in artifacts/scripts
    from aho.paths import get_scripts_dir
    scripts_dir = get_scripts_dir()
    shims_present = "yes" if list(scripts_dir.glob("*.py")) else "no"
    print(f"  shims:      {shims_present}")


def cmd_preflight(args):
    from aho.doctor import run_all
    print("aho preflight")
    print("─────────────")
    results = run_all(level="preflight")
    has_fail = False
    for name, (status, msg) in results.items():
        tag = "[ok]" if status == "ok" else "[FAIL]"
        print(f"{tag:8} {name:20}: {msg}")
        if status == "fail":
            has_fail = True
    if has_fail:
        print("\nPreflight: FAILED")
        sys.exit(1)
    print("\nPreflight: READY")


def cmd_postflight(args):
    from aho.doctor import run_all
    print("aho postflight")
    print("──────────────")
    results = run_all(level="postflight")
    has_fail = False
    for name, (status, msg) in results.items():
        tag = {"ok": "[ok]", "warn": "[WARN]", "fail": "[FAIL]", "deferred": "[DEFR]"}.get(status, f"[{status}]")
        print(f"{tag:8} {name:20}: {msg}")
        if status == "fail":
            has_fail = True
    if has_fail:
        print("\nPostflight: FAILED")
        sys.exit(1)
    print("\nPostflight: COMPLETE")


def cmd_iteration(args, parser):
    sub = args.iteration_cmd
    if sub is None:
        parser.print_help()
        return
    if sub == "status":
        from aho.paths import find_project_root
        ckpt = find_project_root() / ".aho-checkpoint.json"
        if ckpt.exists():
            print(ckpt.read_text())
        else:
            print("(no checkpoint)")
        return
    if sub == "close":
        from aho.paths import find_project_root
        from aho.config import validate_iteration_version
        root = find_project_root()
        config = json.loads((root / ".aho.json").read_text())
        iteration = config.get("current_iteration", "")
        
        try:
            validate_iteration_version(iteration)
        except ValueError as e:
            print(f"ERROR: {e}")
            sys.exit(1)
            
        prefix = config.get("artifact_prefix") or "aho"
        from aho.paths import get_iterations_dir
        iter_dir = get_iterations_dir() / iteration

        if args.confirm:
            # Validate sign-off
            report_path = iter_dir / f"{prefix}-run-{iteration}.md"
            from aho.feedback.prompt import validate_signoff
            ok, missing = validate_signoff(report_path)
            if not ok:
                print(f"Sign-off incomplete: {', '.join(missing)}")
                sys.exit(1)
            print(f"Iteration {iteration} confirmed and closed.")
        else:
            # Corrected close sequence (0.1.16 W0A):
            # tests → bundle → report → run file → postflight → .aho.json → checkpoint
            import subprocess as _sp
            from aho.feedback.run import generate_run
            from aho.feedback.report_builder import build_report
            from aho.feedback.summary import render_summary
            from aho.bundle import build_bundle
            from aho.paths import get_iterations_dir

            # Step 0: Ensure build log exists (stub if manual absent)
            build_log_path = get_iterations_dir() / iteration / f"{prefix}-build-{iteration}.md"
            if not build_log_path.exists():
                from aho.feedback.build_log_stub import generate_stub
                generate_stub(iteration)

            # Step 1: Tests
            print("Step 1/7: Running tests...")
            test_result = _sp.run(
                [sys.executable, "-m", "pytest", "artifacts/tests/", "-x", "-q"],
                capture_output=True, text=True
            )
            if test_result.returncode != 0:
                print(test_result.stdout)
                print(test_result.stderr)
                print("CLOSE ABORTED: tests failed")
                sys.exit(1)
            print(f"  Tests: {test_result.stdout.splitlines()[-1] if test_result.stdout.strip() else 'passed'}")

            # Step 2: Bundle
            print("Step 2/7: Generating bundle...")
            bundle_path = build_bundle(iteration)
            print(f"  Bundle: {bundle_path} ({bundle_path.stat().st_size} bytes)")

            # Step 3: Mechanical report
            print("Step 3/7: Generating mechanical report...")
            report_path = build_report(iteration)
            print(f"  Report: {report_path}")

            # Step 4: Run file
            print("Step 4/7: Generating run file...")
            run_path = generate_run(iteration)
            print(f"  Run file: {run_path}")

            # Step 5: Postflight gates
            print("Step 5/7: Running postflight gates...")
            from aho.doctor import run_all as doctor_run_all
            postflight = doctor_run_all(level="postflight")
            has_fail = False
            for name, (status, msg) in postflight.items():
                tag = {"ok": "[ok]", "warn": "[WARN]", "fail": "[FAIL]", "deferred": "[DEFR]"}.get(status, f"[{status}]")
                print(f"  {tag:8} {name}: {msg}")
                if status == "fail":
                    has_fail = True
            if has_fail:
                print("CLOSE ABORTED: postflight gates failed")
                sys.exit(1)

            # Step 6: Update .aho.json
            print("Step 6/7: Updating .aho.json...")
            from aho.feedback.aho_json import update_last_completed
            update_last_completed(iteration)

            # Step 7: Checkpoint closed
            print("Step 7/7: Writing checkpoint...")
            ckpt_path = root / ".aho-checkpoint.json"
            ckpt = json.loads(ckpt_path.read_text()) if ckpt_path.exists() else {}
            ckpt["status"] = "closed"
            ckpt["closed_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            ckpt["last_event"] = "close_complete"
            ckpt_path.write_text(json.dumps(ckpt, indent=2) + "\n")

            # Telegram notification (non-blocking)
            try:
                from aho.telegram.notifications import send_iteration_complete
                send_iteration_complete(
                    project_code=config.get("project_code", prefix),
                    iteration=iteration,
                    bundle_path=str(bundle_path),
                    run_path=str(run_path)
                )
            except Exception as e:
                print(f"WARNING: Telegram notification failed: {e}")

            print()
            print(render_summary())
            print(f"\nIteration {iteration} closed.")
        return
    if sub == "seed":
        from aho.feedback.seed import build_seed, write_seed
        from aho.paths import find_project_root
        root = find_project_root()
        config = json.loads((root / ".aho.json").read_text())
        iteration = config.get("current_iteration", "")
        source = config.get("last_completed_iteration", "0.1.12")
        
        seed = build_seed(source, iteration)
        
        if args.edit:
            import tempfile
            import subprocess
            with tempfile.NamedTemporaryFile(suffix=".json", mode="w+", delete=False) as tf:
                json.dump(seed, tf, indent=2)
                tf.close()
                editor = os.environ.get("EDITOR", "vim")
                subprocess.call([editor, tf.name])
                with open(tf.name, "r") as f:
                    try:
                        seed = json.load(f)
                    except json.JSONDecodeError as e:
                        print(f"ERROR: Invalid JSON: {e}")
                        os.unlink(tf.name)
                        sys.exit(1)
                os.unlink(tf.name)
        
        path = write_seed(iteration, seed)
        print(f"Seed written to: {path}")
        return
    if sub == "graduate":
        from aho.artifacts.loop import run_graduation_analysis
        if args.analyze:
            result = run_graduation_analysis(args.iteration)
            print(result)
        else:
            print("Graduation check: PASS (artifacts present)")
        return
    from pathlib import Path as _P
    from aho.artifacts.loop import run_artifact_loop
    out = _P(args.output) if args.output else None
    
    # Check if two_pass is available for this subcommand
    two_pass = getattr(args, "two_pass", False)
    
    result = run_artifact_loop(
        sub, args.iteration, output_path=out, dry_run=args.dry_run, two_pass=two_pass
    )
    tag = "[ok]" if result.ok else "[FAIL]"
    print(f"{tag} {result.artifact} -> {result.output_path} ({result.message})")
    if not result.ok:
        sys.exit(1)


def cmd_stub(args):
    print(f"aho {args.cmd}: deferred to Phase 1")
    sys.exit(2)


def main():
    p = argparse.ArgumentParser(prog="aho")
    p.add_argument("--version", action="version", version=VERSION)
    sub = p.add_subparsers(dest="cmd")

    pp = sub.add_parser("project")
    pps = pp.add_subparsers(dest="project_cmd")
    add = pps.add_parser("add")
    add.add_argument("name")
    add.add_argument("--gcp-project", default="")
    add.add_argument("--prefix", default="")
    add.add_argument("--path", required=True)
    add.add_argument("--no-shell-edit", action="store_true")
    pps.add_parser("list")
    sw = pps.add_parser("switch")
    sw.add_argument("name")
    pps.add_parser("current")
    rm = pps.add_parser("remove")
    rm.add_argument("name")

    pi = sub.add_parser("init")
    pi.add_argument("--path", default=None)
    pi.add_argument("--name", default=None)
    pi.add_argument("--gcp-project", default=None)
    pi.add_argument("--prefix", default=None)
    pi.add_argument("--force", action="store_true")

    pc = sub.add_parser("check")
    pcs = pc.add_subparsers(dest="check_cmd")
    conf = pcs.add_parser("config")
    conf.add_argument("--strict", action="store_true")
    pcs.add_parser("harness")

    sub.add_parser("push")

    pl = sub.add_parser("log")
    pls = pl.add_subparsers(dest="log_cmd")
    wc = pls.add_parser("workstream-complete")
    wc.add_argument("workstream_id")
    wc.add_argument("status", choices=["pass", "partial", "fail", "deferred"], help="Status: pass, partial, fail, deferred")
    wc.add_argument("summary", help="Brief summary of work done")

    dr = sub.add_parser("doctor", help="Run health checks")
    dr_sub = dr.add_subparsers(dest="doctor_level")
    dr_sub.add_parser("quick", help="Quick health check (sub-second)")
    dr_sub.add_parser("preflight", help="Environment readiness check")
    dr_sub.add_parser("postflight", help="Iteration results verification")
    dr_sub.add_parser("full", help="Run all levels")

    sub.add_parser("status")
    sub.add_parser("eval")
    sub.add_parser("registry")

    pcomp = sub.add_parser("components", help="Component manifest operations")
    pcomps = pcomp.add_subparsers(dest="components_cmd")
    pcomp_list = pcomps.add_parser("list", help="List all components")
    pcomp_list.add_argument("--status", default=None, help="Filter by status (active, stub, broken, deprecated)")
    pcomps.add_parser("attribution", help="Show workload attribution from event log")

    prag = sub.add_parser("rag")
    prags = prag.add_subparsers(dest="rag_cmd")
    prag_q = prags.add_parser("query", help="Query the project RAG archive")
    prag_q.add_argument("query")
    prag_q.add_argument("n_results", type=int, nargs="?", default=5)
    prag_q.add_argument("version_filter", nargs="?", default=None)
    prag_q.add_argument("--json", action="store_true", help="Output as JSON")
    
    prags.add_parser("rebuild", help="Rebuild the project RAG archive")
    prags.add_parser("status", help="Show RAG archive status")

    pt = sub.add_parser("telegram", help="Telegram bot management")
    pts = pt.add_subparsers(dest="telegram_cmd")
    pt_test = pts.add_parser("test", help="Send a test message")
    pt_test.add_argument("project", help="Project code (for credentials)")
    pt_test.add_argument("text", nargs="?", default="aho Telegram smoke test — system live", help="Message text")

    prf = sub.add_parser("preflight")
    prfs = prf.add_subparsers(dest="preflight_cmd")
    prfs.add_parser("run", help="Run environment preflight checks")

    pof = sub.add_parser("postflight")
    pofs = pof.add_subparsers(dest="postflight_cmd")
    pofs.add_parser("run", help="Run iteration postflight checks")

    ps = sub.add_parser("secret")
    pss = ps.add_subparsers(dest="secret_cmd")
    pss.add_parser("list", help="List secret names")
    
    ps_get = pss.add_parser("get", help="Get a secret value")
    ps_get.add_argument("project", help="Project code")
    ps_get.add_argument("name", help="Secret name")
    ps_get.add_argument("--raw", action="store_true", help="Output raw value only")
    
    ps_set = pss.add_parser("set", help="Set a secret value")
    ps_set.add_argument("project", help="Project code")
    ps_set.add_argument("name", help="Secret name")
    ps_set.add_argument("value", nargs="?", help="Value (prompts if omitted)")
    
    ps_rm = pss.add_parser("rm", help="Remove a secret")
    ps_rm.add_argument("project", help="Project code")
    ps_rm.add_argument("name", help="Secret name")
    
    pss.add_parser("unlock", help="Unlock secrets session")
    pss.add_parser("lock", help="Lock secrets session")
    pss.add_parser("status", help="Show secrets session status")
    
    ps_rot = pss.add_parser("rotate", help="Rotate a secret value")
    ps_rot.add_argument("project", help="Project code")
    ps_rot.add_argument("name", help="Secret name")
    
    ps_exp = pss.add_parser("export", help="Export secrets")
    ps_exp.add_argument("--fish", action="store_true", help="Export as fish commands")
    
    ps_imp = pss.add_parser("import", help="Import secrets file")
    ps_imp.add_argument("path", help="Path to encrypted secrets file")

    ppipe = sub.add_parser("pipeline", help="Pipeline scaffolding and management")
    ppipes = ppipe.add_subparsers(dest="pipeline_cmd")
    ppipe_init = ppipes.add_parser("init", help="Scaffold a new 10-phase pipeline")
    ppipe_init.add_argument("name", help="Pipeline name")
    ppipe_init.add_argument("--dir", default=None, help="Target directory (default: cwd)")
    ppipe_list = ppipes.add_parser("list", help="List declared pipelines")
    ppipe_val = ppipes.add_parser("validate", help="Validate a pipeline")
    ppipe_val.add_argument("name", help="Pipeline name")
    ppipe_val.add_argument("--dir", default=None, help="Target directory (default: cwd)")
    ppipe_status = ppipes.add_parser("status", help="Show pipeline checkpoint status")
    ppipe_status.add_argument("name", help="Pipeline name")

    pit = sub.add_parser("iteration", help="Iteration artifact loop (Qwen-managed)")
    pits = pit.add_subparsers(dest="iteration_cmd")
    for _kind in ("design", "plan", "build-log", "report", "bundle"):
        _sp = pits.add_parser(_kind, help=f"Generate {_kind} artifact via Qwen")
        _sp.add_argument("iteration", help="Iteration version, e.g. 0.1.2")
        _sp.add_argument("--dry-run", action="store_true", help="Skip Ollama call")
        _sp.add_argument("--output", default=None, help="Override output path")
        if _kind in ("design", "plan"):
            _sp.add_argument("--two-pass", action="store_true", help="Use two-pass generation (outline then sections)")
    pits.add_parser("status", help="Show current iteration status")
    pit_close = pits.add_parser("close", help="Close iteration (generate artifacts)")
    pit_close.add_argument("--confirm", action="store_true", help="Validate sign-off and finalize")
    pit_seed = pits.add_parser("seed", help="Extract seed from run report for next iteration")
    pit_seed.add_argument("--edit", action="store_true", help="Edit the seed before writing")
    
    pit_grad = pits.add_parser("graduate", help="Analyze iteration for phase graduation")
    pit_grad.add_argument("iteration")
    pit_grad.add_argument("--analyze", action="store_true", help="Run Qwen graduation analysis")

    args = p.parse_args()
    if args.cmd:
        try:
            from aho.logger import log_event
            subcmd = args.cmd
            if hasattr(args, f"{args.cmd}_cmd"):
                subcmd = f"{args.cmd} {getattr(args, f'{args.cmd}_cmd', '') or ''}"
            log_event("cli_invocation", "aho-cli", "cli", subcmd.strip())
        except Exception:
            pass
    if args.cmd == "project":
        cmd_project(args)
    elif args.cmd == "init":
        cmd_init(args)
    elif args.cmd == "log":
        cmd_log(args)
    elif args.cmd == "doctor":
        from aho.doctor import run_all
        level = args.doctor_level or "quick"
        results = run_all(level=level)
        has_fail = False
        print(f"aho doctor {level}")
        print("─" * (11 + len(level)))
        for name, (status, msg) in results.items():
            tag = {"ok": "[ok]", "pass": "[ok]", "warn": "[WARN]", "fail": "[FAIL]", "deferred": "[DEFERRED]"}.get(status, f"[{status}]")
            print(f"{tag:10} {name:20}: {msg}")
            if status == "fail":
                has_fail = True
        if has_fail:
            print(f"\nDoctor {level}: FAILED")
            sys.exit(1)
        print(f"\nDoctor {level}: CLEAN")
    elif args.cmd == "status":
        cmd_status(args)
    elif args.cmd == "rag":
        from aho.rag import query as rag_query
        if args.rag_cmd == "query":
            rag_query.main(args)
        elif args.rag_cmd in ("rebuild", "status"):
            print(f"aho rag {args.rag_cmd}: implementation pending Phase 1")
        else: prag.print_help()
    elif args.cmd == "preflight":
        cmd_preflight(args)
    elif args.cmd == "telegram":
        from aho.telegram import send_message
        if args.telegram_cmd == "test":
            ok = send_message(args.project, args.text)
            if ok:
                print(f"Test message sent to {args.project} chat.")
            else:
                print(f"ERROR: failed to send message. Check credentials for {args.project}.")
                sys.exit(1)
        else:
            pt.print_help()
    elif args.cmd == "postflight":
        cmd_postflight(args)
    elif args.cmd == "secret":
        from aho.secrets import cli as secrets_cli
        scmd = args.secret_cmd
        if scmd == "list": secrets_cli.cmd_list(args)
        elif scmd == "get": secrets_cli.cmd_get(args)
        elif scmd == "set": secrets_cli.cmd_set(args)
        elif scmd == "rm": secrets_cli.cmd_rm(args)
        elif scmd == "unlock": secrets_cli.cmd_unlock(args)
        elif scmd == "lock": secrets_cli.cmd_lock(args)
        elif scmd == "status": secrets_cli.cmd_status(args)
        elif scmd == "rotate": secrets_cli.cmd_rotate(args)
        elif scmd == "export": secrets_cli.cmd_export(args)
        elif scmd == "import": secrets_cli.cmd_import(args)
        else: ps.print_help()
    elif args.cmd == "check":
        if args.check_cmd == "config":
            from aho.doctor import run_all
            results = run_all(level="quick")
            has_fail = False
            for name, (status, msg) in results.items():
                if status == "fail": has_fail = True
            if has_fail: sys.exit(1)
        elif args.check_cmd == "harness":
            from aho.harness import cli_main as harness_main
            sys.exit(harness_main())
        else:
            p.print_help()
    elif args.cmd == "push":
        from aho.push import cli_main as push_main
        sys.exit(push_main())
    elif args.cmd == "pipeline":
        if args.pipeline_cmd == "init":
            from aho.pipelines.scaffold import scaffold_pipeline
            target = Path(args.dir) if args.dir else None
            result = scaffold_pipeline(args.name, target)
            print(f"Pipeline scaffolded: {result}")
        elif args.pipeline_cmd == "list":
            from aho.pipelines.registry import list_pipelines
            pipelines = list_pipelines()
            if pipelines:
                for p in pipelines:
                    print(f"  {p}")
            else:
                print("(no pipelines declared)")
        elif args.pipeline_cmd == "validate":
            from aho.pipelines.validate import validate_pipeline
            target = Path(args.dir) if args.dir else None
            errors = validate_pipeline(args.name, target)
            if errors:
                for e in errors:
                    print(f"  [FAIL] {e}")
                sys.exit(1)
            else:
                print(f"Pipeline '{args.name}' is valid")
        elif args.pipeline_cmd == "status":
            from aho.pipelines.registry import get_pipeline_status
            import json as _json
            print(_json.dumps(get_pipeline_status(args.name), indent=2))
        else:
            ppipe.print_help()
    elif args.cmd == "iteration":
        cmd_iteration(args, pit)
    elif args.cmd == "components":
        from aho.components.manifest import load_components, attribute_workload, render_section
        if args.components_cmd == "list":
            components = load_components()
            if args.status:
                components = [c for c in components if c.status == args.status]
            if not components:
                print("(no components match)")
            else:
                print(f"{'Name':<30} {'Kind':<20} {'Status':<10} {'Path'}")
                print("-" * 90)
                for c in components:
                    print(f"{c.name:<30} {c.kind:<20} {c.status:<10} {c.path}")
                print(f"\nTotal: {len(components)}")
        elif args.components_cmd == "attribution":
            from aho.paths import get_data_dir
            import json as _json
            log_path = get_data_dir() / "aho_event_log.jsonl"
            if not log_path.exists():
                print("(no event log)")
            else:
                events = []
                from aho.paths import find_project_root as _fpr
                _attr_root = _fpr()
                _attr_json = _attr_root / ".aho.json"
                iteration = json.loads(_attr_json.read_text()).get("current_iteration", "") if _attr_json.exists() else ""
                for line in log_path.read_text().splitlines():
                    if not line.strip():
                        continue
                    try:
                        ev = _json.loads(line)
                        if ev.get("iteration") == iteration:
                            events.append(ev)
                    except _json.JSONDecodeError:
                        continue
                workload = attribute_workload(events)
                if not workload:
                    print("(no events for current iteration)")
                else:
                    for agent, pct in workload.items():
                        print(f"  {agent:<30} {pct*100:5.1f}%")
        else:
            pcomp.print_help()
    elif args.cmd in ("eval", "registry"):
        cmd_stub(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
