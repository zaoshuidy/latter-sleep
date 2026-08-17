#!/usr/bin/env python3
"""Build a PNG-page StPageFlip variant from the approved V002 sample."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from PIL import Image

from render_lost_human_world_flipbook import render as render_v002


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "projects" / "lost-human-world-cover"
EBOOK = PROJECT / "ebook"
PAGE_DIR = EBOOK / "pages-v003"
OUTPUT = EBOOK / "lost-human-world-ebook-v003-png.html"
RENDER_SOURCE = EBOOK / ".page-render-v003.html"
CHAPTER_ASSET = (
    PROJECT
    / "chapter-opener"
    / "generated"
    / "chapter-opener-v001-300dpi.png"
)
FULL_COVER_ASSET = PROJECT / "generated" / "full-cover-v001-preview.png"

PAGE_FILES = (
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
)


def physical_pages(source: str) -> list[str]:
    pages = re.findall(r'(<section class="book-page.*?</section>)', source, flags=re.S)
    if len(pages) != len(PAGE_FILES):
        raise ValueError(f"expected {len(PAGE_FILES)} physical pages, got {len(pages)}")
    return pages


def render_capture_source() -> str:
    source = render_v002()
    style = re.search(r"<style>(.*?)</style>", source, flags=re.S)
    if style is None:
        raise ValueError("V002 style block is missing")
    frames = "\n".join(
        f'<div class="render-frame" data-render-index="{index}">{page}</div>'
        for index, page in enumerate(physical_pages(source))
    )
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=1000,initial-scale=1">
  <title>《失落人间》V003 PNG 页面渲染源</title>
  <style>
{style.group(1)}
    html,body {{ width:1000px; min-width:1000px; height:1448px; min-height:1448px; margin:0; overflow:hidden; background:transparent; }}
    .render-frame {{ display:none; position:relative; width:1000px; height:1448px; overflow:hidden; }}
    .render-frame.is-active {{ display:block; }}
    .render-frame > .book-page {{ position:absolute; left:0; top:0; transform:scale(2); transform-origin:0 0; }}
  </style>
</head>
<body>
{frames}
  <script>
    const index = Math.max(0, Math.min(13, Number(new URLSearchParams(location.search).get('page') || 0)));
    document.querySelector(`[data-render-index="${{index}}"]`).classList.add('is-active');
    document.documentElement.dataset.renderReady = 'true';
  </script>
</body>
</html>
'''


def png_page_markup(page: str, filename: str) -> str:
    opening = re.match(r"(<section\b[^>]*>)", page, flags=re.S)
    if opening is None:
        raise ValueError("invalid physical page markup")
    clean_opening = re.sub(
        r'class="[^"]+"', 'class="book-page png-page"', opening.group(1), count=1
    )
    inner = page[len(opening.group(1)) : -len("</section>")]
    inner = re.sub(r"<img\b[^>]*>", "", inner, flags=re.S)
    return (
        clean_opening
        + f'<img class="page-image" src="pages-v003/{filename}" alt="" aria-hidden="true">'
        + f'<div class="page-text-layer">{inner}</div>'
        + "</section>"
    )


def install_approved_png_overrides() -> None:
    """Bind the approved chapter spread and back-cover trim to their slots."""
    PAGE_DIR.mkdir(parents=True, exist_ok=True)
    with Image.open(CHAPTER_ASSET) as chapter:
        midpoint = chapter.width // 2
        chapter.crop((0, 0, midpoint, chapter.height)).resize(
            (1000, 1448), Image.Resampling.LANCZOS
        ).convert("RGB").save(PAGE_DIR / PAGE_FILES[5], format="PNG")
        chapter.crop((midpoint, 0, chapter.width, chapter.height)).resize(
            (1000, 1448), Image.Resampling.LANCZOS
        ).convert("RGB").save(PAGE_DIR / PAGE_FILES[6], format="PNG")

    with Image.open(FULL_COVER_ASSET) as cover:
        x_scale = cover.width / 309
        y_scale = cover.height / 216
        trim_box = (
            round(3 * x_scale),
            round(3 * y_scale),
            round((3 + 145) * x_scale),
            round((3 + 210) * y_scale),
        )
        cover.crop(trim_box).resize(
            (1000, 1448), Image.Resampling.LANCZOS
        ).convert("RGB").save(PAGE_DIR / PAGE_FILES[13], format="PNG")


def render_png_flipbook() -> str:
    missing = [name for name in PAGE_FILES if not (PAGE_DIR / name).is_file()]
    if missing:
        raise FileNotFoundError("missing rendered PNG pages: " + ", ".join(missing))

    source = render_v002()
    pages = physical_pages(source)
    replacement = "\n          ".join(
        png_page_markup(page, filename) for page, filename in zip(pages, PAGE_FILES)
    )
    source = re.sub(
        r'(<div class="flip-book" id="book">).*?(</div>\s*<span class="engine-note">)',
        rf"\1\n          {replacement}\n        \2",
        source,
        count=1,
        flags=re.S,
    )
    source = source.replace(
        "</style>",
        '''    .page-image { position:absolute; inset:0; z-index:1; display:block; width:100%; height:100%; object-fit:cover; pointer-events:none; }
    .page-text-layer { position:absolute; inset:0; z-index:2; overflow:hidden; opacity:.001; color:transparent; user-select:text; }
    .page-text-layer * { color:transparent!important; text-shadow:none!important; }
    .png-page::before,.png-page::after { content:none!important; }
  </style>''',
        1,
    )
    source = source.replace("真实翻页电子样书 V002", "PNG 页面翻页电子样书 V003")
    source = source.replace("早睡的猫 · 电子样书 V002", "早睡的猫 · 电子样书 V003 · PNG 页面")
    source = source.replace(
        'data-reader-engine="StPageFlip@2.0.7"',
        'data-reader-engine="StPageFlip@2.0.7" data-reader-render="png-pages"',
    )
    source = source.replace(
        "StPageFlip 2.0.7 · 本地离线引擎",
        "StPageFlip 2.0.7 · 14 张本地 PNG 页面",
    )
    return source


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--render-source", action="store_true")
    args = parser.parse_args()
    if args.render_source:
        RENDER_SOURCE.write_text(render_capture_source(), encoding="utf-8")
        print(RENDER_SOURCE)
        return 0
    install_approved_png_overrides()
    OUTPUT.write_text(render_png_flipbook(), encoding="utf-8")
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
