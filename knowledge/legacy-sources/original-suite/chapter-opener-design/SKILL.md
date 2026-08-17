---
name: chapter-opener-design
description: "章首页一键预览生成器：为中国文艺书籍生成章节开篇页预览效果（PNG/HTML）。用户输入章节内容，1 分钟内生成可直接查看的章首页视觉预览。适用于中国文艺书籍章首页设计。"
---

# Chapter Opener Design Skill

> 章首页一键预览生成 V4.0
> 适用：中国文艺书籍章首页（Chapter Opener）即时预览
> 更新：2026-04-29
>
> **范围声明**：本技能只负责生成章首页的「预览效果」，即让用户在屏幕上直接看到章节开篇的视觉样子。
> 后续的 InDesign 排版、目录生成、正文页处理、印前检查等流程，由独立的书籍排版工作流负责，不在本技能范围内。

---

## 1. 技能定位

**一句话**：用户给一段章节内容，Claude 在 1 分钟内生成一张可直接查看的章首页预览图（PNG/HTML）。

**与完整书籍排版的边界**：

| 本技能负责（预览层） | 后续排版工作流负责（印刷层） |
|---------------------|---------------------------|
| 单章首页视觉效果预览 | 全书 InDesign 结构化排版 |
| 模板推荐与版式标注 | 目录、正文页、补位页处理 |
| 用户确认设计方向 | PDF/X-4 终稿输出、印前检查 |
| 截图/浏览器预览 | 字体嵌入、CMYK 转换、出血设置 |

**为什么分开**：
- 设计师（和用户）需要先「看到效果」才能决策
- 预览生成快（秒级），排版生成慢（分钟级）
- 预览不依赖 InDesign，任何设备都能跑

---

## 2. 执行纪律（铁律）

```
[章首页预览铁律]
1. 禁止任何章节标题使用系统默认黑体（推荐：思源宋体、方正清刻本悦宋）
2. 禁止高饱和色块填充（HSV S > 35%）作为背景
3. 禁止图片素材无文本意象关联
4. 禁止忽略留白呼吸感（章首页留白面积 ≥ 35%）
5. 禁止直接复制封面设计（必须是变奏关系）
6. 预览图必须标注「预览稿」水印，防止误作终稿

[纸船工作室品牌约束]
- 无 ISBN / 无定价 / 无腰封
- 章首页不出现工作室印记
- 章首页无页码
```

---

## 3. 五十一模板体系（核心资产）

章首页模板库存放于知识库：
```
D:\ob\章首页设计知识库\templates\chapter-pages\
├── _index.json          ← 总索引（51个模板清单）
├── text-only\_all.json  ← 纯文字类 17个
├── hybrid\_all.json      ← 图文结合类 17个
└── bleed\_all.json       ← 跨版图类 17个
```

### 三大类总览

| 类别 | 编号范围 | 数量 | 核心特征 | 留白范围 |
|------|---------|------|---------|---------|
| **纯文字** Text-Only | T-01 ~ T-17 | 17 | 无图，靠字体/留白/排向变化 | 35–65% |
| **图文结合** Hybrid | H-01 ~ H-17 | 17 | 图与文共存，权力关系多样 | 25–55% |
| **跨版图** Bleed | B-01 ~ B-17 | 17 | 图像出血或跨页，视觉冲击 | 10–55% |

### 纯文字类 T-01 ~ T-17（17个）

以文字为绝对主角，通过字体、字距、留白、排向变化营造章节仪式感。

| 编号 | 名称 | 留白 | 核心特征 | 适用场景 |
|------|------|------|---------|---------|
| T-01 | 竖排大字居中 | 45–55% | 最经典，竖排居中，大留白包围 | 诗集、哲学散文、东方气质 |
| T-02 | 竖排偏右 | 40–50% | 左侧大留白，非对称张力 | 现代文学、日式美学 |
| T-03 | 竖排偏左 | 40–50% | 右侧大留白，反常设计感 | 先锋文学、实验文本 |
| T-04 | 横排大字居上 | 45–55% | 标题在上，下方如湖面留白 | 国际感、现代文学、翻译作品 |
| T-05 | 横排大字居下 | 45–55% | 标题沉底，上方辽阔留白 | 回忆录、厚重感文本 |
| T-06 | 横排居中 | 50–60% | 严格对称，最稳 | 古典文学、正剧、仪式感 |
| T-07 | 章节号独立页上部 | 50–65% | 数字极大化（72px）低透明，标题在下 | 数字美学、概念书籍 |
| T-08 | 章节号独立页下部 | 50–65% | 数字在下极大化，标题在上 | 艺术书籍、反常设计 |
| T-09 | 上下分离型 | 50–60% | 号极上、题极下，中间60%+纯粹留白 | 冥想文本、东方哲学 |
| T-10 | 双层标题错落 | 40–50% | 主标题+副标题大小错落 | 复合标题、学术散文 |
| T-11 | 题跋主导型 | 45–55% | 引言比标题更醒目 | 题跋体、序言感章节 |
| T-12 | 诗行断裂型 | 50–60% | 标题像诗句分行 | 诗集、诗意散文 |
| T-13 | 活字排版感 | 35–45% | 参差错落如铅字 | 历史文本、复古感 |
| T-14 | 手札书信体 | 40–50% | 模拟私人信件排版 | 书信集、日记体 |
| T-15 | 极简网格 | 55–65% | 严格网格，无装饰，极端克制 | 极简主义、设计类书籍 |
| T-16 | 古典对开 | 40–50% | 模拟线装古籍版式 | 古籍新编、传统文化 |
| T-17 | 现代主义 | 45–55% | 极端大小对比（10px vs 48px） | 当代艺术、建筑文本 |

### 图文结合类 H-01 ~ H-17（17个）

图像与文字共享版面，通过位置、大小、层级关系建立呼吸感。

| 编号 | 名称 | 留白 | 图片占比 | 核心特征 |
|------|------|------|---------|---------|
| H-01 | 小图左上文字右下 | 35–45% | 20–30% | 对角线构图 |
| H-02 | 小图右上文字左下 | 35–45% | 20–30% | H-01镜像，反向平衡 |
| H-03 | 小图左下文字右上 | 35–45% | 20–30% | 下沉重量感 |
| H-04 | 小图右下文字左上 | 35–45% | 20–30% | H-03镜像 |
| H-05 | 圆形图环绕文字 | 40–50% | 15–25% | 圆形/椭圆，如印章月亮 |
| H-06 | 竖条图左文字右 | 30–40% | 25–35% | 左侧竖条如屏风 |
| H-07 | 竖条图右文字左 | 30–40% | 25–35% | H-06镜像 |
| H-08 | 横条图上文字下 | 35–45% | 25–35% | 顶部天窗 |
| H-09 | 横条图下文字上 | 35–45% | 25–35% | 底部地基 |
| H-10 | 图底低透明叠字 | 25–35% | 60–75% | 大图低透明（15%），文字叠印 |
| H-11 | 图文对半垂直分割 | 25–35% | 40–50% | 50/50权力对等 |
| H-12 | 图章式 | 45–55% | 10–20% | 方形小图如印章在角落 |
| H-13 | 线描白描图文字 | 40–50% | 15–25% | 淡色线描，博物志感 |
| H-14 | 照片框式 | 35–45% | 20–30% | 白边+阴影，如拍立得 |
| H-15 | 多图小网格 | 30–40% | 25–35% | 2×2小图网格 |
| H-16 | 负形留白 | 45–55% | 20–30% | 图与文字共享有机边界 |
| H-17 | 拼贴错落 | 25–35% | 30–45% | 多张图+文字块拼贴 |

### 跨版图类 B-01 ~ B-17（17个）

图像或色块出血至裁切线，或横跨对开两页。

| 编号 | 名称 | 留白 | 图片占比 | 核心特征 |
|------|------|------|---------|---------|
| B-01 | 单页全出血满版反白 | 20–30% | 100% | 最强烈，如电影海报 |
| B-02 | 单页上半出血下半文字 | 35–45% | 50–60% | 地平线分割 |
| B-03 | 单页下半出血上半文字 | 35–45% | 50–60% | 地基稳定感 |
| B-04 | 单页左半出血右半文字 | 30–40% | 50–55% | 左侧竖构图 |
| B-05 | 单页右半出血左半文字 | 30–40% | 50–55% | B-04镜像 |
| B-06 | 斜向分割出血 | 30–40% | 50–60% | 15°斜线分割 |
| B-07 | 中央留白出血 | 25–35% | 65–75% | 四周图，中央开窗 |
| B-08 | 边框出血 | 45–55% | 45–55% | 四周边缘图，中央留白 |
| B-09 | 跨页左图右文 | 25–35% | 50–55% | 对开，左页全图 |
| B-10 | 跨页右图左文 | 25–35% | 50–55% | 对开，右页全图 |
| B-11 | 跨页上半出血 | 30–40% | 55–65% | 对开上半宽幅图 |
| B-12 | 跨页中央窗式 | 20–30% | 70–80% | 对开四周图，中央大窗 |
| B-13 | 条带式跨页 | 40–50% | 20–30% | 水平条带贯穿对开 |
| B-14 | 纹理满版无图 | 35–45% | 100% | 纯肌理，无具体图像 |
| B-15 | 水墨晕染出血 | 30–45% | 80–90% | 边缘自然消散 |
| B-16 | 摄影为主文字极小 | 10–20% | 80–90% | 14px文字退到角落 |
| B-17 | 插画满版叠字 | 20–30% | 85–95% | 文字叠在插画留白处 |

---

## 4. 一键生成流程（六阶段）

### Stage 0: 信息收集（一次性）

**必须信息**（缺失则一次性询问，不问第二遍）：
- [ ] **书名**
- [ ] **章节名/章节号**（如"第一章 春归"）
- [ ] **章节正文开头 1–3 段**（用于提取情绪关键词）
- [ ] **是否有配图素材**：有 / 无 / 待定

**可选信息**（未提供则自动推断）：
- 情绪关键词（从正文提取：离别/温暖/寂静/辽阔/怀旧等）
- 开本尺寸（默认 140mm × 210mm）
- 模板偏好（如用户明确说"想要大量留白"）

**输出**: `0_config/content_blocks.json`

```json
{
  "book_title": "四时来信",
  "chapter_number": "第一章",
  "chapter_title": "春归",
  "epigraph": "（如有题跋）",
  "body_excerpt": "正文开头1-3段...",
  "emotion_tags": ["温暖", "复苏", "轻盈"],
  "has_images": false,
  "page_size": {"width_mm": 140, "height_mm": 210}
}
```

### Stage 1: 智能模板推荐（自动）

根据 `content_blocks.json` 自动计算推荐模板，**从 51 个模板中智能匹配**。

Claude 在执行时读取知识库索引：
```
D:\ob\章首页设计知识库\templates\chapter-pages\_index.json
```

**推荐算法（51模板版）**：

```python
def recommend_template_51(content_blocks):
    emotions = content_blocks.get("emotion_tags", [])
    has_images = content_blocks.get("has_images", False)
    image_count = content_blocks.get("image_count", 0)
    image_type = content_blocks.get("image_type", "")

    # 第一层：无图 → 纯文字类 T-01~T-17
    if not has_images:
        if any(e in emotions for e in ["极简", "克制", "寂静", "哲学", "诗", "冥想"]):
            return pick_from(["T-15", "T-01", "T-09", "T-12"])
        if any(e in emotions for e in ["古典", "传统", "历史", "古籍"]):
            return pick_from(["T-16", "T-13", "T-14"])
        if any(e in emotions for e in ["现代", "先锋", "实验", "观念", "建筑"]):
            return pick_from(["T-17", "T-03", "T-07"])
        if any(e in emotions for e in ["私密", "日记", "书信", "手札"]):
            return "T-14"
        if any(e in emotions for e in ["离别", "温暖", "季节", "轻盈", "日常"]):
            return pick_from(["T-04", "T-05", "T-10", "T-02"])
        if any(e in emotions for e in ["沉稳", "重量", "回忆", "厚重"]):
            return pick_from(["T-05", "T-06", "T-11"])
        return "T-01"

    # 第二层：有图 → 看图片数量和类型
    if image_count >= 3:
        return pick_from(["H-15", "H-17"])
    if image_count == 2:
        return pick_from(["H-11", "H-15"])

    if image_type in ["风景", "地平线", "天空", "远景"]:
        return pick_from(["H-08", "H-09", "B-02", "B-03", "B-13"])
    if image_type in ["人物", "肖像", "竖构图", "树木", "建筑"]:
        return pick_from(["H-06", "H-07", "B-04", "B-05"])
    if image_type in ["符号", "印章", "小物", "徽章"]:
        return pick_from(["H-05", "H-12"])
    if image_type in ["摄影", "纪实", "黑白"]:
        return pick_from(["H-14", "B-16", "H-01"])
    if image_type in ["插画", "手绘", "水彩", "儿童"]:
        return pick_from(["H-13", "B-17"])
    if image_type in ["线描", "白描", "博物", "植物", "昆虫"]:
        return "H-13"
    if image_type in ["水墨", "晕染", "宣纸", "东方"]:
        return pick_from(["B-15", "B-14"])

    # 第三层：情绪驱动（有图但类型不明）
    if any(e in emotions for e in ["冲击", "浓烈", "史诗", "力量", "震撼"]):
        return pick_from(["B-01", "B-02", "B-16", "B-07"])
    if any(e in emotions for e in ["氛围", "朦胧", "记忆", "梦境"]):
        return pick_from(["H-10", "B-14", "B-15", "B-08"])
    if any(e in emotions for e in ["温暖", "日常", "轻盈", "阳光"]):
        return pick_from(["H-01", "H-02", "H-14", "H-08"])
    if any(e in emotions for e in ["旅行", "道路", "时间", "流动"]):
        return pick_from(["B-13", "H-17", "B-06"])
    if any(e in emotions for e in ["悲伤", "离别", "秋雨", "冬天"]):
        return pick_from(["B-03", "H-09", "B-15"])
    if any(e in emotions for e in ["春天", "复苏", "绿色", "生长"]):
        return pick_from(["H-05", "H-13", "H-08"])

    # 默认 fallback
    return pick_from(["H-01", "T-01", "H-08", "T-04"])

def pick_from(candidates):
    return candidates[0]
```

**输出**: `0_config/template_recommendation.json`

```json
{
  "recommended_template": "T-01",
  "template_name": "竖排大字居中",
  "category": "text-only",
  "reason": "无配图+内敛情绪（诗/哲学），推荐最经典的竖排居中",
  "confidence": 0.88,
  "alternatives": ["T-15", "T-09"],
  "kb_path": "D:\\ob\\章首页设计知识库\\templates\\chapter-pages\\text-only\\_all.json",
  "user_override_allowed": true
}
```

**交互方式**：
- Claude 直接告知推荐结果：「根据「第一章 春归」的内容（无配图，情绪：温暖/轻盈），从 51 个模板中推荐 **T-01 竖排大字居中**，留白 45–55%。如需更换，直接回复编号（如 T-02 / H-01 / B-03），或描述偏好（如"想要有图""想要出血效果"）。」
- 用户不回复 = 默认接受推荐
- 用户回复编号（如 T-03 / H-05 / B-01）= 切换模板
- 用户回复描述（如"想要大量留白""想要图片在左上角"）= 重新匹配

### Stage 2: 内容解析与版式计算（自动）

**2a. 解析章节结构**
- chapter_number → chapter_title → chapter_subtitle → epigraph → body_first_paragraph

**2b. 计算版式参数**

根据模板类型计算精确坐标（以 140mm×210mm 为例）：

```json
{
  "template": "A",
  "layout": {
    "page_size": {"width_mm": 140, "height_mm": 210},
    "safe_margin_mm": 15,
    "title_zone": {"x": 15, "y": 60, "w": 110, "h": 90},
    "chapter_number": {
      "text": "第一章",
      "font": "Source Han Serif Heavy",
      "size_pt": 14,
      "x_mm": 70,
      "y_mm": 75,
      "align": "center"
    },
    "chapter_title": {
      "text": "春归",
      "font": "Source Han Serif Heavy",
      "size_pt": 28,
      "x_mm": 70,
      "y_mm": 100,
      "align": "center"
    },
    "epigraph": {
      "text": "",
      "font": "Source Han Serif Light",
      "size_pt": 9,
      "x_mm": 70,
      "y_mm": 140,
      "align": "center"
    }
  }
}
```

**输出**: `2_work/layout_spec.json`

### Stage 3: 高保真预览生成（核心）

**生成 HTML 文件**到桌面固定路径：
```
C:\Users\yang\Desktop\章首页预览\{书名}_{章节号}_preview.html
```

**HTML 必须做到**：
1. **真实比例**：按 140mm×210mm 的精确比例渲染（可用 CSS `aspect-ratio` 或固定像素）
2. **真实字体**：调用 Google Fonts 的 Noto Serif SC（思源宋体 Web 版）
3. **真实留白**：留白比例严格匹配模板规格
4. **水印覆盖**：半透明「预览稿 · 非印刷版本」斜向水印
5. **占位标记**：如有图片位，用虚线框 + 标签标注

**CSS 核心参数（模板 A 示例）**：

```css
.page {
  width: 397px;   /* 140mm ≈ 397px @ 72dpi */
  height: 595px;  /* 210mm ≈ 595px @ 72dpi */
  background: #FAF8F5;
  position: relative;
  margin: 0 auto;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}

.chapter-number {
  font-family: "Noto Serif SC", serif;
  font-weight: 700;
  font-size: 14px;
  color: #3A3A3A;
  letter-spacing: 0.3em;
  position: absolute;
  top: 25%;       /* ~60mm from top */
  left: 50%;
  transform: translateX(-50%);
}

.chapter-title {
  font-family: "Noto Serif SC", serif;
  font-weight: 700;
  font-size: 36px;
  color: #2C2C2C;
  letter-spacing: 0.15em;
  position: absolute;
  top: 38%;       /* ~100mm from top */
  left: 50%;
  transform: translateX(-50%);
}

.watermark {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-30deg);
  font-size: 24px;
  color: rgba(200, 200, 200, 0.35);
  white-space: nowrap;
  pointer-events: none;
}
```

**模板参数读取方式**：

生成 HTML 时，Claude 读取对应模板的 JSON 规格文件获取 CSS 参数：

```
纯文字类: D:\ob\章首页设计知识库\templates\chapter-pages\text-only\_all.json
图文结合类: D:\ob\章首页设计知识库\templates\chapter-pages\hybrid\_all.json
跨版图类: D:\ob\章首页设计知识库\templates\chapter-pages\bleed\_all.json
```

每个模板 JSON 包含完整的 `css_params` 对象，定义：
- `writing_mode`: horizontal-tb / vertical-rl
- `bg_color`: 背景色
- `title_color` / `subtitle_color`: 文字色
- `title_size` / `number_size`: 字号
- `image_position` / `image_width` / `image_height`: 图片区域（如适用）
- `text_align` / `text_margin_top`: 文字定位
- `watermark`: 水印样式

**常见背景色速查**：
| 色值 | 适用模板 | 气质 |
|------|---------|------|
| `#FAF8F5` | 大多数纯文字类 | 温暖纸感 |
| `#FFFFFF` | 现代/图文类 | 干净明亮 |
| `#F5F0E8` | 古典/手札类 | 古纸质感 |
| `#1A1A1A` | 出血满版反白 | 深沉力量 |
| `#E8E0D5` | 色块/肌理类 | 低饱和温暖 |
| `#F0EBE3` | 复古/活字类 | 做旧纸感 |

**输出**: `3_preview/{章节名}_preview.html`

### Stage 4: 截图/导出（自动）

Claude 使用 gstack `/browse` 或 Playwright MCP 打开生成的 HTML，截图保存为 PNG：

```
C:\Users\yang\Desktop\章首页预览\{书名}_{章节号}_preview.png
```

截图后关闭浏览器，将 PNG 直接展示给用户。

**输出**: `3_preview/{章节名}_preview.png`

### Stage 5: 微调与确认（可选交互）

**默认**：用户看到预览图，满意即结束。

**微调指令**（用户可任选）：
- 「换模板 T-03」→ 返回 Stage 2，读取 T-03 JSON 重新计算版式 → 重新生成预览
- 「换成有图的」→ 从 hybrid 类重新匹配推荐 → 重新生成预览
- 「标题再大一点」→ 调整 `title_size` → 重新生成预览
- 「留白再多一点」→ 调整 `title_top` 或 `margin` → 重新生成预览
- 「换成竖排」→ 切换 writing-mode → 重新生成预览

**每次微调 = 5 秒内重新生成预览图**，无需任何外部工具。

### Stage 6: 输出交付物清单

一键生成结束后，输出以下文件：

```
C:\Users\yang\Desktop\章首页预览\{书名}_{章节号}\
├── 0_config/
│   ├── content_blocks.json
│   └── template_recommendation.json
├── 2_work/
│   └── layout_spec.json
└── 3_preview/
    ├── {章节名}_preview.html    ← 高保真网页预览
    └── {章节名}_preview.png     ← 截图文件（给用户看）
```

---

## 5. 目录结构（简化版）

```
C:\Users\yang\Desktop\章首页预览\{书名}_{章节号}\
├── 0_config/              # 解析与推荐配置
│   ├── content_blocks.json
│   └── template_recommendation.json
├── 2_work/                # 版式计算
│   └── layout_spec.json
└── 3_preview/             # 预览输出
    ├── {章节名}_preview.html
    └── {章节名}_preview.png
```

> 注：`1_raw/`、`4_final/`、`5_report/` 不在本技能范围内，归后续排版工作流。

---

## 6. 一键生成性能指标

| 步骤 | 耗时 |
|------|------|
| Stage 0 信息收集 | 用户输入时间 |
| Stage 1 模板推荐 | < 1 秒（纯计算） |
| Stage 2 版式计算 | < 1 秒（纯计算） |
| Stage 3 HTML 生成 | < 2 秒（文件写入） |
| Stage 4 截图 | 3–5 秒（浏览器打开+截图） |
| **总计** | **~10 秒**（不含用户输入） |

---

## 7. 错误码速查

| 错误码 | 说明 | 修复策略 |
|--------|------|---------|
| E-SKILL-001 | skill 读取失败 | 检查路径，确认 skill 存在 |
| E-PARSE-001 | 正文解析失败 | 提示用户提供结构化文本 |
| E-TPL-001 | 模板推荐置信度过低 | 列出所有 5 个模板让用户选 |
| E-LAYOUT-001 | 标题字数超限 | 建议拆分标题或缩小字号 |
| E-HTML-001 | HTML 生成失败 | 检查输出路径可写性 |
| E-SCREEN-001 | 浏览器截图失败 | 降级为只输出 HTML，让用户手动打开 |

---

## 附录 A: HTML 预览模板

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>章首页预览 - {书名} · {章节名}</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #e8e8e8;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 40px;
            font-family: "Noto Serif SC", "SimSun", serif;
        }
        .page-wrapper {
            display: flex;
            gap: 40px;
            align-items: flex-start;
        }
        .page {
            width: 397px;      /* 140mm @ 72dpi */
            height: 595px;     /* 210mm @ 72dpi */
            background: {bg_color};
            position: relative;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        /* 图片占位区（模板 B/C/D 用） */
        .image-placeholder {
            position: absolute;
            border: 2px dashed #ccc;
            background: repeating-linear-gradient(
                45deg,
                transparent,
                transparent 10px,
                rgba(200,200,200,0.2) 10px,
                rgba(200,200,200,0.2) 20px
            );
            display: flex;
            align-items: center;
            justify-content: center;
            color: #999;
            font-size: 12px;
        }
        /* 文字元素 */
        .chapter-number {
            position: absolute;
            font-weight: 600;
            font-size: {number_size}px;
            color: {number_color};
            letter-spacing: 0.3em;
            left: 50%;
            transform: translateX(-50%);
            top: {number_y}%;
        }
        .chapter-title {
            position: absolute;
            font-weight: 700;
            font-size: {title_size}px;
            color: {title_color};
            letter-spacing: 0.15em;
            left: 50%;
            transform: translateX(-50%);
            top: {title_y}%;
            text-align: center;
            line-height: 1.4;
        }
        .epigraph {
            position: absolute;
            font-weight: 300;
            font-size: {epigraph_size}px;
            color: {epigraph_color};
            left: 50%;
            transform: translateX(-50%);
            top: {epigraph_y}%;
            text-align: center;
            font-style: italic;
            max-width: 70%;
            line-height: 1.8;
        }
        /* 水印 */
        .watermark {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-25deg);
            font-size: 22px;
            color: rgba(180, 180, 180, 0.3);
            white-space: nowrap;
            pointer-events: none;
            font-weight: 400;
            letter-spacing: 0.2em;
        }
        /* 信息面板 */
        .info-panel {
            width: 280px;
            background: white;
            border-radius: 8px;
            padding: 24px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
        }
        .info-panel h3 {
            font-size: 16px;
            margin-bottom: 16px;
            color: #333;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-size: 13px;
        }
        .info-label { color: #888; }
        .info-value { color: #333; font-weight: 500; }
        .tag {
            display: inline-block;
            background: #f0f0f0;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 12px;
            margin-right: 6px;
        }
    </style>
</head>
<body>
    <div class="page-wrapper">
        <div class="page">
            <!-- 图片占位（根据模板动态插入） -->
            <div class="watermark">预览稿 · 非印刷版本</div>
            <div class="chapter-number">{章节号}</div>
            <div class="chapter-title">{章节名}</div>
            <div class="epigraph">{题跋}</div>
        </div>
        <div class="info-panel">
            <h3>章首页规格</h3>
            <div class="info-row"><span class="info-label">模板</span><span class="info-value">{模板名}</span></div>
            <div class="info-row"><span class="info-label">留白</span><span class="info-value">{留白比例}</span></div>
            <div class="info-row"><span class="info-label">字体</span><span class="info-value">{字体名}</span></div>
            <div class="info-row"><span class="info-label">开本</span><span class="info-value">{开本}</span></div>
            <div class="info-row"><span class="info-label">情绪</span><span>{情绪标签}</span></div>
        </div>
    </div>
</body>
</html>
```

---

## 附录 B: 模板 CSS 变量对照表

生成 HTML 时，根据模板类型填充以下变量：

| 变量 | A 纯文字 | B 图文 | C 符号 | D 满版 | E 色块 |
|------|---------|--------|--------|--------|--------|
| `bg_color` | `#FAF8F5` | `#FFFFFF` | `#FAF8F5` | `#1A1A1A` | `#E8E0D5` |
| `number_color` | `#3A3A3A` | `#3A3A3A` | `#3A3A3A` | `#E0E0E0` | `#4A4A4A` |
| `title_color` | `#2C2C2C` | `#2C2C2C` | `#2C2C2C` | `#FFFFFF` | `#3A3A3A` |
| `epigraph_color` | `#5A5A5A` | `#5A5A5A` | `#5A5A5A` | `#C0C0C0` | `#6A6A6A` |
| `number_size` | 14 | 14 | 14 | 14 | 14 |
| `title_size` | 32 | 28 | 30 | 36 | 28 |
| `epigraph_size` | 10 | 10 | 10 | 10 | 10 |
| `number_y` | 22% | 55% | 20% | 65% | 22% |
| `title_y` | 32% | 68% | 35% | 78% | 35% |
| `epigraph_y` | 55% | 85% | 58% | 90% | 58% |
