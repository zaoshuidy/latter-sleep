#!/usr/bin/env python3
"""Evaluate a candidate Skill using fixed evidence thresholds."""

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


def evaluate_candidate(baseline: list[dict[str, Any]], candidate: list[dict[str, Any]]) -> dict[str, Any]:
    before = {item["case_id"]: float(item["score"]) for item in baseline}
    after = {item["case_id"]: float(item["score"]) for item in candidate}
    if len(before) != len(baseline) or len(after) != len(candidate):
        raise ValueError("case_id values must be unique")
    if set(before) != set(after):
        raise ValueError("baseline and candidate must use the same case_ids")
    if any(score < 0 or score > 1 for score in [*before.values(), *after.values()]):
        raise ValueError("scores must be between 0 and 1")

    count = len(before)
    baseline_score = sum(before.values()) / count if count else 0.0
    candidate_score = sum(after.values()) / count if count else 0.0
    improvement = ((candidate_score - baseline_score) / baseline_score) if baseline_score else (1.0 if candidate_score > 0 else 0.0)
    regressions = sorted(case_id for case_id in before if after[case_id] < before[case_id])
    reasons = []
    if count < 15:
        reasons.append("fewer than 15 confirmed cases")
    if improvement + 1e-12 < 0.10:
        reasons.append("relative improvement is below 10 percent")
    if regressions:
        reasons.append("one or more cases regressed")
    status = "rejected" if reasons else "proposed"
    proposal = {
        "version": "1.0",
        "case_count": count,
        "baseline_score": round(baseline_score, 6),
        "candidate_score": round(candidate_score, 6),
        "improvement": round(improvement, 6),
        "regressions": regressions,
        "human_approval": "pending",
        "rollback_path": "archive/skills/formal-previous",
        "status": status,
        "reasons": reasons,
    }
    errors = validate_data(proposal, "evolution-proposal")
    if errors:
        raise ValueError("evolution-proposal: " + "; ".join(errors))
    return proposal


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    before = json.loads(args.baseline.read_text(encoding="utf-8"))
    after = json.loads(args.candidate.read_text(encoding="utf-8"))
    proposal = evaluate_candidate(before, after)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if proposal["status"] == "proposed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
