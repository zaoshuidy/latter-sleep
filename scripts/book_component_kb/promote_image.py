from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.book_component_kb.paths import load_json
from ai.book_component_kb.review import (
    prepare_promotion,
    validate_sidecar_output,
    write_json_sidecar_atomic as _write_json_atomic,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a human-pending accumulation proposal sidecar without changing an image or library."
    )
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--source-image", type=Path, required=True)
    parser.add_argument(
        "--target-component",
        choices=("cover", "toc", "chapter-opener", "illustration-decoration"),
        required=True,
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    inputs = (args.review, args.source_image)
    try:
        validate_sidecar_output(args.output, inputs)
        proposal = prepare_promotion(
            load_json(args.review), args.source_image, args.target_component
        )
        _write_json_atomic(args.output, proposal, inputs)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
