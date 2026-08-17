# 组件 Prompt 到图像的受控管线

封面、目录、章首页或插画装饰已有正式组件方向时使用。只有完整项目 artifact 链通过 production 校验后才能生成、selected 或形成待审批 proposal。

## 1. 路径与 fail closed

从实际 Skill 绝对路径解析套件，不依赖 cwd：

```bash
SKILL_FILE="/absolute/path/to/current/skills/create-book-images/SKILL.md"
SUITE_ROOT="$(cd -P "$(dirname "$SKILL_FILE")/../.." && pwd)"
SUITE_PYTHON="$SUITE_ROOT/.venv/bin/python"
PROJECT_ROOT="/absolute/path/to/current/book-project"
```

套件 runtime/schema 使用 `SUITE_ROOT`；项目事实全部使用 `PROJECT_ROOT` 内真实、单链接普通文件。缺文件、外部路径、`..`、symlink、hardlink、知识库路径/inode 别名、ID/hash/component/真实 `record_id` 列表不一致均 fail closed。只有口头方向或“最美的书风格”等宽泛描述时不得调用 `imagegen`。

## 2. Production Prompt 与生成授权

项目内保存 schema 有效且 `status=approved` 的 selection、`status=available` 的 production retrieval result、project config、design genome、output spec 和 committed `book-component-prompt`。selection 必须通过 `validate_selection`，真实 record ID 必须回查 available 组件库中的同组件 record；当前只有 cover 库 available，其他组件没有正式库时 fail closed。使用 `compile_component_prompt` 真实复编译，结果必须与 committed Prompt 完整相等；不得手改编译产物。

生成 payload 使用闭合 `book-project-image-generation-payload`：只含 `background_prompt` 和 `referenced_image_paths`。默认 `editable-overlay` 的 background 不含最终文字；封面 `integrated-typography` 的 background 只能包含 production compiler 写入 `INTEGRATED_TEXT` 的 `exact-project-text`。两种模式都保存 `editable_text_overlay` 或等值可编辑文字层备份，不能把 overlay 文件作为模型引用。

封面一体化模式只有一个额外门：`integrated_text` 必须来自项目已确认文字，且 ISBN、条码、二维码、定价、CIP 永远禁止。不得手改 Prompt 添加文案，也不得从案例复制原书文字。

用户看到最终 background、必要引用、费用动作和输出位置并明确授权后，保存 schema 有效的 `book-project-image-generation-authorization`。它绑定 selection/retrieval result/prompt/payload 的真实文件 SHA-256、component、费用动作、输出路径以及每个引用的精确项目相对路径、SHA-256 与 MIME。该 artifact 是可审计授权记录，不是操作者身份的密码学证明；机器不得自行代替用户批准。

```python
from pathlib import Path
from ai.book_component_kb.review import (
    ProjectGenerationEvidencePaths,
    validate_generation_bundle,
)

generation_evidence = ProjectGenerationEvidencePaths(
    project_config=Path(PROJECT_ROOT) / "inputs/project.json",
    genome=Path(PROJECT_ROOT) / "inputs/design-genome.json",
    selection=Path(PROJECT_ROOT) / "inputs/reference-selection.json",
    retrieval_result=Path(PROJECT_ROOT) / "inputs/retrieval-result.json",
    output_spec=Path(PROJECT_ROOT) / "inputs/output-spec.json",
    prompt=Path(PROJECT_ROOT) / "inputs/component-prompt.json",
    generation_payload=Path(PROJECT_ROOT) / "payloads/generation.json",
    generation_authorization=Path(PROJECT_ROOT) / "approvals/generation.json",
)
with validate_generation_bundle(Path(PROJECT_ROOT), generation_evidence) as execution:
    execution.verify()  # 交接前末端复验
    background = execution.background_prompt
    authorized_reference_bytes = [
        material.content for material in execution.reference_materials
    ]
    # 必须在此上下文内调用 imagegen adapter；adapter 只消费 background
    # 与上述稳定 bytes，不得重新读取 material.relative_path。
    # 调用返回后、离开上下文前再次 execution.verify()。
    execution.verify()
```

生成前入口从项目内真实 artifact 路径以同一安全 fd/字节快照读取并计算 SHA，不接受调用者 dict 代替。引用必须与授权清单精确相同，且是 `PROJECT_ROOT` 内可解码、`st_nlink=1`、非 symlink/知识库 inode 的图片；拒绝 `overlays/`、overlay sidecar、外部路径、`..` 和未授权文件。空引用清单合法。`generated/...` 的每级父目录必须已存在且无 link，输出叶子必须不存在；身份链在返回前再次验证。

公开入口返回闭合 `GenerationExecutionBundle`，其中 reference 是已授权时固定的不可变 bytes、SHA 与 MIME，而不是稍后重新打开的可变项目路径。`imagegen` adapter 必须在 bundle 上下文内只消费 `background_prompt` 与 `reference_materials[].content`；生成前及返回后调用 `verify()`，最后 `close()`。磁盘 reference 在 preflight 后变化时，即使 bundle 中原 bytes 仍稳定，也必须停止本次付费调用；绝不能把变化后的 `relative_path` 交给模型。overlay 值始终不传。

## 3. Version evidence

生图后读取真实输出文件，保存 schema 有效的 `book-project-image-version`：

- `image_id/prompt_id/selection_id/component_type/record_ids`；
- 项目内 output path、真实 SHA、解码 MIME/dimensions、`V001` 等版本和初始 `status=draft`；
- selection、retrieval result、Prompt、generation payload、generation authorization 五个真实文件 SHA。

主 `image-manifest.json` 仍是轻量索引；Prompt、overlay、payload、两类授权与 version 都是独立项目 artifact。不得写入组件知识库。

## 4. 人工选择与 selected review

draft 先完成七项 review：

1. `no_unwanted_text`
2. `safe_zones_clear`
3. `genome_consistent`
4. `reference_transformed`
5. `print_crop_valid`
6. `truthfulness_valid`
7. `provenance_complete`

封面使用 `integrated-typography` 时，再检查四项：`integrated_text_exact`、`no_extra_text`、`typography_usable`、`machine_identifiers_absent`。任一失败都不能 selected；直接重生，或回退到无字背景加可编辑文字层，不对错误文字图做无止境修补。

只有七项全部为 true 且用户明确选定具体 image/hash/version 后，才保存闭合 `book-project-image-selection-approval`。它绑定 approval ID、审批主体、selection/prompt/component、image ID/version/SHA 和合法日期。review 的 `human_selection` 保存同一 approval ID、主体、version、image SHA，以及该真实 approval artifact 的文件 SHA。

项目 API 使用闭合路径对象重新安全读取所有事实，真实调用 compiler 与 generation preflight，并重算全部 hash：

```python
from pathlib import Path
from ai.book_component_kb.review import (
    ProjectImageEvidencePaths,
    review_project_image,
)

evidence = ProjectImageEvidencePaths(
    project_config=Path(PROJECT_ROOT) / "inputs/project.json",
    genome=Path(PROJECT_ROOT) / "inputs/design-genome.json",
    selection=Path(PROJECT_ROOT) / "inputs/reference-selection.json",
    retrieval_result=Path(PROJECT_ROOT) / "inputs/retrieval-result.json",
    output_spec=Path(PROJECT_ROOT) / "inputs/output-spec.json",
    prompt=Path(PROJECT_ROOT) / "inputs/component-prompt.json",
    generation_payload=Path(PROJECT_ROOT) / "payloads/generation.json",
    generation_authorization=Path(PROJECT_ROOT) / "approvals/generation.json",
    version=Path(PROJECT_ROOT) / "versions/IMAGE-V001.json",
    selection_approval=Path(PROJECT_ROOT) / "approvals/image-selection.json",
    source_image=Path(PROJECT_ROOT) / "generated/IMAGE-V001.jpg",
)
reviewed = review_project_image(
    Path(PROJECT_ROOT),
    evidence,
    selected_review,
    output_sidecar=Path(PROJECT_ROOT) / "reviews/REVIEW-IMAGE-V001.json",
)
```

批准 artifact 必须是项目内真实、单链接普通 JSON；API 从同一安全打开的 fd 读取不可变 bytes，同时解析和计算 SHA，形成全链 snapshot。API 校验其 schema、真实文件 SHA，并逐项绑定 review/version/image/prompt/selection/retrieval result。写 review sidecar 时，这组 snapshots 会贯穿原子发布临界区，在 link 前和 link 后末端复验；任一事实变化都会回滚新 sidecar 且无残留。它形成可复核的人工选择凭证，但仍不宣称密码学证明操作者身份。

## 5. Promotion 与不可覆盖输出

`review_project_image` 只能新建 `reviews/*.json`；`prepare_project_promotion` 只能新建 `promotions/*.json`。目标必须不存在；已有 Prompt、selection、overlay、version、manifest、approval、review 或 proposal 均不能被覆盖、别名或 hardlink 替换。原子发布固定 PROJECT_ROOT/角色目录的 dev+inode，发布后再次验证；角色目录被 rename/reparent 时从已打开 dirfd 删除逃逸文件并 fail closed。修订必须使用新文件名/版本。

`TARGET_COMPONENT` 从已验证 selection 的 `component_type` 取得；shell 语境只引用 `$TARGET_COMPONENT`，不写死 cover，也不把 cover fixture 伪装成其他组件：

```python
from ai.book_component_kb.review import prepare_project_promotion

TARGET_COMPONENT = validated_selection["component_type"]
proposal = prepare_project_promotion(
    Path(PROJECT_ROOT),
    evidence,
    Path(PROJECT_ROOT) / "reviews/REVIEW-IMAGE-V001.json",
    TARGET_COMPONENT,
    output_sidecar=Path(PROJECT_ROOT) / "promotions/PROMOTE-IMAGE-V001.json",
)
```

promotion 会再次重读并验证完整证据链；落盘 selected review 本身也用同一项目 snapshot helper 检查单链接、知识库 inode、同 fd bytes/JSON/SHA，并与其余 snapshots 一起贯穿 proposal 发布前后。读取后变成 rejected、替换 inode 或 hardlink 到项目外时必须失败且不留 proposal。输出只能是 `status=proposed`、`human_approval=pending`、`target_lifecycle=accumulation`；`draft/rejected/archived` 不得 promotion。proposal 仍留在项目目录，后续人工批准后才能交知识库维护流程；本 Skill 永不直接写库。

## 验收

| 阶段 | 通过条件 |
|---|---|
| Prompt | production 重编译完整相等；background 仅含所选模式允许的文字 |
| 生成授权 | 真实 artifact 绑定 payload、费用、输出和精确引用 |
| 输出 | 项目内真实 path/hash/MIME/dimensions；version 初始 draft |
| 人工选择 | 真实 selection approval artifact 与 review SHA/字段逐项绑定 |
| Review | 基础七项 true；一体化封面另需四项 true；只新建 reviews 文件 |
| Promotion | 再验证全链；只新建 proposed/pending/accumulation proposal |
