# 当前结论

现在不能生成，也不能把结果加入正式封面知识库或标记为 `approved`。当前输入只有“口头通过”和“最美的书风格”这类宽泛方向，必须按组件图像管线 **fail closed**；本次不会调用 `imagegen`，也不会创建虚假的 selection、Prompt、review、promotion 或项目 sidecar。

## 当前门禁与状态

- `selection`：未提供 schema 有效且 `status=approved` 的 `book-component-reference-selection`；口头通过不能替代正式 selection。
- `Prompt`：未提供 schema 有效、可由 production compiler 复现的 `book-component-prompt`。
- `record IDs`：未提供真实组件 `record_id`；不能用“最美的书风格”代替，也不能在 selection、Prompt、manifest 或 sidecar 中省略。
- 一致性：尚无法核验 selection 与 Prompt 的 `selection_id`、`component_type=cover` 和全部 `record_id` 是否一致。
- 生成授权：你表达了希望立即生成的意图，但生成前仍须先向你展示最终 `background_prompt`、必要图像引用、预计费用动作和输出位置，再取得对这些具体内容的明确授权；目前尚未形成有效的费用与生成授权。
- 图像状态：没有生成文件，因此不存在 `draft` 版本、真实路径、SHA-256、MIME 或尺寸。
- review 状态：未创建；不能跳过七项证据检查，也不能由我自行把任何版本标为 `selected`。review 没有机器自行 `approved` 的状态。
- promotion 状态：未创建；只有人工选定的 `selected` review 才能产生 `status=proposed`、`human_approval=pending`、`target_lifecycle=accumulation` 的 proposal。
- 知识库状态：未写入，且本 Skill 永不直接新增或修改正式组件知识库、records、assets、manifest 或 derived indexes。

## 需要补齐的输入

1. schema 有效且 `status=approved` 的封面 `book-component-reference-selection`，其中保留真实 selection ID 和每个组件 record ID。
2. schema 有效的封面 `book-component-prompt`。
3. 用于复编译的项目配置、design genome 和 output spec。
4. 可核验的参考文件；如“纸船工作室标记”是既有图形标识，还需提供可编辑矢量文件或透明底素材及使用确认。
5. 当前图书项目的绝对路径及约定输出位置。

## 文字与图像分层

生成模型只接收无字底图的 `background_prompt`，不能接收或绘制书名、作者名、studio 名称或标记。最终文字与标识应保存到可编辑 overlay sidecar，并由后续排版层叠加：

- 书名：`四时来信`
- 作者：`林舟`
- 工作室：`纸船工作室`（若为图形标记，使用获准的可编辑标识资产）

这些内容不能烘焙进图片像素；封面成品应由“无字背景图 + 可编辑文字/标识层”组成。

## 补齐输入后的可执行管线

1. 校验 approved selection、组件 Prompt、项目配置、design genome 和 output spec，并用 production compiler 复编译 Prompt；逐字段一致才继续，不能手工修补编译产物。
2. 向你展示最终无字 `background_prompt`、必要参考图、预计费用动作和真实输出位置，取得明确授权。
3. 仅将 `background_prompt` 和必要且已授权的图像引用传给 `imagegen`；overlay 键值、真实书名、作者和 studio 不传入模型。
4. 读取真实输出文件，在项目目录记录 path、SHA-256、MIME、dimensions、version、Prompt/overlay sidecar 和 provenance；初始状态只能是 `draft`。
5. 为该 draft 完成 `no_unwanted_text`、`safe_zones_clear`、`genome_consistent`、`reference_transformed`、`print_crop_valid`、`truthfulness_valid`、`provenance_complete` 七项 review。七项全为 true 后，仍需你明确选择具体文件 hash/版本，才能将 review 标记为 `selected`。
6. 只有 `selected` review 才能在项目目录生成 promotion proposal；其状态必须保持 `proposed / pending / accumulation`。即使你随后批准 proposal，也需交给后续知识库维护流程重新核验来源、重复项、组件隔离和完整性，再决定是否接管。

因此，我不会按当前要求跳过 Prompt sidecar、图像 review 或 promotion proposal，也不会自行判断“好看”后写库。请先提供上述正式输入；输入齐全后，我可以先产出可审核的生成前包，但在你明确批准具体 Prompt、引用、费用动作和输出位置前仍不会调用生成。
