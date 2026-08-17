#!/usr/bin/env python3
"""Validate fixed-template slots without modifying source content."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.contracts import validate_data


def _item(slot_id: str, status: str, source_asset_id: str | None, reason: str, actions: list[str]) -> dict[str, Any]:
    return {
        "slot_id": slot_id,
        "status": status,
        "source_asset_id": source_asset_id,
        "reason": reason,
        "suggested_actions": actions,
    }


def validate_slots(template: dict[str, Any], assets: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Return one deterministic status per slot plus any template-level error."""
    report: list[dict[str, Any]] = []
    schema_errors = validate_data(template, "template-spec")
    if schema_errors:
        return [_item("__template__", "invalid_template_spec", None, "; ".join(schema_errors), ["修正模板定义后重新校验"])]

    pages = template["pages"]
    if template["fixed_pages"] != len(pages):
        report.append(
            _item(
                "__template__",
                "page_count_mismatch",
                None,
                f"声明 {template['fixed_pages']} 页，实际定义 {len(pages)} 页",
                ["补齐页面定义", "由人工确认固定页数"],
            )
        )

    seen: set[str] = set()
    for page in pages:
        for slot in page["slots"]:
            slot_id = slot["slot_id"]
            asset_id = slot.get("source_asset_id")
            if not asset_id:
                if slot["required"]:
                    report.append(_item(slot_id, "missing_required", None, "必填槽尚未指定素材", ["补充匹配素材", "交由人工确认"])); continue
                report.append(_item(slot_id, "unfilled_optional", None, "可选槽未指定素材", ["保持留白", "补充匹配素材"])); continue

            if asset_id in seen and not slot.get("allow_repeat", False):
                report.append(_item(slot_id, "duplicate_asset", asset_id, "同一素材已在前序槽位使用", ["选择其他素材", "由人工明确批准复用"])); continue
            seen.add(asset_id)

            asset = assets.get(asset_id)
            if asset is None:
                report.append(_item(slot_id, "missing_asset", asset_id, "指定素材不在素材事实表", ["补充素材", "更新素材映射"])); continue
            if asset.get("asset_type") != slot["slot_type"]:
                report.append(_item(slot_id, "type_mismatch", asset_id, "素材类型与槽位类型不一致", ["选择类型匹配的素材"])); continue

            if slot["slot_type"] == "text" and asset.get("char_count", 0) > slot["capacity_chars"]:
                report.append(
                    _item(
                        slot_id,
                        "text_overflow",
                        asset_id,
                        f"完整原文 {asset.get('char_count', 0)} 字，槽位容量 {slot['capacity_chars']} 字",
                        ["增加可变页", "换用容量更大的已批准页面家族", "保持原文并续排到后续页", "交由人工处理"],
                    )
                ); continue

            if slot["slot_type"] == "image":
                actual = asset.get("aspect_ratio")
                expected = slot["aspect_ratio"]
                if not isinstance(actual, (int, float)) or abs(actual - expected) / expected > 0.05:
                    report.append(
                        _item(
                            slot_id,
                            "ratio_mismatch",
                            asset_id,
                            f"图片比例 {actual!r} 与槽位比例 {expected} 不匹配",
                            ["选择比例更匹配的图片", "在不损害关键内容时调整裁切比例", "交由人工处理"],
                        )
                    ); continue

            report.append(_item(slot_id, "ready", asset_id, "素材与槽位匹配", []))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("asset_facts", type=Path)
    parser.add_argument("project_id")
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    template = json.loads(args.template.read_text(encoding="utf-8"))
    assets = json.loads(args.asset_facts.read_text(encoding="utf-8"))
    report = validate_slots(template, assets)
    pages = template.get("pages", [])
    page_plan = {
        "version": "1.0",
        "project_id": args.project_id,
        "page_families": sorted({page["family_id"] for page in pages}),
        "pages": pages,
        "overflow_items": [item for item in report if item["status"] not in {"ready", "unfilled_optional"}],
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "slot-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "page-plan.json").write_text(json.dumps(page_plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
