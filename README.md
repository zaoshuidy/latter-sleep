# Book Production Skills V1.2

个人使用的中文图书生产 Skill 套件，覆盖模板书与人生纪念书的项目路由、编辑设计、图片生产、质量复核、HTML 电子样书、Windows InDesign 校样和 Skill 维护。

## 当前可用能力

- 9 个个人 Codex Skills。
- 封面知识库：50 条，状态 `available`。
- 章首页知识库：50 条，状态 `available`。
- 《失落人间》完整测试项目：封面、目录、章首页、正文、页眉页脚、离线 HTML 翻页样书与 14 页 InDesign/PDF proof。
- 高清流畅翻页：StPageFlip 2.0.7 Canvas 图片模式、图片预解码、Retina 2x 适配、顺序图片回退。

## 安装

```bash
python3 scripts/install_personal.py --replace
```

安装后运行时位于 `~/.codex/book-production-skills-v1`，9 个 Skill 入口位于 `~/.codex/skills`。

## 验证

```bash
.venv/bin/python scripts/validate_all.py
```

## 发布包

桌面交付包默认名：`BookSkill_图书生产Skills套件_V1.2_2026-08-17.zip`。对应 SHA-256 记录在同名 `_SHA256.txt` 文件中。

详细说明见：

- `docs/BookSkill_V1.2_交付说明.md`
- `docs/图书生产Skills套件使用说明.md`
- `docs/Skill与知识库位置索引.md`

## 使用边界

- Windows 版可通过 `InDesign.Application.2025` 构建 INDD/PDF 校样；当前批准页面只有约 175 PPI 且为扁平图像，因此示例不是印刷级可编辑成书。
- 当前版本不包含公开网页前端或云服务。
- 知识库中的外部案例和图片仅作内部研究与索引；其公开可访问性不构成复制、改编、再发行或商业印刷授权。
- 本仓库应保持私有，除非完成独立版权清理。
