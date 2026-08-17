#!/usr/bin/env python3
"""Build a deterministic release ZIP plus SHA-256 checksum."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ZIP = Path.home() / "Desktop" / "BookSkill_图书生产Skills套件_V1.2_2026-08-17.zip"
DEFAULT_SHA = Path.home() / "Desktop" / "BookSkill_图书生产Skills套件_V1.2_2026-08-17_SHA256.txt"
SOURCE_ARCHIVE = ROOT.parent / "图书知识库与制作Skills套件_2026-08-06.zip"
MANIFEST = ROOT / "RELEASE-MANIFEST.json"
FIXED_ZIP_TIME = (2026, 8, 17, 0, 0, 0)
EXCLUDED_PARTS = {
    ".venv",
    "__pycache__",
    ".git",
    ".codegraph",
    ".pytest_cache",
    ".superpowers",
}
EXCLUDED_NAMES = {".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def release_files() -> list[Path]:
    return [
        path
        for path in sorted(ROOT.rglob("*"))
        if path.is_file()
        and path != MANIFEST
        and not EXCLUDED_PARTS.intersection(path.relative_to(ROOT).parts)
        and path.name not in EXCLUDED_NAMES
        and path.suffix not in EXCLUDED_SUFFIXES
    ]


def write_manifest(files: list[Path], release_name: str) -> dict[str, object]:
    if not SOURCE_ARCHIVE.is_file():
        raise FileNotFoundError(f"source archive not found: {SOURCE_ARCHIVE}")
    upstream = json.loads((ROOT / "knowledge" / "indexes" / "upstream-skills.json").read_text(encoding="utf-8"))
    manifest = {
        "release": release_name,
        "version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "built_at": datetime(2026, 8, 17, tzinfo=timezone.utc).isoformat(),
        "source_archive": SOURCE_ARCHIVE.name,
        "source_archive_sha256": sha256(SOURCE_ARCHIVE),
        "upstream_commits": {item["id"]: item["commit"] for item in upstream["skills"]},
        "file_count_excluding_manifest": len(files),
        "files": {
            path.relative_to(ROOT).as_posix(): sha256(path)
            for path in files
        },
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def add_file(archive: zipfile.ZipFile, path: Path) -> None:
    relative = path.relative_to(ROOT).as_posix()
    info = zipfile.ZipInfo(f"book-production-skills-v1/{relative}", FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (0o755 if path.suffix == ".py" else 0o644) << 16
    archive.writestr(info, path.read_bytes())


def build(output_zip: Path, checksum_file: Path, replace: bool) -> str:
    for output in (output_zip, checksum_file):
        if output.exists() and not replace:
            raise FileExistsError(f"output already exists; use --replace: {output}")
    files = release_files()
    write_manifest(files, output_zip.stem)
    files = release_files() + [MANIFEST]
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w") as archive:
        for path in sorted(files):
            add_file(archive, path)
    with zipfile.ZipFile(output_zip) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP integrity failure: {bad}")
    digest = sha256(output_zip)
    checksum_file.write_text(f"{digest}  {output_zip.name}\n", encoding="utf-8")
    return digest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_ZIP)
    parser.add_argument("--checksum", type=Path, default=DEFAULT_SHA)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    digest = build(args.output.resolve(), args.checksum.resolve(), args.replace)
    print(json.dumps({"zip": str(args.output.resolve()), "sha256": digest}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
