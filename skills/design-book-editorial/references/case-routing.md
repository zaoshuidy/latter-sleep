# 案例路由

正式方向只使用 `knowledge/indexes/design-case-index.json` 中的 `confirmed` 记录。优先顺序：

1. 中国正式出版物、国家或行业书籍设计奖、出版社与设计机构项目页。
2. 国外正式出版物、国际奖项、设计机构和专业设计媒体作为补充。
3. 社媒只用于发现线索；普通网页调用现有 `scrape`，小红书专项调用 `xhs-benchmark`。发现结果先标 `candidate`，核验后才能升为 `confirmed`。

每个封面、目录、章首页、正文、图片页、页眉页脚至少 10 个确认案例。案例可以启发构图、层级、网格、材料和节奏，但项目必须：

- 至少组合两个参考来源；
- 保存 `borrowed_elements` 与 `changed_elements`；
- 改变与项目内容有关的构图逻辑、比例、字体、色彩或材料中的至少一项；
- 不复制受保护图像、完整页面或单一案例的独特组合。

外部案例门槛关闭后，可再读取 `knowledge/indexes/approved-project-case-index.json` 作为正向项目方法证据。仅使用组件匹配、状态为 `approved-positive` 且 artifact 哈希仍闭合的记录；它不进入 10 个外部 `confirmed` 案例计数。借用 `reusable_principles` 时必须同时遵守 `non_copyable_elements`，不得复制旧项目书名、正文、页码、精确坐标或完整页面。

`legacy_source`: `knowledge/legacy-sources/original-suite/chinese-book-interior-typesetting/SKILL.md`
