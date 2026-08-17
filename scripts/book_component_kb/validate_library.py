from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.book_component_kb.validate import validate_library


def positive_integer(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate an existing book component knowledge base without rebuilding it."
    )
    parser.add_argument(
        "--component-root",
        type=Path,
        required=True,
        help="required prebuilt component directory containing records/, assets/, and derivatives.",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        required=True,
        help="required shared source-registry JSON path.",
    )
    parser.add_argument(
        "--required-count",
        type=positive_integer,
        default=50,
        help="availability threshold (default: 50).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = validate_library(args.component_root, args.registry, args.required_count)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if not report["valid"]:
        return 1
    return 0 if report["status"] == "available" else 2


if __name__ == "__main__":
    raise SystemExit(main())
