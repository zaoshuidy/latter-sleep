from __future__ import annotations

import copy
import importlib
import importlib.util
import unittest

from ai.contracts import validate_data


def valid_project() -> dict:
    return {
        "version": "1.0",
        "project_id": "BOOK-LOST-HUMAN-WORLD",
        "title": "失落人间",
        "subtitle": "在所有归途之外",
        "author": "早睡的猫",
        "mode": "template",
        "primary_category": "literary-fiction",
        "tags": ["double-displacement"],
        "confirmer": "用户",
        "page_plan": {"fixed_pages": 1},
        "cover_text_registry": [
            {
                "text_id": "BACK-COPY-001",
                "surface": "back",
                "role": "back-cover-copy",
                "value": "他从所有归途之外经过。",
                "language": "zh-CN",
            },
            {
                "text_id": "SPINE-TITLE-001",
                "surface": "spine",
                "role": "title",
                "value": "失落人间",
                "language": "zh-CN",
            },
        ],
    }


def valid_output_spec() -> dict:
    entries = [
        {
            "text_id": "TITLE-001",
            "surface": "front",
            "role": "title",
            "value": "失落人间",
            "language": "zh-CN",
        },
        {
            "text_id": "SUBTITLE-001",
            "surface": "front",
            "role": "subtitle",
            "value": "在所有归途之外",
            "language": "zh-CN",
        },
        {
            "text_id": "AUTHOR-001",
            "surface": "front",
            "role": "author",
            "value": "早睡的猫",
            "language": "zh-CN",
        },
    ]
    return {
        "text_rendering_mode": "integrated-typography",
        "integrated_text": entries,
        "editable_text_backup": {
            item["text_id"]: item["value"] for item in entries
        },
    }


class CoverIntegratedTypographyPolicyTests(unittest.TestCase):
    def policy(self):
        spec = importlib.util.find_spec("ai.book_component_kb.integrated_text")
        self.assertIsNotNone(spec, "integrated text policy module is missing")
        return importlib.import_module("ai.book_component_kb.integrated_text")

    def test_policy_module_exists(self) -> None:
        self.policy()

    def test_front_project_truth_is_normalized_into_an_immutable_plan(self) -> None:
        policy = self.policy()
        plan = policy.validate_integrated_typography(
            valid_project(), "cover", valid_output_spec()
        )
        self.assertEqual("integrated-typography", plan.mode)
        self.assertIsInstance(plan.entries, tuple)
        self.assertIsInstance(plan.backup, tuple)
        self.assertEqual(
            ["失落人间", "在所有归途之外", "早睡的猫"],
            [entry.value for entry in plan.entries],
        )
        with self.assertRaises((AttributeError, TypeError)):
            plan.entries[0].value = "被篡改"

    def test_registered_back_and_spine_text_are_accepted(self) -> None:
        policy = self.policy()
        output = valid_output_spec()
        output["integrated_text"] = copy.deepcopy(
            valid_project()["cover_text_registry"]
        )
        output["editable_text_backup"] = {
            item["text_id"]: item["value"] for item in output["integrated_text"]
        }
        plan = policy.validate_integrated_typography(valid_project(), "cover", output)
        self.assertEqual(("back", "spine"), tuple(item.surface for item in plan.entries))

    def test_editable_overlay_mode_remains_unchanged(self) -> None:
        policy = self.policy()
        self.assertIsNone(
            policy.validate_integrated_typography(
                valid_project(), "cover", {"text_rendering_mode": "editable-overlay"}
            )
        )

    def test_non_cover_and_surface_role_mismatches_are_rejected(self) -> None:
        policy = self.policy()
        with self.assertRaisesRegex(ValueError, "cover"):
            policy.validate_integrated_typography(
                valid_project(), "toc", valid_output_spec()
            )
        mismatches = (
            ("back", "subtitle"),
            ("spine", "subtitle"),
            ("front", "back-cover-copy"),
            ("spine", "recommendation"),
        )
        for surface, role in mismatches:
            with self.subTest(surface=surface, role=role):
                output = valid_output_spec()
                output["integrated_text"][0]["surface"] = surface
                output["integrated_text"][0]["role"] = role
                with self.assertRaisesRegex(ValueError, "surface.*role"):
                    policy.validate_integrated_typography(
                        valid_project(), "cover", output
                    )

    def test_unregistered_text_duplicate_ids_and_backup_mismatch_are_rejected(self) -> None:
        policy = self.policy()
        mutations = []
        unregistered = valid_output_spec()
        unregistered["integrated_text"][0]["value"] = "模型编造宣传语"
        unregistered["editable_text_backup"]["TITLE-001"] = "模型编造宣传语"
        mutations.append(("registered", unregistered))
        duplicate_id = valid_output_spec()
        duplicate_id["integrated_text"][1]["text_id"] = "TITLE-001"
        duplicate_id["editable_text_backup"] = {
            item["text_id"]: item["value"]
            for item in duplicate_id["integrated_text"]
        }
        mutations.append(("unique", duplicate_id))
        mismatch = valid_output_spec()
        mismatch["editable_text_backup"]["TITLE-001"] = "失落人问"
        mutations.append(("backup", mismatch))
        for message, output in mutations:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    policy.validate_integrated_typography(
                        valid_project(), "cover", output
                    )

    def test_machine_identifiers_are_rejected_even_under_allowed_roles(self) -> None:
        policy = self.policy()
        forbidden = (
            "ISBN 978-7-5537-8418-2",
            "9787553784182",
            "7 8 7 5 5 3 7 8 4 1 8 2",
            "请在此绘制条码",
            "barcode area",
            "放置二维码",
            "QR code",
            "定价：58.00元",
            "￥58",
            "RMB 58",
            "CNY 58",
            "CIP 数据",
            "书号待定",
            "发行编号 001",
            "机器码",
        )
        for value in forbidden:
            with self.subTest(value=value):
                output = valid_output_spec()
                output["integrated_text"][0]["value"] = value
                output["editable_text_backup"]["TITLE-001"] = value
                with self.assertRaisesRegex(ValueError, "machine identifier"):
                    policy.validate_integrated_typography(
                        valid_project(), "cover", output
                    )
                self.assertTrue(policy.contains_machine_identifier(value))

    def test_project_cover_text_registry_is_schema_valid(self) -> None:
        self.assertEqual([], validate_data(valid_project(), "project-config"))


if __name__ == "__main__":
    unittest.main()
