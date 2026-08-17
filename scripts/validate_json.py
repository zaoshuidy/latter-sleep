#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from ai.contracts import load_and_validate


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a project JSON file against a suite schema.")
    parser.add_argument("schema")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        load_and_validate(args.path, args.schema)
    except (FileNotFoundError, ValueError) as exc:
        print(exc)
        return 1
    print(f"valid: {args.schema} {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
