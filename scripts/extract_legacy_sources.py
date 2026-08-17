#!/usr/bin/env python3
"""Selectively copy immutable legacy source files from the original ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from pathlib import Path
from zipfile import ZipFile


SUITE_ROOT = "图书知识库与制作Skills套件_2026-08-06"
V1_SELECTION = {
    f"{SUITE_ROOT}/02-核心Skills/openclaw/chapter-opener-design/SKILL.md": "chapter-opener-design/SKILL.md",
    f"{SUITE_ROOT}/02-核心Skills/openclaw/toc-design/SKILL.md": "toc-design/SKILL.md",
    f"{SUITE_ROOT}/02-核心Skills/openclaw/running-headers-design/SKILL.md": "running-headers-design/SKILL.md",
    f"{SUITE_ROOT}/02-核心Skills/openclaw/print-composition/SKILL.md": "print-composition/SKILL.md",
    f"{SUITE_ROOT}/03-补充Skills/chinese-book-interior-typesetting/SKILL.md": "chinese-book-interior-typesetting/SKILL.md",
    f"{SUITE_ROOT}/02-核心Skills/openclaw/paper-boat-brand/SKILL.md": "paper-boat-brand/SKILL.md",
}


def _safe_target(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise ValueError(f"unsafe target path: {relative}")
    target = root.joinpath(*rel.parts)
    if root.resolve() not in target.resolve().parents:
        raise ValueError(f"unsafe target path: {relative}")
    return target


def extract_selected(zip_path: Path, target: Path, mapping: dict[str, str]) -> dict[str, dict[str, object]]:
    """Extract exactly the mapping entries; never mutate the archive."""
    zip_path = Path(zip_path)
    target = Path(target)
    resolved_targets = {source: _safe_target(target, relative) for source, relative in mapping.items()}

    with ZipFile(zip_path) as archive:
        normalized_names = {unicodedata.normalize("NFC", name): name for name in archive.namelist()}
        actual_names: dict[str, str] = {}
        for source in mapping:
            normalized = unicodedata.normalize("NFC", source)
            if normalized not in normalized_names:
                raise KeyError(f"legacy source not found: {source}")
            actual_names[source] = normalized_names[normalized]

        result: dict[str, dict[str, object]] = {}
        for source, destination in resolved_targets.items():
            data = archive.read(actual_names[source])
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            result[source] = {
                "target_path": destination.relative_to(target).as_posix(),
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
            }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_path", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    result = extract_selected(args.zip_path, args.target, V1_SELECTION)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
