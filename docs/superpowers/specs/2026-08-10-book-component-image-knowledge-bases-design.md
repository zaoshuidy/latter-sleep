# 中国图书部件图片知识库与全流程设计

日期：2026-08-10  
状态：待用户审核  
适用套件：`book-production-skills-v1`  
参考包：`/Users/edy/Desktop/商业图文生产Skill与知识库_极速艺术字版_V3_20260807.zip`  
参考包 SHA-256：`3941d5376afb0896c0689e725ba5f1a3b55ef63faae2feecf688d08632dad4ba`

## 1. 背景

现有图书生产套件已经建立封面、目录、章首页等编辑设计案例索引，但仍缺少像商业图文 V3 那样具备本地图片、单图拆解、派生分类、可解释检索、Prompt 台账、审核状态和哈希闭环的完整图片知识库。

本设计不复制商业海报案例，也不把商业海报的一遍式图文生成方式用于图书。它只借鉴商业图文 V3 已有的知识库工程和治理方式，为中国图书部件分别建设专业图片知识库。

## 2. 目标用户

主要用户是个人 Mac 上进行中文纪念书、书信日记、散文诗歌、成长纪念和集体纪念图书制作的设计负责人。系统同时供 Codex Agent 调用，用于案例检索、视觉方向、提示词编译、生图审核和认可案例回流。

## 3. 目标

1. 建立四个相互隔离的中国图书部件知识库。
2. 每个知识库首版含 50 个有效案例，共 200 条记录。
3. 案例时间范围固定为 2017—2026 年。
4. 每张案例图具备本地资产、来源、部件专用拆解、检索字段和 SHA-256。
5. 每次检索返回 5 本不同书的真实案例，并解释匹配原因。
6. 把参考选择编译为图书部件专用 Prompt，统一调用系统 `imagegen`。
7. 保持书名、目录项、章节标题、页码等关键文字为可编辑文字层。
8. 建立图片版本审核和认可案例回流机制。

## 4. 范围

### 4.1 首版四个知识库

1. `cover`：封面系统知识库。
2. `toc`：目录设计知识库。
3. `chapter-opener`：章首页知识库。
4. `illustration-decoration`：插画与装饰元素知识库。

### 4.2 明确排除

- 正文图文跨页知识库。
- 整版图片与跨页知识库。
- 页眉页脚图片知识库；继续使用现有模板。
- 版权页。
- InDesign、PDF 和印刷执行。
- 网页 Agent 前端。
- 文字校对、改写、删减或补充。
- 商业海报案例直接迁入图书知识库。
- 正式书名、目录文字、章节标题和页码固化进生成图片。
- 自动创建系统定时任务。

## 5. 参考系统取舍

### 5.1 复用的机制

- 本地图片与单图 record 一一绑定。
- `records`、`catalog`、分类索引、检索索引和 `manifest` 分层。
- 资产、record 和派生索引形成 SHA-256 闭环。
- 每项观察保留 `value`、`visibility`、`confidence`、`evidence` 和 `content_tags`。
- 知识库完整性验证先于检索。
- 可解释加权评分、去重、稳定排序和真实候选不足时受控失败。
- 每张参考图明确借鉴字段、已有基础、调整方式、保留和排除内容。
- Prompt、参考图、输出文件、版本和人工审核可追溯。
- 认可结果进入知识库；历史和否决记录归档、不删除。

### 5.2 不复用的机制

- 一遍式生成准确商业文案和艺术字。
- 商品事实、卖点、促销和费用审批。
- 商业用途十分类。
- 固定 22 项商业创意访谈。
- 3:4 海报模板和 Pillow 确定性海报排版。
- 把全部来源统一标记为 `licensed`。

## 6. 架构决策

采用“四库独立、来源共享”架构。

```text
中国图书案例来源总表
├── 封面知识库：50条
├── 目录知识库：50条
├── 章首页知识库：50条
└── 插画与装饰知识库：50条
```

每张图片是一个独立 record。同一本书使用同一 `book_case_id`，同一套设计使用同一 `series_id`。同一本书可以向多个部件知识库贡献不同页面，但在任一单次检索结果中最多出现一次。

未采用统一大库，原因是跨部件字段会造成误检；未采用完整书籍套装优先，原因是公开案例通常缺少同一本书的全部部件。

## 7. 目录结构

```text
knowledge/book-component-libraries/
├── source-registry.json
├── cover/
│   ├── manifest.json
│   ├── catalog.json
│   ├── retrieval-index.json
│   ├── categories/
│   ├── records/
│   └── assets/
├── toc/
│   ├── manifest.json
│   ├── catalog.json
│   ├── retrieval-index.json
│   ├── categories/
│   ├── records/
│   └── assets/
├── chapter-opener/
│   ├── manifest.json
│   ├── catalog.json
│   ├── retrieval-index.json
│   ├── categories/
│   ├── records/
│   └── assets/
└── illustration-decoration/
    ├── manifest.json
    ├── catalog.json
    ├── retrieval-index.json
    ├── categories/
    ├── records/
    └── assets/
```

人工维护内容限于 `source-registry.json`、`records/*.json` 和原始案例图片。`catalog.json`、`categories/*.json`、`retrieval-index.json`、`manifest.json`、哈希和统计报告均由构建脚本生成。

## 8. 来源与积累策略

首版收集中国 2017—2026 年的图书设计案例。来源优先顺序：

1. 中国出版与图书设计相关官方奖项、年鉴和机构页面。
2. 出版社、设计师或设计工作室公开项目。
3. 专业图书设计媒体、展览和院校出版设计资料。
4. 小红书等社交平台仅作为补充发现渠道；需要时调用现有抓取 Skill。

第一阶段采用积累模式，不设授权阻断。所有记录保留 `source_url`、来源平台、采集时间和原始文件哈希；状态统一从 `accumulation` 开始，后续再增加授权治理。不能把未核验素材虚假标记为 `licensed`。

## 9. 共享记录模型

每个单图 record 包含：

```text
identity
source
asset
component_profile
visual_decomposition
reference_transfer
retrieval_features
lifecycle
```

### 9.1 identity

- `record_id`
- `component_type`
- `book_case_id`
- `series_id`
- `record_version`

### 9.2 source

- 书名
- 设计者
- 出版社
- 出版年份
- 来源网址
- 来源平台
- 采集日期

### 9.3 asset

- 包内相对路径
- 文件名
- MIME 类型
- 宽、高和画幅
- SHA-256

### 9.4 visual_decomposition

每项观察统一包含：

- `value`
- `visibility`：`visible/partially_visible/not_visible/uncertain`
- `confidence`
- `evidence`
- `content_tags`

看不清时必须使用 `uncertain` 或 `not_visible`，不得根据文件名、书名、其他页面或常识补全。

### 9.5 reference_transfer

- `include_fields`
- `existing_baseline`
- `adjustment_instruction`
- `preserve_elements`
- `exclude_fields`
- `required_changes`

### 9.6 lifecycle

- `accumulation`
- `confirmed`
- `archived`

## 10. 部件专用分类

### 10.1 封面

- 封一、封四、书脊、勒口及展开连续性。
- 书名、作者和出版社层级。
- 图像型、字体型、抽象型、摄影型、插画型。
- 中心、偏轴、满版、留白、边框和网格构图。
- 书名安全区与可编辑文字区域。
- 色彩、对比、材质、印刷效果和缩略图辨识度。

### 10.2 目录

- 单页、跨页和多页形式。
- 一级至三级标题层级。
- 页码位置和视觉关联。
- 横排、竖排、分栏和自由网格。
- 标题长短、密度和溢出处理。
- 图片、装饰、留白与目录文字关系。
- 阅读顺序和导航清晰度。

### 10.3 章首页

- 单页或跨页形式。
- 章节编号、标题、副标题和引文层级。
- 图片必选、可选或纯文字。
- 留白比例、视觉重心和进入正文的节奏。
- 全书母版一致性。
- 不同长度标题的适配。
- 图片安全区和可编辑标题区。

### 10.4 插画与装饰

- 回忆插画、抽象插画、章节装饰、纹理、底图和分隔元素。
- 手绘、版画、水彩、拼贴、几何和摄影合成媒介。
- 叙事作用和情绪作用。
- 重复、平铺、裁切和延展能力。
- 透明背景需求。
- 与文字区、装订线和出血区的关系。
- 色彩数量、细节密度和印刷适应性。
- 纪实照片与非纪实插画的真实性标记。

## 11. 数据契约

首版新增八个 schema：

1. `book-component-reference-record`
2. `book-component-source-registry`
3. `book-component-retrieval-query`
4. `book-component-retrieval-result`
5. `book-component-reference-selection`
6. `book-component-prompt`
7. `book-component-image-review`
8. `book-component-kb-promotion`

基础 record 使用共享 schema；`component_profile` 通过 `oneOf` 进入四个部件专用结构，避免复制共享字段。

## 12. 检索流程

```text
项目真实内容
→ 确定部件
→ 校验目标知识库
→ 加权评分
→ 按资产和record去重
→ 按book_case_id限制
→ 稳定排序
→ 返回5本不同书
```

封面查询不能返回目录或海报；目录查询必须包含真实层级、页数和标题长度；章首页查询必须包含标题长度、引文和图片条件；插画查询必须包含叙事作用、媒介和真实性类型。

每个候选必须返回真实图片、`record_id`、`book_case_id`、字段分数、总分和匹配原因。不足 5 本不同书时返回真实缺口，不重复、不补造。

## 13. 参考选择与两套方向

用户从 5 个候选中选择 2—3 张，并逐图指定角色：

```text
图1：构图与留白
图2：字体气质与标题区域
图3：色彩、材质或装饰
```

禁止使用“整体借鉴风格”作为映射。每张参考图必须填写 `include_fields`、`existing_baseline`、`adjustment_instruction`、`preserve_elements` 和 `exclude_fields`。

四个部件不分别发展成互相冲突的风格。系统先建立两套全书 `design-genome`，再让四个知识库为每个方向分别提供参考配方。用户审核代表性样页后选择或混合一个方向。

## 14. Prompt 编译

部件 Prompt 固定为：

```text
PROJECT_TRUTH
COMPONENT_ROLE
DESIGN_GENOME
REFERENCE_TRANSFERS
COMPOSITION
IMAGE_CONTENT
COLOR_LIGHT_MATERIAL
EDITABLE_TEXT_SAFE_ZONES
PRINT_AND_CROP
NEGATIVE
OUTPUT_SPEC
```

- 封面生成无字视觉，并标记书名、作者和书脊安全区。
- 目录只生成背景、装饰和图像锚点，不生成目录文字或页码。
- 章首页只生成底图、插画或装饰，不生成章节标题。
- 插画和装饰不得包含可读文字；回忆插画标记为非纪实。

Prompt 编译器只接受已确认设计基因和参考选择，不能自行增加参考元素、正文内容或文字。

## 15. 生图、审核与回流

统一调用系统 `imagegen`。每张图记录：

- `image_id`
- 部件和用途
- Prompt 路径及 SHA-256
- 参考 record ID
- 输出路径及 SHA-256
- 版本
- `draft/selected/archived/rejected`

审核检查：

- 多余文字、乱码或伪页码。
- 可编辑文字安全区。
- 与全书设计基因的一致性。
- 是否过度接近单一案例。
- 裁切、出血、装订和画幅要求。
- Prompt、参考、输出和状态是否可追溯。
- 回忆插画是否错误冒充纪实照片。

只有 `selected` 图片进入正式项目。项目负责人认可后，可通过 `book-component-kb-promotion` 进入对应知识库。否决和旧版本只归档、不删除。

## 16. 人工审核点

1. 五个检索候选及 2—3 张参考映射。
2. 两套全书视觉方向和代表性样页。
3. 生成图片的选中版本。
4. 项目图片是否回流知识库。

人工确认不能由模型自评、沉默或继续执行替代。

## 17. 状态与异常处理

- 图片缺失、不可读或哈希不符：record 不进入检索。
- 相同图片 SHA-256：去重，不复制成新案例。
- 出版年份不在 2017—2026：不计入首版 50 条。
- 部件分类错误：阻断索引构建。
- 少于 50 个有效 record：库状态为 `building`。
- 达到 50 条并全部校验：库状态为 `available`。
- 不足 5 本不同书：检索失败并报告缺口。
- 派生索引与正式 record 不一致：重新构建，不手工修补派生文件。
- 原始采集图和旧 record：归档，不自动删除。

## 18. 测试与验收

### 18.1 知识库完整性

- 四库各 50 条有效 record。
- 共 200 条部件记录。
- 每条 record 绑定真实本地图片和 source registry。
- 所有资产、records、派生索引和 manifest 哈希一致。
- 重复资产和目录逃逸被拒绝。

### 18.2 检索

- 同一查询可重复得到稳定顺序。
- 固定返回 5 本不同书。
- 每个候选具有字段分数和真实匹配说明。
- 不足 5 个时不补造。

### 18.3 生产

- 两套方向共享同一项目事实。
- 所有参考元素都可回溯至 record。
- 封面、目录和章首页生成图不包含最终文字。
- Prompt 与输出建立哈希和版本链。
- 未经人工选择的图不进入正式项目或知识库。

## 19. 第一版交付物

1. 四个知识库目录及 200 条中国案例。
2. 共享来源总表。
3. 八个 JSON schema。
4. 知识库构建器、校验器和检索器。
5. 部件 Prompt 编译器。
6. 图片审核与回流工具。
7. `design-book-editorial` 与 `create-book-images` 的受控升级。
8. 四库位置索引与人用说明文档。
9. 行为测试、单元测试和端到端样例。

## 20. 实施顺序

1. 建立 schema 和空知识库骨架。
2. 实现构建、校验、检索和 Prompt 合同测试。
3. 封面库收集与验证 50 条。
4. 目录库收集与验证 50 条。
5. 章首页库收集与验证 50 条。
6. 插画与装饰库收集与验证 50 条。
7. 更新两个生产 Skill，并逐个完成行为测试。
8. 运行完整端到端样例、重新部署和打包。

四个知识库按上述顺序逐库完成和验收，不在未完成当前库时同时铺开四库，防止质量失控。
