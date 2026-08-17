from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError


FileIdentity = tuple[int, int]


class _SafeRelativePath(Path):
    """A path with a root-relative identity chain; derived paths become plain Paths."""

    __slots__ = ("_asset_root", "_asset_relative", "_asset_identities")

    def __init__(
        self,
        *segments: Path,
        asset_root: Path,
        asset_relative: Path,
        asset_identities: tuple[FileIdentity, ...],
    ) -> None:
        super().__init__(*segments)
        self._asset_root = asset_root
        self._asset_relative = asset_relative
        self._asset_identities = asset_identities

    def with_segments(self, *segments: str | os.PathLike[str]) -> Path:
        """Drop the identity contract when pathlib derives a different path."""
        return Path(*segments)


def _open_flags(*, directory: bool) -> int:
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("Safe asset access requires POSIX O_NOFOLLOW support")
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    flags |= getattr(os, "O_CLOEXEC", 0)
    if directory:
        flags |= getattr(os, "O_DIRECTORY", 0)
    return flags


def _identity(file_stat: os.stat_result) -> FileIdentity:
    return (file_stat.st_dev, file_stat.st_ino)


def _open_relative_regular_file(
    root: Path,
    relative: Path,
    expected_identities: tuple[FileIdentity, ...] | None = None,
) -> tuple[int, tuple[FileIdentity, ...]]:
    """Open a regular root-relative file without following any path component."""
    if not relative.parts:
        raise ValueError("Asset path must reference a file")
    if expected_identities is not None and len(expected_identities) != len(relative.parts) + 1:
        raise ValueError("Asset identity chain does not match the relative path")

    root_fd = -1
    current_fd = -1
    try:
        root_fd = os.open(os.fspath(root), _open_flags(directory=True))
        current_fd = root_fd
        identities = [_identity(os.fstat(root_fd))]
        if expected_identities is not None and identities[0] != expected_identities[0]:
            raise ValueError("Asset root identity changed")
        for index, part in enumerate(relative.parts):
            is_leaf = index == len(relative.parts) - 1
            next_fd = os.open(
                part,
                _open_flags(directory=not is_leaf),
                dir_fd=current_fd,
            )
            if current_fd != root_fd:
                os.close(current_fd)
            current_fd = next_fd
            current_stat = os.fstat(current_fd)
            identities.append(_identity(current_stat))
            if expected_identities is not None and identities[-1] != expected_identities[index + 1]:
                raise ValueError("Asset path identity changed")

        if not stat.S_ISREG(current_stat.st_mode):
            raise ValueError("Asset path must reference a regular file")
        file_fd = current_fd
        current_fd = -1
        return file_fd, tuple(identities)
    except OSError as error:
        raise ValueError("Asset path must reference an existing regular file without links") from error
    finally:
        if current_fd >= 0 and current_fd != root_fd:
            os.close(current_fd)
        if root_fd >= 0:
            os.close(root_fd)


def _open_regular_file(path: Path) -> int:
    if isinstance(path, _SafeRelativePath):
        file_fd, _ = _open_relative_regular_file(
            path._asset_root,
            path._asset_relative,
            path._asset_identities,
        )
        return file_fd

    file_fd = -1
    try:
        file_fd = os.open(os.fspath(path), _open_flags(directory=False))
        if not stat.S_ISREG(os.fstat(file_fd).st_mode):
            raise ValueError("Asset path must reference a regular file")
        result_fd = file_fd
        file_fd = -1
        return result_fd
    except OSError as error:
        raise ValueError("Asset path must reference an existing regular file without links") from error
    finally:
        if file_fd >= 0:
            os.close(file_fd)


def sha256_file(path: Path) -> str:
    """Hash bytes opened atomically; a raw Path protects only its final component."""
    digest = hashlib.sha256()
    file_fd = _open_regular_file(path)
    with os.fdopen(file_fd, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative_file(root: Path, relative: str) -> Path:
    """Return a verified root-relative regular file that consumers can safely reopen."""
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError("Asset path must be a relative path without traversal")

    root_path = Path(os.path.abspath(os.fspath(root)))
    file_fd, identities = _open_relative_regular_file(root_path, relative_path)
    os.close(file_fd)
    display_path = root_path.resolve(strict=True) / relative_path
    return _SafeRelativePath(
        display_path,
        asset_root=root_path,
        asset_relative=relative_path,
        asset_identities=identities,
    )


def read_image_metadata(path: Path) -> dict[str, int | str]:
    """Decode bytes atomically; a raw Path protects only its final component."""
    file_fd = _open_regular_file(path)
    try:
        with os.fdopen(os.dup(file_fd), "rb") as verify_file:
            with Image.open(verify_file) as image:
                image.verify()
        with os.fdopen(os.dup(file_fd), "rb") as decode_file:
            decode_file.seek(0)
            with Image.open(decode_file) as image:
                image.load()
                mime_type = Image.MIME.get(image.format)
                if mime_type is None:
                    raise ValueError("Unsupported image format")
                return {"width": image.width, "height": image.height, "mime_type": mime_type}
    except (UnidentifiedImageError, OSError, SyntaxError) as error:
        raise ValueError("Asset bytes are not a decodable image") from error
    finally:
        os.close(file_fd)


def _reject_nonstandard_json_constant(constant: str) -> None:
    raise ValueError(f"Nonstandard JSON constant: {constant}")


def load_json(path: Path) -> dict[str, Any]:
    """Load JSON atomically; a raw Path protects only its final component."""
    file_fd = _open_regular_file(path)
    with os.fdopen(file_fd, "r", encoding="utf-8") as file:
        data = json.load(file, parse_constant=_reject_nonstandard_json_constant)
    if not isinstance(data, dict):
        raise ValueError("JSON data must be an object")
    return data
