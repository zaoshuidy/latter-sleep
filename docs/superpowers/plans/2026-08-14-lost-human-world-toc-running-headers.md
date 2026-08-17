# 《失落人间》目录与页眉页脚原型 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为《失落人间》生成已批准的 B「归途坐标」双页测试目录与动态页眉页脚原型，并保留可编辑文字、结构化配置和可视预览。

**Architecture:** 以两个相互独立的页面组件交付：`toc/` 负责目录数据与双页导航，`running-headers/` 负责正文跨页中的书名／章名切换。JSON 是测试事实与版式规则源，HTML 是可编辑视觉源，PNG 只作为人工预览；项目测试读取 JSON、HTML 和真实图片元数据完成闭环。

**Tech Stack:** 静态 HTML/CSS、JSON、Python `unittest`、Pillow 图片元数据读取、Google Chrome headless 截图。

## Global Constraints

- 页面成品尺寸固定为 `145 × 210 mm`，跨页为 `290 × 210 mm`。
- 采用 B「归途坐标」：低对比网格、暗红纵轴、章序节点、独立页码列。
- 目录加入序章；不加入尾声、后记或其他后置内容。
- “第一章 车窗里的故乡”来自真实正文；其余章名和全部目录页码必须标记为测试数据。
- 所有目录文字、书名、章名和页码必须是可搜索、可复制、可编辑的 HTML 文字，不得栅格化。
- 正文偶数页左上显示书名，奇数页右上显示章名；目录右页页眉显示“目录”。
- 页码在外侧底部，基线距页底 `12 mm`；不得放在装订侧。
- 章首页、空白页和全出血图片页隐藏页眉与可见页码，内部计数连续。
- 不修改、校对或缩写第一章正文；不创建 InDesign、PDF 或版权页。
- 目录组件知识库仍为 `planned`；产物只能声明为功能原型，不能声明正式 reference selection 已完成。
- 当前工作区不是 Git 仓库；计划中的检查点使用测试结果和文件 SHA，不执行虚假 commit。

---

## File Structure

- Create: `projects/lost-human-world-cover/toc/toc-direction-b-v001-layout.json` — 九个测试目录项、页面尺寸、色彩、网格、区域和测试状态。
- Create: `projects/lost-human-world-cover/toc/toc-direction-b-v001.html` — B 方向双页目录的可编辑视觉源。
- Create: `projects/lost-human-world-cover/toc/toc-direction-b-v001-preview.png` — 目录跨页人工预览。
- Create: `projects/lost-human-world-cover/toc/toc-direction-b-v001-review.md` — 目录准确性与边界检查。
- Create: `projects/lost-human-world-cover/running-headers/running-headers-b-v001-layout.json` — 页眉来源、页码位置和隐藏规则。
- Create: `projects/lost-human-world-cover/running-headers/running-headers-b-v001.html` — 使用第一章真实正文片段的动态页眉页脚跨页。
- Create: `projects/lost-human-world-cover/running-headers/running-headers-b-v001-preview.png` — 页眉页脚人工预览。
- Create: `projects/lost-human-world-cover/running-headers/running-headers-b-v001-review.md` — 左右来源、安全区和正文不变检查。
- Modify: `tests/test_lost_human_world_cover_project.py` — 自动验收上述两个组件。
- Modify: `projects/lost-human-world-cover/README.md` — 登记 B 方向和原型路径。

---

### Task 1: B「归途坐标」目录跨页

**Files:**
- Create: `projects/lost-human-world-cover/toc/toc-direction-b-v001-layout.json`
- Create: `projects/lost-human-world-cover/toc/toc-direction-b-v001.html`
- Test: `tests/test_lost_human_world_cover_project.py`

**Interfaces:**
- Consumes: 已批准设计规格 `docs/superpowers/specs/2026-08-14-lost-human-world-toc-running-headers-design.md`。
- Produces: `toc-direction-b-v001-layout.json` 和含 `data-text-layer="editable"` 的目录 HTML，供 Task 3 截图与审核。

- [ ] **Step 1: Write the failing directory contract test**

在 `LostHumanWorldCoverProjectTests` 增加：

```python
def test_toc_direction_b_v001_keeps_test_entries_editable_and_aligned(self):
    layout = self.load("toc/toc-direction-b-v001-layout.json")
    page_html = (PROJECT / "toc/toc-direction-b-v001.html").read_text(encoding="utf-8")
    expected = [
        ("序章", "灯灭以前", 1),
        ("第一章", "车窗里的故乡", 6),
        ("第二章", "白昼的缝隙", 24),
        ("第三章", "没有回声的房间", 42),
        ("第四章", "雨停在城外", 62),
        ("第五章", "旧门向里开", 84),
        ("第六章", "乡音之外", 106),
        ("第七章", "临时住址", 130),
        ("第八章", "人间无岸", 154),
    ]
    self.assertEqual(expected, [(x["level"], x["title"], x["page"]) for x in layout["entries"]])
    self.assertEqual([145, 210], layout["page_trim_mm"])
    self.assertEqual("prototype", layout["status"])
    self.assertTrue(layout["test_content"]["synthetic_titles"])
    self.assertTrue(layout["test_content"]["provisional_pages"])
    self.assertIn('data-text-layer="editable"', page_html)
    self.assertEqual(9, page_html.count('class="toc-entry"'))
    self.assertNotIn("toc-component-selection", layout)
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
.venv/bin/python -m unittest \
  tests.test_lost_human_world_cover_project.LostHumanWorldCoverProjectTests.test_toc_direction_b_v001_keeps_test_entries_editable_and_aligned -v
```

Expected: `FileNotFoundError` for `toc/toc-direction-b-v001-layout.json`.

- [ ] **Step 3: Create the exact JSON fact source**

JSON must use this top-level contract:

```json
{
  "schema_version": "1.0",
  "layout_id": "TOC-LOST-HUMAN-WORLD-B-V001",
  "project_id": "BOOK-LOST-HUMAN-WORLD",
  "component_type": "toc",
  "direction": "B-return-coordinate",
  "status": "prototype",
  "page_trim_mm": [145, 210],
  "spread_trim_mm": [290, 210],
  "entries": [],
  "test_content": {
    "synthetic_titles": true,
    "provisional_pages": true,
    "only_source_confirmed_title": "第一章 车窗里的故乡"
  },
  "palette": {"paper": "#F1EDE4", "ink": "#1C1B19", "accent": "#7A2428", "quiet": "#B8AEA0"},
  "layout": {
    "opening_mode": "spread",
    "left_entries": [0, 1, 2, 3, 4],
    "right_entries": [5, 6, 7, 8],
    "page_number_alignment": "fixed-right-column",
    "long_title_fallback": "wrap-with-hanging-indent-and-fixed-page-column"
  }
}
```

按规格表逐项填入九个 `entries`，不得增加尾声或后记。

- [ ] **Step 4: Create the editable HTML spread**

HTML 使用 1740 × 1260 px 跨页画布，对应既有正文样张比例；核心 DOM 固定为：

```html
<main class="spread" data-text-layer="editable" data-prototype-status="test-content">
  <section class="page left-page" aria-label="目录左页"></section>
  <section class="page right-page" aria-label="目录右页"></section>
</main>
```

每个目录项使用：

```html
<div class="toc-entry" data-entry-index="0" data-page-status="provisional">
  <span class="chapter-node">00</span>
  <span class="chapter-title">灯灭以前</span>
  <span class="chapter-page">1</span>
</div>
```

CSS 必须建立固定章序列、可换行章名列和固定页码列；目录页眉分别为“失落人间”与“目录”，页脚为外侧 `2`、`3`。

- [ ] **Step 5: Run the directory test and verify GREEN**

Run the Step 2 command. Expected: `OK`.

- [ ] **Step 6: Record a non-Git checkpoint**

Run:

```bash
shasum -a 256 \
  projects/lost-human-world-cover/toc/toc-direction-b-v001-layout.json \
  projects/lost-human-world-cover/toc/toc-direction-b-v001.html
```

Save the two hashes in Task 3 review notes; do not claim a Git commit.

---

### Task 2: 动态页眉页脚正文跨页

**Files:**
- Create: `projects/lost-human-world-cover/running-headers/running-headers-b-v001-layout.json`
- Create: `projects/lost-human-world-cover/running-headers/running-headers-b-v001.html`
- Test: `tests/test_lost_human_world_cover_project.py`

**Interfaces:**
- Consumes: `manuscript/chapter-01.md` 的正文段落 11—18；模板语义 `paired-standard` 与 `folio-outer`。
- Produces: 动态页眉页脚 JSON 和 HTML，供 Task 3 截图与审核。

- [ ] **Step 1: Write the failing running-header contract test**

```python
def test_running_headers_b_v001_use_real_text_and_mirrored_sources(self):
    source = (PROJECT / "manuscript/chapter-01.md").read_text(encoding="utf-8")
    source_paragraphs = [x.strip() for x in source.split("\n\n")[1:] if x.strip()]
    layout = self.load("running-headers/running-headers-b-v001-layout.json")
    page_html = (PROJECT / "running-headers/running-headers-b-v001.html").read_text(encoding="utf-8")
    rendered = [
        html_module.unescape(re.sub(r"<[^>]+>", "", value)).strip()
        for value in re.findall(r'<p data-source-index="\d+">(.*?)</p>', page_html, flags=re.S)
    ]
    self.assertEqual(source_paragraphs[10:18], rendered)
    self.assertEqual("失落人间", layout["running_headers"]["verso_source_value"])
    self.assertEqual("车窗里的故乡", layout["running_headers"]["recto_source_value"])
    self.assertEqual("outer-bottom", layout["folio"]["position"])
    self.assertEqual(12, layout["folio"]["bottom_mm"])
    self.assertEqual(["chapter-opener", "blank", "full-bleed-image"], layout["hidden_page_types"])
    self.assertIn('data-running-source="book-title"', page_html)
    self.assertIn('data-running-source="chapter-title"', page_html)
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
.venv/bin/python -m unittest \
  tests.test_lost_human_world_cover_project.LostHumanWorldCoverProjectTests.test_running_headers_b_v001_use_real_text_and_mirrored_sources -v
```

Expected: `FileNotFoundError` for `running-headers-b-v001-layout.json`.

- [ ] **Step 3: Create the running-header JSON**

Use the exact values:

```json
{
  "schema_version": "1.0",
  "layout_id": "RUNNING-HEADERS-LOST-HUMAN-WORLD-B-V001",
  "project_id": "BOOK-LOST-HUMAN-WORLD",
  "status": "prototype",
  "template": "paired-standard",
  "source_paragraph_range": [11, 18],
  "running_headers": {
    "verso_source": "book_title",
    "verso_source_value": "失落人间",
    "recto_source": "chapter_title",
    "recto_source_value": "车窗里的故乡"
  },
  "folio": {"position": "outer-bottom", "bottom_mm": 12, "folios": [8, 9]},
  "hidden_page_types": ["chapter-opener", "blank", "full-bleed-image"],
  "long_title_fallback": "use-approved-short-title-or-hide-running-head"
}
```

- [ ] **Step 4: Create the editable正文 HTML**

复用 V002 的 `10.5 pt / 17.5 pt / 2 em / 0 pt` 正文规则。偶数页页眉节点必须是：

```html
<span class="running-header verso" data-running-source="book-title">失落人间</span>
```

奇数页页眉节点必须是：

```html
<span class="running-header recto" data-running-source="chapter-title">车窗里的故乡</span>
```

正文只复制源段落 11—18，并保留 `data-source-index`；页码 8、9 分别位于左页左下和右页右下。

- [ ] **Step 5: Run the running-header test and verify GREEN**

Run the Step 2 command. Expected: `OK`.

- [ ] **Step 6: Record a non-Git checkpoint**

```bash
shasum -a 256 \
  projects/lost-human-world-cover/running-headers/running-headers-b-v001-layout.json \
  projects/lost-human-world-cover/running-headers/running-headers-b-v001.html
```

---

### Task 3: 预览、视觉检查和项目登记

**Files:**
- Create: `projects/lost-human-world-cover/toc/toc-direction-b-v001-preview.png`
- Create: `projects/lost-human-world-cover/toc/toc-direction-b-v001-review.md`
- Create: `projects/lost-human-world-cover/running-headers/running-headers-b-v001-preview.png`
- Create: `projects/lost-human-world-cover/running-headers/running-headers-b-v001-review.md`
- Modify: `projects/lost-human-world-cover/README.md`
- Test: `tests/test_lost_human_world_cover_project.py`

**Interfaces:**
- Consumes: Task 1 与 Task 2 的 HTML/JSON。
- Produces: 两张 1740 × 1260 PNG、两份审核记录、README 状态，供用户视觉评判。

- [ ] **Step 1: Extend tests to require real previews**

在 Task 1/2 两个测试中分别加入：

```python
metadata = read_image_metadata(PROJECT / "toc/toc-direction-b-v001-preview.png")
self.assertEqual({"width": 1740, "height": 1260}, {"width": metadata["width"], "height": metadata["height"]})
```

另一张路径替换为 `running-headers/running-headers-b-v001-preview.png`。

- [ ] **Step 2: Run both tests and verify RED**

Expected: both fail because preview PNG files do not exist.

- [ ] **Step 3: Render both HTML files with Chrome headless**

```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CHROME" --headless --disable-gpu --hide-scrollbars \
  --window-size=1740,1260 \
  --screenshot="$(pwd)/projects/lost-human-world-cover/toc/toc-direction-b-v001-preview.png" \
  "file://$(pwd)/projects/lost-human-world-cover/toc/toc-direction-b-v001.html"
"$CHROME" --headless --disable-gpu --hide-scrollbars \
  --window-size=1740,1260 \
  --screenshot="$(pwd)/projects/lost-human-world-cover/running-headers/running-headers-b-v001-preview.png" \
  "file://$(pwd)/projects/lost-human-world-cover/running-headers/running-headers-b-v001.html"
```

- [ ] **Step 4: Inspect both previews visually**

Use `view_image` on both PNGs. Confirm:

- gutter is visible but no text enters it;
- all nine directory items are legible;
- `106/130/154` share one right-aligned column;
- header hierarchy is weaker than body text;
- left folio is on the left outer edge, right folio on the right outer edge;
- no crop, overflow, placeholder, broken glyph or accidental scroll bar.

If any check fails, edit the relevant HTML and rerender before continuing.

- [ ] **Step 5: Write review records and README entry**

Each review Markdown must record source/status, exact visual checks, prototype boundary, HTML/JSON/PNG SHA-256, and state that no InDesign/PDF/reference selection was created. README adds a “目录与页眉页脚测试” section linking both prototypes and marking B selected.

- [ ] **Step 6: Run focused and full verification**

```bash
.venv/bin/python -m unittest tests.test_lost_human_world_cover_project -v
.venv/bin/python scripts/validate_all.py
```

Expected: project tests all pass; full suite exits `0`; cover remains `available/50`; chapter-opener remains valid; TOC remains honestly `planned`.

- [ ] **Step 7: Final non-Git checkpoint**

```bash
shasum -a 256 \
  projects/lost-human-world-cover/toc/toc-direction-b-v001-* \
  projects/lost-human-world-cover/running-headers/running-headers-b-v001-* \
  projects/lost-human-world-cover/README.md
```

Report hashes and test counts; do not claim a commit.

---

## Plan Self-Review

- Spec coverage: the plan covers the directory spread, dynamic running headers, outer folios, hidden page types, real first-chapter text, editable HTML, JSON sources, PNG previews, prototype labeling and full regression.
- Placeholder scan: no `TBD`, `TODO`, “implement later” or undefined function/type remains.
- Type consistency: both tests use the existing project `load()` helper; JSON property names match the implementation snippets; preview paths match Chrome output paths.
- Scope: TOC and running headers remain two independent components with one shared visual direction; no unrelated refactor or InDesign/PDF work is included.
