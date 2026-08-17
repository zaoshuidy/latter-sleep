#!/usr/bin/env python3
"""Run the complete offline release validation for the Skill suite."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
SKILLS = (
    "book-production-router",
    "build-template-book",
    "plan-memorial-book",
    "design-book-editorial",
    "create-book-images",
    "review-book-production",
    "build-book-flipbook",
    "build-indesign-book",
    "evolve-book-skills",
)
PLANNED_COMPONENTS = (
    "toc",
    "illustration-decoration",
)
COMPONENT_VALIDATION_TIMEOUT_SECONDS = 120


def run(label: str, command: list[str]) -> None:
    print(f"\n[{label}]")
    result = subprocess.run(command, cwd=ROOT, text=True)
    if result.returncode:
        raise SystemExit(result.returncode)


def verify_upstream() -> None:
    index_path = ROOT / "knowledge" / "indexes" / "upstream-skills.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    sys.path.insert(0, str(ROOT / "scripts"))
    from fetch_upstream_skill import verify_snapshot

    errors: list[str] = []
    for record in index["skills"]:
        snapshot = ROOT / record["snapshot_path"]
        errors.extend(f"{record['id']}: {item}" for item in verify_snapshot(snapshot, record["files"]))
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"\n[upstream] verified {len(index['skills'])} immutable snapshot(s)")


def component_validation_command(
    *,
    root: Path = ROOT,
    python_executable: str = sys.executable,
    component: str = "cover",
) -> list[str]:
    """Build one production component-library validation command."""
    library_root = root / "knowledge" / "book-component-libraries"
    return [
        python_executable,
        str(root / "scripts" / "book_component_kb" / "validate_library.py"),
        "--component-root",
        str(library_root / component),
        "--registry",
        str(library_root / "source-registry.json"),
        "--required-count",
        "50",
    ]


def _component_summary(cover_status: str, chapter_status: str = "planned") -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "components": [
            {"component": "cover", "status": cover_status},
            {"component": "toc", "status": "planned"},
            {"component": "chapter-opener", "status": chapter_status},
            {"component": "illustration-decoration", "status": "planned"},
        ],
    }


def validate_component_libraries(
    *,
    root: Path = ROOT,
    runner: Callable[..., object] = subprocess.run,
    python_executable: str = sys.executable,
) -> dict[str, object]:
    """Run the read-only cover validator and enforce release availability."""
    command = component_validation_command(
        root=root,
        python_executable=python_executable,
    )
    cover_root = root / "knowledge" / "book-component-libraries" / "cover"
    try:
        result = runner(
            command,
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
            timeout=COMPONENT_VALIDATION_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        result = subprocess.CompletedProcess(
            command,
            1,
            stdout="",
            stderr=(
                "component validator timed out after "
                f"{COMPONENT_VALIDATION_TIMEOUT_SECONDS} seconds"
            ),
        )
    except OSError as error:
        result = subprocess.CompletedProcess(command, 1, stdout="", stderr=str(error))

    stdout = getattr(result, "stdout", "") or ""
    stderr = getattr(result, "stderr", "") or ""
    returncode = getattr(result, "returncode", 1)
    if stdout:
        print(stdout.rstrip())
    if stderr:
        print(stderr.rstrip(), file=sys.stderr)

    try:
        validator_report = json.loads(stdout)
    except (json.JSONDecodeError, TypeError):
        validator_report = None

    available = (
        cover_root.is_dir()
        and returncode == 0
        and isinstance(validator_report, dict)
        and validator_report.get("valid") is True
        and validator_report.get("status") == "available"
        and isinstance(validator_report.get("record_count"), int)
        and not isinstance(validator_report.get("record_count"), bool)
        and validator_report["record_count"] >= 50
        and isinstance(validator_report.get("errors"), list)
        and not validator_report["errors"]
    )
    if available:
        cover_status = "available"
    elif not cover_root.is_dir():
        cover_status = "missing"
    else:
        cover_status = "building"

    chapter_status = "planned"
    chapter_root = root / "knowledge" / "book-component-libraries" / "chapter-opener"
    if chapter_root.is_dir():
        chapter_command = component_validation_command(
            root=root,
            python_executable=python_executable,
            component="chapter-opener",
        )
        try:
            chapter_result = runner(
                chapter_command,
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
                timeout=COMPONENT_VALIDATION_TIMEOUT_SECONDS,
            )
        except (subprocess.TimeoutExpired, OSError):
            chapter_result = None
        if chapter_result is not None:
            try:
                chapter_report = json.loads(getattr(chapter_result, "stdout", "") or "")
            except (json.JSONDecodeError, TypeError):
                chapter_report = None
            if isinstance(chapter_report, dict) and chapter_report.get("valid") is True:
                chapter_status = (
                    "available"
                    if chapter_report.get("status") == "available"
                    and isinstance(chapter_report.get("record_count"), int)
                    and not isinstance(chapter_report.get("record_count"), bool)
                    and chapter_report["record_count"] >= 50
                    and chapter_report.get("errors") == []
                    else "building"
                )
            else:
                chapter_status = "invalid"

    summary = _component_summary(cover_status, chapter_status)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    if not available:
        exit_code = returncode if isinstance(returncode, int) and returncode > 0 else 1
        raise SystemExit(exit_code)
    return summary


def main(
    *,
    run_step: Callable[[str, list[str]], None] = run,
    component_gate: Callable[[], dict[str, object]] = validate_component_libraries,
    upstream_verifier: Callable[[], None] = verify_upstream,
) -> int:
    run_step(
        "unit and end-to-end tests",
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
    )

    validator = Path.home() / ".codex" / "skills" / ".system" / "skill-creator" / "scripts" / "quick_validate.py"
    if not validator.is_file():
        raise SystemExit(f"quick_validate.py not found: {validator}")
    for name in SKILLS:
        run_step(
            f"Skill validation: {name}",
            [sys.executable, str(validator), str(ROOT / "skills" / name)],
        )

    run_step(
        "design case coverage",
        [
            sys.executable,
            "skills/design-book-editorial/scripts/check_case_library.py",
            "knowledge/indexes/design-case-index.json",
        ],
    )
    component_gate()
    upstream_verifier()
    print(
        f"\nPASS: {len(SKILLS)} Skills, schema/tests, case coverage, "
        "cover availability, and upstream integrity"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
