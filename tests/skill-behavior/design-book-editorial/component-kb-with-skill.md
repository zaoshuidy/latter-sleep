现在不能直接给出两个正式封面方向、完整 Prompt，也不能执行“每方向生成 4 张”。原因不是信息不足，而是封面组件知识库的人工映射门禁尚未关闭：必须先展示本轮检索到的 5 个 cover 候选，由你为每个方向选择 2—3 个参考及可借字段；我再转写为两份 `status=draft` 的 selection，完整回显其 ID、文件路径和 SHA-256；只有你按 `selection_id + SHA-256` 二次批准后，才能形成正式方向与 Prompt。本 Skill 本身不调用 `imagegen`。

这轮只使用 `cover` 记录，不会拿目录、章首页案例补位，也不会使用常见网页灵感。材料与印刷工艺不能依据图片外观推断，没有确定证据时只能标为待确认。

已接收的项目事实：书名《四时来信》；书信/日记类纪念书；主题“季节与来信”；已确认章节“第一章 春归”；成品 140 mm × 210 mm。作者、工作室、正文片段与项目图片均未提供；其中作者与工作室后续只能保留为“待确认（可编辑文字层）”，不得虚构。

## 本轮只读校验

- 正式案例索引：cover 有 10 个 `confirmed` 案例，校验通过。
- cover 组件库：`valid=true`、`status=available`、`record_count=50`、`errors=[]`。
- 检索：`query_id=QUERY-COV-FOUR-SEASONS-LETTERS-0001`，`component_type=cover`，返回 exactly 5 个候选，且对应 5 个不同的 `book_case_id`。

## 5 个封面候选

### 1. COV-CN-0004｜《我是外公外婆带大的孩子》

![COV-CN-0004](/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/cover/assets/COV-CN-0004.jpg)

- `record_id`：`COV-CN-0004`
- `book_case_id`：`BOOK-CN-0004`
- 完整 `component_profile`：`cover_scope=front`；`visual_strategy=mixed`；`composition=centered`；`title_zone=top`；`spine_relationship=not-visible`；`thumbnail_recognition=medium`
- 来源：[最美的书官网](https://beautyofbooks.cn/bookdetail?id=525)
- 本地资产：`/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/cover/assets/COV-CN-0004.jpg`
- `visual_strategy`：匹配值 `mixed`；来源为 record `component_profile`；`field_score=0.20`；可选。
- `composition`：匹配值 `centered`；来源为 record `component_profile`；`field_score=0.20`；可选。
- `title_zone`：匹配值 `top`；来源为 record `component_profile`；`field_score=0.15`；可选。
- `color`：匹配值 `白色、黑色`；来源为 record `retrieval_features.color_tags` 与本轮 `match_explanation`；`field_score=0.15`；可选。
- `material`：无匹配值；record 中没有 visibility 非 uncertain 的材料观察，本轮也明确为 `no certain indexed observation`；`field_score=0.00`；不可选，不能凭图片推断。
- `mood`：匹配值 `怀念、温柔、私密`；来源为 record `retrieval_features.mood_tags` 与本轮 `match_explanation`；`field_score=0.10`；可选。
- `cover_scope`：匹配值 `front`；来源为 record `component_profile`；`field_score=0.05`；可选。
- `book_category`：无匹配值；record 中没有 visibility 非 uncertain 的类别观察，本轮也明确为 `no certain indexed observation`；`field_score=0.00`；不可选。

### 2. COV-CN-0005｜《西影的名字叫西影》

![COV-CN-0005](/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/cover/assets/COV-CN-0005.jpg)

- `record_id`：`COV-CN-0005`
- `book_case_id`：`BOOK-CN-0005`
- 完整 `component_profile`：`cover_scope=front`；`visual_strategy=photography`；`composition=full-bleed`；`title_zone=center`；`spine_relationship=not-visible`；`thumbnail_recognition=medium`
- 来源：[最美的书官网](https://beautyofbooks.cn/bookdetail?id=527)
- 本地资产：`/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/cover/assets/COV-CN-0005.jpg`
- `visual_strategy`：匹配值 `photography`；来源为 record `component_profile`；`field_score=0.20`；可选。
- `composition`：匹配值 `full-bleed`；来源为 record `component_profile`；`field_score=0.20`；可选。
- `title_zone`：匹配值 `center`；来源为 record `component_profile`；`field_score=0.15`；可选。
- `color`：匹配值 `橙色、灰绿色`；来源为 record `retrieval_features.color_tags` 与本轮 `match_explanation`；`field_score=0.15`；可选。
- `material`：无匹配值；record 中没有 visibility 非 uncertain 的材料观察，本轮也明确为 `no certain indexed observation`；`field_score=0.00`；不可选，不能凭图片推断。
- `mood`：匹配值 `怀旧、时间感、温暖`；来源为 record `retrieval_features.mood_tags` 与本轮 `match_explanation`；`field_score=0.10`；可选。
- `cover_scope`：匹配值 `front`；来源为 record `component_profile`；`field_score=0.05`；可选。
- `book_category`：无匹配值；record 中没有 visibility 非 uncertain 的类别观察，本轮也明确为 `no certain indexed observation`；`field_score=0.00`；不可选。

### 3. COV-CN-0031｜《姑苏繁华录——苏州桃花坞木版年画特展作品集》

![COV-CN-0031](/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/cover/assets/COV-CN-0031.jpg)

- `record_id`：`COV-CN-0031`
- `book_case_id`：`BOOK-CN-0031`
- 完整 `component_profile`：`cover_scope=front`；`visual_strategy=mixed`；`composition=asymmetric`；`title_zone=top`；`spine_relationship=independent`；`thumbnail_recognition=medium`
- 来源：[BeautyOfBooks](https://beautyofbooks.cn/bookdetail?id=328)
- 本地资产：`/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/cover/assets/COV-CN-0031.jpg`
- `visual_strategy`：匹配值 `mixed`；来源为 record `component_profile`；`field_score=0.20`；可选。
- `composition`：匹配值 `asymmetric`；来源为 record `component_profile`；`field_score=0.20`；可选。
- `title_zone`：匹配值 `top`；来源为 record `component_profile`；`field_score=0.15`；可选。
- `color`：匹配值 `浅灰`；来源为 record `retrieval_features.color_tags` 与本轮 `match_explanation`；`field_score=0.15`；可选。
- `material`：无匹配值；record 中没有 visibility 非 uncertain 的材料观察，本轮也明确为 `no certain indexed observation`；`field_score=0.00`；不可选，不能把可见构形推断为材料或工艺。
- `mood`：匹配值 `克制、档案感`；来源为 record `retrieval_features.mood_tags` 与本轮 `match_explanation`；`field_score=0.10`；可选。
- `cover_scope`：匹配值 `front`；来源为 record `component_profile`；`field_score=0.05`；可选。
- `book_category`：无匹配值；record 中没有 visibility 非 uncertain 的类别观察，本轮也明确为 `no certain indexed observation`；`field_score=0.00`；不可选。

### 4. COV-CN-0036｜《乡村与木刻》

![COV-CN-0036](/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/cover/assets/COV-CN-0036.jpg)

- `record_id`：`COV-CN-0036`
- `book_case_id`：`BOOK-CN-0036`
- 完整 `component_profile`：`cover_scope=front`；`visual_strategy=mixed`；`composition=asymmetric`；`title_zone=vertical`；`spine_relationship=not-visible`；`thumbnail_recognition=strong`
- 来源：[BeautyOfBooks](https://beautyofbooks.cn/bookdetail?id=468)
- 本地资产：`/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/cover/assets/COV-CN-0036.jpg`
- `visual_strategy`：匹配值 `mixed`；来源为 record `component_profile`；`field_score=0.20`；可选。
- `composition`：匹配值 `asymmetric`；来源为 record `component_profile`；`field_score=0.20`；可选。
- `title_zone`：匹配值 `vertical`；来源为 record `component_profile`；`field_score=0.15`；可选。
- `color`：匹配值 `米白、黑色`；来源为 record `retrieval_features.color_tags` 与本轮 `match_explanation`；`field_score=0.15`；可选。
- `material`：无匹配值；record 只确认“木刻风”视觉效果，没有 visibility 非 uncertain 的实际材料或版画工艺观察；本轮为 `no certain indexed observation`；`field_score=0.00`；不可选，不能由图像风格推断工艺。
- `mood`：匹配值 `纪实`；来源为 record `retrieval_features.mood_tags` 与本轮 `match_explanation`；`field_score=0.10`；可选。
- `cover_scope`：匹配值 `front`；来源为 record `component_profile`；`field_score=0.05`；可选。
- `book_category`：无匹配值；record 中没有 visibility 非 uncertain 的类别观察，本轮也明确为 `no certain indexed observation`；`field_score=0.00`；不可选。

### 5. COV-CN-0047｜《一群马 满天星》

![COV-CN-0047](/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/cover/assets/COV-CN-0047.jpg)

- `record_id`：`COV-CN-0047`
- `book_case_id`：`BOOK-CN-0047`
- 完整 `component_profile`：`cover_scope=front`；`visual_strategy=mixed`；`composition=asymmetric`；`title_zone=vertical`；`spine_relationship=not-visible`；`thumbnail_recognition=strong`
- 来源：[BeautyOfBooks](https://beautyofbooks.cn/bookdetail?id=476)
- 本地资产：`/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/cover/assets/COV-CN-0047.jpg`
- `visual_strategy`：匹配值 `mixed`；来源为 record `component_profile`；`field_score=0.20`；可选。
- `composition`：匹配值 `asymmetric`；来源为 record `component_profile`；`field_score=0.20`；可选。
- `title_zone`：匹配值 `vertical`；来源为 record `component_profile`；`field_score=0.15`；可选。
- `color`：匹配值 `灰色、白色、黑色`；来源为 record `retrieval_features.color_tags` 与本轮 `match_explanation`；`field_score=0.15`；可选。
- `material`：无匹配值；record 中没有 visibility 非 uncertain 的材料观察，本轮也明确为 `no certain indexed observation`；`field_score=0.00`；不可选，不能凭图片推断。
- `mood`：匹配值 `寂静、沉思`；来源为 record `retrieval_features.mood_tags` 与本轮 `match_explanation`；`field_score=0.10`；可选。
- `cover_scope`：匹配值 `front`；来源为 record `component_profile`；`field_score=0.05`；可选。
- `book_category`：无匹配值；record 中没有 visibility 非 uncertain 的类别观察，本轮也明确为 `no certain indexed observation`；`field_score=0.00`；不可选。

## 请先完成简洁映射

请为方向 A、方向 B 各选择 2—3 个不同的 `record_id`，并只从对应候选中 `field_score > 0` 的字段选择要借用的关系，同时写明调整意图。图片只作内部参考；不能复制原书文字、具体图形、原图像内容、原色值或单一案例的独特组合。

可直接这样回复：

```text
方向 A：
- COV-CN-____：借 visual_strategy / composition / ...；调整为……
- COV-CN-____：借 title_zone / mood / ...；调整为……

方向 B：
- COV-CN-____：借 color / cover_scope / ...；调整为……
- COV-CN-____：借 composition / title_zone / ...；调整为……
```

收到后，我会把你的简洁映射转写为两份完整、可校验的 `status=draft` selection，逐份完整回显并报告 `selection_id + SHA-256`，然后停止等待二次批准。在此之前不会输出正式两方向、Prompt 或生成数量，也不会调用生图工具。
