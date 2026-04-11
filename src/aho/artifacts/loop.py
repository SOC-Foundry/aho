"""The Qwen-managed artifact loop.

run_artifact_loop() renders the appropriate Jinja2 template for an
artifact kind, sends it to Qwen via Ollama, validates the response with
the cheap structural checks in schemas.py, and writes the final Markdown
to the iteration's artifacts directory.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, NamedTuple

from aho.artifacts.qwen_client import QwenClient
from aho.artifacts.repetition_detector import DegenerateGenerationError
from aho.artifacts.evaluator import evaluate_text
from aho.artifacts.schemas import SCHEMAS, validate_artifact
from aho.artifacts.templates import render_prompt
from aho.artifacts.context import build_full_context
from aho.paths import find_project_root, get_iterations_dir
from aho.rag.archive import query_archive
from aho.logger import log_event


class LoopResult(NamedTuple):
    artifact: str
    output_path: Path
    words: int
    ok: bool
    message: str
    retries: int = 0


ARTIFACT_KINDS: List[str] = ["design", "plan", "build-log", "report", "bundle", "run"]
MAX_RETRIES = 3


def _project_meta() -> Dict:
    root = find_project_root()
    aho_json = root / ".aho.json"
    if not aho_json.exists():
        return {}
    return json.loads(aho_json.read_text())


def _iteration_dir(iteration: str) -> Path:
    return get_iterations_dir() / iteration


def _build_workstreams() -> List[dict]:
    """Helper for template rendering."""
    root = find_project_root()
    ckpt_path = root / ".aho-checkpoint.json"
    if not ckpt_path.exists():
        return []
    
    ckpt = json.loads(ckpt_path.read_text())
    streams = []
    for wid, info in sorted(ckpt.get("workstreams", {}).items()):
        if isinstance(info, str):
            # Handle simple status strings used in early iteration skeletons
            streams.append({
                "id": wid,
                "description": "",
                "status": info,
                "agent": "unknown"
            })
        else:
            streams.append({
                "id": wid,
                "description": info.get("description", ""),
                "status": info.get("status", "pending"),
                "agent": info.get("agent", "unknown")
            })
    return streams


def _load_prior(iteration: str, current_artifact: str) -> Dict[str, str]:
    """Load artifacts already generated for this iteration."""
    prior = {}
    iter_dir = _iteration_dir(iteration)
    meta = _project_meta()
    prefix = meta.get("artifact_prefix", "aho")

    for earlier in ARTIFACT_KINDS:
        if earlier == current_artifact:
            break
        
        # Check both canonical and versioned filenames
        paths = [
            iter_dir / f"{prefix}-{earlier}-{iteration}.md",
            iter_dir / f"{prefix}-{earlier}-{iteration.split('.')[0]}.{iteration.split('.')[1]}.{iteration.split('.')[2]}.md"
        ]
        for p in paths:
            if p.exists():
                prior[earlier] = p.read_text()
                break
    return prior


def _build_system_prompt(seed_text: str = "") -> str:
    """Build the enriched system prompt with trident, pillars, and bundle spec."""
    from aho.artifacts.templates import _load_harness_blocks
    blocks = _load_harness_blocks()

    prompt = (
        "You are Qwen acting as the aho artifact author. Produce a single "
        "well-structured Markdown document for the requested aho iteration "
        "artifact. Be concrete, reference workstreams by id (W0, W1, W2, ...), and "
        "write so a junior engineer with no prior aho context can follow along. "
        "Do not output anything except the artifact body.\n\n"
        "=== THE ELEVEN PILLARS ===\n"
        f"{blocks.get('pillars_block', blocks.get('ten_pillars_block', ''))}\n\n"
        "=== BUNDLE STRUCTURE (§1–§22) ===\n"
        "Every iteration produces a bundle with 22 sections: "
        "§1 Design, §2 Plan, §3 Build Log, §4 Report, §5 Run Report, "
        "§6 Harness, §7 README, §8 CHANGELOG, §9 CLAUDE.md, §10 GEMINI.md, "
        "§11 .aho.json, §12 Sidecars, §13 Gotcha Registry, §14 Script Registry, "
        "§15 MANIFEST, §16 install.fish, §17 COMPATIBILITY, §18 projects.json, "
        "§19 Event Log, §20 File Inventory, §21 Environment, §22 Component Checklist.\n"
    )

    if seed_text:
        prompt += f"\n\n=== GROUND TRUTH (SEED) ===\n{seed_text}\n"
    
    return prompt


def generate_outline(artifact_type: str, seed: dict, context: str) -> dict:
    """Produce an outline for a document using Nemotron (better at JSON)."""
    client = QwenClient(model="nemotron-mini:4b")
    system = _build_system_prompt(seed_text=json.dumps(seed, indent=2))
    prompt = (
        f"Produce an outline for a {artifact_type} document for iteration {seed.get('target_iteration')}.\n"
        "Respond with a JSON object following this schema:\n"
        "{\n"
        "  \"sections\": [\n"
        "    {\"id\": \"sec1\", \"title\": \"Section Title\", \"summary\": \"What to cover\", \"target_words\": 300}\n"
        "  ]\n"
        "}\n"
        f"Context enrichment:\n{context}"
    )
    
    text = client.generate(prompt, system=system, json_format=True)
    
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end != -1:
            return json.loads(text[start:end])
        return json.loads(text)
    except Exception as e:
        print(f"[aho.loop] Failed to parse outline JSON: {e}", file=sys.stderr)
        raise NotImplementedError(f"Two-pass failed: outline unparseable: {e}")


def generate_section(section: dict, seed: dict, context: str, artifact_type: str) -> str:
    """Generate a single section of an artifact."""
    client = QwenClient()
    system = _build_system_prompt(seed_text=json.dumps(seed, indent=2))
    
    prompt = (
        f"Task: Write section '{section['title']}' for the {artifact_type} artifact.\n"
        f"Summary of section: {section['summary']}\n"
        f"Target length: {section['target_words']} words.\n\n"
        f"Relevant context:\n{context}\n\n"
        "Output the section content in Markdown, including the header. Do not output anything else."
    )
    
    max_tokens = int(section.get("target_words", 500) * 2.0)
    return client.generate(prompt, system=system, max_tokens=max_tokens)


def assemble_from_sections(sections_text: List[str], artifact_type: str, metadata: dict) -> str:
    """Concatenate sections into a single document."""
    header = f"# {metadata.get('prefix', 'aho')} {artifact_type} — {metadata.get('iteration')}\n\n"
    return header + "\n\n".join(sections_text)


def run_graduation_analysis(iteration: str) -> str:
    """Special one-off loop for phase graduation check."""
    system = _build_system_prompt()
    prompt = (
        f"Perform a graduation analysis for iteration {iteration}. "
        "Recommend graduation to Phase 1 based on the Pillars and the Phase 0 objective."
    )
    
    client = QwenClient()
    text = client.generate(prompt, system=system)
    return text


def generate_build_log_synthesis(iteration: str) -> Path:
    """Check for manual build log and return its path."""
    meta = _project_meta()
    prefix = meta.get("artifact_prefix", "aho")
    manual_path = _iteration_dir(iteration) / f"{prefix}-build-log-{iteration}.md"
    if not manual_path.exists():
        raise FileNotFoundError(
            f"Manual build log not found at {manual_path}. "
            f"Write the manual build log first, then run synthesis. See ADR-042."
        )
    return manual_path


def run_artifact_loop(
    artifact: str,
    iteration: str,
    *,
    output_path: Optional[Path] = None,
    client: Optional[QwenClient] = None,
    dry_run: bool = False,
    two_pass: bool = False,
) -> LoopResult:
    if artifact not in SCHEMAS:
        raise ValueError(f"unknown artifact: {artifact}")

    meta = _project_meta()
    prefix = meta.get("artifact_prefix", "aho")
    iter_dir = _iteration_dir(iteration)

    if artifact == "build-log" and not dry_run:
        generate_build_log_synthesis(iteration)
    iter_dir.mkdir(parents=True, exist_ok=True)

    spec = SCHEMAS[artifact]

    # Load seed
    seed_path = iter_dir / "seed.json"
    seed_text = ""
    seed_data = {}
    if seed_path.exists():
        try:
            seed_data = json.loads(seed_path.read_text())
            seed_text = json.dumps(seed_data, indent=2)
        except Exception:
            pass

    context = {
        "iteration": iteration,
        "prefix": prefix,
        "project": meta.get("name", "aho"),
        "project_code": meta.get("project_code", "ahomw"),
        "now_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "workstreams": _build_workstreams(),
        "prior_artifacts": _load_prior(iteration, artifact),
        "seed": seed_text,
    }

    if two_pass:
        print(f"[aho.loop] Starting two-pass generation for {artifact}...", file=sys.stderr)
        from aho.artifacts.context import get_rag_context
        rag = get_rag_context(context["project_code"], artifact, iteration)
        
        outline = generate_outline(artifact, seed_data, rag)
        sections = []
        for i, sec in enumerate(outline.get("sections", [])):
            print(f"[aho.loop] Generating section {i+1}/{len(outline['sections'])}: {sec['title']}", file=sys.stderr)
            sec_rag = query_archive(context["project_code"], f"{artifact} {sec['title']} {sec['summary']}", top_k=2)
            sec_rag_text = "\n\n".join([r["document"] for r in sec_rag])
            
            section_text = generate_section(sec, seed_data, sec_rag_text, artifact)
            sections.append(section_text)
        
        best_text = assemble_from_sections(sections, artifact, context)
        best_words = len(best_text.split())
        ok = True
        msg = f"two-pass complete ({best_words} words)"
        retries = 0

        eval_result = evaluate_text(best_text, project_root=find_project_root(),
                                    seed=seed_data, artifact_type=f"{artifact}_synthesis")
        if eval_result["severity"] == "reject":
            log_event("synthesis_evaluator_reject", "evaluator", artifact,
                      "evaluate", output_summary=str(eval_result["errors"][:3]),
                      status="reject", error=eval_result["message"])
            ok = False
            msg = f"synthesis evaluator rejected: {eval_result['message']}"
    else:
        prompt = render_prompt(artifact, context)
        prompt = build_full_context(context["project_code"], artifact, iteration, base_context=prompt)

        if dry_run:
            text = (
                f"# DRY RUN — {artifact} for iteration {iteration}\n\n"
                f"prompt length: {len(prompt)} chars\n"
            )
            if output_path is None:
                suffix = "-synthesis" if artifact == "build-log" else ""
                output_path = iter_dir / f"{prefix}-{artifact}{suffix}-{iteration}.md"
            output_path.write_text(text)
            return LoopResult(
                artifact=artifact,
                output_path=output_path,
                words=len(text.split()),
                ok=True,
                message="dry run",
            )

        if artifact in ("design", "plan"):
            canonical = iter_dir / f"{prefix}-{artifact}-{iteration}.md"
            parts = iteration.split(".")
            version = f"{parts[0]}.{parts[1]}.{parts[2]}" if len(parts) >= 3 else iteration
            version_path = iter_dir / f"{prefix}-{artifact}-{version}.md"
            if canonical.exists() or version_path.exists():
                existing = canonical if canonical.exists() else version_path
                text = existing.read_text()
                return LoopResult(
                    artifact=artifact,
                    output_path=existing,
                    words=len(text.split()),
                    ok=True,
                    message=f"immutable — using existing {existing.name} (ADR-012)",
                )

        client = client or QwenClient()
        system = _build_system_prompt(seed_text=seed_text)

        best_text = ""
        best_words = 0
        retries = 0

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if attempt > 1:
                    ok, msg = validate_artifact(artifact, best_text)
                    eval_result = evaluate_text(best_text, project_root=find_project_root(),
                                                seed=seed_data, artifact_type=f"{artifact}_synthesis")

                    retry_prompt = (
                        f"{prompt}\n\n"
                        f"IMPORTANT: Your previous output failed validation: {msg}\n"
                    )
                    if eval_result["errors"]:
                        retry_prompt += f"Hallucinations detected: {eval_result['errors']}\n"
                    
                    retry_prompt += (
                        "Please correct the structural issues and ensure all required sections are present. "
                        "Do not pad with repetition if you run out of content."
                    )
                    text = client.generate(retry_prompt, system=system)
                else:
                    text = client.generate(prompt, system=system)
                
                text = text.strip() + "\n"
            except DegenerateGenerationError as e:
                print(f"[aho.loop] DEGENERATE GENERATION DETECTED: {e}", file=sys.stderr)
                best_text = f"\n\n<!-- DEGENERATE GENERATION DETECTED: {e} -->\n\n"
                best_words = 0
                break

            best_text = text
            best_words = len(text.split())
            
            ok, msg = validate_artifact(artifact, text)
            eval_result = evaluate_text(text, project_root=find_project_root(),
                                       seed=seed_data, artifact_type=f"{artifact}_synthesis")
            if eval_result["severity"] == "reject":
                log_event("synthesis_evaluator_reject", "evaluator", artifact,
                          "evaluate", output_summary=str(eval_result["errors"][:3]),
                          status="reject", error=eval_result["message"])
                ok = False
                msg = f"Hallucination rejection: {eval_result['message']}. Issues: {eval_result['errors']}"

            if ok:
                break

            retries += 1
            print(f"[aho.loop] {artifact} attempt {attempt}: {msg}, retrying...",
                file=sys.stderr)

    if output_path is None:
        suffix = "-synthesis" if artifact == "build-log" else ""
        output_path = iter_dir / f"{prefix}-{artifact}{suffix}-{iteration}.md"

    output_path.write_text(best_text)

    return LoopResult(
        artifact=artifact,
        output_path=output_path,
        words=best_words,
        ok=ok,
        message=msg if not ok else f"ok ({best_words} words)",
        retries=retries,
    )
