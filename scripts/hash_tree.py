#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def hash_tree(root: Path, excludes: set[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in excludes for part in path.relative_to(root).parts):
            continue
        result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a stable SHA-256 manifest for a directory tree.")
    parser.add_argument("root", type=Path)
    parser.add_argument("--exclude", action="append", default=[])
    args = parser.parse_args()
    print(json.dumps(hash_tree(args.root.resolve(), set(args.exclude)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
