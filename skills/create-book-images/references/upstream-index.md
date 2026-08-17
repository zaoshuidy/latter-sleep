# 上游原件索引

唯一索引文件：`knowledge/indexes/upstream-skills.json`。

`gc-minimal-zine-poster` 的完整、未总结上游快照位于该索引的 `snapshot_path`，以 `commit` 和逐文件 SHA-256 锁定。使用前运行：

```bash
python scripts/fetch_upstream_skill.py --verify-index knowledge/indexes/upstream-skills.json
```

不得直接编辑快照。需要更新时重新抓取新 commit 到新版本目录，经人工确认后再切换索引。
