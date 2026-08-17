from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "design-book-editorial"
SKILL_PATH = SKILL_ROOT / "SKILL.md"
PROTOCOL_PATH = SKILL_ROOT / "references" / "component-knowledge-retrieval.md"
BASELINE_PATH = (
    ROOT
    / "tests"
    / "skill-behavior"
    / "design-book-editorial"
    / "component-kb-baseline.md"
)
COVER_ROOT = ROOT / "knowledge" / "book-component-libraries" / "cover"
REGISTRY = ROOT / "knowledge" / "book-component-libraries" / "source-registry.json"
QUERY = ROOT / "examples" / "component-kb-cover-demo" / "query.json"
CASE_INDEX = ROOT / "knowledge" / "indexes" / "design-case-index.json"
WITH_SKILL_PATH = (
    ROOT
    / "tests"
    / "skill-behavior"
    / "design-book-editorial"
    / "component-kb-with-skill.md"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class EditorialDesignComponentKnowledgeSkillTests(unittest.TestCase):
    def test_approved_project_system_can_route_directly_to_one_visual_v001(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")

        for required in (
            "直接成稿路由",
            "已有经用户批准的稳定视觉系统",
            "直接生成一版可视 V001",
            "省略单独的书面设计规格",
            "不跳过可编辑文字",
            "生成结果的人工评判",
        ):
            with self.subTest(required=required):
                self.assertIn(required, skill)

    def test_cover_text_mode_is_a_small_explicit_design_choice(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")
        protocol = PROTOCOL_PATH.read_text(encoding="utf-8")
        for required in (
            "editable-overlay",
            "integrated-typography",
            "仅限 `cover`",
            "正封、封底、书脊",
            "ISBN、条码、二维码、定价、CIP",
            "可编辑备份",
        ):
            with self.subTest(required=required):
                self.assertIn(required, skill + protocol)
        self.assertIn("非视觉事实一次询问", skill)
        self.assertIn("视觉判断循序渐进", skill)

    def test_skill_routes_formal_component_directions_to_the_full_protocol(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("references/component-knowledge-retrieval.md", skill)
        self.assertIn('SKILL_FILE="/absolute/path/to/current/skills/design-book-editorial/SKILL.md"', skill)
        self.assertIn('cd -P "$(dirname "$SKILL_FILE")/../.."', skill)
        self.assertIn('"$SUITE_ROOT/.venv/bin/python"', skill)
        self.assertIn("不得调用 `imagegen`", skill)

    def test_protocol_closes_the_real_reference_mapping_gate(self) -> None:
        protocol = PROTOCOL_PATH.read_text(encoding="utf-8")
        required_contracts = (
            "status=available",
            "exactly 5",
            "不同 `book_case_id`",
            "本地真实资产",
            "2—3",
            "include_fields",
            "exclude_fields",
            "status=draft",
            "不是正式 selection",
            "selection_id",
            "SHA-256",
            "status=approved",
            "validate_selection",
            "validate_selection_prompt_safety",
            "完整回显前",
            "项目书名长度",
            "真实书名",
            "metadata",
            "overlay",
            "field_scores",
            ">0",
            "匹配值",
            "来源",
            "可选性",
            "material",
            "book_category",
            "不可选",
            "component_type",
            "fail closed",
            "不得整体复制",
            "待确认（可编辑文字层）",
        )
        for contract in required_contracts:
            with self.subTest(contract=contract):
                self.assertIn(contract, protocol)

        self.assertIn('SKILL_FILE="/absolute/path/to/current/skills/design-book-editorial/SKILL.md"', protocol)
        self.assertIn('cd -P "$(dirname "$SKILL_FILE")/../.."', protocol)
        self.assertIn('"$SUITE_ROOT/.venv/bin/python"', protocol)
        self.assertIn(
            '"$SUITE_ROOT/skills/design-book-editorial/scripts/check_case_library.py"',
            protocol,
        )

    def test_protocol_commands_return_five_bound_cover_books_without_touching_baseline(
        self,
    ) -> None:
        before_baseline = sha256(BASELINE_PATH)
        skill_file = SKILL_PATH.resolve()
        root_resolution = subprocess.run(
            [
                "bash",
                "-c",
                'cd -P "$(dirname "$SKILL_FILE")/../.." && pwd',
            ],
            env={"SKILL_FILE": str(skill_file)},
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, root_resolution.returncode, root_resolution.stderr)
        suite_root = Path(root_resolution.stdout.strip())
        self.assertEqual(ROOT.resolve(), suite_root)
        suite_python = suite_root / ".venv" / "bin" / "python"

        with tempfile.TemporaryDirectory() as external_directory:
            check_case = subprocess.run(
                [
                    str(suite_python),
                    str(
                        suite_root
                        / "skills"
                        / "design-book-editorial"
                        / "scripts"
                        / "check_case_library.py"
                    ),
                    str(suite_root / "knowledge" / "indexes" / "design-case-index.json"),
                ],
                cwd=external_directory,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, check_case.returncode, check_case.stderr)
            self.assertTrue(json.loads(check_case.stdout)["ok"])

            validator = subprocess.run(
                [
                    str(suite_python),
                    str(suite_root / "scripts" / "book_component_kb" / "validate_library.py"),
                    "--component-root",
                    str(COVER_ROOT),
                    "--registry",
                    str(REGISTRY),
                    "--required-count",
                    "50",
                ],
                cwd=external_directory,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, validator.returncode, validator.stderr)
            report = json.loads(validator.stdout)
            self.assertTrue(report["valid"])
            self.assertEqual("available", report["status"])
            self.assertEqual(50, report["record_count"])
            self.assertEqual([], report["errors"])

            retrieval = subprocess.run(
                [
                    str(suite_python),
                    str(
                        suite_root
                        / "scripts"
                        / "book_component_kb"
                        / "retrieve_references.py"
                    ),
                    "--component-root",
                    str(COVER_ROOT),
                    "--registry",
                    str(REGISTRY),
                    "--query",
                    str(QUERY.resolve()),
                    "--limit",
                    "5",
                ],
                cwd=external_directory,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, retrieval.returncode, retrieval.stderr)
            result = json.loads(retrieval.stdout)
            self.assertEqual("available", result["status"])
            self.assertEqual(5, len(result["candidates"]))
            self.assertEqual(
                5, len({candidate["book_case_id"] for candidate in result["candidates"]})
            )

            for candidate in result["candidates"]:
                record_path = COVER_ROOT / "records" / f"{candidate['record_id']}.json"
                record = json.loads(record_path.read_text(encoding="utf-8"))
                asset_path = COVER_ROOT.parent / record["asset"]["relative_path"]
                self.assertTrue(asset_path.is_file(), asset_path)
                self.assertEqual(
                    candidate["book_case_id"], record["identity"]["book_case_id"]
                )
                self.assertTrue(record["source"]["source_url"].startswith("https://"))
                self.assertEqual(
                    {
                        "cover_scope",
                        "visual_strategy",
                        "composition",
                        "title_zone",
                        "spine_relationship",
                        "thumbnail_recognition",
                    },
                    set(record["component_profile"]),
                )

        self.assertEqual(before_baseline, sha256(BASELINE_PATH))

    def test_fresh_green_behavior_meets_the_two_stage_reference_gate(self) -> None:
        behavior = WITH_SKILL_PATH.read_text(encoding="utf-8")

        self.assertEqual(5, behavior.count("!["))
        for record_id in (
            "COV-CN-0004",
            "COV-CN-0005",
            "COV-CN-0031",
            "COV-CN-0036",
            "COV-CN-0047",
        ):
            with self.subTest(record_id=record_id):
                self.assertIn(record_id, behavior)
        self.assertGreaterEqual(behavior.count("component_profile"), 5)
        self.assertGreaterEqual(behavior.count("https://beautyofbooks.cn/"), 5)
        self.assertGreaterEqual(
            len(re.findall(r"`field_scores?=0\.[0-9]{2}`", behavior)),
            40,
        )
        self.assertGreaterEqual(behavior.count("匹配值"), 5)
        self.assertGreaterEqual(behavior.count("来源为"), 30)
        self.assertGreaterEqual(
            len(re.findall(r"(?m)^.*`material`.*(?:0(?:\.0+)?|0 分).*不可选.*$", behavior)),
            5,
        )
        self.assertGreaterEqual(
            len(
                re.findall(
                    r"(?m)^.*`book_category`.*(?:0(?:\.0+)?|0 分).*不可选.*$",
                    behavior,
                )
            ),
            5,
        )

        for forbidden in (
            "生图提示词",
            "每方向 4 张",
            "共 8 张",
            "imagegen__imagegen",
            "## 正式方向 A",
            "## 正式方向 B",
            "烫金",
            "压凹",
            "局部 UV",
            "触感膜",
            "纸张建议",
            "装订建议",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, behavior)

        required_gate_evidence = (
            "简洁映射",
            "转写为两份 `status=draft`",
            "selection_id",
            "SHA-256",
            "完整回显",
            "二次批准",
            "material",
            "book_category",
            "不可选",
        )
        for evidence in required_gate_evidence:
            with self.subTest(evidence=evidence):
                self.assertIn(evidence, behavior)


if __name__ == "__main__":
    unittest.main()
