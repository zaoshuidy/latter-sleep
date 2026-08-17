#!/usr/bin/env python3
"""Review production integrity and enforce two formal human gates."""

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


def _safe_project_file(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if candidate != root.resolve() and root.resolve() not in candidate.parents:
        raise ValueError(f"source path escapes project root: {relative}")
    return candidate


def review_project(project_root: Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    data = json.loads((root / "review-input.json").read_text(encoding="utf-8"))
    errors = validate_data(data, "review-input")
    if errors:
        raise ValueError("review-input: " + "; ".join(errors))

    integrity_failures = []
    for source in data["source_texts"]:
        path = _safe_project_file(root, source["path"])
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if actual != source["expected_sha256"]:
            integrity_failures.append(source["source_id"])

    checks = [{
        "check_id": "source_integrity",
        "status": "passed" if not integrity_failures else "failed",
        "reason": "all source hashes match" if not integrity_failures else "hash mismatch: " + ", ".join(integrity_failures),
    }]
    for check_id, passed in data["production_checks"].items():
        checks.append({
            "check_id": check_id,
            "status": "passed" if passed else "failed",
            "reason": "confirmed" if passed else "production check not satisfied",
        })

    failed = any(item["status"] == "failed" for item in checks)
    gates = data["gates"]
    if failed:
        status, next_action = "blocked", "resolve_failed_checks"
    elif gates["sample_review"] != "approved":
        status, next_action = "blocked", "await_sample_review"
    elif gates["final_review"] != "approved":
        status, next_action = "ready", "await_final_review"
    else:
        status, next_action = "approved", "complete"

    report = {
        "version": "1.0",
        "project_id": data["project_id"],
        "checks": checks,
        "gates": gates,
        "status": status,
        "next_action": next_action,
    }
    report_errors = validate_data(report, "review-report")
    if report_errors:
        raise ValueError("review-report: " + "; ".join(report_errors))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    report = review_project(args.project_root)
    output_dir = args.output_dir or args.project_root
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "review-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "gate-status.json").write_text(json.dumps(report["gates"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if report["status"] == "approved" else 2


if __name__ == "__main__":
    raise SystemExit(main())
