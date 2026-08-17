# 《失落人间》封面测试项目

状态：完整封面 V001 已选定  
设计规格：`../../docs/superpowers/specs/2026-08-12-lost-human-world-cover-design.md`  
执行计划：`../../docs/superpowers/plans/2026-08-12-cover-integrated-typography-minimal.md`

## 项目事实

- 书名：失落人间
- 副标题：在所有归途之外
- 作者：早睡的猫
- 类型：文学小说
- 范围：145 × 210 mm 完整封面展开稿；70g 轻型纸、200 页、13 mm 暂定书脊、3 mm 出血
- 选定方向：B「不属于任何一页」
- 参考关系：C2《何物》的留白与中心信息 + C4《芳华修远》的抽象中轴；不复制原图形、坐标、文字或工艺。
- 文字模式：正封 `integrated-typography`；封底与书脊使用可编辑真文字。
- 选定正封：`generated/cover-v001.png`；1042 × 1509 PNG；SHA-256 `bf10257ee0d53d3dce0407b8b3e7a01704b684ad7cc4c8eae298686efc1a5599`
- 选定展开稿：`generated/full-cover-v001-preview.png`；3650 × 2551 PNG，300 DPI。
- 可编辑展开源：`generated/full-cover-v001.svg`；独立嵌图版：`generated/full-cover-v001-print.svg`。

## 本轮确认

1. 用户已选择方向 B，并批准现代宋体骨架、中轴竖排与暗红未闭合边界方案。
2. 用户已明确同意生成一张首稿。
3. V001 的书名、副标题、作者均准确，无额外文字与机器标识。
4. 用户于 2026-08-13 确认 V001 为选定稿；不生成 V002。
5. 用户于 2026-08-13 确认完整封面展开稿 V001 通过；书脊宽度在正式印刷前交印厂复核。

## 章首页测试

- 第一章：`第一章 车窗里的故乡`。
- 选定参考：`CHO-CN-0006` 与 `CHO-CN-0011`，只借用抽象关系、高留白和纵向可编辑信息区，不复制原案例内容。
- 正式 selection：`chapter-opener/reference-selection-A.json`，状态 `approved`。
- 母版规格：`chapter-opener/chapter-opener-master.json`。
- 可视预览：`chapter-opener/chapter-opener-preview.html`。
- 章号、章题为可编辑真文字；背景不包含可读文字。本阶段未调用 imagegen。

## 第一章正文样张

- 已批准正文首跨页：`body-opening/body-opening-v001.html`，测试页码 6—7。
- 连续正文样张 V001：`body-pages/chapter-01-body-pages-v001.html`，测试页码 8—13；已由统一规范版取代。
- 第一章 49 个正文段落已全部进入可编辑 HTML；没有改写或校对正文。
- 连续样张当前等待人工视觉确认；页码仍为暂定值。
- 统一规范版：`typeset/chapter-01-typeset-v002.html`，将全部正文按行业基线重排为测试页码 6—11。
- V002 正文采用五号宋体等价 10.5 pt、17.5 pt 行距、段后 0、首行缩进两字，页码位于外侧底部 12 mm。
- 用户于 2026-08-14 确认 V002 视觉与阅读节奏通过；该参数组已写入 `design-book-editorial` 作为普通 32 开文学小说的默认起点。

## 目录与页眉页脚测试

- 用户已选定并批准方向 B「归途坐标」：低对比坐标网格、暗红导航轴与克制的成对页眉。
- 目录可编辑原型：`toc/toc-direction-b-v001.html`；视觉预览：`toc/toc-direction-b-v001-preview.png`；审查记录：`toc/toc-direction-b-v001-review.md`。
- 页眉页脚可编辑原型：`running-headers/running-headers-b-v001.html`；视觉预览：`running-headers/running-headers-b-v001-preview.png`；审查记录：`running-headers/running-headers-b-v001-review.md`。
- 目录包含序章与八章；除 `第一章 车窗里的故乡` 外，其余章名均为功能测试文字，全部页码为暂定值。
- 页眉采用左页书名、右页章名的成对导航；页码镜像位于外侧底部 12 mm。
- 目录、页眉、页码均为可编辑真文字。本阶段未进入 InDesign、正式 PDF、版权页或最终页序。
- 目录组件知识库当前仍为 `planned`；本测试没有伪造正式案例检索或人工选择。

## 扉页测试

- 扉页 V001 延续方向 B「归途坐标」：左页空白，右页使用断续暗红纵轴、竖排书名与高留白。
- 可编辑原型：`title-page/title-page-v001.html`；视觉预览：`title-page/title-page-v001-preview.png`；结构数据：`title-page/title-page-v001-layout.json`；审查记录：`title-page/title-page-v001-review.md`。
- 页面仅使用真实文字：书名「失落人间」、副标题「在所有归途之外」、作者「早睡的猫」、工作室标识「纸船工作室」。
- `纸船工作室` 以 `studio_mark` 登记，放在通常的出版标识位置，但不冒充法定出版社事实。
- 左右页均不显示页眉与页码；所有文字为可编辑 HTML 真文字。本阶段未进入 InDesign、PDF、版权页或正式印刷文件。

## 可翻阅 HTML 电子样书

- PNG 页面实验版：`ebook/lost-human-world-ebook-v003-png.html`；14个物理位置分别嵌入 `ebook/pages-v003/` 下的14张本地 PNG；预览：`ebook/lost-human-world-ebook-v003-png-preview.png`。
- V003 的章首页左右页直接取自批准的 `chapter-opener-v001-300dpi.png`；封底直接从批准的 `full-cover-v001-preview.png` 按145 × 210 mm封底净尺寸裁切，不使用CSS仿制图。
- V003 保留 V002 的 StPageFlip 翻页、硬封/软页、目录跳转和页序；另保留透明的正文检索层。V002 继续作为真文字优先版，不被覆盖。
- 最新正式测试版：`ebook/lost-human-world-ebook-v002.html`；静态预览：`ebook/lost-human-world-ebook-v002-preview.jpg`；审查记录：`ebook/lost-human-world-ebook-v002-review.md`。
- V002 使用本地固定版本 `page-flip@2.0.7`（StPageFlip）驱动真实翻页，不再维护手写翻页状态机；封面为硬页，内文为软页。
- V002 含 14 个物理页面，并保留扉页、两页目录、章首页、第一章全部 49 个真实正文段落与封底；文字仍可选择、搜索和复制。
- 单文件阅读器：`ebook/lost-human-world-ebook-v001.html`；静态预览：`ebook/lost-human-world-ebook-v001-preview.png`；审查记录：`ebook/lost-human-world-ebook-v001-review.md`。
- 电子样书包含 7 个可翻阅画面：封面、扉页、目录、第一章章首页、正文 6—7、8—9、10—11 页。
- 支持页面左右按钮、书页边缘点击、键盘方向键、目录抽屉跳转、进度提示和浏览器全屏。
- 第一章 49 个真实正文段落全部保持为可选择 HTML 文字；其余章节仅在测试目录中登记，没有伪造后续正文。
- 封面复用已批准 `generated/cover-v001.png`；内页沿用方向 B「归途坐标」与行业正文基线。

## Windows InDesign 校样

- 2026-08-17 已通过 `InDesign.Application.2025` COM 在 Adobe InDesign 20.4.1.4 完成首次端到端构建。
- 输入：`ebook/pages-v003/` 的 14 个已批准物理单页；输出：`indesign/book-proof.indd`、`indesign/book-proof.pdf`、`indesign/indesign-build-report.json`。
- InDesign 返回 14 页、14 个链接，PDF 页面视觉抽检见 `indesign/qa-proof-contact-sheet.png`。
- 当前页面为 1000 × 1448 px，在 145 × 210 mm 成品尺寸下最低有效分辨率约 175.14 PPI；同时内页是扁平图片，因此本次状态为 proof，不是 300 PPI 印刷成品或可编辑正文排版。

## Windows InDesign 原生可编辑版

- `indesign/editable-v001/book-editable-v001.indd`：14 页、145 × 210 mm 大32开、51 个原生文本框、15 个段落样式和 6 组父页角色。
- `indesign/editable-v001/book-editable-v001.idml`：跨版本可编辑备份。
- `indesign/editable-v001/book-editable-v001.pdf`：原生排版 PDF 校样。
- 扉页、目录、章首页、49 段正文、页眉和页码全部为 InDesign 原生可编辑文字；正文使用思源宋体 10.5 pt、17.5 pt 行距、两字首行缩进和连续线程文本框。
- 封面与封底从 3650 × 2551、300 PPI 的完整展开图按 145 × 210 mm 成品区裁切；不再使用 1000 × 1448 的电子样书截图。
- 视觉 QA 通过，0 overset、0 missing links、0 low-resolution links；报告位于 `indesign/editable-v001/editable-build-report.json`。

## 检查点

### Task 1：文学小说分类

- `schemas/project-config.schema.json`：`7843908c9020f485901a0fe5f1292d360f556a50468bdd75a91152881af7ac7b`
- `tests/test_contracts.py`：`fcf16207a86f694e309993df052a7abd835fc2cd2635bc64f9869e7cc5103bd9`
- `tests.test_contracts`：7/7 通过。
- `tests.test_component_kb_contracts`：18/18 通过。

### Task 2：项目与正式检索

- `inputs/project.json`：`f37af9ddc064ac0b3c2bfe1872e432b49dde4ad625b3239aca282ad44811fff5`
- `inputs/query.json`：`1e42bc61ca6146e9e77f2d70a998302f0b3f19ee038f401bdb3cd2908f62e35f`
- `retrieval/retrieval-result.json`：`f7c73187c3ee2e2ea2fda1b1e9b26aa105bcbcfd472e33ab54c5f9ce84b916d9`
- 检索结果：`available`，5 本不同图书；正式 query 只执行一次。
- 组件库：`valid=true`、`status=available`、50 条、`errors=[]`。

### Task 3：案例与字体证据

- `retrieval/case-comparison.md`：`ea823dcbc2cf3fa0117674ea28961bbd82754d51040c713456fef77a9370d19e`
- `retrieval/typography-evidence.md`：`dcff3b18eaa3cfdf051fcb7318415c35fa294749c5da36bffc837c0e516f83a9`
- `retrieval/case-board.html`：`73b3ec3e36429948b98bbc3565ed585c7fd8ff1875c4f95944277fe4819a8596`
- 5/5 本地图片可解码，尺寸与 SHA 和 record 完全一致。
- 字体页使用 Adobe 与方正字库官方来源；当前 Mac 尚未安装推荐字体，视觉板仅表示排版结构。
