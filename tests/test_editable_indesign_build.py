import importlib.util
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "build-indesign-book" / "scripts" / "build_editable_indesign.py"
PROJECT = ROOT / "projects" / "lost-human-world-cover"


def load_module():
    spec = importlib.util.spec_from_file_location("build_editable_indesign", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load editable InDesign builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EditableInDesignBuildTests(unittest.TestCase):
    def test_manuscript_parser_preserves_title_and_all_paragraphs(self):
        module = load_module()
        chapter_title, paragraphs = module.parse_manuscript(
            PROJECT / "manuscript" / "chapter-01.md"
        )
        self.assertEqual("第一章 车窗里的故乡", chapter_title)
        self.assertEqual(49, len(paragraphs))
        self.assertEqual("车开出城的时候，雨还没有落下来。", paragraphs[0])
        self.assertEqual("他望着窗外，没有立刻开口。", paragraphs[-1])

    def test_cover_crop_uses_physical_full_cover_geometry_at_300_ppi(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "spread.png"
            Image.new("RGB", (3650, 2551), "white").save(source, dpi=(300, 300))
            front = Path(tmp) / "front.png"
            back = Path(tmp) / "back.png"
            module.crop_cover_pages(
                source,
                front,
                back,
                spread_width_mm=309,
                spread_height_mm=216,
                trim_width_mm=145,
                trim_height_mm=210,
                bleed_mm=3,
                spine_width_mm=13,
            )
            with Image.open(front) as front_image:
                self.assertEqual((1713, 2481), front_image.size)
            with Image.open(back) as back_image:
                self.assertEqual((1713, 2481), back_image.size)

    def test_generated_jsx_uses_native_styles_parents_threads_and_vertical_text(self):
        module = load_module()
        chapter_title, paragraphs = module.parse_manuscript(
            PROJECT / "manuscript" / "chapter-01.md"
        )
        toc = module.load_json(PROJECT / "toc" / "toc-direction-b-v001-layout.json")
        jsx = module.build_editable_jsx(
            project_id="BOOK-TEST",
            book_title="失落人间",
            subtitle="在所有归途之外",
            author="早睡的猫",
            studio_mark="纸船工作室",
            chapter_title=chapter_title,
            paragraphs=paragraphs,
            toc_entries=toc["entries"],
            front_cover=Path("D:/assets/front.png"),
            back_cover=Path("D:/assets/back.png"),
            indd_path=Path("D:/output/book-editable.indd"),
            idml_path=Path("D:/output/book-editable.idml"),
            pdf_path=Path("D:/output/book-editable.pdf"),
        )
        for required in (
            "P-BD-01",
            "P-CH-TTL",
            "P-TOC-ENTRY",
            "A-Body",
            "B-Blank",
            "C-FrontMatter",
            "D-TOC",
            "E-Chapter",
            "F-BodyFirst",
            "nextTextFrame",
            "StoryHorizontalOrVertical.VERTICAL",
            'pageWidth = "145mm"',
            'pageHeight = "210mm"',
            "baselineDivision = 17.5",
        ):
            self.assertIn(required, jsx)
        self.assertNotIn("pages-v003", jsx)


if __name__ == "__main__":
    unittest.main()
