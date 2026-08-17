---
name: Chinese Book Interior Typesetting 中文书籍内页排版
description: "Chinese book interior typesetting expert. Focuses on chapter openers, table of contents, front matter, and body text layout based on 'China's Most Beautiful Books' cases. Implements InDesign parent-page families, paragraph/character/object styles, threaded text frames, keep options, baseline grids, and preflight checks. Transforms aesthetic principles into AI-executable structured protocols."
allowed-tools: Bash, WriteFile, ReadFile
---

# 中国书籍内文装帧与 InDesign–AI 规则手册 v2

> **适用对象**：AI 排版系统、InDesign 模板开发、OpenClaw/Codex 执行规格化
> **聚焦范围**：章首页、目录、前置页、正文页（暂不含内文插图自动插入，仅保留接口）
> **核心样本**：《草叶手帖》《观照——栖居的哲学》《许茂和他的女儿们》《金圣叹选批唐诗六百首》《陈从周造园三章》《梦影红楼》《骨科小手术》《我是外公外婆带大的孩子》

---

## 一、中国案例 6 条设计共识

### 1. 首先不是"满"，而是"收"

《草叶手帖》的公开评语：**简约文字编排、充分留白、弱化页码、整体疏朗空灵**。AI 排版时不能天然把页面塞满，而要默认追求"信息够用，视觉留气口"。

### 2. 章首页依靠"页间关系"而不是单页堆料

《许茂和他的女儿们》：**图与文分列左右页，左页文字顶格上方，右页画面形成主视觉，页码和文本线框一起控制阅读方向**。章首页和正文第一页的关系，往往不是一页解决，而是一个**跨页单位**解决。

### 3. "副文本层级"必须清楚

《金圣叹选批唐诗六百首》：**二色印刷区分主次文本，字体级数合理，便于区分不同体例**。AI 不能只识别"标题/正文"，还必须识别：**正文、批注、题解、引文、脚注、图题、目录层级、眉题**。

### 4. 不靠"平均分配图文"，而靠"图像调度"

《陈从周造园三章》：**照片尺寸变化、空间感强、图文经营有致、章节划分甚至做到书口检索**；《观照——栖居的哲学》：**分镜头式图像切割、矢量分解图、宏观与微观层级对照**。AI 不能只会"左图右文"一种死办法，而要有**一套可切换的图像叙述模板**。

### 5. 传统题材不等于复古堆砌

《梦影红楼》：**采用经折装的传统形制，但画面与文字分列、字号适中、利于阅读**；《陈从周造园三章》也是**现代感文字排法里保留传统意味**。AI 不能把"中国风"误解成满页纹样、仿古边框、重装饰，而应理解为：**阅读秩序先行，传统气息靠比例、纸感、色调、编排节奏来实现**。

### 6. "最美的书"评审明确偏向"设计回归阅读"

国家新闻出版署对 2024 年"最美的书"的总结：评委持续偏好**"文质彬彬"、贴近读者、平实质朴、回归阅读、适合普通读者翻阅携带**的作品。规则引擎默认方向不应该是"越炫越好"，而应该是"越清楚、越贴合内容越好"。

---

## 二、6 种 InDesign 母版类型

先定义页面角色（page_role），再映射到父页代码。

### A. `P-FM-TOC`：前置页 / 目录页母版

对应：《草叶手帖》《我是外公外婆带大的孩子》这一类偏轻阅读气质的书。核心不是花，而是留白和层级。

**InDesign 落地：**
- 用 **Parent Pages** 建立固定版心、页码位置、目录标题位置
- 目录不要手排，尽量由 **TOC Style** 驱动
- 目录层级至少拆成：`TOC_L1 / TOC_L2 / TOC_PageNo / TOC_Title`

### B. `P-CH-OPEN-R`：章首页右页母版

对应：《梦影红楼》《许茂和他的女儿们》等中文文学与艺术书。章首页应默认落在**奇数页右页**。

**InDesign 落地：**
- 段落样式中的 **Keep Options > Start Paragraph** 设为下一奇数页；或插入 **Odd Page Break**
- 章首页父页中默认不放运行头；页码可采用 **blind folio**（内部继续计算、页面不显示页码）
- 页码格式和分节用 **Layout > Numbering & Section Options** 管理

### C. `P-BD-TXT-L` / `P-BD-TXT-R`：正文左右页母版

对应：《草叶手帖》《金圣叹选批唐诗六百首》。体例清楚，正文本身稳定，页码和眉题尽量减负。

**InDesign 落地：**
- 正文必须优先用 **threaded text frames** 串成主文本流，而不是每页单独塞字
- 标题、正文、引文、批注全部走 **Paragraph Styles / Character Styles**
- 正文页统一基线节奏，设置文档级或文本框级 **baseline grid**

### D. `P-BD-FIRST`：章首页后的正文第一页母版

适合中国大量"正文开篇需要缓冲"的书：第一页正文不放运行头，页顶留更大呼吸区，首段可允许更宽松段前距，必要时可有引题或题记。

**InDesign 落地：**
- `P-BD-FIRST` 不要直接继承完整正文父页，可以从正文父页复制后删掉运行头，只保留页码策略和正文主文本框
- 首段与章标题关系必须走 **Keep Options**，至少设置 `Keep With Next`、`Keep Lines Together`，避免章标题孤立在页底

### E. `P-POEM-NOTE`：诗歌 / 批注 / 体例复杂页母版

对应：《金圣叹选批唐诗六百首》。**多层体例并存**问题。

**InDesign 落地：**
- 用 **Nested Styles / Drop Caps and Nested Styles / GREP Style** 处理局部层级，不要手工涂格式
- 批注、题解、原文、注文必须拆分为独立段落样式，不许只靠字号差别临时改

### F. `P-IMG-ANALYTIC`：分析图 / 图文说明页母版

对应：《观照——栖居的哲学》《骨科小手术》。分镜式图像、矢量剖析、图文一一对应。

**InDesign 落地：**
- 图框、说明框、编号框全部挂 **Object Styles**
- 图文页不要让 AI 自由摆，而应限定为几套固定槽位：`full_bleed / split_half / analytic_grid / caption_stack`
- 如果以后加入章首页插图，也优先走这一套槽位思路

---

## 三、InDesign 硬操作规则

### 1. 文档层规则

新建模板时先锁定：
- 文档是否 Facing Pages
- 页面尺寸、边距、出血
- 是否启用基线网格
- 正文主文本流是否贯通
- 父页集合是否完整

### 2. 样式层规则

AI 不允许直接说"这里大一点、那里小一点"，而必须先选样式名。

**推荐命名：**
- 段落样式：`P-CH-NO` `P-CH-TTL` `P-BD-01` `P-BD-FIRST` `P-QUOTE` `P-NOTE`
- 字符样式：`C-EM` `C-SMALLCAP` `C-NUM` `C-ANNOT`
- 对象样式：`O-TXT-MAIN` `O-TXT-NOTE` `O-IMG-ANALYTIC` `O-CAPTION`

样式可分组，可跨文档导入，也可以把 Word 样式映射到 InDesign 样式。

### 3. 章节分页规则

- 章首页默认右页
- 若上一章结束在右页，则自动补一张空白左页
- 单文档时用 `Start Paragraph = Next Odd Page` 或 `Odd Page Break`
- 多文档书籍时用 Book 的 `Continue On Next Odd Page + Insert Blank Page`

### 4. 正文线程规则

- 正文必须属于 `story_main`
- 章首页空白页不得加入正文线程
- 加删页后保持线程
- 检测到 overset 先看线程是否断，再考虑加页或换母版

### 5. 行文稳定规则

- 标题必须 `Keep With Next`
- 正文首段避免寡行孤行
- 题记与首段不得拆页
- 基线网格若启用，正文 leading 必须与网格匹配

### 6. 目录与前置页规则

- 目录条目来源必须是段落样式，不接受人工手填目录
- 页码格式变化只能走 section
- 目录更新后再检查是否有 overset

---

## 四、AI 结构化协议

### AI 不读"审美描述"，AI 读"版面对象"

不要写：
- "章首页要有呼吸感"
- "目录要显得空灵"
- "页码不要太抢眼"

要写成：
- `chapter opener top white space >= 18mm`
- `folio visibility = hidden on chapter opener`
- `TOC page title frame width = 0.62 * live_area_width`
- `max text frame fill ratio = 0.82`

### AI 不做"自由设计"，只做"在候选模板中选择"

不让 AI 输出任意坐标。让它在 6 类母版中选 1 个，再在这个母版的参数区间里做微调：

- 先选 `P-CH-OPEN-R`
- 再填 `title_lines <= 3`
- 再填 `chapter_no_position = top_left`
- 再填 `folio_visibility = false`

### AI 的操作词必须和 InDesign 术语对齐

推荐统一动词：
- `apply_parent`
- `apply_paragraph_style`
- `apply_character_style`
- `thread_to_next_frame`
- `insert_odd_page_break`
- `create_section`
- `align_to_baseline_grid`
- `create_toc`
- `preflight_check`
- `package_for_print`

### AI 的每一步都要有"成功判定"

- `apply_parent` 成功 = 页面父页名称匹配
- `thread_to_next_frame` 成功 = 当前文本框 `nextTextFrame` 非空
- `chapter opener` 成功 = 页码为奇数且在右页
- `body page` 成功 = `overflows == false`
- `preflight_check` 成功 = 无缺字、断链、低清图、overset text

---

## 五、建议采用的 JSON 结构

```json
{
  "document_profile": {
    "facing_pages": true,
    "page_size": "145mm*210mm",
    "baseline_grid": {
      "enabled": true,
      "increment": "16pt"
    },
    "section_policy": "body_arabic"
  },
  "style_map": {
    "chapter_number": "P-CH-NO",
    "chapter_title": "P-CH-TTL",
    "body_first": "P-BD-FIRST",
    "body_main": "P-BD-01",
    "quote": "P-QUOTE",
    "note": "P-NOTE"
  },
  "parent_map": {
    "frontmatter_toc": "P-FM-TOC",
    "chapter_open_right": "P-CH-OPEN-R",
    "body_left": "P-BD-TXT-L",
    "body_right": "P-BD-TXT-R",
    "body_first": "P-BD-FIRST",
    "blank_left": "P-BLANK-L"
  },
  "chapter_rule": {
    "start_on": "odd_page",
    "if_previous_ends_on_odd": "insert_blank_left",
    "folio_on_opener": false,
    "running_header_on_opener": false
  },
  "layout_rule": {
    "title_keep_with_next_lines": 3,
    "prevent_orphans_widows": true,
    "main_story_thread_required": true,
    "max_fill_ratio": 0.82
  }
}
```

---

## 六、错误码表

### 章节与分页

| 错误码 | 说明 | 修复 |
|--------|------|------|
| `E-CH-001` | 章首页不在奇数页 | 插入 odd page break 或补空白左页 |
| `E-CH-002` | 章首页继承了正文运行头 | 切换到 `P-CH-OPEN-R` 并清理父页覆盖 |
| `E-CH-003` | 空白页出现在右页 | 重排分页，保证空白页只作左页补位 |

### 正文与线程

| 错误码 | 说明 | 修复 |
|--------|------|------|
| `E-TXT-001` | 正文 story 断链 | 重建文本框 threading |
| `E-TXT-002` | 正文 overset | 检查线程 → 检查 Keep Options → 检查基线/leading 冲突 → 必要时增页 |
| `E-TXT-003` | 标题和首段拆页 | 提高 `Keep With Next` 或 `Start Paragraph` 规则 |

### 样式与结构

| 错误码 | 说明 | 修复 |
|--------|------|------|
| `E-STY-001` | 同类段落出现局部覆盖 | 清除 override，回到段落样式 |
| `E-STY-002` | 副文本误用正文样式 | 重新映射样式；必要时通过 Word Style Mapping 或 XML tag/style mapping 自动纠偏 |

### 印前与输出

| 错误码 | 说明 |
|--------|------|
| `E-PRF-001` | Preflight 报缺字或断链 |
| `E-PRF-002` | 低分辨率图 |
| `E-PRF-003` | overset text |
| `E-PRF-004` | 包装失败或忽略预检错误后继续输出 |

---

## 七、执行顺序（固定）

1. 读取 `document_setup`，创建文档与基础版心
2. 根据样本/项目选择 `page_families`
3. 把正文、目录、章题、题记、附录先转成 `content_blocks`
4. 先套 `style_map`，再决定 `page_role`
5. 把 `chapter_title` 统一推到 `next_odd_page`
6. 应用父页，建立线程文本框
7. 跑 `keep_rule` 和 `overset` 检查
8. 最后才允许做少量节奏性例外

**铁律**：未通过 overset、keep 冲突、章节起始页、页码、预检检查之前，不得导出 PDF。

---

## 八、核心外部资料

- Adobe 官方帮助：使用主页/父页；页码和章节；设置段落格式（保持选项、段落起始）；串接框架间的文本与智能文本重排；定位对象；对象样式；文本绕排；预检与打包
- 2023/2024 年"最美的书"获奖作品与评语：国家新闻出版署、文汇报、解放日报·上观新闻等公开报道
- 补充案例：红星新闻《寻绣记》出版记

**说明**：为保证报告可执行，正文所有规则都尽量落在 InDesign 的明确菜单路径、样式设置、父页切换与预检逻辑上；案例部分主要服务于"为什么这样定规则"，而不是替代最终的项目模板。


---

## 九、OpenClaw 执行级规范（Phase 1）

> **范围限定**：只处理前置页、目录页、章首页、空白补位页、章首页后正文第一页、普通正文左右页。**暂不处理**内文插图、页中图片避让、复杂跨页图文编排、表格/索引/脚注系统。

---

### 9.1 系统提示词（核心规则）

你是一个专门为 Adobe InDesign 服务的图书内文排版执行代理。

你的任务不是自由设计，而是严格按照既定模板、样式、父页、分页规则和错误修复顺序，完成中文图书内文排版。

你必须遵守以下原则：

1. **你只能在预定义的 InDesign 对象体系内工作**：
   - Parent Pages
   - Paragraph Styles
   - Character Styles
   - Object Styles
   - Threaded Text Frames
   - Sections
   - TOC Styles
   - Baseline Grid
   - Preflight
   - Package for Print

2. **你不能自行发明新的视觉规则**。你只能：
   - 选择既有父页
   - 应用既有样式
   - 插入既有分页类型
   - 执行既有修复策略
   - 输出结构化错误报告

3. **你必须优先保证阅读秩序，而不是视觉炫技**。默认目标：
   - 章首页必须在奇数页右页
   - 页面层级必须清楚
   - 正文线程必须连续
   - 样式必须统一
   - 不允许局部手工覆盖成为常态
   - 遇到错误必须先检测后修复

4. **你当前阶段禁止处理内文插图**。除非任务明确说明，否则你不得插入页中图片，不得处理页中图文绕排，不得生成图像相关布局。

5. **你必须使用 InDesign 原生术语输出动作**。允许使用的动作词包括：
   - `apply_parent`
   - `apply_paragraph_style`
   - `apply_character_style`
   - `create_text_frame`
   - `thread_to_next_frame`
   - `insert_odd_page_break`
   - `insert_blank_left_page`
   - `create_section`
   - `create_toc`
   - `align_to_baseline_grid`
   - `preflight_check`
   - `package_for_print`
   - `clear_overrides`
   - `switch_parent`
   - `add_page_after`
   - `repair_thread`

6. **你不能直接说"这里更美观一点"或"适当调整"**。所有决策必须改写为：对象、属性、约束、校验结果，四段式输出。

7. **你必须优先使用模板和样式，而不是局部坐标硬改**。只有在模板允许的参数范围内，才可以做微调。

8. **你必须输出可验证结果**。每一步都必须有 `success_check`。例如：
   - 章首页成功 = 页面为奇数页且父页为 `P-CH-OPEN-R`
   - 正文页成功 = 所属主文本流未断链且无 overset
   - 空白页成功 = 父页为 `P-BLANK-L` 且无可见正文对象

9. **修复顺序必须严格遵守优先级**。不得跳过检测直接粗暴缩小字号。默认修复顺序：
   - 检查分页
   - 检查父页
   - 检查线程
   - 检查 Keep Options
   - 检查样式覆盖
   - 必要时补页
   - 必要时切换母版
   - 最后才允许微调段前后距
   - **禁止直接破坏正文基础字号和行距体系**

10. **你的输出必须分为三层**：`layout_plan`、`execution_steps`、`validation_report`

你服务的对象是中文图书内文排版。默认风格目标：回归阅读、层级清晰、留白克制、章首页有明确节奏变化、正文稳定连续、适合 InDesign 模板化执行。

---

### 9.2 任务边界（Phase 1）

**范围内**：
- 扉页/前置页模板应用
- 目录页生成与更新
- 章首页奇数页规则
- 空白左页补位
- 章首页后的正文第一页
- 正文左右页父页切换
- 主文本流 threading
- Keep Options
- 样式统一
- overset 检测与修复
- Preflight 检查

**范围外**：
- 页中插图
- 章节间插画
- 复杂图文混排
- 表格自动布局
- 数学公式
- 索引系统
- 脚注和尾注高级处理
- 封面与封底
- 印厂参数个性化适配

任何超出范围的请求，你必须标记为 `deferred_module`，而不是自行处理。

---

### 9.3 模板字典（固定命名，不允许自创）

#### Parent Pages

| 代码 | 用途 |
|------|------|
| `P-FM-TOC` | 前置页/目录页 |
| `P-CH-OPEN-R` | 章首页右页 |
| `P-BLANK-L` | 空白左页 |
| `P-BD-FIRST` | 章首页后的正文第一页 |
| `P-BD-TXT-L` | 正文左页 |
| `P-BD-TXT-R` | 正文右页 |
| `P-POEM-NOTE` | 诗歌/批注/复杂体例页 |

#### Paragraph Styles

| 代码 | 用途 |
|------|------|
| `P-CH-NO` | 章号 |
| `P-CH-TTL` | 章标题 |
| `P-CH-SUB` | 章副标题 |
| `P-EPIGRAPH` | 题记 |
| `P-BD-FIRST` | 首段正文 |
| `P-BD-01` | 普通正文 |
| `P-BD-QUOTE` | 引文 |
| `P-NOTE` | 批注/注释 |
| `P-TOC-H1` | 目录一级 |
| `P-TOC-H2` | 目录二级 |
| `P-TOC-PNO` | 目录页码 |
| `P-RUNHEAD` | 运行头 |
| `P-FOLIO` | 页码 |

#### Character Styles

| 代码 | 用途 |
|------|------|
| `C-EM` | 强调 |
| `C-SC` | 小型大写/特殊强调 |
| `C-NUM` | 数字号 |
| `C-ANNOT` | 注释内部强调 |

#### Object Styles

| 代码 | 用途 |
|------|------|
| `O-TXT-MAIN` | 主文本框 |
| `O-TXT-FIRST` | 首页正文框 |
| `O-TXT-TOC` | 目录文本框 |
| `O-TXT-CHOPEN` | 章首页文本框 |
| `O-FOLIO` | 页码框 |
| `O-RUNHEAD` | 运行头框 |

---

### 9.4 输入结构（JSON）

```json
{
  "project_id": "book_interior_v1",
  "phase": "phase_1_text_only",
  "document_profile": {
    "facing_pages": true,
    "page_size": "140mmx210mm",
    "bleed": "3mm",
    "baseline_grid": {
      "enabled": true,
      "increment": "16pt"
    },
    "section_policy": "body_arabic"
  },
  "style_map": {
    "chapter_number": "P-CH-NO",
    "chapter_title": "P-CH-TTL",
    "chapter_subtitle": "P-CH-SUB",
    "epigraph": "P-EPIGRAPH",
    "body_first": "P-BD-FIRST",
    "body_main": "P-BD-01",
    "quote": "P-BD-QUOTE",
    "note": "P-NOTE",
    "toc_h1": "P-TOC-H1",
    "toc_h2": "P-TOC-H2",
    "toc_page_no": "P-TOC-PNO"
  },
  "parent_map": {
    "frontmatter_toc": "P-FM-TOC",
    "chapter_open_right": "P-CH-OPEN-R",
    "blank_left": "P-BLANK-L",
    "body_first": "P-BD-FIRST",
    "body_left": "P-BD-TXT-L",
    "body_right": "P-BD-TXT-R",
    "poem_note": "P-POEM-NOTE"
  },
  "chapter_rule": {
    "start_on": "odd_page",
    "blank_insert_policy": "insert_blank_left_if_previous_ends_on_odd",
    "folio_on_opener": false,
    "runhead_on_opener": false
  },
  "layout_rule": {
    "title_keep_with_next": true,
    "prevent_orphans_widows": true,
    "main_story_thread_required": true,
    "allow_manual_override": false,
    "max_fill_ratio": 0.82
  },
  "content_blocks": [
    {
      "type": "chapter",
      "chapter_no": "第一章",
      "chapter_title": "山雨欲来",
      "chapter_subtitle": "",
      "epigraph": "",
      "body_text": "正文内容……"
    }
  ]
}
```

---

### 9.5 输出结构（JSON）

```json
{
  "layout_plan": {
    "document_mode": "facing_pages",
    "chapter_start_policy": "odd_page_only",
    "main_story_name": "story_main",
    "selected_parents": [
      "P-FM-TOC",
      "P-CH-OPEN-R",
      "P-BLANK-L",
      "P-BD-FIRST",
      "P-BD-TXT-L",
      "P-BD-TXT-R"
    ]
  },
  "execution_steps": [
    {
      "step_id": "S001",
      "action": "apply_parent",
      "target": "page_15",
      "params": {
        "parent_name": "P-CH-OPEN-R"
      },
      "success_check": {
        "page_parent_equals": "P-CH-OPEN-R"
      }
    }
  ],
  "validation_report": {
    "status": "pass",
    "errors": [],
    "warnings": [],
    "checks": [
      {
        "check_id": "V001",
        "name": "chapter_open_on_odd_page",
        "result": "pass"
      }
    ]
  }
}
```

---

### 9.6 执行顺序清单（Stage 1-8）

#### Stage 1：初始化文档检查

先检查：
1. 是否为 facing pages
2. 是否存在全部必需父页
3. 是否存在全部必需段落样式
4. 是否存在主文本框对象样式
5. 是否启用或定义了 baseline grid
6. 是否已有 section 规则

输出：`init_check_report`

#### Stage 2：前置页处理

动作顺序：
1. `apply_parent(P-FM-TOC)` 到前置页
2. 建立目录标题框与目录文本框
3. 通过 `create_toc`
4. 应用 `P-TOC-H1 / P-TOC-H2 / P-TOC-PNO`
5. 检查目录是否 overset
6. 检查目录页是否误入正文线程

成功条件：
- 目录来自样式生成
- 目录无 overset
- 目录页父页正确

#### Stage 3：章首页处理

动作顺序：
1. 找到全部 `chapter` block
2. 判断章节起始位置所落页码
3. 若目标页不是奇数页右页，则执行：
   - `insert_odd_page_break` 或
   - `insert_blank_left_page`
4. 在章首页页应用 `P-CH-OPEN-R`
5. 应用 `P-CH-NO`、`P-CH-TTL`、`P-CH-SUB`、`P-EPIGRAPH`
6. 章首页默认隐藏运行头和页码显示
7. 验证章首页是否真在奇数页右页

成功条件：
- 章首页在奇数页
- 父页正确
- 章标题未拆页
- 章首页不带正文运行头

#### Stage 4：空白补位页处理

动作顺序：
1. 若上一章结束在奇数页右页，则补一页左页空白页
2. 对空白页应用 `P-BLANK-L`
3. 清除所有可见正文对象
4. 禁止加入 `story_main`
5. 检查是否误显示页码或运行头

成功条件：
- 空白页在左页
- 无正文内容
- 无线程连接
- 无可见 folio/runhead

#### Stage 5：章首页后正文第一页

动作顺序：
1. 在章首页后找到正文第一页
2. 应用 `P-BD-FIRST`
3. 创建或启用正文首框 `O-TXT-FIRST`
4. 将正文首段应用 `P-BD-FIRST`
5. 首段必须与前一标题系统保持 `Keep With Next / Keep Lines Together` 规则兼容
6. 检查该页是否误带普通运行头

成功条件：
- 正文第一页样式正确
- 页面节奏与普通正文页不同
- 线程连续
- 无 overset

#### Stage 6：普通正文页处理

动作顺序：
1. 左页应用 `P-BD-TXT-L`
2. 右页应用 `P-BD-TXT-R`
3. 统一正文样式为 `P-BD-01`
4. 建立 `story_main` 线程
5. 绑定页码与运行头
6. 按需要对齐 baseline grid
7. 检查 overset

成功条件：
- 左右页父页正确
- 主文本流连续
- 样式无异常覆盖
- 无 overset

#### Stage 7：验证与修复

按下面顺序修复，不能乱跳：
1. 检查分页错误
2. 检查父页错误
3. 检查线程断裂
4. 检查 Keep Options
5. 检查样式覆盖
6. 必要时补页
7. 必要时切换父页
8. 必要时微调段前段后
9. 仍失败则输出人工审查错误

#### Stage 8：印前检查

动作顺序：
1. `preflight_check`
2. 检查缺字
3. 检查断链
4. 检查 overset
5. 检查页码/section 连续性
6. 检查可见对象是否落在错误父页
7. 通过后 `package_for_print`

成功条件：
- 无致命预检错误
- 结构完整
- 章节分页正确
- 样式体系未崩坏

---

### 9.7 错误码表

#### 分页与章节

| 错误码 | 说明 |
|--------|------|
| `E-CH-001` | 章首页不在奇数页 |
| `E-CH-002` | 章首页误带运行头 |
| `E-CH-003` | 章首页误显示页码 |
| `E-CH-004` | 空白补位页不在左页 |
| `E-CH-005` | 空白补位页存在正文对象 |

#### 正文流

| 错误码 | 说明 |
|--------|------|
| `E-TXT-001` | 主文本流断链 |
| `E-TXT-002` | 正文 overset |
| `E-TXT-003` | 标题与首段拆页 |
| `E-TXT-004` | 目录页误入正文线程 |
| `E-TXT-005` | 首段页误用普通正文父页 |

#### 样式系统

| 错误码 | 说明 |
|--------|------|
| `E-STY-001` | 局部样式覆盖未清除 |
| `E-STY-002` | 章标题误用正文样式 |
| `E-STY-003` | 目录条目未使用 TOC 样式 |
| `E-STY-004` | 页码框未使用 O-FOLIO |
| `E-STY-005` | 运行头框未使用 O-RUNHEAD |

#### 印前

| 错误码 | 说明 |
|--------|------|
| `E-PRF-001` | 缺字 |
| `E-PRF-002` | 缺链接 |
| `E-PRF-003` | overset text |
| `E-PRF-004` | 分节或页码异常 |
| `E-PRF-005` | package 输出失败 |

---

### 9.8 修复逻辑

修复原则：
1. 不得优先缩小正文字号
2. 不得优先破坏基础行距
3. 不得把局部硬改当作正式修复
4. 必须优先修复结构，再修复视觉

默认修复顺序：
A. 分页
B. 父页
C. 文本线程
D. Keep Options
E. 样式覆盖
F. 增页
G. 切换父页
H. 微调段前段后
I. 输出人工审查

当出现 overset 时：
- 先检查 frame threading
- 再检查是否误插空白页到正文流
- 再检查标题保留规则是否过强
- 再检查首段页是否误用正文父页
- 最后才允许补页

当出现章首页落错页时：
- 先插 odd page break
- 若前章已落在奇数右页末尾，则补左页空白页
- 再应用章首页父页
- 再验证页码奇偶

---

### 9.9 禁止事项

1. 禁止自由新增未定义样式名
2. 禁止自由新增未定义父页名
3. 禁止以"手工微调很多对象位置"替代模板化布局
4. 禁止把正文内容放进空白补位页
5. 禁止让章首页出现在偶数页左页
6. 禁止目录手工录入
7. 禁止遇到 overset 就直接缩字号
8. 禁止忽略样式覆盖问题
9. 禁止把当前阶段扩展到内文插图
10. 禁止输出模糊描述，必须输出结构化动作和校验

---

### 9.10 任务启动词

```
任务：执行中文图书内文排版 Phase 1。

目标：
- 建立前置页、目录页、章首页、空白补位页、正文第一页、普通正文页的稳定排版流程
- 严格基于 InDesign 的 Parent Pages、Paragraph Styles、Character Styles、Object Styles、Threaded Text Frames、Sections、TOC Styles、Baseline Grid、Preflight
- 章首页必须在奇数页右页
- 暂不处理内文插图

要求：
1. 先做初始化检查
2. 再处理目录页
3. 再处理章首页和空白补位页
4. 再处理正文第一页和普通正文页
5. 再做线程、样式、分页验证
6. 最后输出 validation_report 和错误码
7. 所有动作都必须使用既定对象名和样式名
8. 所有修复都必须遵守既定修复顺序
9. 不允许自由发挥视觉设计
10. 输出必须是 layout_plan + execution_steps + validation_report
```

---

## 十、下一步待补充

当前规范已覆盖执行级规则、模板字典、输入输出结构、错误码和修复逻辑。后续仍需补充：

1. **固定模板样本**：每个父页到底有哪些文本框、坐标区、页码框、运行头框
2. **内容识别映射表**：原稿里的"第一章 / 一、 / 引文 / 注释 / 正文首段"分别怎么映射到样式


---

## 十一、Phase 1B：内容识别规则 + 样式映射表 + 章首页页面对象清单

> **目标**：让 OpenClaw 先学会"认内容"，再把识别结果稳定映射到 InDesign 的 Parent Pages / Paragraph Styles / Character Styles / Object Styles / Threaded Text Frames。

---

### 11.1 内容识别总原则

OpenClaw 不允许直接把原稿整篇灌进 InDesign。它必须先做一轮**结构化解析**，把原稿拆成块。

**识别优先级（必须按此顺序，不能乱序）**：

```
chapter_number
chapter_title
chapter_subtitle
epigraph
body_first_paragraph
body_main
quote_block
note_block
toc_entry
frontmatter_title
unknown_block
```

- 先判断是不是章节系统
- 再判断是不是题记/副标题
- 再判断是不是正文首段
- 最后才当普通正文

否则很容易把"第一章 山雨欲来"错误识别成普通正文第一段。

---

### 11.2 内容块类型定义（11 种）

#### 1. frontmatter_title

用于：扉页标题、目录页标题、前言标题、序言标题、后记标题、附录标题

```json
{
  "block_type": "frontmatter_title"
}
```

#### 2. chapter_number

用于：第一章、第一回、第一部、第一辑

注意：它只识别"章号单元"，不自动等于章标题。

例如：
```
第一章
山雨欲来
```
这里是**两个块**，不是一个块。

#### 3. chapter_title

用于：章标题主标题、与章号分开的标题行

例如：
```
第一章
山雨欲来
```
`山雨欲来` 应识别为 `chapter_title`。

#### 4. chapter_subtitle

用于：章副标题、小标题、解释性副题

例如：
```
第一章
山雨欲来
旧秩序开始松动
```
第三行识别为 `chapter_subtitle`。

#### 5. epigraph

用于：题记、章首页引句、章前短引文

典型特征：
- 字数较短
- 常独立成段
- 前后留空
- 可能带作者署名

例如：
```
"所有风暴来临之前，世界都过于平静。"
——某位作者
```

#### 6. body_first_paragraph

用于：章首页后的正文首段

注意：它不是靠"视觉第一段"决定，而是靠"它是某章节正文流中的第一段"决定。

#### 7. body_main

用于：普通正文段落、连续叙述段、非首段正文

#### 8. quote_block

用于：独立引文、引号块、左右缩进式引文

当前阶段只做纯文字引文，不处理引文内图片。

#### 9. note_block

用于：注释、编者按、小型解释性说明、批注型短段落

#### 10. toc_entry

用于：目录一级条目、目录二级条目、对应页码项

注意：目录本身不建议从纯文本人工识别后硬排。更稳的方式还是从标题段落样式自动生成 TOC。但如果用户给的是"已整理好的目录文本"，可以临时识别为 `toc_entry`。

#### 11. unknown_block

只在无法判断时使用。一旦进入 `unknown_block`，OpenClaw 不能自行排版，必须输出：

```json
{
  "status": "needs_review",
  "error_code": "E-PARSE-001",
  "reason": "unknown_block_detected"
}
```

---

### 11.3 内容识别规则（A-H）

#### 规则 A：章节编号识别

**允许的中文章节编号形式**：
```
第一章、第一回、第一部、第一辑
第 一 章、第1章、第 1 章
Chapter 1、CHAPTER 1
```

**正则建议**：
```regex
^(第[\s　]*[一二三四五六七八九十百千万0-9０-９]+[\s　]*(章|回|部|辑))$|^(Chapter[\s　]*[0-9]+)$|^(CHAPTER[\s　]*[0-9]+)$
```

**识别结果**：
```json
{
  "block_type": "chapter_number",
  "raw_text": "第一章",
  "normalized_text": "第一章",
  "style_target": "P-CH-NO",
  "parent_target": "P-CH-OPEN-R"
}
```

#### 规则 B：章标题识别

**优先判为 chapter_title 的条件**（满足任意一条即可）：
- 紧跟在 `chapter_number` 后面
- 单独占一行
- 字数通常较短，建议阈值 `2 <= length <= 24`
- 前后被空行包围
- 不以句号结尾为优先
- 不含明显正文式长句结构

**禁止误判条件**（满足以下情况时不判为章标题）：
- 长于 40 字
- 多句连写
- 出现明显正文标点密度
- 紧接上一正文段而非章节断点

**识别结果**：
```json
{
  "block_type": "chapter_title",
  "raw_text": "山雨欲来",
  "style_target": "P-CH-TTL",
  "parent_target": "P-CH-OPEN-R"
}
```

#### 规则 C：章副标题识别

**条件**：
- 位于 `chapter_title` 后一行
- 字数较标题更长但明显短于正文
- 常为解释性语句
- 可以带破折号、副题性质

**识别结果**：
```json
{
  "block_type": "chapter_subtitle",
  "raw_text": "旧秩序开始松动",
  "style_target": "P-CH-SUB",
  "parent_target": "P-CH-OPEN-R"
}
```

#### 规则 D：题记识别

**条件**：
- 通常位于章首页正文前
- 短文本
- 可包含引号
- 可跟随署名行
- 与正文之间有空行

**署名规则**：如果题记后出现 `——作者名`，则这一行仍归入 `epigraph`。当前阶段可以先不拆，统一走 `P-EPIGRAPH`。

**识别结果**：
```json
{
  "block_type": "epigraph",
  "raw_text": ""所有风暴来临之前，世界都过于平静。"\n——某位作者",
  "style_target": "P-EPIGRAPH",
  "parent_target": "P-CH-OPEN-R"
}
```

#### 规则 E：正文首段识别（最关键）

**判断条件**（必须同时满足）：
- 已进入某个章节
- 当前段是章节标题系统之后的第一段正文
- 不属于题记
- 不属于引文块
- 不属于注释块

**识别结果**：
```json
{
  "block_type": "body_first_paragraph",
  "style_target": "P-BD-FIRST",
  "parent_target": "P-BD-FIRST",
  "story_target": "story_main"
}
```

#### 规则 F：普通正文识别

凡是：
- 不属于章节系统
- 不属于题记
- 不属于目录
- 不属于引文
- 不属于注释

则默认进入 `body_main`。

**识别结果**：
```json
{
  "block_type": "body_main",
  "style_target": "P-BD-01",
  "parent_target": "P-BD-TXT-L|P-BD-TXT-R",
  "story_target": "story_main"
}
```

#### 规则 G：引文识别

**识别条件**：
- 整段被引号包裹
- 或明显短于正文并独立成段
- 或前后段落关系显示其为引用内容
- 可包含作者署名

**识别结果**：
```json
{
  "block_type": "quote_block",
  "style_target": "P-BD-QUOTE",
  "story_target": "story_main"
}
```

#### 规则 H：注释识别

**识别条件**：
- 以"注：""编者按：""说明："开头
- 或语义上明显为补充说明
- 通常较短
- 不作为主叙述推进

**识别结果**：
```json
{
  "block_type": "note_block",
  "style_target": "P-NOTE",
  "parent_target": "P-POEM-NOTE|P-BD-TXT-L|P-BD-TXT-R"
}
```

---

### 11.4 内容识别状态机

OpenClaw 不要"猜"，而要按状态流转：

```
STATE_START
→ 若识别到 frontmatter_title，则进入 STATE_FRONTMATTER
→ 若识别到 chapter_number，则进入 STATE_CHAPTER_OPEN
→ 其余进入 STATE_BODY

STATE_FRONTMATTER
→ 可接受 frontmatter_title / toc_entry
→ 若识别到 chapter_number，则切换到 STATE_CHAPTER_OPEN

STATE_CHAPTER_OPEN
→ 接受 chapter_number
→ 接受 chapter_title
→ 可接受 chapter_subtitle
→ 可接受 epigraph
→ 第一个正文段进入 body_first_paragraph
→ 之后切换到 STATE_BODY

STATE_BODY
→ 接受 body_main / quote_block / note_block
→ 若识别到 chapter_number，则切换到 STATE_CHAPTER_OPEN
```

---

### 11.5 样式映射总表

| 内容块 | 段落样式 | 父页 | 文本流 |
|--------|---------|------|--------|
| frontmatter_title | P-TOC-H1 / 自定义前置标题样式 | P-FM-TOC | 非 story_main |
| toc_entry_l1 | P-TOC-H1 | P-FM-TOC | 非 story_main |
| toc_entry_l2 | P-TOC-H2 | P-FM-TOC | 非 story_main |
| chapter_number | P-CH-NO | P-CH-OPEN-R | 非 story_main |
| chapter_title | P-CH-TTL | P-CH-OPEN-R | 非 story_main |
| chapter_subtitle | P-CH-SUB | P-CH-OPEN-R | 非 story_main |
| epigraph | P-EPIGRAPH | P-CH-OPEN-R | 非 story_main |
| body_first_paragraph | P-BD-FIRST | P-BD-FIRST | story_main |
| body_main | P-BD-01 | P-BD-TXT-L/R | story_main |
| quote_block | P-BD-QUOTE | P-BD-TXT-L/R | story_main |
| note_block | P-NOTE | P-POEM-NOTE 或正文页 | story_main/局部独立 |

---

### 11.6 章首页页面对象清单

#### 章首页固定对象列表

章首页父页 `P-CH-OPEN-R` 中，建议至少定义以下对象：

| 对象 ID | 用途 |
|---------|------|
| `OBJ-CHOPEN-NO` | 章号文本框 |
| `OBJ-CHOPEN-TITLE` | 章标题文本框 |
| `OBJ-CHOPEN-SUB` | 章副标题文本框 |
| `OBJ-CHOPEN-EPIGRAPH` | 题记文本框 |
| `OBJ-CHOPEN-FOLIO` | 章首页页码框（默认隐藏） |
| `OBJ-CHOPEN-RUNHEAD` | 章首页运行头框（默认禁用） |
| `OBJ-CHOPEN-SAFE` | 章首页安全版心区（逻辑对象） |

#### 每个对象的职责

**`OBJ-CHOPEN-NO`**
- 只承载章号（第一章、第二回、Part One）
- 不与章标题混排在同一框里
- 优先单独文本框
- 应用 `P-CH-NO`
- 对象样式可用 `O-TXT-CHOPEN`

**`OBJ-CHOPEN-TITLE`**
- 只承载章标题主标题
- 只允许主标题，不允许同时混入副标题
- 应用 `P-CH-TTL`
- 必须是章首页视觉主对象之一

**`OBJ-CHOPEN-SUB`**
- 承载章副标题
- 无内容时允许为空
- 有内容时单独存在
- 应用 `P-CH-SUB`

**`OBJ-CHOPEN-EPIGRAPH`**
- 承载题记
- 无题记时允许隐藏
- 有题记时不得挤压标题框
- 超限时应优先移动到可配置备用区域，而不是压缩标题区

**`OBJ-CHOPEN-FOLIO`**
- 默认不显示数字
- 允许内部保留对象用于切换 house style
- 当前阶段 `folio_visibility = false`

**`OBJ-CHOPEN-RUNHEAD`**
- 当前阶段默认禁用
- 不得继承普通正文运行头

---

### 11.7 章首页对象参数协议

```json
{
  "page_template": "P-CH-OPEN-R",
  "objects": [
    {
      "object_id": "OBJ-CHOPEN-NO",
      "object_type": "text_frame",
      "object_style": "O-TXT-CHOPEN",
      "paragraph_style": "P-CH-NO",
      "required": true,
      "content_source": "chapter_number",
      "bounds_role": "chapter_no_zone",
      "max_lines": 2
    },
    {
      "object_id": "OBJ-CHOPEN-TITLE",
      "object_type": "text_frame",
      "object_style": "O-TXT-CHOPEN",
      "paragraph_style": "P-CH-TTL",
      "required": true,
      "content_source": "chapter_title",
      "bounds_role": "chapter_title_zone",
      "max_lines": 4
    },
    {
      "object_id": "OBJ-CHOPEN-SUB",
      "object_type": "text_frame",
      "object_style": "O-TXT-CHOPEN",
      "paragraph_style": "P-CH-SUB",
      "required": false,
      "content_source": "chapter_subtitle",
      "bounds_role": "chapter_subtitle_zone",
      "max_lines": 3
    },
    {
      "object_id": "OBJ-CHOPEN-EPIGRAPH",
      "object_type": "text_frame",
      "object_style": "O-TXT-CHOPEN",
      "paragraph_style": "P-EPIGRAPH",
      "required": false,
      "content_source": "epigraph",
      "bounds_role": "chapter_epigraph_zone",
      "max_lines": 8
    }
  ]
}
```

---

### 11.8 章首页装配顺序

OpenClaw 不要自己乱摆，按这个顺序装配：

1. **Step 1**：检查当前章首页目标页是否为奇数右页。不是就先修分页，不许先放内容。
2. **Step 2**：应用 `P-CH-OPEN-R`。
3. **Step 3**：放置 `OBJ-CHOPEN-NO`。
4. **Step 4**：放置 `OBJ-CHOPEN-TITLE`。
5. **Step 5**：如有副标题，放置 `OBJ-CHOPEN-SUB`。
6. **Step 6**：如有题记，放置 `OBJ-CHOPEN-EPIGRAPH`。
7. **Step 7**：章首页不加入 `story_main`。
8. **Step 8**：正文第一页另起 `P-BD-FIRST`，正文首段进入 `story_main`。

---

### 11.9 章首页验证规则

```
V-CHOPEN-001  页面必须为奇数页右页
V-CHOPEN-002  页面父页必须为 P-CH-OPEN-R
V-CHOPEN-003  章号对象必须存在且仅承载 chapter_number
V-CHOPEN-004  标题对象必须存在且仅承载 chapter_title
V-CHOPEN-005  副标题为空时对象可隐藏，不得占据正文区域
V-CHOPEN-006  题记超限时不得破坏标题区
V-CHOPEN-007  章首页不得属于 story_main
V-CHOPEN-008  章首页不得带正文运行头
V-CHOPEN-009  章首页不得误显普通页码
```

---

### 11.10 Phase 1B 内容识别错误码

| 错误码 | 说明 |
|--------|------|
| `E-PARSE-001` | 无法识别内容块类型 |
| `E-PARSE-002` | 章号与章标题混在同一块且无法安全拆分 |
| `E-PARSE-003` | 章副标题与题记冲突 |
| `E-PARSE-004` | 首段正文识别失败 |
| `E-PARSE-005` | 正文段误判为标题 |
| `E-PARSE-006` | 目录文本误入正文章节流 |
| `E-PARSE-007` | 章节切换点丢失 |
| `E-PARSE-008` | 题记过长，不适合当前章首页模板 |

---

### 11.11 修复策略

OpenClaw 识别出错时，不允许凭感觉处理，必须按顺序修。

#### 对 `E-PARSE-002`（章号与章标题混在同一块）

例如：
```
第一章 山雨欲来
```

修复顺序：
1. 尝试按首个章节编号模式拆分
2. 左侧进入 `chapter_number`
3. 右侧进入 `chapter_title`
4. 若右侧为空，则标记人工检查

#### 对 `E-PARSE-003`（章副标题与题记冲突）

修复顺序：
1. 优先保留紧随标题、无引号、解释性更强的文本为 `chapter_subtitle`
2. 明显引句样式、带引号或署名者归为 `epigraph`
3. 仍无法判断时进入人工审查

#### 对 `E-PARSE-004`（首段正文识别失败）

修复顺序：
1. 找最后一个章节系统块
2. 在其后第一个非空、非题记、非引文段落标记为 `body_first_paragraph`
3. 后续段落自动归入 `body_main`

---

### 11.12 Phase 1B 任务模板

```
任务：执行中文图书内文排版 Phase 1B。

目标：
1. 先对原稿进行结构化解析
2. 识别内容块类型
3. 将内容块映射到既定的 InDesign 样式和父页
4. 生成章首页对象装配计划
5. 输出识别报告、映射结果、错误码和修复建议

要求：
- 不得直接将原稿整篇灌入页面
- 必须先识别 block_type
- 必须使用既定样式名和父页名
- 章首页必须按对象清单装配
- 正文首段必须单独识别
- 章首页不加入 story_main
- 不处理内文插图
- 输出必须包含 parse_report、mapping_result、chapter_open_plan、validation_report
```

---

### 11.13 Phase 1B 推荐输出格式

```json
{
  "parse_report": [
    {
      "block_id": "B001",
      "raw_text": "第一章",
      "block_type": "chapter_number",
      "confidence": 0.98
    },
    {
      "block_id": "B002",
      "raw_text": "山雨欲来",
      "block_type": "chapter_title",
      "confidence": 0.95
    }
  ],
  "mapping_result": [
    {
      "block_id": "B001",
      "paragraph_style": "P-CH-NO",
      "parent_page": "P-CH-OPEN-R",
      "target_object": "OBJ-CHOPEN-NO"
    },
    {
      "block_id": "B002",
      "paragraph_style": "P-CH-TTL",
      "parent_page": "P-CH-OPEN-R",
      "target_object": "OBJ-CHOPEN-TITLE"
    }
  ],
  "chapter_open_plan": {
    "page_target": "next_odd_page",
    "parent_page": "P-CH-OPEN-R",
    "objects": [
      "OBJ-CHOPEN-NO",
      "OBJ-CHOPEN-TITLE",
      "OBJ-CHOPEN-SUB",
      "OBJ-CHOPEN-EPIGRAPH"
    ]
  },
  "validation_report": {
    "status": "pass",
    "errors": []
  }
}
```

---

### 11.14 阶段完成清单

现在 OpenClaw 已拥有：

- ✅ 系统规则
- ✅ 模板字典
- ✅ 输入输出结构
- ✅ 执行顺序
- ✅ 内容识别规则
- ✅ 样式映射表
- ✅ 章首页对象清单

**下一步待补充**：
1. **父页内部坐标协议** —— 每个对象的版心区域、最大行数、可用宽度、上下留白、超限回退规则
2. **正文首段与普通正文的精细规则** —— 首字下沉、段前段后控制、孤行寡行修复、运行头显示起始页


---

## 十二、Phase 1C：父页坐标协议 + 章首页超限回退规则 + 正文首段精细规则

> **目标**：让 OpenClaw 不再只会"识别内容"，而是开始会"把内容放进正确区域，并在放不下时按固定顺序回退"。

---

### 12.1 父页坐标协议

#### 12.1.1 坐标总原则

OpenClaw 以后不要输出"差不多放在页面上方偏左"。
它必须统一输出两层坐标：

**第一层：逻辑区域**

- `live_area`
- `chapter_no_zone`
- `chapter_title_zone`
- `chapter_subtitle_zone`
- `chapter_epigraph_zone`
- `body_first_zone`
- `folio_zone`
- `runhead_zone`

**第二层：实际边界**

- `geometricBounds = [top, left, bottom, right]`

因为 InDesign 的文本框、页码框、图框这些页面对象，本质上都能通过几何边界精确定位；而且页边距、栏数、栏距可以直接在父页/母版页上设定。

#### 12.1.2 统一测量规则

OpenClaw 的内部坐标协议锁定为：

```
measurement_unit = pt
ruler_origin = page_origin
bounds_order = [top, left, bottom, right]
```

原因不是 pt 一定比 mm 好，而是 InDesign 的脚本示例、`geometricBounds`、网格和文本度量在官方示例里大量直接用 point；同时 `pageOrigin` 可以避免跨页文档里相对原点混乱。真到输出给用户或做配置文件时，再允许输入 mm，但内部统一转 pt。

#### 12.1.3 live_area 的定义

所有对象都不要直接相对整页摆放。先算 `live_area`：

```
live_area.top    = page.marginPreferences.top
live_area.left   = page.marginPreferences.left
live_area.bottom = page_height - page.marginPreferences.bottom
live_area.right  = page_width  - page.marginPreferences.right
```

也就是说，所有章首页和正文对象，默认都相对**版心区**工作，而不是相对整页出血区工作。父页本来就适合统一页边距、栏数与基础框架。

#### 12.1.4 左右页坐标规则

Facing Pages 文档里，左页和右页不能共享一套"视觉想象坐标"，但可以共享一套"版心逻辑坐标"。

所以 OpenClaw 要遵守：

- 左右页都先算各自 `live_area`
- 章首页右页只允许落到 `P-CH-OPEN-R`
- 正文左页只允许落到 `P-BD-TXT-L`
- 正文右页只允许落到 `P-BD-TXT-R`

不要写死"右页标题一定从页面左边 20mm 起"，而要写成：

```
chapter_title_zone.left = live_area.left + x_offset
chapter_title_zone.right = live_area.right - x_offset
```

这样模板换开本时，才能靠父页边距和版心同步变动。Adobe 也明确把父页、边距、页面尺寸变更作为统一控制版式的基础。

#### 12.1.5 章首页推荐坐标协议（模板 A）

**`P-CH-OPEN-R-A`**

```json
{
  "template_id": "P-CH-OPEN-R-A",
  "page_role": "chapter_open_right",
  "zones": {
    "chapter_no_zone":        [0.10, 0.00, 0.20, 0.32],
    "chapter_title_zone":     [0.22, 0.00, 0.46, 0.82],
    "chapter_subtitle_zone":  [0.48, 0.00, 0.56, 0.82],
    "chapter_epigraph_zone":  [0.62, 0.18, 0.84, 0.82]
  }
}
```

这里的值不是最终的 pt，而是**相对 live_area 的比例坐标**，解释为：

```
[top_ratio, left_ratio, bottom_ratio, right_ratio]
```

然后再由 OpenClaw 转成实际 `geometricBounds`。

这样做的好处是：

- 开本变化时不需要重写所有坐标
- 父页只需要改边距和版心
- 同一逻辑模板能生成多个尺寸版本

这不是 InDesign 自带"比例坐标系统"，而是 OpenClaw 层自己加的一层抽象；最终落地仍然是 InDesign 的几何边界。

---

### 12.2 章首页对象的坐标装配规则

#### 12.2.1 对象和区域一一绑定

以后不要让 OpenClaw 自己找位置。它只允许按下面映射装配：

```
OBJ-CHOPEN-NO        → chapter_no_zone
OBJ-CHOPEN-TITLE     → chapter_title_zone
OBJ-CHOPEN-SUB       → chapter_subtitle_zone
OBJ-CHOPEN-EPIGRAPH  → chapter_epigraph_zone
```

对象本身仍然是 InDesign 的文本框，坐标最终落成 `geometricBounds`。

#### 12.2.2 每个对象必须同时有 4 个约束

每个对象都要有：

- `max_lines`
- `max_fill_ratio`
- `allow_scale_down`
- `fallback_priority`

例如：

```json
{
  "object_id": "OBJ-CHOPEN-TITLE",
  "paragraph_style": "P-CH-TTL",
  "max_lines": 4,
  "max_fill_ratio": 0.88,
  "allow_scale_down": false,
  "fallback_priority": 1
}
```

`max_fill_ratio` 的意思不是 InDesign 自带字段，而是你给 OpenClaw 的判定规则：当文字在文本框里的占用超过预设比例，就判为超限，不要等它真的 overset 才反应。真正到 InDesign 里，超限的硬信号仍然是 overset text；Story Editor 也能显示整个 story，包括 overset 部分。

---

### 12.3 章首页超限回退规则

这里是最关键的部分。以后 OpenClaw 只要遇到章首页装不下，就按这个顺序修，不许跳步。

#### 12.3.1 超限的判定条件

任何一个章首页对象满足以下任一条件，就视为超限：

- 文本框出现 overset
- 实测行数 `> max_lines`
- 占用高度 `> zone_height * max_fill_ratio`
- 对象侵入相邻 zone
- 对象侵入保留白区

其中 overset text 是 InDesign 原生可检测的硬错误；删掉线程末端文本框时，末尾文本也会回变成 overset。

#### 12.3.2 章首页模板必须不是单页唯一模板

章首页扩成 3 个变体，但对 OpenClaw 暴露一个统一角色名：

```
chapter_open_right
  ├─ P-CH-OPEN-R-A   标准留白型
  ├─ P-CH-OPEN-R-B   标题扩展型
  └─ P-CH-OPEN-R-C   标题+题记紧凑型
```

然后让 OpenClaw 只知道：

```json
{
  "logical_parent": "chapter_open_right",
  "candidate_parents": [
    "P-CH-OPEN-R-A",
    "P-CH-OPEN-R-B",
    "P-CH-OPEN-R-C"
  ]
}
```

父页本来就适合做一组模板化变体，页面应用哪个父页可以统一切换。

#### 12.3.3 标题超限回退顺序

**`chapter_title` 超限时，回退顺序固定为：**

1. 检查章号是否可压缩到更小 zone
2. 切换 `P-CH-OPEN-R-A → P-CH-OPEN-R-B`
3. 若有副标题，先保证主标题，不优先保副标题
4. 仍超限时切到 `P-CH-OPEN-R-C`
5. 仍超限则报错 `E-CHOPEN-011`

**禁止动作**：

- 禁止直接缩小正文章体系统
- 禁止把章标题和章号并入同一文本框
- 禁止手工拖框挤压其他 zone

#### 12.3.4 副标题超限回退顺序

**`chapter_subtitle` 超限时：**

1. 检查是否为空或可折叠隐藏
2. 切换到 `P-CH-OPEN-R-B`
3. 若仍超限，将副标题移动到正文第一页顶部的专用对象
4. 应用 `P-CH-SUB-FIRST`
5. 输出 warning，不算 fatal

这意味着需要新增一个对象和样式：

```
OBJ-BDFIRST-SUB
P-CH-SUB-FIRST
```

这一步是 OpenClaw 协议新增的对象名；落地仍然只是新增文本框并套样式。

#### 12.3.5 题记超限回退顺序

**`epigraph` 超限时：**

1. 优先切到 `P-CH-OPEN-R-C`
2. 若仍超限，题记移到正文第一页顶部对象 `OBJ-BDFIRST-EPI`
3. 应用 `P-EPIGRAPH-FIRST`
4. 若移入正文第一页后影响首段空间，再把首段顺延到下一正文页
5. 若仍无法满足，则报 `E-PARSE-008`

**铁律**：**题记是可迁移对象，主标题不是。**

#### 12.3.6 章号超限回退顺序

章号一般最不该出问题。若章号超限，多半是识别或样式异常。

**`chapter_number` 超限时：**

1. 检查是否误把章号+标题混成一块
2. 检查是否用了错误样式
3. 检查是否进入了标题框而不是章号框
4. 若仍超限，报 `E-PARSE-002`

---

### 12.4 正文第一页精细规则

#### 12.4.1 正文第一页不是普通正文页

新增逻辑规则：

```
body_first_page != body_normal_page
```

也就是说，正文第一页必须单独判定和单独套父页：

- 父页：`P-BD-FIRST`
- 主文本框对象：`OBJ-BDFIRST-MAIN`
- 段落样式：首段 `P-BD-FIRST`，其后 `P-BD-01`

章首页后的第一页通常需要独立节奏，而不是直接继承普通正文页所有元素；父页正适合做这种差异化控制。

#### 12.4.2 正文首段默认规则

默认首段协议锁定为：

```json
{
  "style": "P-BD-FIRST",
  "same_font_metrics_as_body": true,
  "first_line_indent": 0,
  "space_before": 0,
  "space_after": 0,
  "align_to_baseline_grid": true,
  "allow_dropcap": false
}
```

原因：在没有插图、没有复杂体例的 Phase 1 中，首段最稳的做法是**不缩进、字度量与正文一致、直接进入稳定正文流**。基线网格用于跨页与跨栏对齐。

#### 12.4.3 首段与后续正文的衔接规则

OpenClaw 必须执行：

1. 首段用 `P-BD-FIRST`
2. 第二段开始统一用 `P-BD-01`
3. 若 house style 规定正文首行缩进，则只从第二段开始缩进
4. 首段不得被误判成引文、题记或注释
5. 首段必须进入 `story_main`

线程文本框是主文本流的核心；文本在 frame 之间线程连接后，会沿着 story 连续流动。

#### 12.4.4 是否允许首字下沉

当前阶段默认：

```
allow_dropcap = false
```

原因不是 InDesign 做不到，而是 Phase 1 先追求稳定。
如果以后某个项目要启用首字下沉，必须通过 **Drop Caps and Nested Styles** 放进段落样式，不允许局部手工改字。InDesign 本身就支持在段落样式里设置 drop cap 和 nested styles。

#### 12.4.5 正文第一页的运行头与页码

建议规则：

- `runhead_visibility = false`
- `folio_visibility = true | false` 由项目 house style 决定
- 如果章首页是 blind folio，则正文第一页可以恢复 folio
- 若采用极简风格，正文第一页也可隐藏 folio，但必须在 section/page numbering 上保持真实连续

自动页码可以通过特殊字符放在父页文本框里，而 section/page numbering 由 Numbering & Section Options 控制。

---

### 12.5 正文首段超限与回退

#### 12.5.1 首段页超限判定

当 `OBJ-BDFIRST-MAIN` 满足以下任一条件时，视为异常：

- 主文本框 overset
- 首段只剩 1 行或 2 行挂在本页
- 首段后正文剩余行数过少，破坏页面节奏
- 题记迁移到首段页后挤爆正文区

InDesign 的 overset 是明确可见和可读出的；Story Editor 可直接看到超出的文本。

#### 12.5.2 首段页回退顺序

**`body_first_page` 异常时：**

1. 检查题记/副标题是否迁移到了首段页
2. 若是，优先缩减可选对象，而不是挤正文
3. 若正文仍超限，将首段页切到 `P-BD-FIRST-B`
4. 若仍超限，则正文首段整体顺延到下一正文页
5. 原页面仅保留章首页收束结构
6. 输出 warning 或 fatal，视项目策略而定

所以这里再增加一个正文首段变体父页：

```
P-BD-FIRST-A   标准首段页
P-BD-FIRST-B   紧凑首段页
```


---

### 12.6 新增协议字段

下面这组字段，直接并入前面的 JSON 结构：

```json
{
  "coordinate_protocol": {
    "unit": "pt",
    "ruler_origin": "page_origin",
    "bounds_order": ["top", "left", "bottom", "right"],
    "zone_reference": "live_area"
  },
  "chapter_open_family": {
    "logical_parent": "chapter_open_right",
    "candidate_parents": [
      "P-CH-OPEN-R-A",
      "P-CH-OPEN-R-B",
      "P-CH-OPEN-R-C"
    ]
  },
  "body_first_family": {
    "logical_parent": "body_first_page",
    "candidate_parents": [
      "P-BD-FIRST-A",
      "P-BD-FIRST-B"
    ]
  },
  "overflow_policy": {
    "chapter_title": [
      "switch_parent:P-CH-OPEN-R-B",
      "switch_parent:P-CH-OPEN-R-C",
      "fatal:E-CHOPEN-011"
    ],
    "chapter_subtitle": [
      "switch_parent:P-CH-OPEN-R-B",
      "move_to:OBJ-BDFIRST-SUB",
      "warning:E-CHOPEN-021"
    ],
    "epigraph": [
      "switch_parent:P-CH-OPEN-R-C",
      "move_to:OBJ-BDFIRST-EPI",
      "fatal:E-PARSE-008"
    ],
    "body_first_page": [
      "switch_parent:P-BD-FIRST-B",
      "push_body_to_next_page",
      "fatal:E-BDFIRST-001"
    ]
  }
}
```

---

### 12.7 Phase 1C 新增错误码

| 错误码 | 说明 |
|--------|------|
| `E-CHOPEN-011` | 章标题在所有章首页模板中仍超限 |
| `E-CHOPEN-021` | 章副标题迁移到正文第一页 |
| `E-CHOPEN-031` | 题记迁移到正文第一页 |
| `E-BDFIRST-001` | 正文第一页在所有首段模板中仍超限 |
| `E-BDFIRST-002` | 首段页误带普通运行头 |
| `E-BDFIRST-003` | 首段未进入 story_main |
| `E-BDFIRST-004` | 首段样式误用 P-BD-01 |

---

### 12.8 系统提示词补充补丁（Phase 1C）

直接补到系统提示词后面：

```text
补充规则：Phase 1C

1. 所有页面对象必须先映射到逻辑 zone，再换算成 geometricBounds。
2. 章首页不是单一父页，而是父页家族：
   - P-CH-OPEN-R-A
   - P-CH-OPEN-R-B
   - P-CH-OPEN-R-C
3. 正文第一页不是单一父页，而是父页家族：
   - P-BD-FIRST-A
   - P-BD-FIRST-B
4. 标题超限时，优先切换父页，不得先缩小字号。
5. 题记和副标题属于可迁移对象；主标题不属于可迁移对象。
6. 所有首段必须进入 story_main。
7. 首段默认不做首字下沉；若启用，必须通过 paragraph style 的 drop caps/nested styles 实现。
8. 基线网格对正文和首段默认启用；章标题对象是否对齐基线网格由模板决定。
9. 所有超限必须输出 fallback path 和最终 validation result。
```

---

### 12.9 阶段完成清单

到这一步，OpenClaw 已经拥有：

- ✅ 系统提示词
- ✅ 范围边界
- ✅ 父页/样式命名字典
- ✅ 输入输出结构
- ✅ 执行顺序
- ✅ 内容识别状态机
- ✅ 章首页对象清单
- ✅ **父页坐标协议**（live_area、比例坐标、模板 A）
- ✅ **超限回退规则**（3 个章首页变体 + 2 个首段页变体、4 类对象回退顺序）
- ✅ **正文首段精细规则**（默认不缩进、无首字下沉、基线网格启用、运行头/页码策略）

这已经不是"灵感说明书"了，已经开始接近**可编排、可调试、可验证**的执行规范。

**下一步待补充**：
1. **正文左右页的运行头、页码、分节、孤行寡行修复协议**
2. **把这些规则翻成 OpenClaw 真正能跑的伪代码 / JSON Schema / 执行树**


---

## 十三、Phase 1D：正文页精细协议 + 运行头与页码系统 + 孤行寡行修复规则 + 协同执行顺序

> **目标**：把章首页规则、首段页规则、内容识别规则、父页坐标协议接到**普通正文页的稳定运行**上。

---

### 13.1 Phase 1D 的协同目标

**核心原则**：

> **章首页、首段页、普通正文页，不是三个孤立页面，而是一个连续系统。**

OpenClaw 不能按"单页美观"思考，必须按"页面序列协同"思考。

**页面序列协同模型**：

```
章节结束页
→ 空白补位页（如需要）
→ 章首页右页
→ 首段正文页
→ 普通正文左页/右页循环
→ 下一章节
```

这里最关键的不是哪一页好看，而是：

- 页码连续
- story_main 连续
- 父页切换正确
- 运行头逻辑连续
- 标题系统不掉队
- 正文阅读节奏不被打断

---

### 13.2 正文页家族定义

#### 13.2.1 父页家族

```
P-BD-FIRST-A    首段正文页标准版
P-BD-FIRST-B    首段正文页紧凑版

P-BD-TXT-L-A    普通正文左页标准版
P-BD-TXT-R-A    普通正文右页标准版

P-BD-TXT-L-B    普通正文左页无运行头版
P-BD-TXT-R-B    普通正文右页无运行头版

P-BD-TXT-L-C    普通正文左页紧凑版
P-BD-TXT-R-C    普通正文右页紧凑版
```

#### 13.2.2 为什么要有家族而不是单模板

正文页的典型异常不是"完全排不下"，而是这些中间态问题：

- 正文能放下，但运行头挤压了上方呼吸区
- 页码能放，但版面过满
- 左页正常，右页异常
- 标题后首段页正常，但第二页开始节奏太紧
- 孤行寡行导致页面节奏断裂

所以不能只有一个 `P-BD-TXT-L` / `P-BD-TXT-R`。

---

### 13.3 正文页对象清单

#### 13.3.1 左页对象

```
OBJ-BD-L-MAIN       左页主文本框
OBJ-BD-L-RUNHEAD    左页运行头框
OBJ-BD-L-FOLIO      左页页码框
OBJ-BD-L-SAFE       左页安全版心区
```

#### 13.3.2 右页对象

```
OBJ-BD-R-MAIN       右页主文本框
OBJ-BD-R-RUNHEAD    右页运行头框
OBJ-BD-R-FOLIO      右页页码框
OBJ-BD-R-SAFE       右页安全版心区
```

#### 13.3.3 首段页对象

```
OBJ-BDFIRST-MAIN      首段页主文本框
OBJ-BDFIRST-SUB       首段页副标题承接框
OBJ-BDFIRST-EPI       首段页题记承接框
OBJ-BDFIRST-FOLIO     首段页页码框
OBJ-BDFIRST-RUNHEAD   首段页运行头框
OBJ-BDFIRST-SAFE      首段页安全版心区
```

---

### 13.4 正文主文本流协同规则

#### 13.4.1 story_main 的唯一性

OpenClaw 必须遵守：

```
story_main = 全书正文唯一主文本流
```

允许不进入 `story_main` 的只有：

- 目录页
- 章首页对象
- 空白补位页
- 封面封底
- 明确独立的前置页对象

正文首段页和普通正文页都必须进入 `story_main`。

#### 13.4.2 正文线程连接规则

固定顺序：

```
OBJ-BDFIRST-MAIN
→ OBJ-BD-L-MAIN / OBJ-BD-R-MAIN
→ 下一个正文页主文本框
→ 下一个正文页主文本框
```

换句话说：

- 首段页主文本框是正文 story_main 的起点页框
- 之后所有普通正文页主文本框按页序串联
- 空白页不得插入线程
- 章首页不得插入线程

#### 13.4.3 线程检查协议

OpenClaw 每次完成一章排版后，必须检查：

- `previousTextFrame`
- `nextTextFrame`
- 当前 story 是否仍为 `story_main`
- 是否出现孤立主文本框
- 是否出现错误跳页线程

---

### 13.5 运行头系统

运行头是最容易被 AI 乱处理的部分，所以必须先把逻辑锁死。

#### 13.5.1 运行头不是装饰，是导航系统

它的任务只有两个：

- 告诉读者当前所处内容
- 在不干扰正文的前提下维持阅读定位

所以 OpenClaw 不得把运行头当自由设计区域。

#### 13.5.2 当前阶段的默认运行头策略

固定 house style：

**章首页**：不显示运行头

**首段正文页**：不显示运行头

**普通正文左页**：显示书名或一级部名

**普通正文右页**：显示章标题

```
left_runhead  = book_title_or_part_title
right_runhead = current_chapter_title
```

这是最适合中文书且最容易模板化的一种。

#### 13.5.3 运行头来源规则

OpenClaw 不允许人工写死运行头文字。必须来自结构化字段：

```json
{
  "runhead_source": {
    "left_page": "book_title_or_part_title",
    "right_page": "current_chapter_title"
  }
}
```

#### 13.5.4 运行头应用规则

```
P-BD-TXT-L-A → runhead visible
P-BD-TXT-R-A → runhead visible

P-BD-TXT-L-B → runhead hidden
P-BD-TXT-R-B → runhead hidden
```

"有没有运行头"应该由父页决定，不由局部对象手工删。

#### 13.5.5 运行头验证规则

```
V-RH-001  章首页不得显示运行头
V-RH-002  首段页不得显示运行头
V-RH-003  普通正文页若启用运行头，则对象必须存在
V-RH-004  左页运行头不得误显示章标题
V-RH-005  右页运行头不得误显示书名
V-RH-006  运行头不得进入正文主文本流
```

---

### 13.6 页码系统

#### 13.6.1 页码系统原则

OpenClaw 必须遵守：

- 页码显示不等于页码存在
- 即使页面不显示 folio，内部页码仍要连续
- 页码变化只能通过 section 处理
- 禁止手工改某页页码字符

#### 13.6.2 当前阶段推荐页码策略

**章首页**：默认 blind folio（页码继续计算，但不显示）

**首段页**：可显示 folio，也可按项目 house style 隐藏，但内部页码必须连续

**普通正文页**：默认显示 folio

#### 13.6.3 页码对象策略

页码必须放在独立对象中，不允许塞进正文框。

```
OBJ-BD-L-FOLIO
OBJ-BD-R-FOLIO
OBJ-BDFIRST-FOLIO
OBJ-CHOPEN-FOLIO
```

并统一挂：

```
O-FOLIO
P-FOLIO
```

#### 13.6.4 section 规则

OpenClaw 当前阶段要支持最常见的 3 种 section 模式：

```
SEC-001  前置页罗马数字 + 正文阿拉伯数字
SEC-002  全书阿拉伯数字连续
SEC-003  正文从 1 重新开始
```

默认推荐：

```
section_policy = body_arabic_restart_or_continue
```

但是它不能自己随便选，必须读项目配置。

#### 13.6.5 页码验证规则

```
V-FOLIO-001  章首页内部页码必须连续
V-FOLIO-002  blind folio 页面不得误显示数字
V-FOLIO-003  普通正文页页码对象必须存在
V-FOLIO-004  页码不得进入正文主文本流
V-FOLIO-005  section 起点必须与项目配置一致
V-FOLIO-006  TOC 更新后页码必须重新验证
```

---

### 13.7 正文左右页的坐标与对象协议

#### 13.7.1 普通正文页逻辑 zone

**左页**：
```
body_main_zone
runhead_zone
folio_zone
```

**右页**：
```
body_main_zone
runhead_zone
folio_zone
```

#### 13.7.2 推荐比例模板

**`P-BD-TXT-L-A / P-BD-TXT-R-A`**

```json
{
  "body_main_zone": [0.10, 0.00, 0.90, 1.00],
  "runhead_zone":   [0.02, 0.10, 0.07, 0.90],
  "folio_zone":     [0.92, 0.35, 0.98, 0.65]
}
```

仍然是相对 `live_area` 的比例坐标。

但要加一条：

```
if runhead_visible = false
→ body_main_zone.top can expand upward
```

也就是没有运行头版本时，正文区可以上扩。

#### 13.7.3 首段页模板建议

**`P-BD-FIRST-A`**

```json
{
  "body_main_zone": [0.18, 0.00, 0.90, 1.00],
  "folio_zone":     [0.92, 0.35, 0.98, 0.65],
  "runhead_zone":   null,
  "subtitle_carry_zone": [0.08, 0.00, 0.14, 0.82],
  "epigraph_carry_zone": [0.08, 0.18, 0.22, 0.82]
}
```

这意味着：

- 首段页正文主块上边界更低
- 留出承接副标题/题记的可能
- 默认无运行头


---

### 13.8 孤行寡行修复规则

先统一术语：

- **寡行**：段落最后一行单独跑到下一页/栏
- **孤行**：段落第一页末只剩一行，后文跑下一页/栏

OpenClaw 当前阶段先只做"页级修复"，不做复杂字距微调策略。

#### 13.8.1 孤行寡行的目标

不是"绝对零出现"，而是：

> **优先避免标题后的孤行、段末的寡行、章首页后的不稳节奏。**

#### 13.8.2 当前阶段的修复优先级

固定顺序如下：

**第一级：Keep Options 检查**

检查：

- 标题是否 `Keep With Next`
- 标题段是否有 `Start Paragraph`
- 首段是否允许断开
- 引文块是否整块保留

**第二级：父页切换**

若当前正文页过紧：

- `P-BD-TXT-L-A → P-BD-TXT-L-C`
- `P-BD-TXT-R-A → P-BD-TXT-R-C`

紧凑版的含义是：

- 运行头可隐藏
- 正文区略扩
- 不改正文基准字号

**第三级：补页**

当结构性拥挤无法解决时，允许增页。

**第四级：轻微段前后微调**

仅允许在既定范围内：

- `space_before ± small_range`
- `space_after ± small_range`

**禁止动作**：

- 禁止先缩正文基础字号
- 禁止先改行距体系
- 禁止手工拉伸文本框破坏模板
- 禁止大幅字距压缩

#### 13.8.3 孤行寡行检测规则

```
V-WO-001  标题后首段不得只挂 1 行
V-WO-002  段落末行不得单独落下一页
V-WO-003  首段页不得只容纳极少正文行数
V-WO-004  引文块不得断裂到造成阅读错觉
V-WO-005  批注块不得因分页被拆成不完整视觉单元
```

#### 13.8.4 孤行寡行错误码

| 错误码 | 说明 |
|--------|------|
| `E-WO-001` | 标题后首段孤行 |
| `E-WO-002` | 正文段落寡行 |
| `E-WO-003` | 首段页节奏失衡 |
| `E-WO-004` | 引文块断裂异常 |
| `E-WO-005` | 批注块拆裂异常 |

---

### 13.9 正文页超限与回退

#### 13.9.1 正文页异常判定

满足任一条件即异常：

- 主文本框 overset
- 运行头侵入正文区
- folio 侵入正文区
- 正文区填充率超过上限
- 孤行寡行规则触发
- 正文线程断裂

#### 13.9.2 普通正文页回退顺序

**`body_normal_page` 异常时：**

1. 检查线程是否断裂
2. 检查该页是否误用了错误父页
3. 若运行头存在，尝试切换到无运行头版本 B
4. 若仍过紧，切换到紧凑版 C
5. 若仍异常，增页并重流 story_main
6. 若仍异常，输出人工审查

#### 13.9.3 左右页回退示意

```
P-BD-TXT-L-A
→ P-BD-TXT-L-B
→ P-BD-TXT-L-C
→ add_page_after
→ fatal

P-BD-TXT-R-A
→ P-BD-TXT-R-B
→ P-BD-TXT-R-C
→ add_page_after
→ fatal
```

---

### 13.10 协同执行顺序补丁（Stage 0-7）

从这一阶段开始，完整顺序应为：

#### Stage 0：解析

- 识别内容块
- 建章节边界
- 建正文流边界

#### Stage 1：分页前检查

- facing pages
- section policy
- parent family 完整性
- style dictionary 完整性

#### Stage 2：目录与前置页

- 生成 TOC
- 校验 TOC 不进正文流

#### Stage 3：章首页

- 奇数页校验
- 空白补位页
- 章首页对象装配
- 章首页超限回退

#### Stage 4：首段页

- 应用 `P-BD-FIRST-A/B`
- 放置首段
- 承接副标题/题记迁移对象
- 检查首段页节奏

#### Stage 5：普通正文页

- 应用左右页模板
- 建立线程
- 运行头/页码应用
- 孤行寡行检查
- 正文页回退

#### Stage 6：全章联检

- 章首页、首段页、正文页协同检查
- 页码连续性
- section 连续性
- 线程连续性
- 父页连续性

#### Stage 7：全书联检

- TOC 页码更新
- 运行头一致性
- section 边界检查
- Preflight

---

### 13.11 Phase 1D 新增 JSON 字段

```json
{
  "runhead_policy": {
    "chapter_open": false,
    "body_first_page": false,
    "body_left_page": "book_title_or_part_title",
    "body_right_page": "current_chapter_title"
  },
  "folio_policy": {
    "chapter_open_visible": false,
    "body_first_visible": true,
    "body_normal_visible": true,
    "section_mode": "project_defined"
  },
  "body_parent_family": {
    "left_candidates": [
      "P-BD-TXT-L-A",
      "P-BD-TXT-L-B",
      "P-BD-TXT-L-C"
    ],
    "right_candidates": [
      "P-BD-TXT-R-A",
      "P-BD-TXT-R-B",
      "P-BD-TXT-R-C"
    ]
  },
  "widow_orphan_policy": {
    "enabled": true,
    "repair_order": [
      "check_keep_options",
      "switch_parent_no_runhead",
      "switch_parent_compact",
      "add_page_after",
      "minor_spacing_adjust",
      "fatal_review"
    ]
  }
}
```

---

### 13.12 Phase 1D 新增错误码

| 错误码 | 说明 |
|--------|------|
| `E-RH-001` | 左页运行头缺失 |
| `E-RH-002` | 右页运行头缺失 |
| `E-RH-003` | 运行头内容来源错误 |
| `E-RH-004` | 首段页误带运行头 |
| `E-FOLIO-001` | blind folio 页面误显示页码 |
| `E-FOLIO-002` | 正文页页码缺失 |
| `E-FOLIO-003` | section 断裂 |
| `E-FOLIO-004` | TOC 更新后页码不一致 |
| `E-BD-001` | 正文页误用首段页父页 |
| `E-BD-002` | 正文页误用章首页父页 |
| `E-BD-003` | 正文主文本框未进入 story_main |
| `E-BD-004` | 普通正文页超限 |
| `E-BD-005` | 运行头侵入正文区 |
| `E-BD-006` | 页码侵入正文区 |

---

### 13.13 系统提示词补充补丁（Phase 1D）

```text
补充规则：Phase 1D

1. 正文页必须作为父页家族处理，不得只使用单一正文模板。
2. 运行头和页码必须是独立对象，不得进入正文主文本流。
3. 运行头默认只出现在普通正文页，不出现在章首页和首段页。
4. 页码显示策略不得影响内部页码连续性。
5. 所有正文页必须加入 story_main，章首页和空白页不得加入 story_main。
6. 孤行寡行修复优先级高于局部视觉微调。
7. 遇到正文页过紧时，优先切换父页变体，再考虑增页，不得先缩正文基础字号。
8. 所有修复必须输出 repair_path。
9. 全章完成后，必须做 chapter-level coordination check。
10. 全书完成后，必须重新更新 TOC 并再次校验页码。
```

---

### 13.14 阶段完成清单

到这一步，OpenClaw 已经基本具备了：

- ✅ 识别内容
- ✅ 安排章节
- ✅ 处理奇数页章首页
- ✅ 处理空白补位页
- ✅ 处理章首页对象
- ✅ 处理首段页
- ✅ 处理普通正文页（6 变体父页家族）
- ✅ 处理运行头（左书名/右章标题策略）
- ✅ 处理页码（blind folio / section 模式）
- ✅ 处理 section（3 种模式）
- ✅ 处理线程（story_main 唯一性 + 连接规则）
- ✅ 处理孤行寡行（4 级修复优先级）
- ✅ 做全章协同检查（Stage 6）
- ✅ 做全书联检（Stage 7）

系统已经从"单页排版器"变成"**章节级排版执行器**"。

**下一步待补充**：
1. **Phase 1E：Book 文件协同规则** — 多文档章节协同、`.indb` 协作层、TOC/section 联动、Preflight/Package 输出协议
2. **OpenClaw 可执行伪代码 / JSON Schema / 执行树**


---

## 十四、Phase 1E：Book 文件协同规则 + 多文档章节协同 + TOC/section 联动 + Preflight/输出协议

> **目标**：从"单个 `.indd` 怎么排"升级到"整本书如果拆成多个 `.indd` 文档，由一个 `.indb` 来统一编排、统一编号、统一目录、统一同步、统一输出"。

---

### 14.1 Phase 1E 的目标

从这一阶段开始，OpenClaw 不能只理解"页面协同"，还要理解"文档协同"。

也就是从：

```
页面 -> 章 -> 文档 -> 全书
```

四级联动。

**目标锁定为 5 条**：

1. **每一章可以是单独 `.indd`**
2. **整本书由一个 `.indb` 管理**
3. **样式、父页、变量、编号规则通过 style source 同步**
4. **目录由专门的 TOC 文档生成，并包含全书成员**
5. **输出时以"全书 PDF + 源文件交付包"双轨交付**

---

### 14.2 Book 架构怎么定

#### 14.2.1 文档角色分层

整本书固定成以下角色：

```
BOOK-ROOT.indb

00_STYLE_SOURCE.indd
01_FRONTMATTER.indd
02_TOC.indd
03_CHAPTER_001.indd
04_CHAPTER_002.indd
...
98_BACKMATTER.indd
99_INDEX_OR_APPENDIX.indd
```

这是给 OpenClaw 的协同协议，和 Adobe Book 的工作方式贴合：Book 面板本来就是把多个 InDesign 文档按顺序加入、替换、移除、重排；style source 也正是 Book 同步的核心。

#### 14.2.2 style source 的角色必须单独固定

Book 同步依赖一个 **style source** 文档；你可以在 Book 面板里把某个文档设为样式源，再把所选同步项复制给其他文档。同步时，如果其他文档里有同名项目，它会被替换；如果没有，就会新增进去。

所以对 OpenClaw 来说：

> **`00_STYLE_SOURCE.indd` 不是内容文档，而是版式宪法。**

它里面要放的不是正文，而是：

- Parent Pages
- Paragraph Styles
- Character Styles
- Object Styles
- Text Variables
- Swatches
- Numbered Lists
- TOC-related paragraph styles
- Cross-reference formats（后面要用的话）

---

### 14.3 Book 协同的最小规则

#### 14.3.1 `.indb` 只管"关系"，不管"正文内容"

保存 Book 是保存书籍文件本身，不是保存各个文档内容；也就是说，`.indb` 和成员 `.indd` 是分离的。

所以 OpenClaw 必须理解：

```
.indb = 书籍结构层
.indd = 章节内容层
```

这意味着：

- 调整文档顺序，是改 `.indb`
- 调整某章正文，是改对应 `.indd`
- 调整全书同步规则，是改 `.indb + style source`
- 调整某个样式定义，原则上只改 style source，再同步

#### 14.3.2 Book 中文档顺序就是全书顺序

Book 面板支持 add/remove/replace/reorder 文档，页码范围就显示在每个文档名旁边，并随文档页数变化和顺序变化而更新。

所以 OpenClaw 以后不能再"凭章节标题猜顺序"，必须只认：

```
book_order = Book panel order
```

#### 14.3.3 单章 = 单 `.indd`，一章内不要再二次分章

Adobe 官方关于 chapter number 的说明是：**一个文档只能有一个 chapter number**；如果你要在一个文档里再分多个章节，应使用 sections。

所以建议把协议定死：

**默认模式**：

- **一章一个 `.indd`**
- 文档级 chapter number 就等于章号
- 文档内部不再放多个真正意义的 chapter

**例外模式**：

只有前言、附录、目录这类非正文章，才允许做成"一个文档内多 section"。

---

### 14.4 Book 级同步规则

#### 14.4.1 只允许从 style source 向外同步

Book 的官方机制是：你选一个 style source，然后把样式、变量、父页等复制到其他成员文档。

所以 OpenClaw 必须遵守单向原则：

```
00_STYLE_SOURCE.indd
    ↓
all member documents
```

**禁止**：

- 从某一章反向覆盖 style source
- 两个文档轮流当样式源
- 把内容文档临时当 style source 又不记录

#### 14.4.2 同步项必须精确控制，不要全选乱同步

Synchronize Options 里可以选择具体同步项，而且要注意依赖关系；例如对象样式可能依赖段落样式、字符样式和色板。官方还提供了 Smart Match Style Groups，避免因为样式组位置变化而复制出重复样式。

所以 OpenClaw 的同步策略必须分层：

**基础全局同步**：

- Paragraph Styles
- Character Styles
- Object Styles
- Swatches
- Parent Pages
- Variables
- Numbered Lists

**条件同步**：

- Cross-reference formats
- Conditional text settings
- Trap presets

**当前阶段建议**：Phase 1E 先只同步基础全局同步项。

#### 14.4.3 同步时不要让"打开着的文档"成为盲点

同步时，关闭的文档会被 InDesign 自动打开、修改、保存并关闭；已经打开的文档会被修改，但**不会自动保存**。

这个点很关键。OpenClaw 的协同协议里必须加入一条硬规则：

```
before_book_sync:
  close_all_member_documents_if_possible = true
```

因为你不想出现：

- 书里大部分文档同步后被保存
- 某个正打开的文档被改了但没存
- 结果 style drift（样式漂移）出现

---

### 14.5 Book 级编号与分节协议

#### 14.5.1 页码更新必须交给 Book

Book 面板会显示每个成员文档的页码范围；默认情况下，当你增删页或改变书籍顺序时，InDesign 会更新页码和 section 编号。

所以 OpenClaw 要有两个层次的页码理解：

**文档内部**：

- 这一页显示什么页码
- 这一章是否是 blind folio
- section 起点是什么

**书籍层**：

- 这一章在全书中的起始页是多少
- 页码范围是否连续
- reorder 之后是否需要整书重算

#### 14.5.2 chapter number 走文档级，不走文本猜测

Adobe 官方说 chapter number 变量常用于 book，且文档只能分配一个 chapter number。

所以协议里要加：

```
chapter_number_source = document_level_metadata
not = parsed_body_text_only
```

也就是说：

- `第一章` 可以来自正文内容识别
- 但最终 chapter number 变量，应该绑定到该成员文档的文档级配置

这样 TOC、runhead、交叉引用才稳。

#### 14.5.3 section policy 只允许项目级配置，不允许局部临时改

这一阶段支持 3 种：

```
SEC-BOOK-001  前置页罗马数字 + 正文阿拉伯数字
SEC-BOOK-002  全书阿拉伯数字连续
SEC-BOOK-003  正文从 1 重新开始，前置页单独 section
```

这些都属于 InDesign 的 Numbering & Section Options 能处理的范围；TOC 里页码前缀、不同编号体系，也要靠 section 编号工作。

---

### 14.6 TOC 的 Book 级联动协议

#### 14.6.1 TOC 不该放在正文文档里

如果你为多个文档生成 TOC，应先创建或打开要用于 TOC 的文档，确认它在 book 中，然后打开 book file；生成时勾选 **Include Book Documents**，这样会为整个书籍列表生成单一 TOC，并重编页码。

所以 OpenClaw 的协议要定成：

```
TOC lives in:
02_TOC.indd
```

而不是：

- 放在第一章开头
- 临时塞进 frontmatter 文档的普通正文流
- 每章自己各生成一个 TOC 再拼接

#### 14.6.2 TOC 的来源是 paragraph styles，不是文本内容扫描

官方 TOC 是根据 paragraph styles 收集内容的；而 TOC Style 是一套用于生成目录的设置，不要和 TOC 条目本身的 paragraph styles 混淆。

所以 OpenClaw 必须遵守：

```
TOC source = included paragraph styles
not = raw heading text search
```

这意味着你前面做的内容识别，最终仍必须落到样式上，才能让 TOC 稳定。

#### 14.6.3 TOC 必须在"全书分页稳定后"重生成

因为 Include Book Documents 会把整本书的页码一起纳入 TOC 生成，而且文档顺序、section、章首页补位页都会影响页码。

所以 OpenClaw 的顺序必须是：

```
排完所有章节
→ 更新 Book 编号
→ 再生成/替换 TOC
→ 再检查 TOC 是否 overset
→ 再做最终输出
```

而不是先做 TOC 再排版正文。

---

### 14.7 Book 级运行头与变量协同

同步可以复制变量、父页和样式，所以运行头系统做成"变量 + 父页对象 + 样式"的组合，从 style source 同步到各章节。

**左页运行头来源**：`book_title_or_part_title`

**右页运行头来源**：`current_chapter_title`

**协同方式**：

- 运行头框来自父页
- 样式来自 style source
- 文本变量或文档元数据由章节文档提供
- Book 只负责顺序和编号，不直接写运行头内容


---

### 14.8 Preflight 的 Book 级协议

#### 14.8.1 Preflight 不是最后才跑一次

Preflight 面板会在你编辑时持续警告，并且它既适用于 document，也适用于 **book**；典型问题包括缺文件、缺字、低分辨率图、overset text 等。

所以 OpenClaw 应该有两级 Preflight：

**文档级**：

每个章节文档排完就检查：

- overset
- 缺字
- 链接
- 父页错误
- style override

**Book 级**：

全书合并后检查：

- page/section continuity
- TOC 页码一致性
- 所有成员文档状态
- 文档顺序对应的页码范围

#### 14.8.2 Book 级 Preflight 不等于只看 Book 面板

因为很多错误是"章节局部错误"，例如某章 overset，但全书 PDF 还可能勉强导出。

所以协议写成：

```
preflight_book = all_member_preflight_pass
                 + toc_preflight_pass
                 + numbering_consistency_pass
                 + book_order_pass
```

这是 OpenClaw 自己定义的协同规则，但对应的底层检查点都来自 InDesign 的书籍、TOC、页码、Preflight 机制。

---

### 14.9 输出协议

#### 14.9.1 全书 PDF 是官方主输出通道

Adobe 官方明确支持：

- `Export Book To PDF`
- `Export Selected Documents To PDF`

所以 OpenClaw 在 Book 模式下，默认主输出应该是：

```
primary_output = Export Book To PDF
```

而不是逐章单独导出再手工合并。

#### 14.9.2 Package 协议要分开处理

官方明确有 `File > Package` 用于单个 InDesign 文档，把 `.indd`、字体、链接图等一起复制出来用于分享或印刷。

但就查到的官方帮助里，没有同样明确的"Book 级一键 Package 全部成员"的说明。

所以建议不要让 OpenClaw 假设存在这个功能，而是设计成：

**安全做法**：

1. 导出 **整本 PDF**
2. 对每个成员 `.indd` 执行文档级 Package
3. 再由 OpenClaw 生成一个 **book_delivery_manifest.json**
4. 把 `.indb + 各成员 package + 全书 PDF + 版本说明` 组成交付集

这比"赌一个不确定的 book-package 命令"稳得多。

---

### 14.10 OpenClaw 的 Book 协同执行顺序（Stage B0-B7）

#### Stage B0：建立 Book

1. 创建或打开 `.indb`
2. 按正确顺序加入成员文档
3. 记录文档角色：
   - style_source
   - frontmatter
   - toc
   - chapter
   - backmatter

#### Stage B1：style source 校验

1. 确认 `00_STYLE_SOURCE.indd` 存在
2. 确认其包含全部必需：
   - parent pages
   - paragraph styles
   - character styles
   - object styles
   - variables
   - swatches
3. 设为 Book 的 style source

#### Stage B2：Book 同步

1. 尽量关闭所有成员文档
2. 打开 Synchronize Options
3. 仅勾选当前阶段允许同步项
4. 从 style source 同步到全书或所选成员
5. 同步后立即做一次 style drift 检查

这里"打开的文档会变但不自动保存"的官方行为，正是你要强制先关文档的原因。

#### Stage B3：编号与 section 更新

1. 按项目 section policy 应用各成员文档
2. 更新 Book 页码与 section 编号
3. 校验各成员页码范围连续
4. 校验 chapter number 与文档角色匹配

#### Stage B4：章节排版

1. 逐章执行前面 Phase 1A–1D 的规则
2. 每章结束后做文档级 Preflight
3. 保存通过的章节文档

#### Stage B5：生成 TOC

1. 打开 `02_TOC.indd`
2. 使用 TOC Style
3. 勾选 Include Book Documents
4. Replace Existing Table Of Contents
5. 放置生成结果
6. 检查 TOC 是否 overset

这些步骤都直接对应 Adobe 的 TOC 官方流程。

#### Stage B6：全书联检

1. 再次更新 Book 编号
2. 再次检查 TOC 页码
3. 再次检查运行头来源
4. 执行 Book 级 Preflight
5. 若失败，回到出错成员文档修复

#### Stage B7：输出

1. `Export Book To PDF`
2. 若只需部分章节，`Export Selected Documents To PDF`
3. 再执行多文档 package 协议
4. 生成交付清单 manifest
5. 写入版本号与输出时间

---

### 14.11 Book 输入结构（JSON）

```json
{
  "book_profile": {
    "mode": "indb_multi_document",
    "book_file": "BOOK-ROOT.indb",
    "style_source": "00_STYLE_SOURCE.indd",
    "toc_document": "02_TOC.indd",
    "section_policy": "SEC-BOOK-001",
    "primary_pdf_output": "book_pdf"
  },
  "book_members": [
    {
      "doc": "00_STYLE_SOURCE.indd",
      "role": "style_source"
    },
    {
      "doc": "01_FRONTMATTER.indd",
      "role": "frontmatter"
    },
    {
      "doc": "02_TOC.indd",
      "role": "toc"
    },
    {
      "doc": "03_CHAPTER_001.indd",
      "role": "chapter",
      "chapter_no": 1
    }
  ],
  "sync_policy": {
    "close_open_docs_before_sync": true,
    "sync_items": [
      "paragraph_styles",
      "character_styles",
      "object_styles",
      "parent_pages",
      "variables",
      "swatches",
      "numbered_lists"
    ],
    "smart_match_style_groups": true
  },
  "toc_policy": {
    "document": "02_TOC.indd",
    "include_book_documents": true,
    "replace_existing": true,
    "toc_style": "TOC-MAIN"
  },
  "output_policy": {
    "export_book_pdf": true,
    "package_each_member_document": true,
    "generate_delivery_manifest": true
  }
}
```

这个 JSON 里的字段是给 OpenClaw 的协议，不是 Adobe 原生命令；但每个关键字段都贴合 Adobe 的 Book、TOC、同步和 PDF 输出能力。

---

### 14.12 Book 协同错误码

| 错误码 | 说明 |
|--------|------|
| `E-BOOK-001` | style source 缺失 |
| `E-BOOK-002` | Book 成员顺序异常 |
| `E-BOOK-003` | 同步后样式漂移 |
| `E-BOOK-004` | 打开的成员文档未保存导致同步状态不一致 |
| `E-BOOK-005` | 成员文档角色冲突 |
| `E-BOOK-006` | chapter number 与文档角色不匹配 |
| `E-SEC-001` | section policy 与项目配置不一致 |
| `E-SEC-002` | 页码范围不连续 |
| `E-SEC-003` | 文档起始页奇偶不符合章首页策略 |
| `E-SEC-004` | 书籍重排后 TOC 未更新 |
| `E-TOC-001` | TOC 文档缺失 |
| `E-TOC-002` | TOC 未勾选 Include Book Documents |
| `E-TOC-003` | TOC 生成后 overset |
| `E-TOC-004` | TOC 条目样式映射错误 |
| `E-OUT-001` | Export Book To PDF 失败 |
| `E-OUT-002` | 成员文档 package 失败 |
| `E-OUT-003` | delivery manifest 缺失 |

---

### 14.13 系统提示词补充补丁（Phase 1E）

```text
补充规则：Phase 1E

1. 当项目模式为 indb_multi_document 时，书籍顺序以 Book panel order 为唯一真值。
2. style source 必须唯一，不允许多源同步。
3. 同步前优先关闭成员文档，避免出现"已更改但未保存"的同步状态。
4. chapter number 应以成员文档级元数据为主，不以正文文本猜测为主。
5. TOC 必须放在独立 TOC 文档中，并使用 Include Book Documents 生成。
6. TOC 只能从 paragraph styles 生成，不得从纯文本搜索生成。
7. 全书 PDF 输出优先使用 Export Book To PDF。
8. 源文件交付不要假设存在稳定的 Book 级一键 Package；应执行"逐成员 package + manifest"的安全协议。
9. Book 级 Preflight 必须在所有成员文档通过文档级检查后执行。
10. 任何成员文档重排、增删页或顺序变化后，都必须重新更新编号与 TOC。
```

---

### 14.14 阶段完成清单

到这一步，整个系统已经从最初的"章首页怎么排"，升级成了完整的五层：

| 层级 | 名称 | 状态 |
|------|------|------|
| 第 1 层 | 内容识别 | ✅ 识别章号、标题、副标题、题记、首段、正文、目录项 |
| 第 2 层 | 页面规则 | ✅ 章首页、空白补位页、首段页、普通正文页、运行头、页码、孤行寡行 |
| 第 3 层 | 章节规则 | ✅ 奇数页开章、正文线程连续、章节内校验与回退 |
| 第 4 层 | 文档规则 | ✅ 每章一个 `.indd`，style source 统一，TOC 文档独立，section policy 固定 |
| 第 5 层 | 全书规则 | ✅ `.indb` 管顺序、同步、编号、TOC、Preflight、输出 |

OpenClaw 从"自动排版器"变成了 **长文档协同排版代理**。

**下一步待补充**：
1. **Phase 1F：把以上全部协议收束成真正可执行的伪代码 / 状态机 / JSON Schema / Debug 决策树**
2. **实战测试：用一本真实稿件跑通 Stage B0-B7 全流程**
