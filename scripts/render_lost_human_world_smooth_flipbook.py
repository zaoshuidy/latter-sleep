#!/usr/bin/env python3
"""Build the smooth Canvas-image V004 without changing the approved V003."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "projects" / "lost-human-world-cover"
EBOOK = PROJECT / "ebook"
PAGE_DIR = EBOOK / "pages-v003"
V003 = EBOOK / "lost-human-world-ebook-v003-png.html"
OUTPUT = EBOOK / "lost-human-world-ebook-v004-smooth.html"

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

PAGE_LABELS = (
    "正封",
    "封二",
    "扉页",
    "目录左页",
    "目录右页",
    "第一章章首页左页",
    "第一章章首页右页",
    "正文第6页",
    "正文第7页",
    "正文第8页",
    "正文第9页",
    "正文第10页",
    "正文第11页",
    "封底",
)

NAVIGATION = (
    ("封面", 0),
    ("扉页", 2),
    ("目录", 3),
    ("第一章", 5),
    ("正文", 7),
    ("封底", 13),
)

HASH_BY_PAGE = {
    0: "cover",
    2: "title-page",
    3: "contents",
    5: "chapter-one",
    7: "body",
    13: "back-cover",
}


def extract_search_text(source: str) -> list[str]:
    pages = re.findall(r'(<section class="book-page.*?</section>)', source, flags=re.S)
    if len(pages) != len(PAGE_FILES):
        raise ValueError(f"expected {len(PAGE_FILES)} V003 pages, got {len(pages)}")
    result = []
    for page in pages:
        match = re.search(
            r'<div class="page-text-layer">(.*)</div></section>', page, flags=re.S
        )
        fragment = match.group(1) if match else ""
        fragment = re.sub(r"<[^>]+>", " ", fragment)
        result.append(" ".join(html.unescape(fragment).split()))
    return result


def render_smooth_flipbook() -> str:
    missing = [name for name in PAGE_FILES if not (PAGE_DIR / name).is_file()]
    if missing:
        raise FileNotFoundError("missing approved PNG pages: " + ", ".join(missing))
    if not V003.is_file():
        raise FileNotFoundError(V003)

    search_text = extract_search_text(V003.read_text(encoding="utf-8"))
    image_sources = "\n".join(
        f'        <img class="fallback-page" src="pages-v003/{name}" '
        f'alt="{html.escape(label)}" loading="eager">'
        for name, label in zip(PAGE_FILES, PAGE_LABELS)
    )
    search_index = "\n".join(
        f'      <article data-search-page="{index}"><h2>{html.escape(label)}</h2>'
        f'<p>{html.escape(text)}</p></article>'
        for index, (label, text) in enumerate(zip(PAGE_LABELS, search_text))
    )
    navigation = "\n".join(
        f'        <button type="button" data-page-index="{index}">{html.escape(label)}</button>'
        for label, index in NAVIGATION
    )
    labels = ",".join(f'"{label}"' for label in PAGE_LABELS)
    hashes = ",".join(f'{index}:"{value}"' for index, value in HASH_BY_PAGE.items())

    return f'''<!doctype html>
<html lang="zh-CN" class="no-js">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <title>《失落人间》流畅翻页电子样书 V004</title>
  <script>document.documentElement.className='js';</script>
  <style>
    :root {{ color-scheme:dark; font-family:"Songti SC","Noto Serif CJK SC",serif; background:#171513; }}
    * {{ box-sizing:border-box; }}
    html,body {{ min-height:100%; margin:0; }}
    body {{ min-height:100vh; color:#eee9e0; background:radial-gradient(circle at 50% 36%,#302b27,#171513 68%); overflow:hidden; }}
    button {{ font:inherit; }}
    .reader {{ min-height:100vh; display:grid; grid-template-rows:auto minmax(0,1fr) auto; }}
    .toolbar,.controls {{ display:flex; align-items:center; justify-content:space-between; gap:12px; padding:12px 18px; background:rgba(14,12,11,.82); backdrop-filter:blur(12px); z-index:10; }}
    .toolbar {{ border-bottom:1px solid rgba(255,255,255,.09); }}
    .controls {{ border-top:1px solid rgba(255,255,255,.09); justify-content:center; }}
    .title {{ min-width:0; }}
    .title strong,.title small {{ display:block; }}
    .title strong {{ letter-spacing:.12em; }}
    .title small {{ margin-top:2px; color:#aaa198; font:12px/1.3 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif; }}
    .ui-button,.drawer button {{ min-height:38px; border:1px solid rgba(255,255,255,.16); border-radius:999px; padding:7px 14px; color:#eee9e0; background:rgba(255,255,255,.055); cursor:pointer; }}
    .ui-button:hover,.drawer button:hover {{ background:rgba(255,255,255,.12); }}
    .ui-button:disabled {{ opacity:.3; cursor:default; }}
    .stage {{ position:relative; display:grid; place-items:center; min-height:0; padding:20px; overflow:hidden; }}
    .flip-book {{ width:100%; height:100%; }}
    .engine-note {{ position:absolute; left:50%; bottom:8px; transform:translateX(-50%); color:#9d958c; font:11px/1.2 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif; white-space:nowrap; pointer-events:none; }}
    .progress {{ min-width:210px; text-align:center; color:#cfc8be; font:13px/1.2 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif; }}
    .drawer {{ position:fixed; z-index:30; inset:0 auto 0 0; width:min(340px,88vw); padding:78px 20px 24px; background:#211e1b; box-shadow:20px 0 60px rgba(0,0,0,.42); transform:translateX(-105%); transition:transform .24s ease; }}
    .drawer.is-open {{ transform:translateX(0); }}
    .drawer nav {{ display:grid; gap:10px; }}
    .drawer button {{ text-align:left; border-radius:10px; }}
    .drawer button[aria-current="page"] {{ border-color:#bd6669; color:#fff; }}
    .fallback-sequence {{ display:grid; grid-template-columns:repeat(2,minmax(0,500px)); gap:12px; align-items:start; max-width:1012px; max-height:100%; overflow:auto; padding:8px; }}
    .fallback-page {{ display:block; width:100%; height:auto; background:#f4f0e8; box-shadow:0 12px 30px rgba(0,0,0,.28); }}
    .js .fallback-sequence[hidden] {{ display:none; }}
    .search-index {{ position:fixed; left:-10000px; top:0; width:1px; height:1px; overflow:hidden; }}
    .sr-status {{ position:fixed; left:-10000px; width:1px; height:1px; overflow:hidden; }}
    @media (max-width:720px) {{
      .toolbar {{ padding:10px 12px; }} .stage {{ padding:8px; }} .title small,.engine-note {{ display:none; }}
      .controls {{ padding:10px 8px; }} .progress {{ min-width:128px; font-size:12px; }} .ui-button {{ padding:7px 12px; }}
      .fallback-sequence {{ grid-template-columns:1fr; }}
    }}
    @media (prefers-reduced-motion:reduce) {{ .drawer {{ transition:none; }} }}
  </style>
  <noscript><style>#book{{display:none}}#fallback[hidden]{{display:grid}}</style></noscript>
</head>
<body>
  <main class="reader" id="reader" data-reader-engine="StPageFlip@2.0.7" data-reader-render="canvas-images" data-reader-quality="retina-2x" data-reader-state="loading">
    <header class="toolbar">
      <button class="ui-button" id="toc-toggle" type="button" aria-expanded="false">目录</button>
      <div class="title"><strong>失落人间</strong><small>早睡的猫 · V004 Canvas 流畅版</small></div>
      <button class="ui-button" id="fullscreen" type="button">全屏</button>
    </header>
    <section class="stage" aria-label="可翻阅电子样书">
      <div class="flip-book" id="book"></div>
      <section class="fallback-sequence" id="fallback" hidden aria-label="顺序阅读模式">
{image_sources}
      </section>
      <span class="engine-note">StPageFlip 2.0.7 · Canvas 图片模式 · 620ms</span>
    </section>
    <footer class="controls">
      <button class="ui-button" id="previous" type="button">上一页</button>
      <span class="progress" id="progress">正在预载页面…</span>
      <button class="ui-button" id="next" type="button">下一页</button>
    </footer>
  </main>
  <aside class="drawer" id="drawer" aria-hidden="true">
    <nav aria-label="样书目录">
{navigation}
    </nav>
  </aside>
  <section class="search-index" id="search-index" aria-label="全文文字索引">
{search_index}
  </section>
  <p class="sr-status" id="status" aria-live="polite"></p>
  <script src="vendor/node_modules/page-flip/dist/js/page-flip.browser.js"></script>
  <script src="vendor/stpageflip-hidpi.js"></script>
  <script>
    (() => {{
      const reader = document.getElementById('reader');
      const book = document.getElementById('book');
      const fallback = document.getElementById('fallback');
      const fallbackImages = Array.from(document.querySelectorAll('.fallback-page'));
      const pageImages = fallbackImages.map(image => image.getAttribute('src'));
      const labels = [{labels}];
      const hashByPage = {{{hashes}}};
      const pageByHash = Object.fromEntries(Object.entries(hashByPage).map(([page,hash]) => [hash,Number(page)]));
      const previous = document.getElementById('previous');
      const next = document.getElementById('next');
      const progress = document.getElementById('progress');
      const status = document.getElementById('status');
      const drawer = document.getElementById('drawer');
      const tocToggle = document.getElementById('toc-toggle');
      const fullscreen = document.getElementById('fullscreen');
      const setDrawer = open => {{ drawer.classList.toggle('is-open',open); drawer.setAttribute('aria-hidden',String(!open)); tocToggle.setAttribute('aria-expanded',String(open)); }};
      const update = index => {{
        const current = Math.max(0,Math.min(pageImages.length - 1,index));
        previous.disabled = current === 0;
        next.disabled = current >= pageImages.length - 1;
        progress.textContent = `${{labels[current]}} · ${{current + 1}} / ${{pageImages.length}}`;
        status.textContent = `已翻到${{labels[current]}}，第 ${{current + 1}} 页，共 ${{pageImages.length}} 页`;
        document.querySelectorAll('[data-page-index]').forEach(button => button.setAttribute('aria-current',Number(button.dataset.pageIndex) === current ? 'page' : 'false'));
        const anchored = Object.keys(hashByPage).map(Number).filter(page => page <= current).pop() ?? 0;
        history.replaceState(null,'',`#${{hashByPage[anchored]}}`);
      }};
      const showFallback = error => {{
        reader.dataset.readerState = 'fallback';
        book.hidden = true;
        fallback.hidden = false;
        progress.textContent = '顺序阅读模式';
        status.textContent = '翻页引擎未能启动，已显示全部页面。';
        if (error) console.error(error);
      }};
      const predecode = () => Promise.allSettled(fallbackImages.map(image => image.decode()));
      const start = async () => {{
        await predecode();
        try {{
          const pageFlip = new St.PageFlip(book, {{ width:500, height:724, size:'stretch', minWidth:280, maxWidth:500, minHeight:406, maxHeight:724, autoSize:false, showCover:true, usePortrait:true, drawShadow:true, maxShadowOpacity:.20, flippingTime:620, mobileScrollSupport:true, swipeDistance:24 }});
          pageFlip.on('flip', event => update(event.data));
          pageFlip.on('init', event => {{
            update(event.data.page);
            window.bookPageFlipHiDpi = StPageFlipHiDpi.install(pageFlip, book);
          }});
          pageFlip.loadFromImages(pageImages);
          window.bookPageFlip = pageFlip;
          reader.dataset.readerState = 'ready';
          const initialHash = location.hash.replace('#','');
          if (initialHash in pageByHash) pageFlip.turnToPage(pageByHash[initialHash]);
          previous.addEventListener('click',() => pageFlip.flipPrev());
          next.addEventListener('click',() => pageFlip.flipNext());
          document.querySelectorAll('[data-page-index]').forEach(button => button.addEventListener('click',() => {{ pageFlip.turnToPage(Number(button.dataset.pageIndex)); setDrawer(false); }}));
          document.addEventListener('keydown',event => {{ if (event.key === 'ArrowRight' || event.key === 'PageDown' || event.key === ' ') {{ event.preventDefault(); pageFlip.flipNext(); }} if (event.key === 'ArrowLeft' || event.key === 'PageUp') {{ event.preventDefault(); pageFlip.flipPrev(); }} if (event.key === 'Escape') setDrawer(false); }});
        }} catch (error) {{ showFallback(error); }}
      }};
      tocToggle.addEventListener('click',() => setDrawer(!drawer.classList.contains('is-open')));
      fullscreen.addEventListener('click',async() => {{ try {{ if (!document.fullscreenElement) await document.documentElement.requestFullscreen(); else await document.exitFullscreen(); }} catch (_) {{ status.textContent = '当前浏览器未允许全屏，可继续正常阅读。'; }} }});
      document.addEventListener('fullscreenchange',() => {{ fullscreen.textContent = document.fullscreenElement ? '退出全屏' : '全屏'; }});
      start();
    }})();
  </script>
</body>
</html>
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    if output == V003.resolve():
        raise ValueError("refusing to overwrite the approved V003")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_smooth_flipbook(), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
