---
name: create-book-images
description: Use when a Chinese book project needs documentary-photo handling, old-photo restoration boundaries, text-free design imagery, memory illustrations, Codex image generation, prompt records, or indexed upstream image-style skills.
---

# 图书图像制作

统一使用现有系统 `imagegen` 生成或编辑图像，不复制它的执行规则。先确定图像角色，再生成；目录、章首页、正文、页眉、页脚和页码始终使用可编辑文字。只有封面可按下述受控模式生成已登记文字。

封面、目录、章首页或插画装饰已有组件知识库方向时，必须先完整执行 `references/component-prompt-pipeline.md`。输入必须是 approved selection 与 schema 有效的 `book-component-prompt`，并通过 production generation-bundle preflight；只有口头方向或宽泛风格时停止，不调用 `imagegen`。

## 三类图像

先读 `references/image-roles.md`：

- `documentary`：真实照片或扫描件，只允许恢复、裁切和基础调整；不得生成不存在的人物或事件。
- `design`：封面背景、纹理、装饰、抽象视觉等；默认无可读文字。
- `memory-illustration`：依据回忆文字创作的艺术化插画，必须明确标注“回忆插画 / 非纪实照片”，不得伪装成历史证据。

## 工作流程

1. 读取已确认的设计基因、页面计划、真实素材和人工审核意见。
2. 为每张图建立 `image_id`、角色、用途、参考文件和独立 Prompt 文件。
3. 非组件任务按既有 Prompt 合同执行；组件任务服从完整 pipeline。所有生成都需用户对 Prompt 和费用动作明确授权，并在 production `GenerationExecutionBundle` 上下文内只消费已固定的 background 与授权 reference bytes，生成前后复验未变，才使用 `imagegen`。默认不把最终文字写入画面；封面显式选择 `integrated-typography` 时，只可使用已登记项目文字。
4. 输出生成图后，记录版本、输出路径与 `draft/selected/archived/rejected` 状态。
5. 主 `image-manifest.json` 只保存一行级索引字段；完整 Prompt 写入 `prompts/{image_id}.md`。选中版本正常保留，否决版本进入归档索引，不直接删除。
6. 组件图像必须保存 production retrieval result、generation authorization、version 与人工 selection approval 项目 artifact，并由 production API 从同一文件快照重编译、重算 hash、回查组件库真实 record 后形成 selected review；口头选择或调用者自填字段不能替代真实 artifact。本合同提供可审计凭证，不宣称密码学证明操作者身份。
7. review/proposal 只能以新文件写入项目 `reviews/`、`promotions/`，不得覆盖任何项目事实；完整 snapshots（promotion 含落盘 review）必须贯穿 link 前后，变化时回滚且无残留。只有完整证据链通过的 selected review 才能形成待人工维护的 promotion proposal；本 Skill 不直接写组件知识库。

## 封面

按 `references/cover-prompt-contract.md` 生成 `cover-prompt.json`。默认 `editable-overlay` 生成无字底图；`integrated-typography` 仅允许封面已登记文字，使用 `exact-project-text`，同时保留可编辑文字层备份。ISBN、条码、二维码、定价、CIP 绝对不得进入像素。

## 上游风格资产

`gc-minimal-zine-poster` 仅按 `references/upstream-index.md` 定位完整上游原件。不得摘要、改写、合并或覆盖上游目录；项目可引用其文件路径和 commit，但仍需遵守本 Skill 的文字分层与真实性规则。

## 完成标准

- 每张图角色明确，回忆插画没有冒充纪实照片。
- 非封面关键文字不在像素层；封面一体化文字通过四项准确性审核。
- Prompt、参考文件、输出文件和版本状态可追溯。
- 项目事实、授权引用和生成结果没有 hardlink/知识库 inode 别名；review/promotion 不覆盖或逃逸项目角色目录。
- 封面提示词通过 schema。
- 生成前后真实照片的身份事实与源文件保持不变。
