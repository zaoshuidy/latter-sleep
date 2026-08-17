import html as html_module
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "projects" / "lost-human-world-cover"
SKILL = ROOT / "skills" / "build-book-flipbook"


class BookFlipbookTests(unittest.TestCase):
    def test_hidpi_canvas_adapter_uses_retina_backing_pixels(self):
        adapter = (
            PROJECT / "ebook" / "vendor" / "stpageflip-hidpi.js"
        )
        self.assertTrue(adapter.is_file(), adapter)
        program = r"""
const adapter = require(process.argv[1]);
let transform = null;
const canvas = {
  width: 1000,
  height: 724,
  getBoundingClientRect: () => ({width: 1000, height: 724}),
  getContext: () => ({setTransform: (...values) => { transform = values; }})
};
const result = adapter.resizeCanvasForPixelRatio(canvas, 2);
process.stdout.write(JSON.stringify({result, width: canvas.width, height: canvas.height, transform}));
"""
        completed = subprocess.run(
            ["node", "-e", program, str(adapter)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(2000, payload["width"])
        self.assertEqual(1448, payload["height"])
        self.assertEqual([2, 0, 0, 2, 0, 0], payload["transform"])
        self.assertEqual(
            {"changed": True, "ratio": 2, "width": 2000, "height": 1448},
            payload["result"],
        )

    def test_skill_routes_approved_pages_to_a_local_stpageflip_reader(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        engine = (SKILL / "references" / "stpageflip.md").read_text(encoding="utf-8")
        raster = (
            SKILL / "references" / "approved-png-canvas-mode.md"
        ).read_text(encoding="utf-8")

        self.assertIn("StPageFlip", skill)
        self.assertIn("page-flip@2.0.7", skill)
        self.assertIn("展示阶段", skill)
        self.assertIn("不得手写翻页状态机", skill)
        self.assertIn("不得重新设计已批准页面", skill)
        self.assertIn("showCover: true", engine)
        self.assertIn('data-density="hard"', engine)
        self.assertIn("loadFromHTML", engine)
        self.assertIn("MIT", engine)
        self.assertIn("离线", engine)
        self.assertIn("approved-png-canvas-mode.md", skill)
        self.assertIn("视觉还原与流畅度优先", skill)
        self.assertIn("文字可选与硬封壳优先", skill)
        self.assertIn("loadFromImages", raster)
        self.assertIn("预解码", raster)
        self.assertIn("devicePixelRatio", raster)
        self.assertIn("最大 2", raster)
        self.assertIn("flippingTime: 620", raster)
        self.assertIn("maxShadowOpacity: 0.20", raster)
        self.assertIn("外置文字索引", raster)
        self.assertIn("顺序图片回退", raster)
        self.assertIn("不得读取磁盘路径", raster)
        self.assertIn("保留上一版", raster)

    def test_installer_exposes_the_flipbook_skill(self):
        from scripts import install_personal

        self.assertIn("build-book-flipbook", install_personal.SKILLS)
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            skill_home = Path(tmp) / "skills"
            result = install_personal.install(
                ROOT,
                runtime,
                skill_home,
                replace=False,
                install_dependencies=False,
            )
            self.assertIn("build-book-flipbook", result["installed_skills"])
            self.assertEqual(
                (runtime / "skills" / "build-book-flipbook").resolve(),
                (skill_home / "build-book-flipbook").resolve(),
            )

    def test_lost_human_world_v002_uses_the_pinned_engine_and_real_pages(self):
        ebook = PROJECT / "ebook" / "lost-human-world-ebook-v002.html"
        bundle = (
            PROJECT
            / "ebook"
            / "vendor"
            / "node_modules"
            / "page-flip"
            / "dist"
            / "js"
            / "page-flip.browser.js"
        )
        license_file = (
            PROJECT / "ebook" / "vendor" / "node_modules" / "page-flip" / "LICENSE"
        )
        package_lock = PROJECT / "ebook" / "vendor" / "package-lock.json"

        self.assertTrue(ebook.is_file(), ebook)
        self.assertTrue(bundle.is_file(), bundle)
        self.assertTrue(license_file.is_file(), license_file)
        self.assertTrue(package_lock.is_file(), package_lock)
        lock = json.loads(package_lock.read_text(encoding="utf-8"))
        self.assertEqual("2.0.7", lock["packages"]["node_modules/page-flip"]["version"])

        output = ebook.read_text(encoding="utf-8")
        source = (PROJECT / "manuscript" / "chapter-01.md").read_text(encoding="utf-8")
        source_paragraphs = [
            value.strip() for value in source.split("\n\n")[1:] if value.strip()
        ]
        rendered = [
            html_module.unescape(re.sub(r"<[^>]+>", "", value)).strip()
            for value in re.findall(
                r'<p data-source-index="\d+">(.*?)</p>', output, flags=re.S
            )
        ]

        self.assertEqual(source_paragraphs, rendered)
        self.assertEqual(14, len(re.findall(r'<section class="book-page', output)))
        self.assertIn(
            'src="vendor/node_modules/page-flip/dist/js/page-flip.browser.js"',
            output,
        )
        self.assertIn("new St.PageFlip", output)
        self.assertIn("showCover: true", output)
        self.assertIn("autoSize:false", output)
        self.assertIn(".flip-book { display:none; width:100%; height:100%; }", output)
        self.assertIn("loadFromHTML", output)
        self.assertIn('data-density="hard" data-page-role="front-cover"', output)
        self.assertIn('data-density="hard" data-page-role="back-cover"', output)
        self.assertIn('data-reader-engine="StPageFlip@2.0.7"', output)
        self.assertIn("window.bookPageFlip = pageFlip", output)
        self.assertIn('data-role="studio_mark">纸船工作室</', output)
        self.assertIn('src="../generated/cover-v001.png"', output)
        self.assertNotIn("reader-spread", output)
        self.assertNotIn("classList.toggle('is-active'", output)
        self.assertNotRegex(output, r"https?://")

    def test_lost_human_world_v003_embeds_one_local_png_per_physical_page(self):
        ebook = PROJECT / "ebook" / "lost-human-world-ebook-v003-png.html"
        page_dir = PROJECT / "ebook" / "pages-v003"
        generator = ROOT / "scripts" / "render_lost_human_world_png_flipbook.py"

        self.assertTrue(generator.is_file(), generator)
        self.assertTrue(ebook.is_file(), ebook)
        expected_pages = [
            "00-front-cover.png",
            "01-inside-front-cover.png",
            "02-title-page.png",
            "03-toc-left.png",
            "04-toc-right.png",
            "05-chapter-opener-left.png",
            "06-chapter-opener-right.png",
            "07-body-6.png",
            "08-body-7.png",
            "09-body-8.png",
            "10-body-9.png",
            "11-body-10.png",
            "12-body-11.png",
            "13-back-cover.png",
        ]
        self.assertEqual(expected_pages, sorted(path.name for path in page_dir.glob("*.png")))
        for name in expected_pages:
            with Image.open(page_dir / name) as image:
                self.assertEqual("PNG", image.format)
                self.assertEqual((1000, 1448), image.size)

        output = ebook.read_text(encoding="utf-8")
        source = (PROJECT / "manuscript" / "chapter-01.md").read_text(encoding="utf-8")
        source_paragraphs = [
            value.strip() for value in source.split("\n\n")[1:] if value.strip()
        ]
        preserved = [
            html_module.unescape(re.sub(r"<[^>]+>", "", value)).strip()
            for value in re.findall(
                r'<p data-source-index="\d+">(.*?)</p>', output, flags=re.S
            )
        ]

        self.assertEqual(source_paragraphs, preserved)
        self.assertEqual(14, len(re.findall(r'<section class="book-page', output)))
        self.assertEqual(14, len(re.findall(r'<img class="page-image"', output)))
        self.assertEqual(14, len(re.findall(r'src="pages-v003/[^\"]+\.png"', output)))
        self.assertIn('data-reader-render="png-pages"', output)
        self.assertIn('class="page-text-layer"', output)
        self.assertIn("new St.PageFlip", output)
        self.assertIn("showCover: true", output)
        self.assertIn('data-density="hard" data-page-role="front-cover"', output)
        self.assertIn('data-density="hard" data-page-role="back-cover"', output)
        self.assertNotIn('src="../generated/cover-v001.png"', output)
        self.assertNotRegex(output, r"https?://")

    def test_v003_chapter_spread_and_back_cover_come_from_approved_png_assets(self):
        page_dir = PROJECT / "ebook" / "pages-v003"
        chapter_asset = (
            PROJECT
            / "chapter-opener"
            / "generated"
            / "chapter-opener-v001-300dpi.png"
        )
        full_cover = PROJECT / "generated" / "full-cover-v001-preview.png"

        with Image.open(chapter_asset) as chapter:
            midpoint = chapter.width // 2
            expected_left = chapter.crop((0, 0, midpoint, chapter.height)).resize(
                (1000, 1448), Image.Resampling.LANCZOS
            ).convert("RGB")
            expected_right = chapter.crop(
                (midpoint, 0, chapter.width, chapter.height)
            ).resize((1000, 1448), Image.Resampling.LANCZOS).convert("RGB")
        with Image.open(full_cover) as cover:
            x_scale = cover.width / 309
            y_scale = cover.height / 216
            trim_box = (
                round(3 * x_scale),
                round(3 * y_scale),
                round((3 + 145) * x_scale),
                round((3 + 210) * y_scale),
            )
            expected_back = cover.crop(trim_box).resize(
                (1000, 1448), Image.Resampling.LANCZOS
            ).convert("RGB")

        for filename, expected in (
            ("05-chapter-opener-left.png", expected_left),
            ("06-chapter-opener-right.png", expected_right),
            ("13-back-cover.png", expected_back),
        ):
            with Image.open(page_dir / filename) as actual:
                self.assertEqual(expected.tobytes(), actual.convert("RGB").tobytes())

    def test_v003_png_pages_do_not_redraw_legacy_css_decoration(self):
        output = (
            PROJECT / "ebook" / "lost-human-world-ebook-v003-png.html"
        ).read_text(encoding="utf-8")

        self.assertEqual(14, output.count('<section class="book-page png-page"'))
        self.assertNotIn('<section class="book-page chapter-art', output)
        self.assertNotIn('<section class="book-page back-cover', output)
        self.assertIn(
            ".png-page::before,.png-page::after { content:none!important; }",
            output,
        )

    def test_v004_uses_predecoded_canvas_images_without_overwriting_v003(self):
        generator = ROOT / "scripts" / "render_lost_human_world_smooth_flipbook.py"
        v003 = PROJECT / "ebook" / "lost-human-world-ebook-v003-png.html"
        expected_v003_sha = (
            "56de8319719771bcdc0774cd3fb7dc1962da92ad71483cefff49dba75eab8527"
        )

        self.assertTrue(generator.is_file(), generator)
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "lost-human-world-ebook-v004-smooth.html"
            completed = subprocess.run(
                [sys.executable, str(generator), "--output", str(output_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            output = output_path.read_text(encoding="utf-8")

        self.assertEqual(
            expected_v003_sha,
            hashlib.sha256(v003.read_bytes()).hexdigest(),
        )
        self.assertIn('data-reader-render="canvas-images"', output)
        self.assertEqual(14, len(re.findall(r'"pages-v003/[^"]+\.png"', output)))
        self.assertIn("loadFromImages(pageImages)", output)
        self.assertNotIn("loadFromHTML", output)
        self.assertIn("image.decode()", output)
        self.assertIn("flippingTime:620", output)
        self.assertIn("maxShadowOpacity:.20", output)
        self.assertIn('src="vendor/stpageflip-hidpi.js"', output)
        self.assertIn("StPageFlipHiDpi.install(pageFlip, book)", output)
        self.assertIn('data-reader-quality="retina-2x"', output)
        self.assertIn('id="search-index"', output)
        self.assertIn('class="fallback-page"', output)
        self.assertNotIn('class="book-page', output)
        self.assertNotRegex(output, r"https?://")

    def test_flip_smoothness_comparison_loads_only_one_reader_at_a_time(self):
        comparison = PROJECT / "ebook" / "flip-smoothness-comparison.html"

        self.assertTrue(comparison.is_file(), comparison)
        output = comparison.read_text(encoding="utf-8")
        self.assertEqual(1, len(re.findall(r"<iframe\b", output)))
        self.assertIn('id="version-v003"', output)
        self.assertIn('id="version-v004"', output)
        self.assertIn(
            'src="lost-human-world-ebook-v004-smooth.html#cover"', output
        )
        self.assertIn(
            "v003:'lost-human-world-ebook-v003-png.html#cover'", output
        )
        self.assertIn(
            "v004:'lost-human-world-ebook-v004-smooth.html#cover'", output
        )
        self.assertIn("readerFrame.src = versions[button.dataset.version]", output)
        self.assertNotRegex(output, r"https?://")


if __name__ == "__main__":
    unittest.main()
