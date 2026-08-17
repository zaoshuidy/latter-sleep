---
name: build-indesign-book
description: Use when an approved book project must be compiled into Adobe InDesign 2025 on Windows and exported as an INDD document plus a proof or print PDF through the local COM bridge.
---

# 构建 InDesign 成书

这是已批准页面进入桌面出版软件的生产阶段。它只消费前序 Skill 已确认的物理单页，不重新设计页面、不修改正文，也不绕过人工审核。

## 输入门槛

- 页面顺序、奇偶页、空白补位、成品尺寸和项目 ID 已确定。
- 所有输入页面来自同一批准版本，文件名使用连续的两位数字前缀：`00-...`、`01-...`。
- `proof` 模式可用于连接验证和视觉校样。
- `print` 模式要求页面有效分辨率至少 300 PPI，并具有真实印刷出血；不满足时必须阻断，不能只修改元数据冒充印刷级文件。

## Windows 运行

### 原生可编辑排版（优先）

项目提供结构化正文、目录、章首页和页眉页脚时，必须优先运行原生可编辑构建：

```powershell
python skills/build-indesign-book/scripts/build_editable_indesign.py `
  --project-root projects/lost-human-world-cover `
  --output-dir indesign/editable-v001 `
  --execute
```

该模式创建明确的 `145 × 210 mm` 大32开页面、17.5 pt 基线节奏、段落样式、6 组父页角色、线程正文、竖排章题、原生目录、页眉和页码。只有封面与封底使用 300 PPI 图像。

### 扁平页面连接校验（仅 proof）

先执行只编译检查：

```powershell
python skills/build-indesign-book/scripts/build_indesign_book.py `
  --project-root projects/lost-human-world-cover `
  --page-dir ebook/pages-v003 `
  --output-dir indesign `
  --project-id BOOK-LOST-HUMAN-WORLD `
  --title 失落人间
```

确认报告后连接本机 Adobe InDesign 2025：

```powershell
python skills/build-indesign-book/scripts/build_indesign_book.py `
  --project-root projects/lost-human-world-cover `
  --page-dir ebook/pages-v003 `
  --output-dir indesign `
  --project-id BOOK-LOST-HUMAN-WORLD `
  --title 失落人间 `
  --execute
```

## 固定产物

- `build-book.jsx`：可复跑的 InDesign ExtendScript。
- `book-proof.indd`：InDesign 可打开的校样文档。
- `book-proof.pdf`：单页 PDF 校样。
- `indesign-build-report.json`：输入哈希、有效 PPI、阻断项、COM 返回和输出路径。
- `editable-v001/book-editable-v001.indd`：原生可编辑排版文档。
- `editable-v001/book-editable-v001.idml`：跨版本可编辑备份。
- `editable-v001/book-editable-v001.pdf`：原生排版 PDF 校样。
- `editable-v001/editable-build-report.json`：版心、字号、行距、可编辑部件和执行指标。

## 生产规则

- 使用 `InDesign.Application.2025` COM ProgID，不依赖 pywin32、UXP 面板或鼠标坐标。
- 每个批准物理页对应一个 InDesign 页面，按文件名前缀排序。
- 原生模式把结构化正文、目录、章首页和页眉页脚编译为 InDesign 样式、父页角色、矢量元素和线程文本框。
- 扁平校样模式只用于连接验证；不得把页面截图误称为可编辑成书。
- 静态图像清晰度问题使用高分辨率重渲染或超分辨率，不使用视频“补帧”概念处理文字页面。
- 输出存在时只覆盖本 Skill 自己的同名产物，不改动输入页面。

## 完成标准

- COM 返回 Adobe InDesign 名称与版本。
- INDD、PDF 和报告都存在且非空。
- InDesign 页数与输入页面数完全一致。
- 报告明确 `proof` 或 `print`、`print_ready`、有效 PPI 和所有阻断项。
