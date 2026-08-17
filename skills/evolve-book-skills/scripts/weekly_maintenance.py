#!/usr/bin/env python3
"""Build a non-destructive weekly knowledge-maintenance plan."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


def build_maintenance_plan(items: list[dict[str, Any]]) -> dict[str, Any]:
    plan = {
        "week": date.today().isoformat(),
        "added": [],
        "archive_moves": [],
        "invalid_indexes": [],
        "upstream_updates": [],
        "evolution_candidates": [],
    }
    for item in items:
        item_id, state, path = item["id"], item["state"], item["path"]
        if path.startswith("knowledge/upstream/"):
            if state in {"updated", "expired", "negative"}:
                plan["upstream_updates"].append({"id": item_id, "action": "snapshot-new-version-and-propose-index-switch"})
            continue
        if state == "accepted":
            plan["added"].append(item_id)
        elif state in {"expired", "negative", "duplicate"}:
            plan["archive_moves"].append({
                "id": item_id,
                "from": path,
                "to": f"archive/weekly/{date.today().isoformat()}/{Path(path).name}",
                "reason": state,
            })
        elif state == "invalid-index":
            plan["invalid_indexes"].append(item_id)
        elif state == "evolution-candidate":
            plan["evolution_candidates"].append(item_id)
    return plan


def _markdown(plan: dict[str, Any]) -> str:
    sections = [
        ("新增", plan["added"]),
        ("归档", plan["archive_moves"]),
        ("失效索引", plan["invalid_indexes"]),
        ("上游更新候选", plan["upstream_updates"]),
        ("进化候选", plan["evolution_candidates"]),
    ]
    lines = [f"# 每周知识库维护报告 {plan['week']}", ""]
    for title, values in sections:
        lines.extend([f"## {title}", "", json.dumps(values, ensure_ascii=False, indent=2), ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    items = json.loads(args.input.read_text(encoding="utf-8"))
    plan = build_maintenance_plan(items)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "archive-moves.json").write_text(json.dumps(plan["archive_moves"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "weekly-report.md").write_text(_markdown(plan), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
