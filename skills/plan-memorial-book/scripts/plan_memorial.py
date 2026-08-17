#!/usr/bin/env python3
"""Build traceable memorial planning artifacts from read-only source files."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.contracts import validate_data


AXES = ("people", "times", "places", "events", "themes", "image_links", "gaps")
ALLOWED_BASES = {"time", "theme", "place", "relationship", "event", "object", "photo", "hybrid"}


def _raise_for_errors(label: str, data: dict[str, Any], schema: str) -> None:
    errors = validate_data(data, schema)
    if errors:
        raise ValueError(f"{label}: " + "; ".join(errors))


def build_content_map(
    project_id: str,
    sources: dict[str, Path],
    axes: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    missing = [key for key in AXES if key not in axes]
    if missing:
        raise ValueError("content axes missing: " + ", ".join(missing))
    hashes = {source_id: hashlib.sha256(Path(path).read_bytes()).hexdigest() for source_id, path in sorted(sources.items())}
    result = {
        "version": "1.0",
        "project_id": project_id,
        **{key: axes[key] for key in AXES},
        "source_text_hashes": hashes,
    }
    _raise_for_errors("content-map", result, "content-map")
    return result


def validate_structure_options(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(options) not in {2, 3}:
        raise ValueError("structure_options must contain 2 or 3 candidates")
    ids: set[str] = set()
    for option in options:
        required = {"option_id", "bases", "rationale", "unit_order"}
        missing = required - option.keys()
        if missing:
            raise ValueError("structure option missing: " + ", ".join(sorted(missing)))
        if option["option_id"] in ids:
            raise ValueError("option_id values must be unique")
        ids.add(option["option_id"])
        if not option["bases"] or not set(option["bases"]).issubset(ALLOWED_BASES):
            raise ValueError("structure option contains an unsupported basis")
        if any(key in option for key in ("default", "priority", "rank")):
            raise ValueError("structure candidates must not encode a default priority")
    return options


def build_toc_brief(project_id: str, entries: list[dict[str, Any]], layout_scope: str = "to-be-designed") -> dict[str, Any]:
    result = {"version": "1.0", "project_id": project_id, "layout_scope": layout_scope, "entries": entries}
    _raise_for_errors("toc-brief", result, "toc-brief")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    raw = json.loads(args.input.read_text(encoding="utf-8"))

    project_id = raw["project_id"]
    sources = {key: Path(value) for key, value in raw["sources"].items()}
    content_map = build_content_map(project_id, sources, raw["content_axes"])
    options = validate_structure_options(raw["structure_options"])
    structure_output = {"version": "1.0", "project_id": project_id, "options": options}
    _raise_for_errors("structure-options", structure_output, "structure-options")
    toc_brief = build_toc_brief(project_id, raw["toc_entries"], raw.get("layout_scope", "to-be-designed"))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "content-map.json": content_map,
        "structure-options.json": structure_output,
        "toc-brief.json": toc_brief,
    }
    for name, data in outputs.items():
        (args.output_dir / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
