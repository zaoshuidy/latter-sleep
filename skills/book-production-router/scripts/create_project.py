#!/usr/bin/env python3
"""Create the three deterministic intake artifacts for a book project."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.contracts import validate_data


def _raise_for_errors(label: str, errors: list[str]) -> None:
    if errors:
        raise ValueError(f"{label}: " + "; ".join(errors))


def _validate_route_requirements(project: dict[str, Any]) -> None:
    mode = project["mode"]
    primary_mode = project.get("primary_mode")
    effective_mode = primary_mode if mode == "hybrid" else mode
    page_plan = project["page_plan"]

    if mode == "hybrid" and primary_mode not in {"template", "memorial"}:
        raise ValueError("primary_mode is required when mode is hybrid")
    if effective_mode == "template" and "fixed_pages" not in page_plan:
        raise ValueError("page_plan.fixed_pages is required for template-led production")
    if effective_mode == "memorial":
        if "min_pages" not in page_plan or "max_pages" not in page_plan:
            raise ValueError("page_plan.min_pages and page_plan.max_pages are required for memorial-led production")
        if page_plan["min_pages"] > page_plan["max_pages"]:
            raise ValueError("page_plan.max_pages must be greater than or equal to min_pages")


def create_project(raw: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, str]]]:
    """Normalize and validate intake data without touching source assets."""
    source = deepcopy(raw)
    assets = source.pop("assets", [])
    project = {"version": "1.0", **source}
    project.setdefault("brand_profile", "paper-boat")

    _raise_for_errors("project-config", validate_data(project, "project-config"))
    _validate_route_requirements(project)

    manifest = {
        "version": "1.0",
        "project_id": project["project_id"],
        "assets": assets,
    }
    _raise_for_errors("asset-manifest", validate_data(manifest, "asset-manifest"))

    asset_ids = [asset["asset_id"] for asset in assets]
    if len(asset_ids) != len(set(asset_ids)):
        raise ValueError("asset-manifest: asset_id values must be unique")

    open_items = []
    for asset in assets:
        if asset["state"] != "received":
            open_items.append(
                {
                    "asset_id": asset["asset_id"],
                    "state": asset["state"],
                    "reason": asset.get("notes") or "素材尚未确认可用",
                }
            )
    return project, manifest, open_items


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="UTF-8 intake JSON")
    parser.add_argument("output_dir", type=Path, help="Project intake directory")
    args = parser.parse_args()

    raw = json.loads(args.input.read_text(encoding="utf-8"))
    project, manifest, open_items = create_project(raw)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(args.output_dir / "project-config.json", project)
    _write_json(args.output_dir / "asset-manifest.json", manifest)
    _write_json(args.output_dir / "open-items.json", open_items)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
