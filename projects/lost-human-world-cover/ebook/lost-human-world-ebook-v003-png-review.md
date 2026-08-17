# 《失落人间》可翻阅电子样书 V003 PNG 页面实验

## 结果

- 14个物理页面全部转为真正的 PNG，并逐一嵌入对应翻页位置。
- 每张 PNG 为 `1000 × 1448`、RGB，总计 `7,771,221` bytes。
- V002 保持不变；V003 继续使用本地 `page-flip@2.0.7`。
- 首尾为硬封，内部为软页；页面顺序、目录、版式与文字内容没有重新设计。
- PNG 上方保留透明的原始文字层，第一章49个源段落仍可被浏览器检索。
- 章首页左右页分别从批准的 `chapter-opener-v001-300dpi.png` 拆分；封底从批准的 `full-cover-v001-preview.png` 按145 × 210 mm净尺寸裁切。

## 实际浏览器检查

- 初始化：`ready`，`data-reader-render=png-pages`，14页、14张PNG、49个源段落、0个外部资源。
- 首屏：正封 `1 / 14`，上一页禁用，下一页可用。
- 实际点击下一页后进入封二 `2 / 14`。
- 目录跳转实际到达正文第6页 `8 / 14`，URL 为 `#body-6`。
- 目录跳转实际到达封底 `14 / 14`，下一页禁用。
- 抽查目录、章首页、正文第9页与封底，页面内容完整，无裁切或错位。
- 修复后浏览器确认章首页左右图和封底图均完成加载，三张图片的自然尺寸都是 `1000 × 1448`。
- 重复线条修复：PNG 页面容器统一改为 `book-page png-page`，不再继承 `chapter-art`、`back-cover` 等旧设计类；浏览器计算样式确认三个目标页的 `::before`、`::after` 均为 `content:none`，边线为 `0px none`。

## 文件指纹

- `lost-human-world-ebook-v003-png.html`：`56de8319719771bcdc0774cd3fb7dc1962da92ad71483cefff49dba75eab8527`
- `lost-human-world-ebook-v003-png-preview.png`：`04c2c718f1ec31f841f744a85ad06f6680c667380429bfd7af34659c23121bb7`
- 章首页左页：`a60e1752906d7fa7c69986fe5bc99df5efc5115bd09c1b89aa0e9841af820409`
- 章首页右页：`af4797ee9a69b812fc6874c51e5bbb4cbb88ab32a87e0ce301155057991c31b3`
- 封底：`33d4785b3b954da0076fab1a22ab598a8b49d188577f5ba8cf148b3d2872ea3f`
- 14张页面PNG的排序哈希聚合：`975e96bf01c9da34fe0eff6e055fd2e82f579e060a121b7ecb2a3e81a78eb3cc`
- 生成器 `scripts/render_lost_human_world_png_flipbook.py`：`054964af6e4801d6edaaffcef4f8f11ec6ab5bb742b4a9250f52c2f11d78b9f2`

## 边界

PNG 页面能锁定视觉效果，但放大后的文字清晰度和可访问性仍不如 V002 真文字版。因此 V003 作为对比实验版，V002 仍是当前推荐的电子阅读版本。
