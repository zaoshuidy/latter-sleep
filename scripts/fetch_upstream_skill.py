#!/usr/bin/env python3
"""Fetch and verify a complete immutable GitHub repository snapshot."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import ssl
import tarfile
import tempfile
import urllib.request
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any

import certifi


DEFAULT_REPOSITORY = "LiamGvchi/gc-minimal-zine-poster"
USER_AGENT = "book-production-skills-v1"


def _ssl_context() -> ssl.SSLContext:
    """Use a bundled CA set because Framework Python may lack a macOS CA file."""
    return ssl.create_default_context(cafile=certifi.where())


def _request_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30, context=_ssl_context()) as response:
        return json.load(response)


def _request_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60, context=_ssl_context()) as response:
        return response.read()


def file_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def verify_snapshot(root: Path, expected: dict[str, str]) -> list[str]:
    actual = file_hashes(root)
    errors = []
    for path in sorted(set(expected) | set(actual)):
        if path not in actual:
            errors.append(f"missing: {path}")
        elif path not in expected:
            errors.append(f"unexpected: {path}")
        elif actual[path] != expected[path]:
            errors.append(f"modified: {path}")
    return errors


def _safe_members(archive: tarfile.TarFile) -> list[tarfile.TarInfo]:
    members = archive.getmembers()
    for member in members:
        path = PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts or member.issym() or member.islnk():
            raise ValueError(f"unsafe archive member: {member.name}")
    return members


def fetch_snapshot(repository: str, target: Path, index_path: Path) -> dict[str, Any]:
    if target.exists():
        raise FileExistsError(f"snapshot target already exists: {target}")
    repo = _request_json(f"https://api.github.com/repos/{repository}")
    commit_data = _request_json(f"https://api.github.com/repos/{repository}/commits/{repo['default_branch']}")
    commit = commit_data["sha"]
    tarball = _request_bytes(f"https://codeload.github.com/{repository}/tar.gz/{commit}")

    with tempfile.TemporaryDirectory(prefix="book-upstream-") as tmp:
        tmp_root = Path(tmp)
        with tarfile.open(fileobj=io.BytesIO(tarball), mode="r:gz") as archive:
            members = _safe_members(archive)
            archive.extractall(tmp_root, members=members, filter="data")
        roots = [path for path in tmp_root.iterdir() if path.is_dir()]
        if len(roots) != 1:
            raise ValueError("upstream archive must contain exactly one repository root")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(roots[0], target)

    hashes = file_hashes(target)
    required = {"LICENSE", "README.md", "README.zh-CN.md", "SKILL.md"}
    if not required.issubset(hashes):
        raise ValueError("upstream snapshot lacks required original files")
    record = {
        "id": "gc-minimal-zine-poster",
        "repository": repository,
        "source_url": f"https://github.com/{repository}",
        "commit": commit,
        "commit_date": commit_data["commit"]["committer"]["date"],
        "stars_at_fetch": repo["stargazers_count"],
        "license": repo.get("license", {}).get("spdx_id"),
        "fetched_at": date.today().isoformat(),
        "snapshot_path": target.as_posix(),
        "preservation_mode": "full-original-no-summary",
        "archive_sha256": hashlib.sha256(tarball).hexdigest(),
        "files": hashes,
    }
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps({"version": "1.0", "skills": [record]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--target", type=Path)
    parser.add_argument("--index", type=Path)
    parser.add_argument("--verify-index", type=Path)
    args = parser.parse_args()
    if args.verify_index:
        index = json.loads(args.verify_index.read_text(encoding="utf-8"))
        failed = False
        for record in index["skills"]:
            errors = verify_snapshot(Path(record["snapshot_path"]), record["files"])
            if errors:
                failed = True
                print(json.dumps({"id": record["id"], "errors": errors}, ensure_ascii=False, indent=2))
        return 1 if failed else 0
    if args.target is None or args.index is None:
        parser.error("--target and --index are required unless --verify-index is used")
    record = fetch_snapshot(args.repository, args.target, args.index)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
