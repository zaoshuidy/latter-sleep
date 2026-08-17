# 旧 Skill 迁移与保留说明

## 背景与原则

源文件为 `/Users/edy/Desktop/book/图书知识库与制作Skills套件_2026-08-06.zip`，共 27 个 `SKILL.md`。源 ZIP 只读保存；必要知识才进入 V1。完整迁移原件与决定登记在 `knowledge/indexes/legacy-reuse-registry.json`。

决定类型：`合并` 表示只把仍有效的规则写入新版 reference；`配置化` 表示转换为运行配置；`替换` 表示使用新机制；`延后` 表示 V1 不调用；`排除` 表示仅留在源 ZIP。

| # | 旧 Skill | 决定 | V1 去向 / 原因 |
|---:|---|---|---|
| 1 | `book-building-orchestrator` | 替换 | `book-production-router`，消除旧编排冲突 |
| 2 | `book-chapter-opener-automation` | 合并 | 章首页一致性规则进入编辑设计；旧自动化不迁移 |
| 3 | `book-cmyk-image-workflow` | 延后 | V1 只做图像角色与记录，不做印前色彩转换 |
| 4 | `book-flip-display` | 排除 | 翻页展示不属于生产核心 |
| 5 | `book-indesign-com-automation` | 延后 | Windows COM 实现不适合当前 Mac V1 |
| 6 | `make-pdf` | 排除 | V1 不输出印刷 PDF |
| 7 | `book-cover-design` | 替换 | 改用标准化封面提示词和可编辑文字叠加 |
| 8 | `chapter-opener-design` | 合并并保留原件 | `design-book-editorial/references/chapter-opener.md` |
| 9 | `chatgpt-image-generation` | 替换 | 统一使用系统 `imagegen` |
| 10 | `chinese-most-beautiful-book-design` | 合并 | 案例调查方法进入正式案例库规则 |
| 11 | `flipbook-html` | 排除 | 非生产核心 |
| 12 | `indesign-build` | 延后 | V1 不执行排版软件 |
| 13 | `indesign-typesetting-troubleshooting` | 延后 | 待实际软件环境建立后重新评估 |
| 14 | `orchestrator` | 替换 | 统一由新版入口与明确路由处理 |
| 15 | `paper-boat-brand` | 配置化并保留原件 | `knowledge/brand-profiles/paper-boat.json` |
| 16 | `pdf-to-indesign` | 排除 | 当前流程不做 PDF 反向重建 |
| 17 | `print-composition` | 合并并保留原件 | 网格、留白和层级原则进入编辑设计 |
| 18 | `running-headers-design` | 合并并保留原件 | 新建三个可复用 JSON 模板 |
| 19 | `toc-design` | 合并并保留原件 | 目录层级、版心与溢出规则进入新版 reference |
| 20 | `book-flipbook-html` | 排除 | 与第 11 项重复且非核心 |
| 21 | `chinese-book-cover-aesthetics` | 替换 | 旧封面 Skill 不复用；案例仅可另行核验 |
| 22 | `chinese-book-interior-typesetting` | 拆分并保留原件 | 3188 行原件不作运行时 Skill，只按需拆规则 |
| 23 | `chinese-most-beautiful-book-design`（补充版） | 合并 | 去重后进入案例与编辑设计规则 |
| 24 | `com-indesign-word-import` | 延后且不复制 | Windows / COM 依赖 |
| 25 | `indesign-book-layout` | 延后索引 | 唯一保留的后续排版 Skill 索引；V1 不调用 |
| 26 | `indesign-computer-use` | 延后且不复制 | 待本机软件和操作验证后评估 |
| 27 | `银杏纪元_正文排版` | 排除 | 项目专用，不能作为通用能力 |

## 完整原件

V1 只复制 6 份必要原件：章首页、目录、页眉页脚、平面构图、中文内文排版、纸船品牌。每份记录 SHA-256，运行时不直接执行旧 Skill。

另有 `gc-minimal-zine-poster` 作为外部上游完整快照保存。它不属于上述 27 项；其 README、SKILL、LICENSE、examples 和 references 全部保留，只做索引，不做摘要、合并或改写。

## 验收标准

- 源 ZIP SHA-256 保持 `f27c5209a03761f6ce12d8cf00cf32931d563791d088f61e09fa77e9ff3edbb1`。
- 新版运行目录没有旧封面 Skill、翻页 Skill、项目专用 Skill或旧排版自动化。
- `indesign-book-layout` 只有延后索引，没有被复制或调用。
