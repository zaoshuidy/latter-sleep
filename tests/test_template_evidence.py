from copy import deepcopy
import unittest

from ai.contracts import validate_data


class TemplateEvidenceContractTests(unittest.TestCase):
    def valid_candidate_record(self):
        return {
            "schema_version": "1.0",
            "evidence_id": "EVD-LULU-A5-001",
            "template_id": "TPL-LULU-A5-INTERIOR",
            "status": "candidate",
            "original": {
                "provider": "Lulu",
                "source_url": "https://assets.lulu.com/media/templates/book/lulu-book-template-all-a5.zip",
                "relative_path": "research/reference-originals/lulu-book-template-all-a5.zip",
                "sha256": "B604553285B3C811350F34D499377D63E74B9ACFBBD7524FFA4D5871F304A243",
                "format": "zip-with-indd-idml",
            },
            "chinese_book_references": [],
            "adobe_sources": [],
            "print_sources": [],
            "field_mapping_path": None,
            "activation_errors": [
                "requires two Chinese published-book references",
                "requires one Adobe source",
                "requires one print or trim source",
                "requires reviewed field mapping",
            ],
        }

    def valid_approved_record(self):
        record = self.valid_candidate_record()
        record["status"] = "approved"
        record["chinese_book_references"] = [
            "ISBN 9787100000001 / 某出版社 / 2022",
            "ISBN 9787100000002 / 某出版社 / 2024",
        ]
        record["adobe_sources"] = [
            "https://helpx.adobe.com/indesign/using/templates.html",
        ]
        record["print_sources"] = [
            "https://www.example.com/print-trim-guide",
        ]
        record["field_mapping_path"] = "references/templates/lulu-a5/field-mapping-reviewed.json"
        record["activation_errors"] = []
        return record

    def assertSchemaErrorsContain(self, payload, schema_name, *expected_fragments):
        errors = validate_data(payload, schema_name)
        self.assertTrue(errors, "expected schema errors")
        joined = "\n".join(errors)
        for fragment in expected_fragments:
            self.assertIn(fragment, joined)
        return errors

    def test_candidate_record_is_schema_valid(self):
        self.assertEqual([], validate_data(self.valid_candidate_record(), "template-evidence"))

    def test_approved_record_requires_closed_evidence_gate(self):
        record = self.valid_candidate_record()
        record["status"] = "approved"
        self.assertTrue(validate_data(record, "template-evidence"))

    def test_approved_record_is_schema_valid_once_gate_is_complete(self):
        self.assertEqual([], validate_data(self.valid_approved_record(), "template-evidence"))

    def test_approved_record_rejects_each_open_evidence_gate_independently(self):
        cases = [
            (
                "fewer than two chinese_book_references",
                lambda record: record.__setitem__("chinese_book_references", ["ISBN 9787100000001 / 某出版社 / 2022"]),
                ("too short",),
            ),
            (
                "empty adobe_sources",
                lambda record: record.__setitem__("adobe_sources", []),
                ("non-empty",),
            ),
            (
                "empty print_sources",
                lambda record: record.__setitem__("print_sources", []),
                ("non-empty",),
            ),
            (
                "null field_mapping_path",
                lambda record: record.__setitem__("field_mapping_path", None),
                ("not of type 'string'",),
            ),
            (
                "empty field_mapping_path",
                lambda record: record.__setitem__("field_mapping_path", ""),
                ("non-empty",),
            ),
            (
                "nonempty activation_errors",
                lambda record: record.__setitem__("activation_errors", ["still pending"]),
                ("expected to be empty",),
            ),
        ]

        for label, mutate, expected_fragments in cases:
            with self.subTest(label=label):
                record = deepcopy(self.valid_approved_record())
                mutate(record)
                self.assertSchemaErrorsContain(record, "template-evidence", *expected_fragments)

    def test_schema_is_closed_to_unexpected_properties(self):
        record = self.valid_candidate_record()
        record["unexpected"] = True
        self.assertSchemaErrorsContain(record, "template-evidence", "Additional properties are not allowed")


if __name__ == "__main__":
    unittest.main()
