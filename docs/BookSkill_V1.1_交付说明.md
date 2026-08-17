# BookSkill V1.1 交付说明

## 背景

V1.1 把《失落人间》测试项目中已经实际完成并由人工认可的图书生产流程沉淀为可复用 Skill。重点不是增加更多步骤，而是保留能稳定产生成品的最短路径。

## 适用用户

个人使用的中文图书生产者，处理模板书、文学图书和人生纪念书的封面、目录、章首页、正文、页眉页脚及电子样书。

## 已沉淀的成功流程

1. 先明确图书类别、真实文字和物理规格。
2. 组件设计从知识库检索真实案例，只借用经人工选定的构图、留白、题名区等字段，不复制整套案例。
3. 封面、目录、章首页和正文分别完成可视化确认；行业已有稳定规则的正文字号、行距、版心、页码位置直接采用，不重复发明。
4. 已批准页面导出为统一尺寸的物理单页 PNG，严格保持奇偶页、空白补位和封面顺序。
5. 电子样书默认使用 StPageFlip 2.0.7 Canvas 图片模式：图片预解码、620 ms 翻页、较轻阴影、HiDPI 2x 画布。
6. 搜索使用外置文字索引，不在动画页叠加透明文字；引擎失败时按顺序显示图片。
7. 新版另存并保留上一版，离线验证后再交付。

## 两种翻页模式

- **批准图片页**：优先视觉一致、清晰和流畅，使用 `loadFromImages` 与 Retina 适配器。
- **HTML 文字页**：优先文字可选、可搜索和硬封壳语义，使用 `loadFromHTML`。

两者不在同一物理页混用。

## 主要位置

- 路由：`skills/book-production-router/`
- 图书编辑设计：`skills/design-book-editorial/`
- 图片生产：`skills/create-book-images/`
- 电子样书：`skills/build-book-flipbook/`
- 翻页高清模式：`skills/build-book-flipbook/references/approved-png-canvas-mode.md`
- 组件知识库：`knowledge/book-component-libraries/`
- 可运行样例：`projects/lost-human-world-cover/`
- 个人安装：`python scripts/install_personal.py --replace`

## 验收标准

- Skill 与知识库校验通过。
- 《失落人间》电子样书 14 个物理页面顺序正确。
- 批准 PNG 不被 CSS 再绘制或覆盖。
- Retina Canvas 最大 2x，翻页无重复、空白闪烁或明显卡顿。
- 断网可用，并保留顺序图片回退。
- 发布 ZIP 可解压且 SHA-256 与校验文件一致。

## 当前边界

- 本版不执行 InDesign 排版。
- 本版不包含公开网页前端或云端服务。
- 知识库案例仅供内部参考；公开展示不等于获得复制、改编或商业再发行授权。
