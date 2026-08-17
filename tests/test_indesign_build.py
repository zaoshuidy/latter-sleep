import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path

from ai.contracts import validate_data


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "build-indesign-book" / "scripts" / "build_indesign_book.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_indesign_book", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load build_indesign_book.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_png_header(path: Path, width: int, height: int) -> None:
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", 13)
        + b"IHDR"
        + struct.pack(">II", width, height)
        + b"\x08\x06\x00\x00\x00"
    )


class InDesignBuildTests(unittest.TestCase):
    def test_discovers_ordered_uniform_pages_and_reports_proof_resolution(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            page_dir = Path(tmp)
            write_png_header(page_dir / "00-front-cover.png", 1000, 1448)
            write_png_header(page_dir / "01-title-page.png", 1000, 1448)

            pages = module.discover_pages(page_dir)
            report = module.build_report(
                project_id="BOOK-TEST",
                mode="proof",
                pages=pages,
                trim_width_mm=145,
                trim_height_mm=210,
                output_dir=page_dir / "output",
                execution=None,
            )

            self.assertEqual(["00-front-cover.png", "01-title-page.png"], [p.path.name for p in pages])
            self.assertLess(report["quality"]["minimum_effective_ppi"], 300)
            self.assertFalse(report["quality"]["print_ready"])
            self.assertIn("minimum_effective_ppi_below_300", report["quality"]["blockers"])

    def test_rejects_non_contiguous_page_numbers(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            page_dir = Path(tmp)
            write_png_header(page_dir / "00-front-cover.png", 1000, 1448)
            write_png_header(page_dir / "02-title-page.png", 1000, 1448)
            with self.assertRaisesRegex(ValueError, "contiguous"):
                module.discover_pages(page_dir)

    def test_generated_jsx_preserves_page_order_and_output_paths(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page_dir = root / "pages"
            page_dir.mkdir()
            write_png_header(page_dir / "00-front-cover.png", 1740, 2520)
            write_png_header(page_dir / "01-title-page.png", 1740, 2520)
            pages = module.discover_pages(page_dir)
            jsx = module.build_jsx(
                pages=pages,
                project_id="BOOK-TEST",
                document_title="测试图书",
                trim_width_mm=145,
                trim_height_mm=210,
                bleed_mm=0,
                indd_path=root / "output" / "book.indd",
                pdf_path=root / "output" / "book-proof.pdf",
            )

            self.assertLess(jsx.index("00-front-cover.png"), jsx.index("01-title-page.png"))
            self.assertIn('pageWidth = "145mm"', jsx)
            self.assertIn('pageHeight = "210mm"', jsx)
            self.assertIn("doc.save(inddFile)", jsx)
            self.assertIn("doc.exportFile(ExportFormat.PDF_TYPE", jsx)

    def test_example_project_compiles_a_machine_readable_report(self):
        module = load_module()
        project_root = ROOT / "projects" / "lost-human-world-cover"
        pages = module.discover_pages(project_root / "ebook" / "pages-v003")
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            report = module.compile_build(
                project_root=project_root,
                page_dir=project_root / "ebook" / "pages-v003",
                output_dir=output_dir,
                project_id="BOOK-LOST-HUMAN-WORLD",
                document_title="失落人间",
                mode="proof",
                trim_width_mm=145,
                trim_height_mm=210,
                bleed_mm=0,
                execute=False,
            )

            self.assertEqual(len(pages), report["page_count"])
            self.assertEqual("compiled", report["status"])
            self.assertTrue((output_dir / "build-book.jsx").is_file())
            saved = json.loads((output_dir / "indesign-build-report.json").read_text(encoding="utf-8"))
            self.assertEqual("BOOK-LOST-HUMAN-WORLD", saved["project_id"])
            self.assertEqual([], validate_data(saved, "indesign-build-report"))


if __name__ == "__main__":
    unittest.main()
