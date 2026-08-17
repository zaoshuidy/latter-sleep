from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.book_component_kb.paths import load_json
from ai.book_component_kb.retrieve import retrieve


def retrieval_limit(value: str) -> int:
    parsed = int(value)
    if not 1 <= parsed <= 5:
        raise argparse.ArgumentTypeError("must be an integer from 1 through 5")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Retrieve deterministic, explainable references from an available cover library."
    )
    parser.add_argument(
        "--component-root",
        type=Path,
        required=True,
        help="required available cover component directory.",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        required=True,
        help="required shared source-registry JSON path.",
    )
    parser.add_argument(
        "--query",
        type=Path,
        required=True,
        help="required book-component-retrieval-query JSON path.",
    )
    parser.add_argument(
        "--limit",
        type=retrieval_limit,
        required=True,
        help="required result count from 1 through 5.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        query = load_json(args.query)
        result = retrieve(args.component_root, args.registry, query, args.limit)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(
            json.dumps({"error": str(error)}, ensure_ascii=False, sort_keys=True),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
