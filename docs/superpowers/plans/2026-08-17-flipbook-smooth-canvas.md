# 《失落人间》流畅翻页 V004 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不覆盖 V003 的前提下交付使用 StPageFlip Canvas 图片模式的 V004 和动态切换对照页。

**Architecture:** 新生成器读取 V003 已批准 PNG 与 V002 中的导航元数据，输出只含 Canvas 容器的 V004。文字检索索引位于画布外；比较页一次只加载一个版本，避免双引擎同时占用动画循环。

**Tech Stack:** Python 3、静态 HTML/CSS/JavaScript、StPageFlip 2.0.7、unittest。

## Global Constraints

- 不覆盖 V003，不修改 14 张批准 PNG。
- 不新增 CDN、后端、数据库或翻页依赖。
- V004 固定 `loadFromImages`、620ms、阴影 0.20。
- 浏览器 fallback 必须仍可顺序阅读。

---

### Task 1: V004 行为合同与生成器

**Files:**
- Modify: `tests/test_book_flipbook.py`
- Create: `scripts/render_lost_human_world_smooth_flipbook.py`
- Create: `projects/lost-human-world-cover/ebook/lost-human-world-ebook-v004-smooth.html`

**Interfaces:**
- Consumes: `ebook/pages-v003/*.png`、本地 StPageFlip 2.0.7。
- Produces: `render_smooth_flipbook() -> str` 和离线 V004 HTML。

- [x] **Step 1: Write the failing test**

加入断言：V004 文件存在；含 14 个 `pages-v003/*.png` 清单；调用 `loadFromImages` 而不是 `loadFromHTML`；含 `decode()` 预解码、`flippingTime:620`、`maxShadowOpacity:.20`、画布外文字索引和失败回退；V003 字节哈希不变。

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_book_flipbook.BookFlipbookTests.test_v004_uses_predecoded_canvas_images_without_overwriting_v003 -v`

Expected: FAIL because V004 does not exist.

- [x] **Step 3: Write minimal implementation**

生成 V004；预解码后把相对图片数组传给 `pageFlip.loadFromImages(pageImages)`；目录与按键继续调用 StPageFlip；引擎失败时创建顺序 PNG 列表。

- [x] **Step 4: Run test to verify it passes**

Run the same unittest; expected PASS.

### Task 2: 单实例动态比较页

**Files:**
- Modify: `tests/test_book_flipbook.py`
- Create: `projects/lost-human-world-cover/ebook/flip-smoothness-comparison.html`

**Interfaces:**
- Consumes: V003 与 V004 文件。
- Produces: 一次只加载一个 iframe 的版本切换器。

- [x] **Step 1: Write the failing test**

断言比较页同时提供 V003/V004 按钮、默认打开 V004、切换时替换单个 iframe `src`，不并行加载两个翻页引擎。

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_book_flipbook.BookFlipbookTests.test_flip_smoothness_comparison_loads_only_one_reader_at_a_time -v`

Expected: FAIL because comparison HTML does not exist.

- [x] **Step 3: Write minimal implementation**

新增静态比较页，按钮切换唯一 iframe 的 V003/V004 URL，并标记当前版本。

- [x] **Step 4: Run test to verify it passes**

Run the same unittest; expected PASS.

### Task 3: 验证与交付

**Files:**
- Verify only: V003、V004、对照页、14 张 PNG、本地引擎包。

- [x] **Step 1: Run focused tests**

Run: `python3 -m unittest tests.test_book_flipbook -v`

- [x] **Step 2: Run full suite**

Run: `python3 -m unittest discover -s tests -p 'test_*.py'`

- [x] **Step 3: Run static and browser checks**

检查 V004 无外链、14 条图片均存在、V003 SHA-256 未变；通过本地静态服务打开比较页并验证切换、下一页、目录、键盘和 fallback。

- [x] **Step 4: Deliver**

向用户提供 V004 与对照页的绝对可点击路径，并明确 V003 未覆盖。当前 workspace 不是 Git 仓库，因此不执行 commit。
