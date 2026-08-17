阶段一已完成。两份 selection 均保持 `status=draft`，已通过 production schema 与 `validate_selection_prompt_safety` 预检；尚未批准，未调用 `imagegen`。

- 方向 A
  - selection ID：`SEL-COVER-DIR-A-20260812-R2`
  - 绝对路径：`/tmp/task16-round2-fresh/reference-selection-A.json`
  - SHA-256：`10c13853fb7f3eba32c965c61424f7c12379102451702910474d37ed09b48f17`

```json
{
  "schema_version": "1.0",
  "selection_id": "SEL-COVER-DIR-A-20260812-R2",
  "query_id": "QUERY-COV-FOUR-SEASONS-LETTERS-0001",
  "component_type": "cover",
  "selected_references": [
    {
      "record_id": "COV-CN-0031",
      "include_fields": [
        "composition",
        "title_zone",
        "color"
      ],
      "existing_baseline": "本项目已有季节递进与私人通信主题，封面基线以项目自身内容和项目书名长度为边界。",
      "adjustment_instruction": "仅转译非对称构图、上部信息区与浅灰色彩关系，用本项目自身季节与通信主题重新组织案例内容。",
      "preserve_elements": [
        "本项目自身的季节递进主题",
        "本项目自身的私人通信主题",
        "项目书名长度对应的留白需求"
      ],
      "required_changes": [
        "以本项目自身内容替换参考案例的内容组织",
        "改变参考案例的具体比例、间距与层级组合",
        "使该参考只承担所选字段关系而不主导完整封面"
      ],
      "exclude_fields": [
        "原书任何可读文字、书名、作者与机构标记",
        "原书具体图形、原图像内容与可识别细节",
        "原书精确色值与单一案例的独特组合",
        "任何项目最终可读文字或文字像素内容",
        "未选择的 visual_strategy、cover_scope、mood、material 与 book_category"
      ]
    },
    {
      "record_id": "COV-CN-0036",
      "include_fields": [
        "visual_strategy",
        "composition",
        "title_zone"
      ],
      "existing_baseline": "本项目以季节变化和往来通信为内容主线，并保留项目自身的叙事节奏与信息层级。",
      "adjustment_instruction": "借用混合视觉策略、非对称构图与纵向信息区关系，以本项目自身内容重新设计案例结构。",
      "preserve_elements": [
        "本项目自身的季节变化主线",
        "本项目自身的往来通信主题",
        "本项目既有的叙事节奏"
      ],
      "required_changes": [
        "重组混合视觉元素的比例与相互位置",
        "按本项目自身内容建立新的视觉重心",
        "避免沿用参考案例的完整构图路径"
      ],
      "exclude_fields": [
        "原书任何可读文字、书名、作者与机构标记",
        "原书具体图形、原图像内容与可识别细节",
        "原书精确色值与单一案例的独特组合",
        "任何项目最终可读文字或文字像素内容",
        "未选择的 color、cover_scope、mood、material 与 book_category"
      ]
    },
    {
      "record_id": "COV-CN-0047",
      "include_fields": [
        "composition",
        "title_zone",
        "color"
      ],
      "existing_baseline": "本项目维持季节与私人通信交织的主题，整体基线服从项目自身内容和篇章节奏。",
      "adjustment_instruction": "借用非对称构图、纵向信息区与灰白黑色彩关系，以本项目自身季节线索重新设计案例内容。",
      "preserve_elements": [
        "本项目自身的季节线索",
        "本项目自身的私人通信语义",
        "本项目内容形成的篇章节奏"
      ],
      "required_changes": [
        "重新分配构图重心与纵向区域尺度",
        "按本项目自身内容改造色彩占比与明度关系",
        "与其他已选参考共同形成新的字段组合"
      ],
      "exclude_fields": [
        "原书任何可读文字、书名、作者与机构标记",
        "原书具体图形、原图像内容与可识别细节",
        "原书精确色值与单一案例的独特组合",
        "任何项目最终可读文字或文字像素内容",
        "未选择的 visual_strategy、cover_scope、mood、material 与 book_category"
      ]
    }
  ],
  "status": "draft"
}
```

- 方向 B
  - selection ID：`SEL-COVER-DIR-B-20260812-R2`
  - 绝对路径：`/tmp/task16-round2-fresh/reference-selection-B.json`
  - SHA-256：`41b8f029a982dd59c5d77d5f9fcb615210ac197548f861a54aae1a879f642821`

```json
{
  "schema_version": "1.0",
  "selection_id": "SEL-COVER-DIR-B-20260812-R2",
  "query_id": "QUERY-COV-FOUR-SEASONS-LETTERS-0001",
  "component_type": "cover",
  "selected_references": [
    {
      "record_id": "COV-CN-0004",
      "include_fields": [
        "composition",
        "color",
        "title_zone"
      ],
      "existing_baseline": "本项目以季节递进和私人通信为核心语义，封面基线由项目自身内容与项目书名长度决定。",
      "adjustment_instruction": "借用居中构图、黑白色彩关系与上部信息区关系，以本项目自身季节与通信主题重新设计案例内容。",
      "preserve_elements": [
        "本项目自身的季节递进语义",
        "本项目自身的私人通信语义",
        "项目书名长度所需的版面弹性"
      ],
      "required_changes": [
        "以本项目自身内容重建居中结构的层级",
        "调整黑白关系的面积、节奏与留白",
        "改变参考案例的具体比例与独特组合"
      ],
      "exclude_fields": [
        "原书任何可读文字、书名、作者与机构标记",
        "原书具体图形、原图像内容与可识别细节",
        "原书精确色值与单一案例的独特组合",
        "任何项目最终可读文字或文字像素内容",
        "未选择的 visual_strategy、cover_scope、mood、material 与 book_category"
      ]
    },
    {
      "record_id": "COV-CN-0005",
      "include_fields": [
        "visual_strategy",
        "composition",
        "color"
      ],
      "existing_baseline": "本项目保留季节轮转与往来通信主题，并以项目自身内容建立温度和时间层次。",
      "adjustment_instruction": "借用摄影视觉策略、满版构图与橙灰绿色彩关系，以本项目自身季节线索重新设计案例内容。",
      "preserve_elements": [
        "本项目自身的季节轮转主题",
        "本项目自身的往来通信主题",
        "本项目内容形成的时间层次"
      ],
      "required_changes": [
        "用本项目自身内容替换参考图像叙事",
        "重设满版构图中的主体尺度与空间关系",
        "重新平衡色彩占比并避免复刻参考案例"
      ],
      "exclude_fields": [
        "原书任何可读文字、书名、作者与机构标记",
        "原书具体图形、原照片内容与可识别细节",
        "原书精确色值与单一案例的独特组合",
        "任何项目最终可读文字或文字像素内容",
        "未选择的 title_zone、cover_scope、mood、material 与 book_category"
      ]
    }
  ],
  "status": "draft"
}
```

验证结果：两份文件均通过 `book-component-reference-selection` schema；两份文件结合当前项目配置均通过 `validate_selection_prompt_safety`。最终文字仅保留为后续 metadata／可编辑 overlay 边界，本轮没有生成正式方向或图像。

如需进入阶段二，请明确批准以下两组 ID + SHA：

- `SEL-COVER-DIR-A-20260812-R2` + `10c13853fb7f3eba32c965c61424f7c12379102451702910474d37ed09b48f17`
- `SEL-COVER-DIR-B-20260812-R2` + `41b8f029a982dd59c5d77d5f9fcb615210ac197548f861a54aae1a879f642821`

<oai-mem-citation>
<citation_entries>
MEMORY.md:194-205|note=[kept book text editable and separated editorial design from image generation]
</citation_entries>
<rollout_ids>
019fd761-7a91-7941-b5b5-3b3037a3b9a9
</rollout_ids>
</oai-mem-citation>
