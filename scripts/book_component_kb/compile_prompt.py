from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.book_component_kb.paths import load_json
from ai.book_component_kb.prompts import compile_component_prompt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile an approved component selection into a text-free prompt sidecar JSON."
    )
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--genome", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--output-spec", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="destination JSON sidecar; this command never generates image files.",
    )
    return parser.parse_args()


def _write_json_atomic(path: Path, value: dict) -> None:
    if not path.parent.is_dir():
        raise ValueError("output parent directory must already exist")
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as file:
            json.dump(value, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def _paths_alias(first: Path, second: Path) -> bool:
    first_real = os.path.normcase(os.path.realpath(os.path.abspath(first)))
    second_real = os.path.normcase(os.path.realpath(os.path.abspath(second)))
    if first_real == second_real:
        return True
    try:
        return os.path.samefile(first, second)
    except (FileNotFoundError, OSError):
        return False


def _reject_output_input_alias(output: Path, inputs: tuple[Path, ...]) -> None:
    if any(_paths_alias(output, input_path) for input_path in inputs):
        raise ValueError("output path must not alias any input path")


def main() -> int:
    args = parse_args()
    try:
        input_paths = (
            args.project,
            args.genome,
            args.selection,
            args.output_spec,
        )
        _reject_output_input_alias(args.output, input_paths)
        prompt = compile_component_prompt(
            load_json(args.project),
            load_json(args.genome),
            load_json(args.selection),
            load_json(args.output_spec),
        )
        _reject_output_input_alias(args.output, input_paths)
        _write_json_atomic(args.output, prompt)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
