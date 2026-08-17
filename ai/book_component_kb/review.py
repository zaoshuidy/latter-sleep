from __future__ import annotations

import copy
import hashlib
import io
import json
import math
import os
import secrets
import stat
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Callable
from PIL import Image, UnidentifiedImageError

from ai.book_component_kb.paths import (
    _open_regular_file,
    load_json,
    read_image_metadata,
    safe_relative_file,
    sha256_file,
)
from ai.contracts import validate_data
from ai.book_component_kb.prompts import (
    _validate_generation_values,
    compile_component_prompt,
    validate_selection,
)


_CHECK_NAMES = (
    "no_unwanted_text",
    "safe_zones_clear",
    "genome_consistent",
    "reference_transformed",
    "print_crop_valid",
    "truthfulness_valid",
    "provenance_complete",
)
_INTEGRATED_TEXT_CHECK_NAMES = (
    "integrated_text_exact",
    "no_extra_text",
    "typography_usable",
    "machine_identifiers_absent",
)
_COMPONENT_CODES = {
    "cover": "COV",
    "toc": "TOC",
    "chapter-opener": "CHO",
    "illustration-decoration": "ILD",
}
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PRODUCTION_LIBRARY_ROOT = _PROJECT_ROOT / "knowledge" / "book-component-libraries"
_ASCII_CASEFOLD = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"
)


@dataclass(frozen=True)
class ProjectGenerationEvidencePaths:
    project_config: Path
    genome: Path
    selection: Path
    retrieval_result: Path
    output_spec: Path
    prompt: Path
    generation_payload: Path
    generation_authorization: Path


@dataclass(frozen=True)
class ProjectImageEvidencePaths(ProjectGenerationEvidencePaths):
    """Closed paths for facts authorizing one project image version."""

    version: Path
    selection_approval: Path
    source_image: Path


@dataclass(frozen=True)
class _ArtifactSnapshot:
    path: Path
    raw: bytes
    sha256: str
    identity: tuple[int, int]
    size: int
    mtime_ns: int
    data: dict[str, Any] | None


@dataclass(frozen=True)
class AuthorizedReferenceMaterial:
    """Stable authorized image bytes for one generation call boundary."""

    relative_path: str
    content: bytes
    sha256: str
    mime_type: str


class GenerationExecutionBundle:
    """Closed generation input whose project evidence remains re-verifiable."""

    def __init__(
        self,
        project_root: Path,
        background_prompt: str,
        reference_materials: tuple[AuthorizedReferenceMaterial, ...],
        snapshots: tuple[_ArtifactSnapshot, ...],
    ) -> None:
        self._project_root = Path(project_root)
        self.background_prompt = background_prompt
        self.reference_materials = reference_materials
        self._snapshots = snapshots
        self._closed = False
        self._invalid = False

    @property
    def closed(self) -> bool:
        return self._closed

    def verify(self) -> None:
        if self._closed:
            raise ValueError("generation execution bundle is closed")
        try:
            _verify_evidence_snapshots(self._project_root, self._snapshots)
        except BaseException:
            self._invalid = True
            raise

    def close(self) -> None:
        self._closed = True

    def __enter__(self) -> GenerationExecutionBundle:
        if self._closed:
            raise ValueError("generation execution bundle is closed")
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        try:
            if exc_type is None and not self._invalid:
                self.verify()
        finally:
            self.close()


def _validate_schema(value: dict[str, Any], schema_name: str, label: str) -> None:
    errors = validate_data(value, schema_name)
    if errors:
        raise ValueError(f"{label} schema validation failed: {'; '.join(errors)}")


def _canonical_path(path: Path) -> Path:
    return Path(os.path.realpath(os.path.abspath(path)))


def _identity(value: os.stat_result) -> tuple[int, int]:
    return (value.st_dev, value.st_ino)


def _ascii_casefold(value: str) -> str:
    return value.translate(_ASCII_CASEFOLD)


def _paths_alias(first: Path, second: Path) -> bool:
    first_text = _ascii_casefold(os.fspath(_canonical_path(first)))
    second_text = _ascii_casefold(os.fspath(_canonical_path(second)))
    if first_text == second_text:
        return True
    try:
        return os.path.samefile(first, second)
    except (FileNotFoundError, OSError):
        return False


def _has_component_library_marker(path: Path) -> bool:
    parts = tuple(_ascii_casefold(part) for part in path.parts)
    return any(
        parts[index : index + 2] == ("knowledge", "book-component-libraries")
        for index in range(len(parts) - 1)
    )


def validate_sidecar_output(output: Path, inputs: tuple[Path, ...]) -> None:
    """Reject any output that is not an isolated JSON sidecar destination."""
    output_path = Path(output)
    if output_path.suffix != ".json":
        raise ValueError("output sidecar must use a .json filename")
    canonical_output = _canonical_path(output_path)
    canonical_library = _canonical_path(_PRODUCTION_LIBRARY_ROOT)
    output_text = _ascii_casefold(os.fspath(canonical_output))
    library_text = _ascii_casefold(os.fspath(canonical_library))
    try:
        inside_production_library = (
            os.path.commonpath((output_text, library_text)) == library_text
        )
    except ValueError:
        inside_production_library = False
    if inside_production_library or _has_component_library_marker(canonical_output):
        raise ValueError("output sidecar must not target a component knowledge library")
    if any(_paths_alias(output_path, input_path) for input_path in inputs):
        raise ValueError("output sidecar must not alias an input path")
    try:
        if output_path.stat().st_nlink > 1:
            raise ValueError("output sidecar must not be an existing hard-linked file")
    except FileNotFoundError:
        pass


def _open_output_parent(parent: Path) -> tuple[int, tuple[int, int]]:
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("safe sidecar writes require POSIX O_NOFOLLOW support")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    flags |= getattr(os, "O_CLOEXEC", 0)
    try:
        directory_fd = os.open(os.fspath(parent), flags)
        directory_stat = os.fstat(directory_fd)
        if not stat.S_ISDIR(directory_stat.st_mode):
            raise ValueError("output parent must be a directory")
        return directory_fd, (directory_stat.st_dev, directory_stat.st_ino)
    except BaseException:
        if "directory_fd" in locals():
            os.close(directory_fd)
        raise


def _require_current_parent_identity(
    parent: Path, expected_identity: tuple[int, int]
) -> None:
    try:
        current = os.stat(parent, follow_symlinks=False)
    except OSError as error:
        raise ValueError("output parent identity changed") from error
    if not stat.S_ISDIR(current.st_mode) or (
        current.st_dev,
        current.st_ino,
    ) != expected_identity:
        raise ValueError("output parent identity changed")


def _create_temporary_sidecar(directory_fd: int, output_name: str) -> tuple[int, str]:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    flags |= getattr(os, "O_CLOEXEC", 0)
    for _ in range(64):
        temporary_name = f".{output_name}.{secrets.token_hex(12)}.tmp"
        try:
            file_fd = os.open(
                temporary_name,
                flags,
                0o600,
                dir_fd=directory_fd,
            )
            return file_fd, temporary_name
        except FileExistsError:
            continue
    raise ValueError("unable to allocate a unique sidecar temporary file")


def write_json_sidecar_atomic(
    output: Path, value: dict, inputs: tuple[Path, ...]
) -> None:
    """Write one guarded JSON sidecar without re-resolving its parent at commit."""
    output_path = Path(output)
    validate_sidecar_output(output_path, inputs)
    parent = output_path.parent
    directory_fd = -1
    temporary_fd = -1
    temporary_name: str | None = None
    try:
        directory_fd, parent_identity = _open_output_parent(parent)
        validate_sidecar_output(output_path, inputs)
        _require_current_parent_identity(parent, parent_identity)
        temporary_fd, temporary_name = _create_temporary_sidecar(
            directory_fd, output_path.name
        )
        temporary_file = os.fdopen(temporary_fd, "w", encoding="utf-8")
        temporary_fd = -1
        with temporary_file as file:
            json.dump(
                value,
                file,
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            )
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(
            temporary_name,
            output_path.name,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
        temporary_name = None
        os.fsync(directory_fd)
    finally:
        if temporary_fd >= 0:
            os.close(temporary_fd)
        if temporary_name is not None and directory_fd >= 0:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
        if directory_fd >= 0:
            os.close(directory_fd)


def review_image(input_record: dict) -> dict:
    """Validate and return an isolated image-review record.

    A caller may request ``selected`` only when every explicit review check is
    true. Other schema-valid statuses remain review records but never imply
    eligibility for knowledge-base promotion.
    """
    if not isinstance(input_record, dict):
        raise ValueError("review input must be an object")
    reviewed = copy.deepcopy(input_record)
    observations = reviewed.get("observations")
    if isinstance(observations, list):
        for observation in observations:
            if isinstance(observation, dict) and "confidence" in observation:
                confidence = observation["confidence"]
                if (
                    isinstance(confidence, bool)
                    or not isinstance(confidence, (int, float))
                    or not math.isfinite(confidence)
                ):
                    raise ValueError("observation confidence must be a finite number")
    _validate_schema(reviewed, "book-component-image-review", "review")
    if reviewed["status"] == "selected" and not all(
        reviewed["checks"][name] is True for name in _CHECK_NAMES
    ):
        raise ValueError("selected review requires all seven checks to be true")
    if (
        reviewed["status"] == "selected"
        and reviewed.get("text_rendering_mode") == "integrated-typography"
        and not all(
            reviewed["checks"][name] is True
            for name in _INTEGRATED_TEXT_CHECK_NAMES
        )
    ):
        raise ValueError(
            "selected review requires all integrated typography checks to be true"
        )
    if reviewed["status"] == "selected":
        evidence = reviewed["human_selection"]
        if evidence["selected_image_sha256"] != reviewed["image"]["sha256"]:
            raise ValueError("human selection image SHA-256 must match reviewed image")
        if not evidence["approval_id"].strip() or not evidence["approved_by"].strip():
            raise ValueError("human selection audit identifiers must be non-empty")
    return reviewed


def validate_review_text_contract(prompt: dict, reviewed: dict) -> None:
    """Bind the small cover-text review gate to the compiled prompt mode."""
    _validate_schema(prompt, "book-component-prompt", "prompt")
    _validate_schema(reviewed, "book-component-image-review", "review")
    prompt_mode = prompt.get("text_rendering_mode", "editable-overlay")
    review_mode = reviewed.get("text_rendering_mode", "editable-overlay")
    if review_mode != prompt_mode:
        raise ValueError("review text rendering mode must match compiled prompt")
    if prompt_mode == "integrated-typography" and reviewed.get(
        "integrated_text"
    ) != prompt.get("integrated_text"):
        raise ValueError("review integrated text must match compiled prompt")


def _project_regular_file(project_root: Path, path: Path) -> Path:
    supplied_root = Path(os.path.abspath(project_root))
    try:
        root_stat = os.lstat(supplied_root)
    except OSError as error:
        raise ValueError("PROJECT_ROOT must be an existing directory") from error
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        raise ValueError("PROJECT_ROOT must be a real directory without links")
    root = Path(os.path.realpath(supplied_root))
    candidate = Path(path)
    if ".." in candidate.parts:
        raise ValueError("project artifact path must not contain '..'")
    supplied_candidate = Path(
        os.path.abspath(candidate if candidate.is_absolute() else supplied_root / candidate)
    )
    # Preserve the caller's lexical path long enough for ``safe_relative_file``
    # to reject a symlink in any path component.  ``realpath`` alone would hide
    # an in-project link that happens to resolve to another in-project file.
    try:
        supplied_relative = supplied_candidate.relative_to(supplied_root)
    except ValueError:
        supplied_relative = None
    if supplied_relative is not None:
        safe_relative_file(root, supplied_relative.as_posix())
    try:
        if stat.S_ISLNK(os.lstat(supplied_candidate).st_mode):
            raise ValueError("project artifact must not be a symlink")
    except FileNotFoundError:
        pass
    absolute = Path(
        os.path.realpath(
            supplied_candidate
        )
    )
    try:
        relative = absolute.relative_to(root)
    except ValueError as error:
        raise ValueError("project artifact must stay inside PROJECT_ROOT") from error
    if _has_component_library_marker(absolute):
        raise ValueError("project artifact must not target a component knowledge library")
    return safe_relative_file(root, relative.as_posix())


def _production_library_inodes() -> set[tuple[int, int]]:
    result: set[tuple[int, int]] = set()
    for path in _PRODUCTION_LIBRARY_ROOT.rglob("*"):
        try:
            value = os.stat(path, follow_symlinks=False)
        except OSError:
            continue
        if stat.S_ISREG(value.st_mode):
            result.add((value.st_dev, value.st_ino))
    return result


def _snapshot_project_artifact(
    project_root: Path, path: Path, *, json_artifact: bool
) -> _ArtifactSnapshot:
    safe_path = _project_regular_file(project_root, path)
    file_fd = _open_regular_file(safe_path)
    try:
        before = os.fstat(file_fd)
        if before.st_nlink != 1:
            raise ValueError("project artifact must not be a hardlink")
        identity = (before.st_dev, before.st_ino)
        if identity in _production_library_inodes():
            raise ValueError("project artifact must not alias production knowledge bytes")
        with os.fdopen(os.dup(file_fd), "rb") as file:
            raw = file.read()
        after = os.fstat(file_fd)
        if (
            identity != (after.st_dev, after.st_ino)
            or before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
            or before.st_ctime_ns != after.st_ctime_ns
        ):
            raise ValueError("project artifact changed while being snapshotted")
    finally:
        os.close(file_fd)
    data: dict[str, Any] | None = None
    if json_artifact:
        try:
            parsed = json.loads(raw.decode("utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            raise ValueError("project JSON artifact is invalid") from error
        if not isinstance(parsed, dict):
            raise ValueError("project JSON artifact must be an object")
        data = parsed
    return _ArtifactSnapshot(
        path=Path(path),
        raw=raw,
        sha256=hashlib.sha256(raw).hexdigest(),
        identity=identity,
        size=after.st_size,
        mtime_ns=after.st_mtime_ns,
        data=data,
    )


def _verify_snapshot_unchanged(
    project_root: Path, snapshot: _ArtifactSnapshot
) -> None:
    current = _snapshot_project_artifact(
        project_root, snapshot.path, json_artifact=snapshot.data is not None
    )
    if (
        current.identity != snapshot.identity
        or current.raw != snapshot.raw
        or current.sha256 != snapshot.sha256
    ):
        raise ValueError("project artifact changed after its evidence snapshot")


def _verify_evidence_snapshots(
    project_root: Path, snapshots: tuple[_ArtifactSnapshot, ...]
) -> None:
    for snapshot in snapshots:
        _verify_snapshot_unchanged(project_root, snapshot)


def _decode_image_snapshot(snapshot: _ArtifactSnapshot) -> dict[str, Any]:
    try:
        with Image.open(io.BytesIO(snapshot.raw)) as image:
            image.load()
            mime = Image.MIME.get(image.format)
            if mime is None:
                raise ValueError("unsupported project image MIME")
            return {"width": image.width, "height": image.height, "mime_type": mime}
    except (UnidentifiedImageError, OSError, SyntaxError) as error:
        raise ValueError("project image bytes are not decodable") from error


def _validate_generated_output_destination(
    project_root: Path, relative_value: str, *, require_absent: bool
) -> None:
    relative = Path(relative_value)
    if relative.is_absolute() or ".." in relative.parts or len(relative.parts) < 2:
        raise ValueError("generation output must be a project-relative generated path")
    if relative.parts[0] != "generated" or _has_component_library_marker(relative):
        raise ValueError("generation output must remain below generated/")
    root = Path(os.path.abspath(project_root))
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    current_fd = root_fd
    identities = [_identity(os.fstat(root_fd))]
    try:
        for part in relative.parent.parts:
            next_fd = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=current_fd,
            )
            if current_fd != root_fd:
                os.close(current_fd)
            current_fd = next_fd
            identities.append(_identity(os.fstat(current_fd)))
        try:
            os.stat(relative.name, dir_fd=current_fd, follow_symlinks=False)
        except FileNotFoundError:
            leaf_exists = False
        else:
            leaf_exists = True
        if require_absent and leaf_exists:
            raise ValueError("authorized generation output must not already exist")

        # Rewalk from the pinned project root. A parent renamed/reparented after
        # the first traversal cannot satisfy the same identity chain.
        verify_fd = root_fd
        opened: list[int] = []
        try:
            if _identity(os.stat(root, follow_symlinks=False)) != identities[0]:
                raise ValueError("generation output project root identity changed")
            for index, part in enumerate(relative.parent.parts, start=1):
                next_fd = os.open(
                    part,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=verify_fd,
                )
                opened.append(next_fd)
                verify_fd = next_fd
                if _identity(os.fstat(next_fd)) != identities[index]:
                    raise ValueError("generation output parent identity changed")
        finally:
            for value in reversed(opened):
                os.close(value)
    except OSError as error:
        raise ValueError("generation output parents must exist without links") from error
    finally:
        if current_fd != root_fd:
            os.close(current_fd)
        os.close(root_fd)


def _project_sidecar_output(project_root: Path, path: Path, role: str) -> Path:
    """Resolve one new JSON output in its closed project role directory."""
    supplied_root = Path(os.path.abspath(project_root))
    try:
        root_stat = os.lstat(supplied_root)
    except OSError as error:
        raise ValueError("PROJECT_ROOT must be an existing directory") from error
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        raise ValueError("PROJECT_ROOT must be a real directory without links")
    candidate = Path(path)
    if ".." in candidate.parts:
        raise ValueError("project sidecar path must not contain '..'")
    supplied_candidate = Path(
        os.path.abspath(candidate if candidate.is_absolute() else supplied_root / candidate)
    )
    try:
        relative = supplied_candidate.relative_to(supplied_root)
    except ValueError as error:
        raise ValueError("project sidecar must stay inside PROJECT_ROOT") from error
    if _has_component_library_marker(supplied_candidate):
        raise ValueError("project sidecar must not target a component knowledge library")
    if len(relative.parts) != 2 or relative.parts[0] != role:
        raise ValueError(f"project sidecar must be a new file directly under {role}/")
    current = supplied_root
    for part in relative.parent.parts:
        current = current / part
        try:
            current_stat = os.lstat(current)
        except OSError as error:
            raise ValueError("project sidecar parent must already exist") from error
        if stat.S_ISLNK(current_stat.st_mode) or not stat.S_ISDIR(current_stat.st_mode):
            raise ValueError("project sidecar parent must be a real directory")
    try:
        os.lstat(supplied_candidate)
    except FileNotFoundError:
        pass
    else:
        raise ValueError("project sidecar output must not already exist")
    if supplied_candidate.suffix != ".json":
        raise ValueError("project sidecar output must use a .json filename")
    root = Path(os.path.realpath(supplied_root))
    return root / relative


def _write_json_sidecar_new_atomic(
    project_root: Path,
    output: Path,
    role: str,
    value: dict,
    *,
    precommit: Callable[[], None] | None = None,
) -> None:
    """Publish new evidence and roll it back if the role directory is reparented."""
    root_path = Path(os.path.abspath(project_root))
    root_fd = -1
    directory_fd = -1
    temporary_fd = -1
    temporary_name: str | None = None
    published = False
    try:
        root_fd = os.open(
            root_path,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
        root_identity = _identity(os.fstat(root_fd))
        directory_fd = os.open(
            role,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=root_fd,
        )
        parent_identity = _identity(os.fstat(directory_fd))

        def require_bound_role() -> None:
            current_root = os.stat(root_path, follow_symlinks=False)
            current_role = os.stat(role, dir_fd=root_fd, follow_symlinks=False)
            if (
                _identity(current_root) != root_identity
                or _identity(current_role) != parent_identity
            ):
                raise ValueError("project role directory identity changed")

        require_bound_role()
        try:
            os.stat(output.name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("project sidecar output must not already exist")
        temporary_fd, temporary_name = _create_temporary_sidecar(
            directory_fd, output.name
        )
        temporary_file = os.fdopen(temporary_fd, "w", encoding="utf-8")
        temporary_fd = -1
        with temporary_file as file:
            json.dump(value, file, ensure_ascii=False, indent=2, allow_nan=False)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        if precommit is not None:
            precommit()
        try:
            os.link(
                temporary_name,
                output.name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
                follow_symlinks=False,
            )
            published = True
        except FileExistsError as error:
            raise ValueError("project sidecar output must not already exist") from error
        try:
            if precommit is not None:
                precommit()
            require_bound_role()
            declared = os.stat(output, follow_symlinks=False)
            published_stat = os.stat(
                output.name, dir_fd=directory_fd, follow_symlinks=False
            )
            if _identity(declared) != _identity(published_stat):
                raise ValueError("published sidecar is not the declared project path")
        except BaseException:
            if published:
                try:
                    os.unlink(output.name, dir_fd=directory_fd)
                    published = False
                except FileNotFoundError:
                    pass
            raise
        os.unlink(temporary_name, dir_fd=directory_fd)
        temporary_name = None
        os.fsync(directory_fd)
    finally:
        if temporary_fd >= 0:
            os.close(temporary_fd)
        if temporary_name is not None and directory_fd >= 0:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
        if directory_fd >= 0:
            os.close(directory_fd)
        if root_fd >= 0:
            os.close(root_fd)


def _require_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label} binding mismatch")


def _validate_component_records(selection: dict[str, Any]) -> None:
    component = selection["component_type"]
    if component != "cover":
        raise ValueError("only the available cover component library is production-bound")
    for selected in selection["selected_references"]:
        record_id = selected["record_id"]
        if not record_id.startswith("COV-CN-"):
            raise ValueError("cover selection requires COV-CN record IDs")
        record_path = _PRODUCTION_LIBRARY_ROOT / "cover" / "records" / f"{record_id}.json"
        try:
            record = load_json(record_path)
        except (ValueError, OSError) as error:
            raise ValueError("selected record is absent from the production component library") from error
        _validate_schema(record, "book-component-reference-record", "component record")
        if record["record_id"] != record_id or record["component_type"] != component:
            raise ValueError("selected record component binding mismatch")


def _generation_snapshots(
    project_root: Path,
    evidence_paths: ProjectGenerationEvidencePaths,
    *,
    require_output_absent: bool,
) -> tuple[
    dict[str, _ArtifactSnapshot],
    tuple[_ArtifactSnapshot, ...],
    dict[str, Any],
]:
    if not isinstance(evidence_paths, ProjectGenerationEvidencePaths):
        raise ValueError("generation evidence must use the closed path object")
    names = tuple(field.name for field in fields(ProjectGenerationEvidencePaths))
    snapshots = {
        name: _snapshot_project_artifact(
            project_root, getattr(evidence_paths, name), json_artifact=True
        )
        for name in names
    }
    values = {name: snapshot.data for name, snapshot in snapshots.items()}
    project = values["project_config"]
    genome = values["genome"]
    selection = values["selection"]
    retrieval = values["retrieval_result"]
    output_spec = values["output_spec"]
    prompt = values["prompt"]
    payload = values["generation_payload"]
    authorization = values["generation_authorization"]
    assert all(isinstance(value, dict) for value in values.values())
    _validate_schema(retrieval, "book-component-retrieval-result", "retrieval result")
    validate_selection(selection, retrieval)
    _validate_component_records(selection)
    recompiled = compile_component_prompt(project, genome, selection, output_spec)
    _validate_generation_values(
        Path(project_root), selection, prompt, recompiled, payload, authorization
    )
    reference_snapshots: list[_ArtifactSnapshot] = []
    for relative_path, expected in zip(
        payload["referenced_image_paths"],
        authorization["referenced_images"],
        strict=True,
    ):
        reference_snapshot = _snapshot_project_artifact(
            project_root, Path(relative_path), json_artifact=False
        )
        reference_metadata = _decode_image_snapshot(reference_snapshot)
        _require_equal(
            reference_snapshot.sha256,
            expected["sha256"],
            "authorized reference SHA-256",
        )
        _require_equal(
            reference_metadata["mime_type"],
            expected["mime_type"],
            "authorized reference MIME",
        )
        reference_snapshots.append(reference_snapshot)
    for field, expected in (
        ("selection_sha256", snapshots["selection"].sha256),
        ("prompt_sha256", snapshots["prompt"].sha256),
        ("generation_payload_sha256", snapshots["generation_payload"].sha256),
        ("retrieval_result_sha256", snapshots["retrieval_result"].sha256),
    ):
        _require_equal(authorization[field], expected, f"generation authorization {field}")
    _validate_generated_output_destination(
        project_root,
        authorization["output_path"],
        require_absent=require_output_absent,
    )
    _verify_evidence_snapshots(
        project_root, tuple(snapshots.values()) + tuple(reference_snapshots)
    )
    return snapshots, tuple(reference_snapshots), values


def validate_generation_bundle(
    project_root: Path, evidence_paths: ProjectGenerationEvidencePaths
) -> GenerationExecutionBundle:
    """Return stable authorized bytes while keeping disk evidence re-verifiable."""
    snapshots, reference_snapshots, values = _generation_snapshots(
        project_root, evidence_paths, require_output_absent=True
    )
    payload = values["generation_payload"]
    authorization = values["generation_authorization"]
    assert isinstance(payload, dict) and isinstance(authorization, dict)
    reference_materials = tuple(
        AuthorizedReferenceMaterial(
            relative_path=expected["relative_path"],
            content=snapshot.raw,
            sha256=snapshot.sha256,
            mime_type=expected["mime_type"],
        )
        for snapshot, expected in zip(
            reference_snapshots,
            authorization["referenced_images"],
            strict=True,
        )
    )
    return GenerationExecutionBundle(
        project_root=project_root,
        background_prompt=payload["background_prompt"],
        reference_materials=reference_materials,
        snapshots=tuple(snapshots.values()) + reference_snapshots,
    )


validate_project_generation_bundle = validate_generation_bundle


def _load_project_evidence(
    project_root: Path,
    evidence_paths: ProjectImageEvidencePaths,
    review: dict,
) -> tuple[
    Path,
    dict[str, Any],
    dict[str, Any],
    tuple[_ArtifactSnapshot, ...],
]:
    if not isinstance(evidence_paths, ProjectImageEvidencePaths):
        raise ValueError("project image evidence paths must use the closed path object")
    generation_paths = ProjectGenerationEvidencePaths(
        **{
            field.name: getattr(evidence_paths, field.name)
            for field in fields(ProjectGenerationEvidencePaths)
        }
    )
    generation_snapshots, reference_snapshots, values = _generation_snapshots(
        project_root, generation_paths, require_output_absent=False
    )
    extra_snapshots = {
        name: _snapshot_project_artifact(
            project_root, getattr(evidence_paths, name), json_artifact=name != "source_image"
        )
        for name in ("version", "selection_approval", "source_image")
    }
    snapshots = {**generation_snapshots, **extra_snapshots}
    image_snapshot = snapshots["source_image"]
    image = _project_regular_file(project_root, evidence_paths.source_image)
    selection = values["selection"]
    prompt = values["prompt"]
    payload = values["generation_payload"]
    generation_authorization = values["generation_authorization"]
    version = snapshots["version"].data
    selection_approval = snapshots["selection_approval"].data
    assert isinstance(version, dict) and isinstance(selection_approval, dict)
    _validate_schema(version, "book-project-image-version", "version sidecar")
    _validate_schema(
        selection_approval,
        "book-project-image-selection-approval",
        "selection approval",
    )
    reviewed = review_image(review)
    validate_review_text_contract(prompt, reviewed)
    if reviewed["status"] != "selected":
        raise ValueError("project promotion evidence chain requires selected review")

    selection_sha = snapshots["selection"].sha256
    prompt_sha = snapshots["prompt"].sha256
    payload_sha = snapshots["generation_payload"].sha256
    authorization_sha = snapshots["generation_authorization"].sha256
    retrieval_sha = snapshots["retrieval_result"].sha256
    for actual, expected, label in (
        (version["selection_sha256"], selection_sha, "version selection SHA-256"),
        (version["prompt_sha256"], prompt_sha, "version prompt SHA-256"),
        (
            version["generation_payload_sha256"],
            payload_sha,
            "version generation payload SHA-256",
        ),
        (
            version["generation_authorization_sha256"],
            authorization_sha,
            "version generation authorization SHA-256",
        ),
        (
            version["retrieval_result_sha256"],
            retrieval_sha,
            "version retrieval result SHA-256",
        ),
        (
            generation_authorization["selection_sha256"],
            selection_sha,
            "generation authorization selection SHA-256",
        ),
        (
            generation_authorization["prompt_sha256"],
            prompt_sha,
            "generation authorization prompt SHA-256",
        ),
        (
            generation_authorization["generation_payload_sha256"],
            payload_sha,
            "generation authorization payload SHA-256",
        ),
    ):
        _require_equal(actual, expected, label)

    record_ids = [item["record_id"] for item in selection["selected_references"]]
    for actual, expected, label in (
        (version["selection_id"], selection["selection_id"], "version selection_id"),
        (version["prompt_id"], prompt["prompt_id"], "version prompt_id"),
        (
            version["component_type"],
            selection["component_type"],
            "version component_type",
        ),
        (version["record_ids"], record_ids, "version record_ids"),
        (reviewed["prompt_id"], prompt["prompt_id"], "review prompt_id"),
        (
            reviewed["component_type"],
            selection["component_type"],
            "review component_type",
        ),
    ):
        _require_equal(actual, expected, label)

    version_image = _project_regular_file(project_root, Path(version["output_path"]))
    authorized_output = _project_regular_file(
        project_root, Path(generation_authorization["output_path"])
    )
    reviewed_image = _project_regular_file(
        project_root, Path(reviewed["image"]["relative_path"])
    )
    if not all(
        _paths_alias(image, candidate)
        for candidate in (version_image, authorized_output, reviewed_image)
    ):
        raise ValueError("project image paths must bind the same source image")
    image_sha = image_snapshot.sha256
    metadata = _decode_image_snapshot(image_snapshot)
    for actual, expected, label in (
        (version["sha256"], image_sha, "version image SHA-256"),
        (reviewed["image"]["sha256"], image_sha, "review image SHA-256"),
        (version["mime_type"], metadata["mime_type"], "version MIME"),
        (reviewed["image"]["mime_type"], metadata["mime_type"], "review MIME"),
        (
            version["dimensions"],
            {"width": metadata["width"], "height": metadata["height"]},
            "version dimensions",
        ),
    ):
        _require_equal(actual, expected, label)

    approval_sha = snapshots["selection_approval"].sha256
    human_selection = reviewed["human_selection"]
    for actual, expected, label in (
        (
            human_selection["approval_artifact_sha256"],
            approval_sha,
            "review approval artifact SHA-256",
        ),
        (human_selection["approval_id"], selection_approval["approval_id"], "approval_id"),
        (human_selection["approved_by"], selection_approval["approved_by"], "approved_by"),
        (
            human_selection["selected_version"],
            selection_approval["selected_version"],
            "selected version",
        ),
        (
            human_selection["selected_image_sha256"],
            selection_approval["selected_image_sha256"],
            "selected image SHA-256",
        ),
        (selection_approval["selection_id"], selection["selection_id"], "approval selection_id"),
        (selection_approval["prompt_id"], prompt["prompt_id"], "approval prompt_id"),
        (
            selection_approval["component_type"],
            selection["component_type"],
            "approval component_type",
        ),
        (selection_approval["image_id"], version["image_id"], "approval image_id"),
        (selection_approval["selected_version"], version["version"], "approval version"),
        (
            selection_approval["selected_image_sha256"],
            image_sha,
            "approval image SHA-256",
        ),
    ):
        _require_equal(actual, expected, label)
    all_snapshots = tuple(snapshots.values()) + reference_snapshots
    _verify_evidence_snapshots(project_root, all_snapshots)
    return image, version, reviewed, all_snapshots


def review_project_image(
    project_root: Path,
    evidence_paths: ProjectImageEvidencePaths,
    review: dict,
    *,
    output_sidecar: Path | None = None,
) -> dict:
    """Revalidate and record one complete project-local evidence chain."""
    _, _, reviewed, snapshots = _load_project_evidence(
        project_root, evidence_paths, review
    )
    if output_sidecar is not None:
        output = _project_sidecar_output(project_root, output_sidecar, "reviews")
        _write_json_sidecar_new_atomic(
            project_root,
            output,
            "reviews",
            reviewed,
            precommit=lambda: _verify_evidence_snapshots(project_root, snapshots),
        )
    else:
        _verify_evidence_snapshots(project_root, snapshots)
    return reviewed


def prepare_project_promotion(
    project_root: Path,
    evidence_paths: ProjectImageEvidencePaths,
    review_sidecar: Path,
    target_component: str,
    *,
    output_sidecar: Path | None = None,
) -> dict:
    """Revalidate disk evidence and publish only a new pending proposal."""
    review_snapshot = _snapshot_project_artifact(
        project_root, review_sidecar, json_artifact=True
    )
    review = review_snapshot.data
    assert isinstance(review, dict)
    image, _, reviewed, evidence_snapshots = _load_project_evidence(
        project_root, evidence_paths, review
    )
    snapshots = evidence_snapshots + (review_snapshot,)
    if target_component != reviewed["component_type"]:
        raise ValueError("target component must match bound evidence")
    proposal = prepare_promotion(reviewed, image, target_component)
    _verify_evidence_snapshots(project_root, snapshots)
    if output_sidecar is not None:
        output = _project_sidecar_output(project_root, output_sidecar, "promotions")
        _write_json_sidecar_new_atomic(
            project_root,
            output,
            "promotions",
            proposal,
            precommit=lambda: _verify_evidence_snapshots(project_root, snapshots),
        )
    return proposal


def _canonical_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def prepare_promotion(
    review: dict, source_image: Path, target_component: str
) -> dict:
    """Prepare a deterministic, human-pending accumulation proposal only."""
    reviewed = review_image(review)
    if reviewed["status"] != "selected":
        raise ValueError("promotion requires a selected review")
    if target_component not in _COMPONENT_CODES:
        raise ValueError("target component is unsupported")
    if reviewed["component_type"] != target_component:
        raise ValueError("target component must match review component")

    image_path = Path(source_image)
    safe_image = safe_relative_file(image_path.parent, image_path.name)
    first_sha256 = sha256_file(safe_image)
    metadata = read_image_metadata(safe_image)
    second_sha256 = sha256_file(safe_image)
    if first_sha256 != second_sha256:
        raise ValueError("source image changed while it was being verified")
    if metadata["mime_type"] not in {"image/jpeg", "image/png", "image/webp"}:
        raise ValueError("source image MIME is unsupported")
    if reviewed["image"]["mime_type"] != metadata["mime_type"]:
        raise ValueError("review image MIME does not match decoded image bytes")
    if reviewed["image"]["sha256"] != first_sha256:
        raise ValueError("review image SHA-256 does not match source image bytes")

    component_code = _COMPONENT_CODES[target_component]
    record_id = f"ACC-{component_code}-{first_sha256[:16].upper()}"
    identity_material = {
        "review": reviewed,
        "source_sha256": first_sha256,
        "target_component": target_component,
    }
    promotion_digest = hashlib.sha256(_canonical_bytes(identity_material)).hexdigest()
    proposal = {
        "schema_version": "1.0",
        "promotion_id": f"PROMOTE-{component_code}-{promotion_digest[:16].upper()}",
        "review_id": reviewed["review_id"],
        "record_id": record_id,
        "component_type": target_component,
        "status": "proposed",
        "human_approval": "pending",
        "target_lifecycle": "accumulation",
    }
    _validate_schema(proposal, "book-component-kb-promotion", "promotion")
    return proposal
