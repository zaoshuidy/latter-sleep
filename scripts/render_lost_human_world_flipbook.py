#!/usr/bin/env python3
"""Render the approved Lost Human World pages as a StPageFlip HTML sample."""

from __future__ import annotations

import html
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "projects" / "lost-human-world-cover"
SOURCE = PROJECT / "manuscript" / "chapter-01.md"
OUTPUT = PROJECT / "ebook" / "lost-human-world-ebook-v002.html"


def source_paragraphs() -> list[str]:
    blocks = [block.strip() for block in SOURCE.read_text(encoding="utf-8").split("\n\n")]
    paragraphs = [block for block in blocks[1:] if block]
    if len(paragraphs) != 49:
        raise ValueError(f"expected 49 source paragraphs, got {len(paragraphs)}")
    return paragraphs


def paragraph_markup(paragraphs: list[str], start: int, end: int) -> str:
    return "\n".join(
        f'              <p data-source-index="{index}">{html.escape(paragraphs[index - 1])}</p>'
        for index in range(start, end + 1)
    )


def render() -> str:
    paragraphs = source_paragraphs()
    page_ranges = ((1, 5), (6, 10), (11, 18), (19, 26), (27, 39), (40, 49))
    body_pages = [paragraph_markup(paragraphs, start, end) for start, end in page_ranges]
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <title>《失落人间》真实翻页电子样书 V002</title>
  <style>
    :root {{ --paper:#f1ede4; --paper-deep:#ded6c9; --ink:#1c1b19; --accent:#7a2428; --quiet:#8f887e; --desk:#171715; --panel:rgba(31,30,28,.94); --line:rgba(241,237,228,.14); }}
    * {{ box-sizing:border-box; }}
    html,body {{ margin:0; min-height:100%; background:var(--desk); }}
    body {{ min-height:100vh; overflow:hidden; color:#eee9e0; font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif; }}
    button {{ font:inherit; }}
    .reader {{ display:grid; grid-template-rows:58px minmax(0,1fr) 62px; min-height:100vh; background:radial-gradient(circle at 50% 18%,rgba(122,36,40,.16),transparent 36%),linear-gradient(145deg,#24231f,#11110f 68%); }}
    .topbar,.controls {{ position:relative; z-index:50; display:flex; align-items:center; justify-content:space-between; gap:16px; padding:0 24px; background:var(--panel); border-color:var(--line); backdrop-filter:blur(16px); }}
    .topbar {{ border-bottom:1px solid var(--line); }} .controls {{ justify-content:center; border-top:1px solid var(--line); }}
    .book-meta {{ display:flex; align-items:baseline; gap:13px; min-width:0; }} .book-meta strong {{ font:500 16px/1 "Songti SC",STSong,serif; letter-spacing:.18em; }} .book-meta span {{ color:#aaa39a; font-size:11px; letter-spacing:.12em; white-space:nowrap; }}
    .toolbar {{ display:flex; gap:8px; }} .ui-button {{ min-width:38px; height:34px; padding:0 12px; color:#ddd7ce; background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.13); border-radius:999px; cursor:pointer; }}
    .ui-button:hover {{ background:rgba(255,255,255,.1); border-color:rgba(255,255,255,.25); }} .ui-button:focus-visible {{ outline:2px solid #bd6669; outline-offset:2px; }} .ui-button:disabled {{ opacity:.28; cursor:default; }}
    .stage {{ position:relative; display:grid; place-items:center; min-height:0; overflow:hidden; padding:22px 34px; perspective:2200px; }}
    .book-shell {{ position:relative; width:min(94vw,1120px); height:min(calc(100vh - 164px),724px); display:grid; place-items:center; filter:drop-shadow(0 32px 42px rgba(0,0,0,.46)); }}
    .flip-book {{ display:none; width:100%; height:100%; }} .js .flip-book {{ display:block; }}
    .book-page {{ position:relative; width:500px; height:724px; overflow:hidden; color:var(--ink); background:radial-gradient(circle at 30% 18%,rgba(255,255,255,.25),transparent 34%),var(--paper); border:1px solid rgba(75,64,52,.06); }}
    .book-page::after {{ content:""; position:absolute; inset:0; pointer-events:none; box-shadow:inset 0 0 25px rgba(71,54,40,.025); }}
    .cover-page {{ background:#d8d0c3; }} .cover-page img {{ width:100%; height:100%; object-fit:cover; display:block; }}
    .inside-cover {{ background:linear-gradient(90deg,#d9d1c4,var(--paper) 8%,var(--paper)); }}
    .title-page .axis-top,.title-page .axis-bottom {{ position:absolute; left:26%; width:1px; background:var(--accent); }} .title-page .axis-top {{ top:8%; height:30%; }} .title-page .axis-bottom {{ bottom:8%; height:34%; }}
    .title-page .axis-node {{ position:absolute; left:calc(26% - 6px); top:42%; width:12px; height:12px; border:1.5px solid var(--accent); border-radius:50%; }} .title-page .axis-chevron {{ position:absolute; left:calc(26% - 7px); top:55%; width:14px; height:14px; border-right:1.5px solid var(--accent); border-bottom:1.5px solid var(--accent); transform:rotate(45deg); }}
    .vertical-title,.vertical-subtitle,.vertical-author {{ position:absolute; writing-mode:vertical-rl; font-family:"Source Han Serif SC","Noto Serif CJK SC","Songti SC",STSong,serif; }}
    .vertical-title {{ top:19%; right:42%; font-size:32px; letter-spacing:.17em; }} .vertical-subtitle {{ top:27%; right:30%; color:#494641; font-size:14px; letter-spacing:.22em; }} .vertical-author {{ top:53%; right:18%; font-size:15px; letter-spacing:.18em; }}
    .studio-mark {{ position:absolute; right:19%; bottom:7%; color:var(--quiet); font:11px/1 "Songti SC",STSong,serif; letter-spacing:.25em; }} .studio-mark::before {{ content:""; position:absolute; left:-32%; top:-17px; width:58%; border-top:1px solid rgba(122,36,40,.42); }}
    .toc-page {{ padding:72px 53px 58px; }} .toc-label {{ margin:0 0 54px; color:var(--accent); font:12px/1 "Songti SC",STSong,serif; letter-spacing:.32em; }} .toc-list {{ display:grid; gap:34px; }}
    .toc-entry {{ display:grid; grid-template-columns:36px minmax(0,1fr) auto; gap:14px; align-items:baseline; font-family:"Songti SC",STSong,serif; }} .toc-entry .node {{ color:var(--accent); font-size:11px; letter-spacing:.1em; }} .toc-entry .chapter {{ font-size:15px; letter-spacing:.06em; }} .chapter-wrap {{ display:grid; grid-template-columns:auto 1fr; gap:10px; align-items:baseline; }} .leader {{ border-bottom:1px dotted rgba(28,27,25,.18); }} .page-no {{ color:var(--quiet); font-size:11px; }}
    .folio {{ position:absolute; bottom:38px; color:var(--quiet); font:11px/1 "Songti SC",STSong,serif; }} .verso .folio {{ left:53px; }} .recto .folio {{ right:53px; }}
    .chapter-art::before {{ content:""; position:absolute; left:-5%; top:27%; width:80%; height:44%; background:var(--ink); clip-path:polygon(0 11%,50% 0,78% 18%,88% 43%,73% 65%,43% 82%,0 100%); }} .chapter-art::after {{ content:""; position:absolute; left:43%; top:58%; width:46%; border-top:2px solid var(--accent); transform:rotate(-7deg); }}
    .chapter-number {{ position:absolute; top:18%; right:16%; writing-mode:vertical-rl; color:var(--accent); font:14px/1.5 "Songti SC",STSong,serif; letter-spacing:.28em; }} .chapter-title {{ position:absolute; top:31%; right:24%; display:flex; flex-direction:row-reverse; gap:31px; font:32px/1 "Songti SC",STSong,serif; letter-spacing:.16em; }} .chapter-title span {{ writing-mode:vertical-rl; }} .chapter-title span:last-child {{ margin-top:82px; font-size:.78em; }}
    .body-page {{ padding:90px 62px 78px; }} .body-page.opening {{ padding-top:186px; }} .entry-line {{ width:58px; margin:0 0 28px 30px; border-top:2px solid var(--accent); }} .body-text {{ font:12.4px/1.66 "Source Han Serif SC","Noto Serif CJK SC","Songti SC",STSong,serif; text-align:justify; text-justify:inter-ideograph; }} .body-text p {{ margin:0; text-indent:2em; }}
    .running {{ position:absolute; top:45px; color:rgba(28,27,25,.46); font:10px/1 "Songti SC",STSong,serif; letter-spacing:.18em; }} .verso .running {{ left:62px; }} .recto .running {{ right:62px; }}
    .back-cover {{ display:grid; place-items:center; background:var(--paper-deep); }} .back-cover::before {{ content:""; position:absolute; left:-8%; top:31%; width:77%; height:36%; background:var(--ink); clip-path:polygon(0 16%,56% 0,91% 24%,76% 57%,96% 78%,42% 100%,0 82%); }} .back-cover::after {{ content:""; position:absolute; left:30%; top:57%; width:56%; border-top:2px solid var(--accent); transform:rotate(-8deg); }} .back-mark {{ position:absolute; right:54px; bottom:48px; color:#6f6960; font:12px/1 "Songti SC",STSong,serif; letter-spacing:.3em; }}
    .progress {{ min-width:190px; color:#bfb8ae; font-size:12px; text-align:center; letter-spacing:.1em; }}
    .drawer {{ position:fixed; z-index:70; top:58px; right:0; bottom:62px; width:min(360px,88vw); padding:24px; overflow:auto; color:#e9e3da; background:rgba(24,23,21,.98); border-left:1px solid var(--line); box-shadow:-20px 0 60px rgba(0,0,0,.32); transform:translateX(105%); transition:transform .28s ease; }} .drawer.is-open {{ transform:none; }} .drawer h2 {{ margin:0 0 18px; font:500 17px/1.3 "Songti SC",STSong,serif; letter-spacing:.16em; }} .drawer-list {{ display:grid; gap:8px; }}
    .drawer-button {{ display:grid; grid-template-columns:42px 1fr; gap:10px; width:100%; padding:11px 12px; color:#c9c2b9; text-align:left; background:transparent; border:1px solid rgba(255,255,255,.09); border-radius:6px; cursor:pointer; }} .drawer-button:hover,.drawer-button[aria-current="page"] {{ color:white; border-color:rgba(189,102,105,.6); background:rgba(122,36,40,.17); }} .drawer-button .index {{ color:#bd6669; }}
    .screen-reader-status {{ position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); }} .engine-note {{ position:absolute; left:18px; bottom:14px; color:#777067; font-size:10px; letter-spacing:.08em; }}
    .no-js-pages {{ display:grid; gap:18px; padding:24px; }} .js .no-js-pages {{ display:none; }}
    @media(max-width:760px) {{ .reader {{ grid-template-rows:52px minmax(0,1fr) 58px; }} .topbar,.controls {{ padding-inline:12px; }} .book-meta span {{ display:none; }} .stage {{ padding:12px; }} .book-shell {{ width:96vw; height:calc(100vh - 140px); }} .drawer {{ top:52px; bottom:58px; }} .engine-note {{ display:none; }} }}
    @media(prefers-reduced-motion:reduce) {{ *,*::before,*::after {{ scroll-behavior:auto!important; animation-duration:.01ms!important; transition-duration:.01ms!important; }} }}
  </style>
</head>
<body>
  <main class="reader" data-book-id="BOOK-LOST-HUMAN-WORLD" data-reader-state="loading" data-reader-engine="StPageFlip@2.0.7">
    <header class="topbar">
      <div class="book-meta"><strong>失落人间</strong><span>早睡的猫 · 电子样书 V002</span></div>
      <div class="toolbar"><button class="ui-button" id="toc-toggle" type="button" aria-expanded="false" aria-controls="contents-drawer">目录</button><button class="ui-button" id="fullscreen-toggle" type="button">全屏</button></div>
    </header>
    <section class="stage" aria-label="真实翻页电子书阅读区域">
      <div class="book-shell">
        <div class="flip-book" id="book">
          <section class="book-page cover-page" data-density="hard" data-page-role="front-cover" aria-label="正封"><img src="../generated/cover-v001.png" alt="《失落人间》正封"></section>
          <section class="book-page inside-cover verso" data-page-role="inside-front-cover" aria-label="封二空白页"></section>
          <section class="book-page title-page recto" data-page-role="title-page" aria-label="扉页"><span class="axis-top"></span><span class="axis-node"></span><span class="axis-chevron"></span><span class="axis-bottom"></span><span class="vertical-title" data-role="title">失落人间</span><span class="vertical-subtitle" data-role="subtitle">在所有归途之外</span><span class="vertical-author" data-role="author">早睡的猫</span><span class="studio-mark" data-role="studio_mark">纸船工作室</span></section>
          <section class="book-page toc-page verso" data-page-role="toc-left" aria-label="目录左页"><h2 class="toc-label">目录</h2><div class="toc-list"><div class="toc-entry"><span class="node">序</span><span class="chapter-wrap"><span class="chapter">灯灭以前</span><span class="leader"></span></span><span class="page-no">1</span></div><div class="toc-entry"><span class="node">01</span><span class="chapter-wrap"><span class="chapter">车窗里的故乡</span><span class="leader"></span></span><span class="page-no">6</span></div><div class="toc-entry"><span class="node">02</span><span class="chapter-wrap"><span class="chapter">白昼的缝隙</span><span class="leader"></span></span><span class="page-no">24</span></div><div class="toc-entry"><span class="node">03</span><span class="chapter-wrap"><span class="chapter">没有回声的房间</span><span class="leader"></span></span><span class="page-no">42</span></div><div class="toc-entry"><span class="node">04</span><span class="chapter-wrap"><span class="chapter">雨停在城外</span><span class="leader"></span></span><span class="page-no">62</span></div></div><span class="folio">2</span></section>
          <section class="book-page toc-page recto" data-page-role="toc-right" aria-label="目录右页"><h2 class="toc-label">CONTENTS</h2><div class="toc-list"><div class="toc-entry"><span class="node">05</span><span class="chapter-wrap"><span class="chapter">旧门向里开</span><span class="leader"></span></span><span class="page-no">84</span></div><div class="toc-entry"><span class="node">06</span><span class="chapter-wrap"><span class="chapter">乡音之外</span><span class="leader"></span></span><span class="page-no">106</span></div><div class="toc-entry"><span class="node">07</span><span class="chapter-wrap"><span class="chapter">临时住址</span><span class="leader"></span></span><span class="page-no">130</span></div><div class="toc-entry"><span class="node">08</span><span class="chapter-wrap"><span class="chapter">人间无岸</span><span class="leader"></span></span><span class="page-no">154</span></div></div><span class="folio">3</span></section>
          <section class="book-page chapter-art verso" data-page-role="chapter-opener-left" aria-label="第一章章首页左页"></section>
          <section class="book-page recto" data-page-role="chapter-opener-right" aria-label="第一章章首页右页"><span class="chapter-number">第一章</span><div class="chapter-title"><span>车窗里的</span><span>故乡</span></div></section>
          <section class="book-page body-page opening verso" data-page-role="body-6" aria-label="正文第六页"><div class="entry-line"></div><article class="body-text">
{body_pages[0]}
            </article><span class="folio">6</span></section>
          <section class="book-page body-page recto" data-page-role="body-7" aria-label="正文第七页"><article class="body-text">
{body_pages[1]}
            </article><span class="folio">7</span></section>
          <section class="book-page body-page verso" data-page-role="body-8" aria-label="正文第八页"><span class="running">失落人间</span><article class="body-text">
{body_pages[2]}
            </article><span class="folio">8</span></section>
          <section class="book-page body-page recto" data-page-role="body-9" aria-label="正文第九页"><span class="running">第一章　车窗里的故乡</span><article class="body-text">
{body_pages[3]}
            </article><span class="folio">9</span></section>
          <section class="book-page body-page verso" data-page-role="body-10" aria-label="正文第十页"><span class="running">失落人间</span><article class="body-text">
{body_pages[4]}
            </article><span class="folio">10</span></section>
          <section class="book-page body-page recto" data-page-role="body-11" aria-label="正文第十一页"><span class="running">第一章　车窗里的故乡</span><article class="body-text">
{body_pages[5]}
            </article><span class="folio">11</span></section>
          <section class="book-page back-cover" data-density="hard" data-page-role="back-cover" aria-label="封底"><span class="back-mark">纸船工作室</span></section>
        </div>
        <span class="engine-note">StPageFlip 2.0.7 · 本地离线引擎</span>
      </div>
    </section>
    <footer class="controls"><button class="ui-button" id="previous-page" type="button" aria-label="上一页" aria-keyshortcuts="ArrowLeft">←</button><div class="progress" id="progress-label" aria-live="polite">正封 · 1 / 14</div><button class="ui-button" id="next-page" type="button" aria-label="下一页" aria-keyshortcuts="ArrowRight">→</button></footer>
    <aside class="drawer" id="contents-drawer" aria-hidden="true" aria-label="阅读目录"><h2>阅读目录</h2><nav class="drawer-list"><button class="drawer-button" type="button" data-page-index="0"><span class="index">封面</span><span>失落人间</span></button><button class="drawer-button" type="button" data-page-index="2"><span class="index">扉页</span><span>书名与作者</span></button><button class="drawer-button" type="button" data-page-index="3"><span class="index">目录</span><span>全书章节</span></button><button class="drawer-button" type="button" data-page-index="5"><span class="index">第一章</span><span>车窗里的故乡</span></button><button class="drawer-button" type="button" data-page-index="7"><span class="index">正文</span><span>第 6—7 页</span></button><button class="drawer-button" type="button" data-page-index="9"><span class="index">正文</span><span>第 8—9 页</span></button><button class="drawer-button" type="button" data-page-index="11"><span class="index">正文</span><span>第 10—11 页</span></button><button class="drawer-button" type="button" data-page-index="13"><span class="index">封底</span><span>纸船工作室</span></button></nav></aside>
    <div class="screen-reader-status" id="reader-status" aria-live="assertive"></div>
  </main>
  <noscript><div class="no-js-pages">此电子样书需要浏览器 JavaScript 才能显示翻页动画；正文仍保存在本 HTML 中。</div></noscript>
  <script src="vendor/node_modules/page-flip/dist/js/page-flip.browser.js"></script>
  <script>
    document.documentElement.classList.add('js');
    (() => {{
      const reader = document.querySelector('.reader');
      const book = document.getElementById('book');
      const pages = [...document.querySelectorAll('.book-page')];
      const previous = document.getElementById('previous-page');
      const next = document.getElementById('next-page');
      const progress = document.getElementById('progress-label');
      const status = document.getElementById('reader-status');
      const drawer = document.getElementById('contents-drawer');
      const tocToggle = document.getElementById('toc-toggle');
      const fullscreen = document.getElementById('fullscreen-toggle');
      const labels = ['正封','封二','扉页','目录左页','目录右页','章首页左页','第一章','正文第6页','正文第7页','正文第8页','正文第9页','正文第10页','正文第11页','封底'];
      const hashByPage = {{0:'cover',2:'title-page',3:'toc',5:'chapter-opener',7:'body-6',9:'body-8',11:'body-10',13:'back-cover'}};
      const pageByHash = Object.fromEntries(Object.entries(hashByPage).map(([page,hash]) => [hash,Number(page)]));
      const setDrawer = open => {{ drawer.classList.toggle('is-open',open); drawer.setAttribute('aria-hidden',String(!open)); tocToggle.setAttribute('aria-expanded',String(open)); }};
      const update = index => {{
        const current = Math.max(0,Math.min(pages.length - 1,index));
        previous.disabled = current === 0;
        next.disabled = current >= pages.length - 1;
        progress.textContent = `${{labels[current]}} · ${{current + 1}} / ${{pages.length}}`;
        status.textContent = `已翻到${{labels[current]}}，第 ${{current + 1}} 页，共 ${{pages.length}} 页`;
        document.querySelectorAll('[data-page-index]').forEach(button => button.setAttribute('aria-current',Number(button.dataset.pageIndex) === current ? 'page' : 'false'));
        const anchored = Object.keys(hashByPage).map(Number).filter(page => page <= current).pop() ?? 0;
        history.replaceState(null,'',`#${{hashByPage[anchored]}}`);
      }};
      try {{
        const pageFlip = new St.PageFlip(book, {{ width:500, height:724, size:'stretch', minWidth:280, maxWidth:500, minHeight:406, maxHeight:724, autoSize:false, showCover: true, usePortrait:true, drawShadow:true, maxShadowOpacity:.32, flippingTime:850, mobileScrollSupport:true, swipeDistance:24 }});
        pageFlip.on('flip', event => update(event.data));
        pageFlip.on('init', event => update(event.data.page));
        pageFlip.loadFromHTML(document.querySelectorAll('.book-page'));
        window.bookPageFlip = pageFlip;
        reader.dataset.readerState = 'ready';
        const initialHash = location.hash.replace('#','');
        if (initialHash in pageByHash) pageFlip.turnToPage(pageByHash[initialHash]);
        previous.addEventListener('click',() => pageFlip.flipPrev('bottom'));
        next.addEventListener('click',() => pageFlip.flipNext('bottom'));
        document.querySelectorAll('[data-page-index]').forEach(button => button.addEventListener('click',() => {{ pageFlip.turnToPage(Number(button.dataset.pageIndex)); setDrawer(false); }}));
        document.addEventListener('keydown',event => {{ if (event.key === 'ArrowRight' || event.key === 'PageDown' || event.key === ' ') {{ event.preventDefault(); pageFlip.flipNext('bottom'); }} if (event.key === 'ArrowLeft' || event.key === 'PageUp') {{ event.preventDefault(); pageFlip.flipPrev('bottom'); }} if (event.key === 'Escape') setDrawer(false); }});
      }} catch (error) {{ reader.dataset.readerState = 'fallback'; book.style.display = 'grid'; book.style.gap = '18px'; status.textContent = '翻页引擎未加载，已显示顺序阅读模式。'; console.error(error); }}
      tocToggle.addEventListener('click',() => setDrawer(!drawer.classList.contains('is-open')));
      fullscreen.addEventListener('click',async() => {{ try {{ if (!document.fullscreenElement) await document.documentElement.requestFullscreen(); else await document.exitFullscreen(); }} catch (_) {{ status.textContent = '当前浏览器未允许全屏，可继续正常阅读。'; }} }});
      document.addEventListener('fullscreenchange',() => {{ fullscreen.textContent = document.fullscreenElement ? '退出全屏' : '全屏'; }});
    }})();
  </script>
</body>
</html>
'''


def main() -> int:
    OUTPUT.write_text(render(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
