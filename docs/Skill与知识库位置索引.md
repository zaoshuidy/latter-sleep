# Skill 与知识库位置索引

## 使用原则

- 日常修改只在维护源进行；Windows 当前维护源为 `D:\book-production-skills-v1\`。
- Codex 实际调用个人运行副本：`~/.codex/book-production-skills-v1/`。
- `~/.codex/skills/` 下的九个同名目录是入口，不是独立副本。
- 修改维护源后运行 `python scripts/install_personal.py --replace`，不要直接修改安装副本。

## 总位置

| 用途 | 位置 |
|---|---|
| 维护源 | Windows：`D:\book-production-skills-v1\`；Mac：用户自定维护目录 |
| 个人运行副本 | `~/.codex/book-production-skills-v1/` |
| Skill 入口根目录 | `~/.codex/skills/` |
| 机器可读完整索引 | `~/.codex/book-production-skills-v1/LOCATION-INDEX.json` |
| Codex 根目录指针 | `~/.codex/skills/BOOK-PRODUCTION-LOCATION.json` |
| V1.2 BookSkill 发布包 | `~/Desktop/BookSkill_图书生产Skills套件_V1.2_2026-08-17.zip` |
| V1.2 校验文件 | `~/Desktop/BookSkill_图书生产Skills套件_V1.2_2026-08-17_SHA256.txt` |

## 九个 Skill 入口

| Skill | 个人入口 | 真实运行位置 |
|---|---|---|
| `book-production-router` | `~/.codex/skills/book-production-router/` | `~/.codex/book-production-skills-v1/skills/book-production-router/` |
| `build-template-book` | `~/.codex/skills/build-template-book/` | `~/.codex/book-production-skills-v1/skills/build-template-book/` |
| `plan-memorial-book` | `~/.codex/skills/plan-memorial-book/` | `~/.codex/book-production-skills-v1/skills/plan-memorial-book/` |
| `design-book-editorial` | `~/.codex/skills/design-book-editorial/` | `~/.codex/book-production-skills-v1/skills/design-book-editorial/` |
| `create-book-images` | `~/.codex/skills/create-book-images/` | `~/.codex/book-production-skills-v1/skills/create-book-images/` |
| `review-book-production` | `~/.codex/skills/review-book-production/` | `~/.codex/book-production-skills-v1/skills/review-book-production/` |
| `build-book-flipbook` | `~/.codex/skills/build-book-flipbook/` | `~/.codex/book-production-skills-v1/skills/build-book-flipbook/` |
| `build-indesign-book` | `~/.codex/skills/build-indesign-book/` | `~/.codex/book-production-skills-v1/skills/build-indesign-book/` |
| `evolve-book-skills` | `~/.codex/skills/evolve-book-skills/` | `~/.codex/book-production-skills-v1/skills/evolve-book-skills/` |

## 知识库分区

下表路径均位于个人运行副本 `~/.codex/book-production-skills-v1/` 内。

| 内容 | 相对位置 | 维护规则 |
|---|---|---|
| 设计案例主索引 | `knowledge/indexes/design-case-index.json` | 新案例先核验来源，再记录借鉴与变化 |
| 正向项目案例索引 | `knowledge/indexes/approved-project-case-index.json` | 只收用户明确认可、文件哈希闭合的真实项目结果；不增加外部案例计数，不作为一比一套用模板 |
| 旧 Skill 复用登记 | `knowledge/indexes/legacy-reuse-registry.json` | 记录保留、迁移、排除和延后 |
| 上游 Skill 索引 | `knowledge/indexes/upstream-skills.json` | 固定来源、许可、commit 和文件哈希 |
| 纸船品牌配置 | `knowledge/brand-profiles/paper-boat.json` | 作为运行数据，不作为独立 Skill |
| 旧套件完整保留项 | `knowledge/legacy-sources/original-suite/` | 只读保存，不直接修改 |
| 第三方完整快照 | `knowledge/upstream/` | 完整保存，不总结、不覆盖 |
| 每周维护收件箱 | `knowledge/maintenance/inbox/` | 放置当周新增、失效和候选项目清单 |
| 每周维护报告 | `knowledge/maintenance/reports/` | 按日期保存周报与归档移动清单 |
| 组件来源登记 | `knowledge/book-component-libraries/source-registry.json` | 绑定来源页、出版年份证据、采集日期与生命周期 |
| 封面知识库根目录 | `knowledge/book-component-libraries/cover/` | `available`，50 个中国图书案例 |
| 封面机器清单 | `knowledge/book-component-libraries/cover/manifest.json` | 绑定 records、assets 与派生索引的哈希闭环 |
| 封面案例记录 | `knowledge/book-component-libraries/cover/records/` | 50 份结构化案例，只记录来源可证及画面可见信息 |
| 封面原始参考图 | `knowledge/book-component-libraries/cover/assets/` | 内部研究与检索用；公开展示不等于商业复制授权 |
| 章首页知识库根目录 | `knowledge/book-component-libraries/chapter-opener/` | `available`，50 个严格闭环中国图书案例，已开放正式项目检索 |
| 章首页机器清单 | `knowledge/book-component-libraries/chapter-opener/manifest.json` | 绑定章首页 records、assets 与 5 类专用派生索引 |
| 章首页案例记录 | `knowledge/book-component-libraries/chapter-opener/records/` | 只收实际章首页/篇章扉页可见、出版年独立闭环的结构化记录 |
| 章首页原始参考图 | `knowledge/book-component-libraries/chapter-opener/assets/` | 内部研究与检索用；不因公开可下载而获得商业复制授权 |
| 页眉页脚模板 | `templates/running-headers/` | 项目级复用 |
| 数据契约 | `schemas/` | 约束 Skill 间输入输出 |
| 端到端样例 | `examples/four-seasons-letters/` | 用于验证，不冒充完整书稿 |

## 查找顺序

1. Agent 先读取 `~/.codex/skills/BOOK-PRODUCTION-LOCATION.json`。
2. 根据其中的 `location_index` 打开完整机器索引。
3. 根据 `skills` 或 `knowledge` 字段定位具体文件。
4. 需要修改时回到 `maintenance_source`，修改、验证、重新安装。

封面组件检索优先读取机器索引中的 `cover_manifest`、`cover_records` 和 `cover_assets`；章首页检索读取对应的 chapter-opener 清单、记录和资产。不得绕开 manifest 直接把任意图片当成已验证案例。两个库当前均为 `available / 50`，但组件必须严格隔离。目录和插画装饰库仍为 `planned`。

## 更新检查

每次重新安装后确认：

```bash
python -m json.tool ~/.codex/skills/BOOK-PRODUCTION-LOCATION.json
python ~/.codex/book-production-skills-v1/scripts/validate_all.py
```
