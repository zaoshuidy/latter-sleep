#!/usr/bin/env python3
"""Install the complete suite runtime and expose nine personal Codex Skills."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
import venv
from pathlib import Path


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
MARKER = ".book-production-runtime.json"
LOCATION_INDEX = "LOCATION-INDEX.json"
LOCATION_POINTER = "BOOK-PRODUCTION-LOCATION.json"


def _expected_target(runtime: Path, name: str) -> Path:
    return (runtime / "skills" / name).resolve()


def _entry_points_to(entry: Path, target: Path) -> bool:
    try:
        return (entry.exists() or entry.is_symlink()) and entry.resolve() == target.resolve()
    except OSError:
        return False


def _remove_managed_entry(entry: Path) -> None:
    if entry.is_symlink():
        entry.unlink()
        return
    is_junction = getattr(entry, "is_junction", lambda: False)
    if is_junction():
        entry.rmdir()
        return
    raise FileExistsError(f"managed Skill entry has unexpected type: {entry}")


def _create_skill_entry(entry: Path, target: Path) -> None:
    try:
        entry.symlink_to(target, target_is_directory=True)
        return
    except OSError as error:
        if os.name != "nt" or getattr(error, "winerror", None) != 1314:
            raise
    result = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(entry), str(target)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode or not _entry_points_to(entry, target):
        raise OSError(result.stderr.strip() or result.stdout.strip() or "unable to create Skill junction")


def _validate_source(source: Path) -> None:
    required = [source / "VERSION", source / "schemas", source / "knowledge"]
    required.extend(source / "skills" / name / "SKILL.md" for name in SKILLS)
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise ValueError("invalid suite source; missing: " + ", ".join(missing))


def _preflight(runtime: Path, skill_home: Path, replace: bool) -> None:
    for name in SKILLS:
        entry = skill_home / name
        if _entry_points_to(entry, _expected_target(runtime, name)):
            continue
        if entry.exists() or entry.is_symlink():
            raise FileExistsError(f"unmanaged Skill entry will not be overwritten: {entry}")

    pointer = skill_home / LOCATION_POINTER
    if pointer.exists():
        try:
            pointer_data = json.loads(pointer.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise FileExistsError(f"unmanaged location index will not be overwritten: {pointer}") from error
        if pointer_data.get("suite") != "book-production-skills-v1":
            raise FileExistsError(f"unmanaged location index will not be overwritten: {pointer}")

    if not runtime.exists():
        return
    marker = runtime / MARKER
    if not marker.is_file():
        raise FileExistsError(f"unmanaged runtime will not be overwritten: {runtime}")
    if not replace:
        raise FileExistsError(f"runtime already installed; use --replace to update: {runtime}")


def _ignore(_directory: str, names: list[str]) -> set[str]:
    ignored = {name for name in names if name in {".venv", "__pycache__", ".git", ".codegraph", ".DS_Store"}}
    ignored.update(name for name in names if name.endswith((".pyc", ".pyo")))
    return ignored


def _install_dependencies(stage: Path) -> None:
    environment = stage / ".venv"
    venv.EnvBuilder(with_pip=True, clear=True).create(environment)
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--requirement",
            str(stage / "requirements-dev.txt"),
        ],
        check=True,
    )


def _location_index(source: Path, runtime: Path, skill_home: Path) -> dict[str, object]:
    knowledge = runtime / "knowledge"
    component_libraries = knowledge / "book-component-libraries"
    cover_library = component_libraries / "cover"
    chapter_opener_library = component_libraries / "chapter-opener"
    return {
        "suite": "book-production-skills-v1",
        "version": (source / "VERSION").read_text(encoding="utf-8").strip(),
        "host_scope": "personal-windows" if os.name == "nt" else "personal-mac",
        "locations": {
            "maintenance_source": str(source),
            "installed_runtime": str(runtime),
            "skill_entry_root": str(skill_home),
            "knowledge_root": str(knowledge),
            "human_index": str(runtime / "docs" / "Skill与知识库位置索引.md"),
            "source_archive": str(source.parent / "图书知识库与制作Skills套件_2026-08-06.zip"),
            "release_zip": str(Path.home() / "Desktop" / "BookSkill_图书生产Skills套件_V1.2_2026-08-17.zip"),
            "release_checksum": str(Path.home() / "Desktop" / "BookSkill_图书生产Skills套件_V1.2_2026-08-17_SHA256.txt"),
        },
        "skills": {
            name: {
                "entry": str(skill_home / name),
                "runtime_directory": str(runtime / "skills" / name),
                "skill_file": str(runtime / "skills" / name / "SKILL.md"),
            }
            for name in SKILLS
        },
        "knowledge": {
            "design_cases": str(knowledge / "indexes" / "design-case-index.json"),
            "approved_project_cases": str(
                knowledge / "indexes" / "approved-project-case-index.json"
            ),
            "legacy_reuse_registry": str(knowledge / "indexes" / "legacy-reuse-registry.json"),
            "upstream_skills": str(knowledge / "indexes" / "upstream-skills.json"),
            "paper_boat_brand": str(knowledge / "brand-profiles" / "paper-boat.json"),
            "legacy_originals": str(knowledge / "legacy-sources" / "original-suite"),
            "upstream_snapshots": str(knowledge / "upstream"),
            "maintenance_inbox": str(knowledge / "maintenance" / "inbox"),
            "maintenance_reports": str(knowledge / "maintenance" / "reports"),
            "component_source_registry": str(component_libraries / "source-registry.json"),
            "cover_library_root": str(cover_library),
            "cover_manifest": str(cover_library / "manifest.json"),
            "cover_records": str(cover_library / "records"),
            "cover_assets": str(cover_library / "assets"),
            "chapter_opener_library_root": str(chapter_opener_library),
            "chapter_opener_manifest": str(chapter_opener_library / "manifest.json"),
            "chapter_opener_records": str(chapter_opener_library / "records"),
            "chapter_opener_assets": str(chapter_opener_library / "assets"),
            "running_header_templates": str(runtime / "templates" / "running-headers"),
            "schemas": str(runtime / "schemas"),
            "examples": str(runtime / "examples"),
        },
    }


def install(
    source: Path,
    runtime: Path,
    skill_home: Path,
    replace: bool = False,
    install_dependencies: bool = True,
) -> dict[str, object]:
    source = source.resolve()
    runtime = runtime.resolve()
    skill_home = skill_home.resolve()
    _validate_source(source)
    _preflight(runtime, skill_home, replace)

    runtime.parent.mkdir(parents=True, exist_ok=True)
    skill_home.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    stage = runtime.with_name(f".{runtime.name}.install-{token}")
    backup = runtime.with_name(f".{runtime.name}.backup-{token}")
    moved_old = False
    try:
        shutil.copytree(source, stage, ignore=_ignore)
        if install_dependencies:
            _install_dependencies(stage)
        location_index = _location_index(source, runtime, skill_home)
        (stage / LOCATION_INDEX).write_text(json.dumps(location_index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        marker = {
            "suite": "book-production-skills-v1",
            "version": (stage / "VERSION").read_text(encoding="utf-8").strip(),
            "source": str(source),
            "managed_skills": list(SKILLS),
            "runtime_python": str(
                runtime / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            ) if install_dependencies else None,
        }
        (stage / MARKER).write_text(json.dumps(marker, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        if runtime.exists():
            os.replace(runtime, backup)
            moved_old = True
        os.replace(stage, runtime)

        for name in SKILLS:
            entry = skill_home / name
            if _entry_points_to(entry, runtime / "skills" / name):
                _remove_managed_entry(entry)
            _create_skill_entry(entry, runtime / "skills" / name)

        pointer = {
            "suite": "book-production-skills-v1",
            "version": marker["version"],
            "location_index": str(runtime / LOCATION_INDEX),
            "human_index": str(runtime / "docs" / "Skill与知识库位置索引.md"),
        }
        pointer_tmp = skill_home / f".{LOCATION_POINTER}.{token}.tmp"
        pointer_tmp.write_text(json.dumps(pointer, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(pointer_tmp, skill_home / LOCATION_POINTER)

        if moved_old:
            shutil.rmtree(backup)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        if moved_old and not runtime.exists() and backup.exists():
            os.replace(backup, runtime)
        raise

    return {
        "runtime": str(runtime),
        "skill_home": str(skill_home),
        "location_index": str(runtime / LOCATION_INDEX),
        "location_pointer": str(skill_home / LOCATION_POINTER),
        "version": marker["version"],
        "installed_skills": list(SKILLS),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--runtime", type=Path, default=Path.home() / ".codex" / "book-production-skills-v1")
    parser.add_argument("--skill-home", type=Path, default=Path.home() / ".codex" / "skills")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--skip-dependencies", action="store_true", help="Testing only: do not create the managed Python environment")
    args = parser.parse_args()
    try:
        result = install(args.source, args.runtime, args.skill_home, args.replace, not args.skip_dependencies)
    except (FileExistsError, FileNotFoundError, ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
