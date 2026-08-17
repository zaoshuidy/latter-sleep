from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.book_component_kb.build import build_library


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build deterministic book component knowledge-base indexes.")
    parser.add_argument(
        "--component-root",
        type=Path,
        required=True,
        help="required component directory containing records/ and assets/.",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        required=True,
        help="required shared source-registry JSON path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_library(args.component_root, args.registry)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
