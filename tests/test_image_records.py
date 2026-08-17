import unittest

from ai.contracts import validate_data


def valid_cover_prompt():
    return {
        "schema_version": "1.0",
        "project_id": "P-400",
        "concept_id": "COVER-A",
        "reference_ids": ["DC-01-cover", "DC-07-cover"],
        "core_metaphor": "一只沿着时间水面漂行的纸船",
        "composition": {"format": "portrait", "title_safe_area": "upper-third"},
        "subject": ["paper boat", "soft water ripples"],
        "color": ["warm paper white", "muted ink blue"],
        "material": ["uncoated paper", "subtle emboss impression"],
        "lighting": "soft side light",
        "style_constraints": ["restrained", "editorial", "no one-to-one case copy"],
        "negative_constraints": ["no readable text", "no logo", "no fake documentary evidence"],
        "background_prompt": "Portrait book-cover background with a paper boat and muted ink-blue ripples; leave a clean upper-third title area; no readable text or logo.",
        "editable_text_overlay": {
            "title": "editable-text-layer",
            "author": "editable-text-layer",
            "studio_mark": "editable-text-layer"
        },
        "version": "v1",
        "evaluation_status": "draft"
    }


class ImageRecordTests(unittest.TestCase):
    def test_cover_prompt_contract_is_complete(self):
        prompt = valid_cover_prompt()
        self.assertEqual([], validate_data(prompt, "cover-prompt"))
        for field in ["composition", "color", "material", "negative_constraints", "editable_text_overlay"]:
            broken = valid_cover_prompt()
            del broken[field]
            self.assertTrue(validate_data(broken, "cover-prompt"), field)

    def test_cover_background_and_text_overlay_are_separate(self):
        prompt = valid_cover_prompt()
        self.assertIn("no readable text", prompt["background_prompt"])
        self.assertEqual("editable-text-layer", prompt["editable_text_overlay"]["title"])

    def test_image_manifest_uses_sidecar_prompt_and_explicit_role(self):
        manifest = {
            "version": "1.0",
            "project_id": "P-400",
            "images": [{
                "image_id": "IMG-001",
                "image_role": "memory-illustration",
                "use": "chapter opener background",
                "skill": "imagegen",
                "prompt_file": "prompts/IMG-001.md",
                "output_file": "images/IMG-001-v1.png",
                "status": "selected"
            }]
        }
        self.assertEqual([], validate_data(manifest, "image-manifest"))
        manifest["images"][0]["prompt"] = "an illegally inlined long prompt"
        self.assertTrue(validate_data(manifest, "image-manifest"))


if __name__ == "__main__":
    unittest.main()
