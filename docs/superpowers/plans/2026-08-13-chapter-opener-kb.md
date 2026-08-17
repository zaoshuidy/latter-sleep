# 章首页组件知识库实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** 建立中国近十年章首页组件知识库，并在达到 50 条真实有效记录后开放《失落人间》的 5 案例检索。

**Architecture:** 复用现有共享来源表、资产哈希、record、catalog、retrieval-index 和 manifest 机制；为 `chapter-opener` 增加专用 profile、分类字段与检索目标。封面库保持原样，两个组件严格隔离。

**Tech Stack:** Python 3.14、JSON Schema、Pillow、unittest、现有 component-kb CLI。

## Global Constraints

- 案例限中国正式出版图书，出版年 2017–2026。
- 每条必须有直接可见的章首页资产与独立出版年证据。
- 图片只作内部研究，生命周期和授权状态均为 `accumulation`。
- 章节号、标题、引文和页码保持可编辑文字，不进入生成底图。
- 少于 50 条时状态只能为 `building`；不得虚报 `available`。
- 不得跨用封面图片或未经核验的普通内页。

---

### Task 1：章首页数据与构建合同

**Files:**
- Modify: `schemas/book-component-reference-record.schema.json`
- Modify: `schemas/book-component-retrieval-query.schema.json`
- Modify: `ai/book_component_kb/build.py`
- Modify: `ai/book_component_kb/validate.py`
- Test: `tests/test_component_kb_chapter_opener.py`

- [ ] 先写失败测试，锁定章首页 profile、专用分类文件、组件隔离和 `building` 状态。
- [ ] 最小扩展共享构建器和 validator，保持 cover 既有输出字节与测试不变。
- [ ] 运行章首页聚焦测试和原 cover build/validate 回归。

### Task 2：真实案例批次落库

**Files:**
- Create: `knowledge/book-component-libraries/chapter-opener/records/CHO-CN-*.json`
- Create: `knowledge/book-component-libraries/chapter-opener/assets/CHO-CN-*`
- Modify: `knowledge/book-component-libraries/source-registry.json`
- Create: `docs/research/chapter-opener-kb-sources.md`

- [ ] 合并多 Agent 候选，按书名、ISBN、图片 SHA 和可见页面去重。
- [ ] 下载原图并核验 MIME、尺寸、SHA；看不清的记录拒绝落库。
- [ ] 逐条绑定来源、出版年证据和保守可见拆解。
- [ ] 每批构建后运行 validator；不足 50 条保持 `building`。

### Task 3：50 条验收与项目检索

**Files:**
- Create: `projects/lost-human-world-cover/chapter-opener/query.json`
- Create: `projects/lost-human-world-cover/chapter-opener/retrieval-result.json`
- Create: `projects/lost-human-world-cover/chapter-opener/case-board.html`

- [ ] 验证 50 本或满足严格 book diversity 的有效案例、50 个唯一资产 SHA、完整派生哈希闭环。
- [ ] 运行 `valid=true / status=available / record_count=50 / errors=[]` 门禁。
- [ ] 用第一章真实信息执行一次正式检索，返回 5 本不同书。
- [ ] 展示真实资产和逐候选可借字段，等待用户进行两阶段人工映射。
