from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from scripts import validate_all


def completed(returncode: int, payload: object, stderr: str = "") -> SimpleNamespace:
    return SimpleNamespace(
        returncode=returncode,
        stdout=json.dumps(payload, ensure_ascii=False),
        stderr=stderr,
    )


class ValidateAllComponentKnowledgeBaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name) / "suite"
        self.root.mkdir()
        self.cover_root = (
            self.root / "knowledge" / "book-component-libraries" / "cover"
        )

    def _run_gate(self, result: SimpleNamespace) -> tuple[dict[str, object], list[object]]:
        calls: list[object] = []

        def runner(command: list[str], **kwargs: object) -> SimpleNamespace:
            calls.append((command, kwargs))
            return result

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            summary = validate_all.validate_component_libraries(
                root=self.root,
                runner=runner,
                python_executable="/fixture/python",
            )
        self.assertEqual(1, len(calls))
        self.assertEqual(summary, json.loads(output.getvalue().strip().splitlines()[-1]))
        return summary, calls

    def test_command_uses_exact_validator_roots_and_required_count_fifty(self) -> None:
        command = validate_all.component_validation_command(
            root=self.root,
            python_executable="/fixture/python",
        )

        library_root = self.root / "knowledge" / "book-component-libraries"
        self.assertEqual(
            [
                "/fixture/python",
                str(self.root / "scripts" / "book_component_kb" / "validate_library.py"),
                "--component-root",
                str(library_root / "cover"),
                "--registry",
                str(library_root / "source-registry.json"),
                "--required-count",
                "50",
            ],
            command,
        )

    def test_missing_cover_runs_real_command_reports_missing_and_fails(self) -> None:
        calls: list[object] = []

        def runner(command: list[str], **kwargs: object) -> SimpleNamespace:
            calls.append((command, kwargs))
            return completed(1, {"valid": False, "status": "invalid"})

        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as raised:
            validate_all.validate_component_libraries(
                root=self.root,
                runner=runner,
                python_executable="/fixture/python",
            )

        self.assertEqual(1, raised.exception.code)
        self.assertEqual(1, len(calls))
        summary = json.loads(output.getvalue().strip().splitlines()[-1])
        self.assertEqual("missing", summary["components"][0]["status"])
        self.assertEqual(
            ["planned", "planned", "planned"],
            [item["status"] for item in summary["components"][1:]],
        )

    def test_building_cover_reports_building_and_propagates_validator_failure(self) -> None:
        self.cover_root.mkdir(parents=True)
        output = io.StringIO()

        def runner(command: list[str], **kwargs: object) -> SimpleNamespace:
            return completed(
                2,
                {"valid": True, "status": "building", "record_count": 12},
            )

        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as raised:
            validate_all.validate_component_libraries(root=self.root, runner=runner)

        self.assertEqual(2, raised.exception.code)
        summary = json.loads(output.getvalue().strip().splitlines()[-1])
        self.assertEqual("building", summary["components"][0]["status"])

    def test_invalid_existing_cover_fails_and_cannot_be_reported_available(self) -> None:
        self.cover_root.mkdir(parents=True)
        output = io.StringIO()

        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as raised:
            validate_all.validate_component_libraries(
                root=self.root,
                runner=lambda *_args, **_kwargs: completed(
                    1,
                    {"valid": False, "status": "invalid", "errors": ["hash mismatch"]},
                ),
            )

        self.assertEqual(1, raised.exception.code)
        summary = json.loads(output.getvalue().strip().splitlines()[-1])
        self.assertEqual("building", summary["components"][0]["status"])

    def test_available_cover_passes_and_other_components_stay_planned(self) -> None:
        self.cover_root.mkdir(parents=True)
        summary, calls = self._run_gate(
            completed(
                0,
                {
                    "valid": True,
                    "status": "available",
                    "record_count": 50,
                    "errors": [],
                },
            )
        )

        self.assertEqual(
            {
                "schema_version": "1.0",
                "components": [
                    {"component": "cover", "status": "available"},
                    {"component": "toc", "status": "planned"},
                    {"component": "chapter-opener", "status": "planned"},
                    {"component": "illustration-decoration", "status": "planned"},
                ],
            },
            summary,
        )
        _, kwargs = calls[0]
        self.assertEqual(self.root, kwargs["cwd"])
        self.assertTrue(kwargs["text"])
        self.assertTrue(kwargs["capture_output"])
        self.assertFalse(kwargs["check"])
        self.assertEqual(validate_all.COMPONENT_VALIDATION_TIMEOUT_SECONDS, kwargs["timeout"])

    def test_existing_valid_chapter_library_is_reported_building_without_blocking_cover(self) -> None:
        self.cover_root.mkdir(parents=True)
        chapter_root = self.cover_root.parent / "chapter-opener"
        chapter_root.mkdir()
        calls: list[list[str]] = []

        def runner(command: list[str], **_kwargs: object) -> SimpleNamespace:
            calls.append(command)
            if str(chapter_root) in command:
                return completed(
                    2,
                    {
                        "valid": True,
                        "status": "building",
                        "record_count": 18,
                        "errors": [],
                    },
                )
            return completed(
                0,
                {
                    "valid": True,
                    "status": "available",
                    "record_count": 50,
                    "errors": [],
                },
            )

        with contextlib.redirect_stdout(io.StringIO()):
            summary = validate_all.validate_component_libraries(
                root=self.root,
                runner=runner,
                python_executable="/fixture/python",
            )

        self.assertEqual(2, len(calls))
        self.assertEqual(
            {"component": "chapter-opener", "status": "building"},
            summary["components"][2],
        )

    def test_claimed_available_requires_integer_count_at_least_fifty(self) -> None:
        self.cover_root.mkdir(parents=True)
        cases = {
            "missing": None,
            "zero": 0,
            "below-threshold": 49,
            "boolean": True,
            "string": "50",
        }
        for name, record_count in cases.items():
            with self.subTest(name=name):
                payload: dict[str, object] = {
                    "valid": True,
                    "status": "available",
                    "errors": [],
                }
                if name != "missing":
                    payload["record_count"] = record_count

                with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(
                    SystemExit
                ) as raised:
                    validate_all.validate_component_libraries(
                        root=self.root,
                        runner=lambda *_args, **_kwargs: completed(0, payload),
                    )

                self.assertEqual(1, raised.exception.code)

    def test_claimed_available_requires_explicit_empty_errors_list(self) -> None:
        self.cover_root.mkdir(parents=True)
        cases = {
            "missing": None,
            "string": "",
            "mapping": {},
            "nonempty": ["contradiction"],
        }
        for name, errors in cases.items():
            with self.subTest(name=name):
                payload: dict[str, object] = {
                    "valid": True,
                    "status": "available",
                    "record_count": 50,
                }
                if name != "missing":
                    payload["errors"] = errors

                with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(
                    SystemExit
                ) as raised:
                    validate_all.validate_component_libraries(
                        root=self.root,
                        runner=lambda *_args, **_kwargs: completed(0, payload),
                    )

                self.assertEqual(1, raised.exception.code)

    def test_timeout_is_finite_and_fails_with_deterministic_status(self) -> None:
        for cover_exists, expected_status in ((False, "missing"), (True, "building")):
            with self.subTest(cover_exists=cover_exists):
                if cover_exists:
                    self.cover_root.mkdir(parents=True, exist_ok=True)

                def runner(command: list[str], **kwargs: object) -> SimpleNamespace:
                    self.assertEqual(120, kwargs["timeout"])
                    raise subprocess.TimeoutExpired(command, kwargs["timeout"])

                stdout = io.StringIO()
                stderr = io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(
                    stderr
                ), self.assertRaises(SystemExit) as raised:
                    validate_all.validate_component_libraries(
                        root=self.root,
                        runner=runner,
                    )

                self.assertEqual(1, raised.exception.code)
                summary = json.loads(stdout.getvalue().strip().splitlines()[-1])
                self.assertEqual(expected_status, summary["components"][0]["status"])
                self.assertNotIn("TimeoutExpired", stdout.getvalue())
                self.assertNotIn("TimeoutExpired", stderr.getvalue())

    def test_zero_exit_with_nonavailable_payload_still_fails_closed(self) -> None:
        self.cover_root.mkdir(parents=True)

        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as raised:
            validate_all.validate_component_libraries(
                root=self.root,
                runner=lambda *_args, **_kwargs: completed(
                    0, {"valid": True, "status": "building"}
                ),
            )

        self.assertEqual(1, raised.exception.code)

    def test_main_keeps_existing_release_steps_and_cover_gate_fail_closed(self) -> None:
        events: list[str] = []

        def run_step(label: str, command: list[str]) -> None:
            events.append(f"run:{label}")

        def component_gate() -> dict[str, object]:
            events.append("component-gate")
            return {"schema_version": "1.0", "components": []}

        def upstream_verifier() -> None:
            events.append("upstream")

        with mock.patch.object(validate_all.Path, "is_file", return_value=True):
            result = validate_all.main(
                run_step=run_step,
                component_gate=component_gate,
                upstream_verifier=upstream_verifier,
            )

        self.assertEqual(0, result)
        self.assertEqual("run:unit and end-to-end tests", events[0])
        skill_events = [event for event in events if event.startswith("run:Skill validation:")]
        self.assertEqual(9, len(skill_events))
        self.assertIn("run:design case coverage", events)
        self.assertLess(events.index("run:design case coverage"), events.index("component-gate"))
        self.assertLess(events.index("component-gate"), events.index("upstream"))

        with mock.patch.object(validate_all.Path, "is_file", return_value=True):
            with self.assertRaisesRegex(SystemExit, "cover rejected"):
                validate_all.main(
                    run_step=lambda *_args: None,
                    component_gate=lambda: (_ for _ in ()).throw(
                        SystemExit("cover rejected")
                    ),
                    upstream_verifier=lambda: self.fail(
                        "upstream must not hide a component gate failure"
                    ),
                )


if __name__ == "__main__":
    unittest.main()
