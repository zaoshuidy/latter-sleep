#!/usr/bin/env python3
"""Validate confirmed design-case coverage and traceability."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


COMPONENTS = ("cover", "toc", "chapter-opener", "body", "image-page", "running-headers")
REQUIRED = {
    "case_id", "source_url", "source_type", "book_category", "page_component",
    "verification_status", "verified_at", "design_facts", "reuse_scope",
    "borrowed_elements", "changed_elements",
}


def check_case_library(index: dict[str, Any], components: list[str] | tuple[str, ...] = COMPONENTS, minimum: int = 10) -> dict[str, Any]:
    errors: list[str] = []
    counts: Counter[str] = Counter()
    seen: set[str] = set()
    for position, case in enumerate(index.get("cases", [])):
        missing = REQUIRED - case.keys()
        if missing:
            errors.append(f"case[{position}] missing: {', '.join(sorted(missing))}")
            continue
        case_id = case["case_id"]
        if case_id in seen:
            errors.append(f"duplicate case_id: {case_id}")
        seen.add(case_id)
        if case["verification_status"] == "confirmed":
            if not case["source_url"].startswith("https://"):
                errors.append(f"{case_id}: confirmed source must use https")
            if not case["design_facts"] or not case["borrowed_elements"] or not case["changed_elements"]:
                errors.append(f"{case_id}: confirmed case lacks facts or transformation record")
            counts[case["page_component"]] += 1
    missing_counts = {component: max(0, minimum - counts[component]) for component in components if counts[component] < minimum}
    return {
        "ok": not errors and not missing_counts,
        "confirmed_counts": {component: counts[component] for component in components},
        "missing": missing_counts,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index", type=Path)
    parser.add_argument("--minimum", type=int, default=10)
    args = parser.parse_args()
    result = check_case_library(json.loads(args.index.read_text(encoding="utf-8")), COMPONENTS, args.minimum)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
