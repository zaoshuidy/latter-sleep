# BookSkill V1.2 交付说明

## 版本目标

V1.2 在 V1.1 已验证的建项、知识库检索、编辑设计、图像、审核和电子样书流程之后，新增 Windows Adobe InDesign 2025 校样构建。前序 Mac 流程与数据契约保持不变。

## 新增能力

- 新增第 9 个 Skill：`build-indesign-book`。
- 使用 `InDesign.Application.2025` COM ProgID 和可复跑 JSX，不依赖 pywin32、UXP 面板或 GUI 坐标。
- 连续物理单页编译为 INDD、单页 PDF 和机器可读质量报告。
- `proof` 与 `print` 明确分离；低于 300 PPI、无真实出血或扁平图片输入不得标记为印刷级。
- 个人安装器支持 Windows `.venv\Scripts\python.exe` 路径。

## 实际验证

《失落人间》项目的 `ebook/pages-v003/` 已在 Adobe InDesign 20.4.1.4 完成真实构建：

- 14 个输入物理页。
- 14 个 InDesign 页面与 14 个链接。
- 输出 `projects/lost-human-world-cover/indesign/book-proof.indd`。
- 输出 `projects/lost-human-world-cover/indesign/book-proof.pdf`。
- 报告 `projects/lost-human-world-cover/indesign/indesign-build-report.json`。

## 当前质量边界

本次输入页为 1000 × 1448 px，放置到 145 × 210 mm 后最低有效分辨率约 175.14 PPI，且正文为扁平图像。它证明从现有套件到 InDesign 的连接、页序、保存和 PDF 导出已跑通，但不是 300 PPI 印刷成品，也不是可编辑正文排版。

下一阶段应从现有结构化正文、目录、章首页和页眉页脚 JSON/HTML 生成 InDesign 段落样式、主页、线程文本框与可编辑文字层，并补齐真实出血、色彩管理和印厂 PDF/X 预设。
