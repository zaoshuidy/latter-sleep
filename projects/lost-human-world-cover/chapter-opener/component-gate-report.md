# 《失落人间》章首页组件门禁报告

## 测试目标

使用已确认的第一章《车窗里的故乡》，启动 `design-book-editorial` 的章首页流程，并验证正式方向前的组件知识库门禁。

## 已确认项目输入

- 图书：失落人间
- 类型：文学小说
- 章节：第一章《车窗里的故乡》
- 正文：`../manuscript/chapter-01.md`
- 成品规格：145 × 210 mm（32 开）
- 章首页文字：必须保持可编辑，不进入背景图片像素层
- 章首页母版：全书只使用一个母版；默认隐藏页眉页脚

## 门禁结果（2026-08-13 最终更新）

### 通用设计案例索引

`check_case_library.py` 返回：

- `ok=true`
- `chapter-opener=10 confirmed`
- `errors=[]`

这些记录满足通用案例调研的数量要求，但不等于可执行的章首页组件库。

### 正式章首页组件库

维护源目标路径：

`/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/chapter-opener`

已完成首批构建，并使用 `required-count=50` 运行生产 validator，结果为：

- `valid=true`
- `status=available`
- `record_count=50`
- `errors=[]`
- `warnings=[]`
- 退出码：`0`

50 条均绑定本地原图、来源页、独立出版年证据、结构化章首页 profile 和哈希闭环。现有封面库同步重建后仍为 `valid=true / available / 50 / errors=[]`。

## 流程判断

门禁已经打开，并执行一次正式检索和人工选择：

- 未跨用封面组件记录；
- 未把通用案例索引冒充正式组件库；
- 使用第一章《车窗里的故乡》的真实内容与已确认项目规格检索出 5 本不同图书；
- 用户选择并批准方向 A：`CHO-CN-0006 + CHO-CN-0011`；
- reference selection 为 `SEL-LOST-HUMAN-WORLD-CHAPTER-A-001`；
- 2026-08-14 经用户明确授权后调用一次 `imagegen`，生成无字背景 V001；
- 章号与章题仍保存在 SVG 可编辑文字层，没有压入 AI 背景像素。

## 第一版生成结果

- 背景：`generated/chapter-opener-background-v001.png`
- 可编辑组合稿：`generated/chapter-opener-v001.svg`
- 视觉预览：`generated/chapter-opener-v001-preview.png`
- 版本证据：`versions/chapter-opener-v001.json`
- 当前状态：`draft / pending user review`
