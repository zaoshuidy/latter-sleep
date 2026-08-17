## 当前结论

现在不能直接给出《四时来信》的两个正式封面方向，也不能用常见网页灵感、目录案例或章首页案例补位。封面必须只使用 `component_type=cover` 的本地组件知识库；在本轮人工选择并批准 reference mapping 前，我不会替你选择参考、命名正式方向、输出 Prompt、指定生成数量或进入生图。

已完成的只读门禁如下：

- 正式案例索引：封面有 10 个 `confirmed` 案例，达到最低要求。
- 封面组件库：`valid=true`、`status=available`、50 条记录、50 本不同书、`errors=[]`。
- 精确检索：`status=available`，返回恰好 5 个候选，分别来自 5 个不同 `book_case_id`。
- 项目事实：书名为《四时来信》，类型为书信/日记类纪念书，主题为“季节与来信”，已确认章节为“第一章 春归”；旧样例没有正文段落，也没有项目图片，相关内容保持“待确认”，不补造。

## 本轮封面候选

以下图片均为本地知识库中的真实资产，只用于内部参考。后续只能借用你明确批准的字段关系，不能复制原书文字、具体图形、原照片、原色值或任何单一案例的独特组合。

### 1.《我是外公外婆带大的孩子》

![《我是外公外婆带大的孩子》封面候选](/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/cover/assets/COV-CN-0004.jpg)

- `record_id`: `COV-CN-0004`
- `book_case_id`: `BOOK-CN-0004`
- `component_profile`: `cover_scope=front`；`visual_strategy=mixed`；`composition=centered`；`title_zone=top`；`spine_relationship=not-visible`；`thumbnail_recognition=medium`
- 来源：[最美的书官网](https://beautyofbooks.cn/bookdetail?id=525)
- 本地资产：`/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/cover/assets/COV-CN-0004.jpg`

### 2.《西影的名字叫西影》

![《西影的名字叫西影》封面候选](/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/cover/assets/COV-CN-0005.jpg)

- `record_id`: `COV-CN-0005`
- `book_case_id`: `BOOK-CN-0005`
- `component_profile`: `cover_scope=front`；`visual_strategy=photography`；`composition=full-bleed`；`title_zone=center`；`spine_relationship=not-visible`；`thumbnail_recognition=medium`
- 来源：[最美的书官网](https://beautyofbooks.cn/bookdetail?id=527)
- 本地资产：`/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/cover/assets/COV-CN-0005.jpg`

### 3.《姑苏繁华录——苏州桃花坞木版年画特展作品集》

![《姑苏繁华录——苏州桃花坞木版年画特展作品集》封面候选](/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/cover/assets/COV-CN-0031.jpg)

- `record_id`: `COV-CN-0031`
- `book_case_id`: `BOOK-CN-0031`
- `component_profile`: `cover_scope=front`；`visual_strategy=mixed`；`composition=asymmetric`；`title_zone=top`；`spine_relationship=independent`；`thumbnail_recognition=medium`
- 来源：[最美的书官网](https://beautyofbooks.cn/bookdetail?id=328)
- 本地资产：`/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/cover/assets/COV-CN-0031.jpg`

### 4.《乡村与木刻》

![《乡村与木刻》封面候选](/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/cover/assets/COV-CN-0036.jpg)

- `record_id`: `COV-CN-0036`
- `book_case_id`: `BOOK-CN-0036`
- `component_profile`: `cover_scope=front`；`visual_strategy=mixed`；`composition=asymmetric`；`title_zone=vertical`；`spine_relationship=not-visible`；`thumbnail_recognition=strong`
- 来源：[最美的书官网](https://beautyofbooks.cn/bookdetail?id=468)
- 本地资产：`/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/cover/assets/COV-CN-0036.jpg`

### 5.《一群马 满天星》

![《一群马 满天星》封面候选](/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/cover/assets/COV-CN-0047.jpg)

- `record_id`: `COV-CN-0047`
- `book_case_id`: `BOOK-CN-0047`
- `component_profile`: `cover_scope=front`；`visual_strategy=mixed`；`composition=asymmetric`；`title_zone=vertical`；`spine_relationship=not-visible`；`thumbnail_recognition=strong`
- 来源：[最美的书官网](https://beautyofbooks.cn/bookdetail?id=476)
- 本地资产：`/Users/edy/Desktop/book/book-production-skills-v1/knowledge/book-component-libraries/cover/assets/COV-CN-0047.jpg`

## 需要你完成的人工选择

请为“方向 A”和“方向 B”各选 2—3 个 `record_id`。两个方向可以共享候选，但每个方向都必须明确选择，不接受“你看着办”或自动代选。请按下面格式回复；`include_fields` 只能从 `visual_strategy`、`composition`、`title_zone`、`color`、`material`、`mood`、`cover_scope`、`book_category` 中选。

```yaml
方向 A:
  - record_id: COV-CN-____
    include_fields: [____]
    existing_baseline: 四时来信；季节与来信；第一章 春归；140mm × 210mm
    adjustment_instruction: ____
    preserve_elements: [____]
    required_changes: [____]
    exclude_fields: [原书文字, 具体图形, 原图像内容, 原色值, 单一案例独特组合]
  - record_id: COV-CN-____
    include_fields: [____]
    existing_baseline: 四时来信；季节与来信；第一章 春归；140mm × 210mm
    adjustment_instruction: ____
    preserve_elements: [____]
    required_changes: [____]
    exclude_fields: [原书文字, 具体图形, 原图像内容, 原色值, 单一案例独特组合]

方向 B:
  - record_id: COV-CN-____
    include_fields: [____]
    existing_baseline: 四时来信；季节与来信；第一章 春归；140mm × 210mm
    adjustment_instruction: ____
    preserve_elements: [____]
    required_changes: [____]
    exclude_fields: [原书文字, 具体图形, 原图像内容, 原色值, 单一案例独特组合]
  - record_id: COV-CN-____
    include_fields: [____]
    existing_baseline: 四时来信；季节与来信；第一章 春归；140mm × 210mm
    adjustment_instruction: ____
    preserve_elements: [____]
    required_changes: [____]
    exclude_fields: [原书文字, 具体图形, 原图像内容, 原色值, 单一案例独特组合]

批准状态: 批准 / 退回修改
```

## 选择通过后的执行流程与验收

收到选择后，我会先校验每个方向是否有 2—3 条真实记录、字段映射是否完整以及批准状态是否为 `approved`。门禁通过后，才会基于同一组项目事实形成两个正式封面方向，并分别输出可执行的设计概念、设计基因和标准化提示词字段；书名、作者和工作室标记作为可编辑文字层处理，背景图不得包含可读文字。本 Skill 只负责设计方案，不调用 `imagegen`。

本轮停在“人工 reference mapping 待批准”。在你完成上述选择前，不存在合规的完整双方向方案。
