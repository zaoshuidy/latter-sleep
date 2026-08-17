from __future__ import annotations

import json
import os
import re
import stat
import unicodedata
from pathlib import Path
from typing import Any

from ai.contracts import validate_data
from ai.book_component_kb.paths import (
    _open_regular_file,
    read_image_metadata,
    safe_relative_file,
    sha256_file,
)

from .retrieve import COMPONENT_WEIGHTS
from .integrated_text import (
    INTEGRATED_MODE,
    contains_machine_identifier,
    validate_integrated_typography,
)


EXPECTED_BLOCK_ORDER = (
    "PROJECT_TRUTH",
    "COMPONENT_ROLE",
    "DESIGN_GENOME",
    "REFERENCE_TRANSFERS",
    "COMPOSITION",
    "IMAGE_CONTENT",
    "COLOR_LIGHT_MATERIAL",
    "EDITABLE_TEXT_SAFE_ZONES",
    "PRINT_AND_CROP",
    "NEGATIVE",
    "OUTPUT_SPEC",
)
INTEGRATED_BLOCK_ORDER = (
    *EXPECTED_BLOCK_ORDER[:8],
    "INTEGRATED_TEXT",
    *EXPECTED_BLOCK_ORDER[8:],
)

_MAPPING_FIELDS = (
    "record_id",
    "include_fields",
    "existing_baseline",
    "adjustment_instruction",
    "preserve_elements",
    "required_changes",
    "exclude_fields",
)
_OUTPUT_SPEC_FIELDS = {
    "prompt_id",
    "aspect_ratio",
    "component_role",
    "composition",
    "image_content",
    "color_light_material",
    "editable_text_safe_zones",
    "print_and_crop",
    "negative_constraints",
    "editable_text_overlay",
    "editable_text_values",
}
_INTEGRATED_OUTPUT_SPEC_FIELDS = {
    "text_rendering_mode",
    "integrated_text",
    "editable_text_backup",
}
_FORBIDDEN_PIXEL_TEXT_KEYS = {
    "title",
    "title_text",
    "final_title",
    "author",
    "author_text",
    "publisher",
    "publisher_text",
    "publisher_mark",
    "spine_text",
    "page_number",
    "page_numbers",
    "readable_text",
    "text_in_image",
    "render_text",
}
_OVERLAY_FIELDS = {
    "title",
    "author",
    "studio_mark",
    "publisher_mark",
    "spine_text",
    "other_text",
}
_MANDATORY_NEGATIVE_CONSTRAINTS = (
    "no readable text",
    "no title, author, publisher, spine, or page-number glyphs",
    "no logo",
    "no watermark",
)
_INTEGRATED_NEGATIVE_CONSTRAINTS = (
    "no unregistered readable text",
    "no extra text beyond the exact registered project text",
    "no ISBN, barcode, QR code, price, CIP, or machine identifier",
    "no logo",
    "no watermark",
)
_INTEGRATED_CONTRADICTORY_NEGATIVES = frozenset(
    {
        "no readable text",
        "no title glyphs",
        "no author glyphs",
        "no title, author, publisher, spine, or page-number glyphs",
    }
)
_ENGLISH_PIXEL_TEXT_ACTION = re.compile(
    r"\b(?:add(?:s|ed|ing)?|render(?:s|ed|ing)?|show(?:s|ed|ing|n)?|"
    r"writ(?:e|es|ing|ten)|print(?:s|ed|ing)?|display(?:s|ed|ing)?|"
    r"plac(?:e|es|ed|ing)|put(?:s|ting)?|includ(?:e|es|ed|ing)|"
    r"generat(?:e|es|ed|ing)|draw(?:s|ing|n)?|typeset(?:s|ting)?|"
    r"insert(?:s|ed|ing)?|overlay(?:s|ed|ing)?|embed(?:s|ded|ding)?)\b"
)
_ENGLISH_PIXEL_TEXT_OBJECT = re.compile(
    r"\b(?:text|captions?|copy|quotes?|words?|wording|lettering|glyphs?|"
    r"typography(?![-\s]+safe)|title(?![-\s]+(?:zone|area|region|safe|space))|"
    r"author(?:['’]s)?[-\s]+(?:name|text|wording|lettering|glyphs?)|"
    r"publisher(?:['’]s)?(?:[-\s]+(?:name|mark|logo|text|wording|lettering))?|"
    r"spine[-\s]+(?:text|title|wording|lettering|glyphs?)|"
    r"page[-\s]?numbers?|(?:readable|legible)[-\s]+(?:text|words?|lettering)|"
    r"(?:bold|readable|legible|printed|written)[-\s]+letters)\b"
)
_CHINESE_PIXEL_TEXT_ACTION = re.compile(
    r"(?:添加|显示|写入|印制|放置|放在|加入|生成|绘制|排印|印上|写上|"
    r"渲染|呈现|嵌入|叠加)"
)
_CHINESE_PIXEL_TEXT_OBJECT = re.compile(
    r"(?:文字|文案|字符|引语|字样|字形|汉字|书名|"
    r"标题(?!区域|区|安全区|留白区)|作者(?:的)?(?:名|姓名|文字|字样|署名)|"
    r"出版社(?:名称|标志|标识|文字)?|书脊(?:文字|书名|字样)|页码|"
    r"可读文字|可识别文字|排版文字)"
)
_CLAUSE_SPLIT = re.compile(r"[.;；。!?！？\n]+")
_ENGLISH_ACTION_NEGATION = re.compile(
    r"(?:\bno|\bnot|\bnever|\bwithout|\bavoid|\bdo\s+not|"
    r"\bdoes\s+not|\bmust\s+not|\bshould\s+not|\bcannot|\bcan't)\s*$"
)
_CHINESE_ACTION_NEGATION = re.compile(
    r"(?:不要|不得|禁止|避免|切勿|无需|不可|不能|不|勿|无)\s*$"
)
_PIXEL_GENOME_FIELDS = (
    "direction_id",
    "brand_profile",
    "color",
    "grid",
    "page_families",
)


def _normalize(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip().casefold()


def _validate_schema(data: dict[str, Any], schema_name: str, label: str) -> None:
    errors = validate_data(data, schema_name)
    if errors:
        raise ValueError(f"{label} schema validation failed: {'; '.join(errors)}")


def _validate_selection_shape(selection: dict[str, Any]) -> None:
    references = selection.get("selected_references")
    if not isinstance(references, list) or not 2 <= len(references) <= 3:
        raise ValueError("selection must contain 2 or 3 selected references")
    _validate_schema(
        selection,
        "book-component-reference-selection",
        "selection",
    )
    record_ids = [reference["record_id"] for reference in references]
    if len(set(record_ids)) != len(record_ids):
        raise ValueError("selection must use distinct record IDs")

    component_type = selection["component_type"]
    component_weights = COMPONENT_WEIGHTS.get(component_type)
    if component_weights is None:
        raise ValueError(
            f"selection component_type is not supported for reference mapping: "
            f"{component_type}"
        )
    reference_include_fields = frozenset(component_weights)

    for reference in references:
        normalized_include_fields = [
            _normalize(value) for value in reference["include_fields"]
        ]
        if len(normalized_include_fields) != len(set(normalized_include_fields)):
            raise ValueError(
                f"selection include_fields must be unique after normalization for "
                f"{reference['record_id']}"
            )
        include_fields = set(normalized_include_fields)
        unknown_fields = sorted(include_fields - reference_include_fields)
        if unknown_fields:
            raise ValueError(
                f"selection has unknown include_fields for {reference['record_id']}: "
                + ", ".join(unknown_fields)
            )

        normalized_exclude_fields = [
            _normalize(value) for value in reference["exclude_fields"]
        ]
        if len(normalized_exclude_fields) != len(set(normalized_exclude_fields)):
            raise ValueError(
                f"selection exclude_fields must be unique after normalization for "
                f"{reference['record_id']}"
            )
        exclude_fields = set(normalized_exclude_fields)
        if include_fields & exclude_fields:
            raise ValueError(
                f"selection include/exclude conflict for {reference['record_id']}"
            )


def _validate_approved_selection_shape(selection: dict[str, Any]) -> None:
    _validate_selection_shape(selection)
    if selection["status"] != "approved":
        raise ValueError("selection must be explicitly approved")


def validate_selection(
    selection: dict[str, Any], retrieval_result: dict[str, Any]
) -> None:
    """Validate an approved 2-3 reference mapping against retrieved candidates."""
    _validate_approved_selection_shape(selection)
    _validate_schema(
        retrieval_result,
        "book-component-retrieval-result",
        "retrieval result",
    )
    if retrieval_result["status"] != "available":
        raise ValueError("retrieval result must be available")
    if selection["query_id"] != retrieval_result["query_id"]:
        raise ValueError("selection query_id must match retrieval result query_id")
    if selection["component_type"] != retrieval_result["component_type"]:
        raise ValueError(
            "selection component_type must match retrieval result component_type"
        )

    candidates_by_id = {
        candidate["record_id"]: candidate
        for candidate in retrieval_result["candidates"]
    }
    for reference in selection["selected_references"]:
        if reference["record_id"] not in candidates_by_id:
            raise ValueError(
                f"selected record is not a retrieved candidate: {reference['record_id']}"
            )
        candidate = candidates_by_id[reference["record_id"]]
        unavailable_fields = sorted(
            field
            for field in (_normalize(value) for value in reference["include_fields"])
            if candidate["field_scores"].get(field, 0) <= 0
        )
        if unavailable_fields:
            raise ValueError(
                "selection include_fields require matched evidence with field_scores > 0 "
                f"for {reference['record_id']}: " + ", ".join(unavailable_fields)
            )


def _validate_output_spec(output_spec: dict[str, Any]) -> None:
    if not isinstance(output_spec, dict):
        raise ValueError("output_spec must be an object")
    forbidden = sorted(set(output_spec) & _FORBIDDEN_PIXEL_TEXT_KEYS)
    if forbidden:
        raise ValueError(
            "output_spec requests readable text in generated pixels: "
            + ", ".join(forbidden)
        )
    mode = output_spec.get("text_rendering_mode", "editable-overlay")
    allowed = set(_OUTPUT_SPEC_FIELDS)
    if mode == INTEGRATED_MODE:
        allowed.update(_INTEGRATED_OUTPUT_SPEC_FIELDS)
    elif "text_rendering_mode" in output_spec:
        allowed.add("text_rendering_mode")
    if set(output_spec) != allowed:
        missing = sorted(allowed - set(output_spec))
        unknown = sorted(set(output_spec) - allowed)
        raise ValueError(
            f"output_spec has invalid fields; missing={missing}; unknown={unknown}"
        )

    for field in (
        "prompt_id",
        "aspect_ratio",
        "component_role",
        "composition",
        "image_content",
        "color_light_material",
        "editable_text_safe_zones",
        "print_and_crop",
    ):
        if not isinstance(output_spec[field], str) or not output_spec[field].strip():
            raise ValueError(f"output_spec.{field} must be a non-empty string")

    negatives = output_spec["negative_constraints"]
    if (
        not isinstance(negatives, list)
        or not negatives
        or any(not isinstance(value, str) or not value.strip() for value in negatives)
    ):
        raise ValueError(
            "output_spec.negative_constraints must be a non-empty string array"
        )

    overlay = output_spec["editable_text_overlay"]
    if (
        not isinstance(overlay, list)
        or not overlay
        or any(not isinstance(value, str) or value not in _OVERLAY_FIELDS for value in overlay)
        or len(set(overlay)) != len(overlay)
    ):
        raise ValueError(
            "output_spec.editable_text_overlay must contain unique supported editable fields"
        )

    overlay_values = output_spec["editable_text_values"]
    if (
        not isinstance(overlay_values, dict)
        or set(overlay_values) != set(overlay)
        or any(
            not isinstance(value, str) or not value.strip()
            for value in overlay_values.values()
        )
    ):
        raise ValueError(
            "output_spec.editable_text_values must be a non-empty string mapping "
            "with keys exactly matching editable_text_overlay"
        )


def _iter_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _iter_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_strings(item)


def _action_is_negated(clause: str, start: int) -> bool:
    prefix = clause[max(0, start - 24) : start]
    return bool(
        _ENGLISH_ACTION_NEGATION.search(prefix)
        or _CHINESE_ACTION_NEGATION.search(prefix)
    )


def _text_object_is_negated(clause: str, start: int) -> bool:
    prefix = clause[max(0, start - 24) : start]
    return bool(
        _ENGLISH_ACTION_NEGATION.search(prefix)
        or _CHINESE_ACTION_NEGATION.search(prefix)
    )


def _is_cjk_character(value: str) -> bool:
    codepoint = ord(value)
    return (
        0x3400 <= codepoint <= 0x4DBF
        or 0x4E00 <= codepoint <= 0x9FFF
        or 0xF900 <= codepoint <= 0xFAFF
    )


def _title_occurrences(text: str, title: str):
    if len(title) == 1 and _is_cjk_character(title):
        cjk = r"\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
        pattern = re.compile(rf"{re.escape(title)}(?![{cjk}])")
    elif title.isascii():
        pattern = re.compile(
            rf"(?<![a-z0-9_]){re.escape(title)}(?![a-z0-9_])"
        )
    else:
        pattern = re.compile(re.escape(title))
    yield from pattern.finditer(text)


def _contains_explicit_project_title(background_prompt: str, project_title: str) -> bool:
    """Find a title literal without treating short titles as arbitrary substrings."""
    text = _normalize(background_prompt)
    title = _normalize(project_title)
    if not title:
        return False

    cjk_count = sum(_is_cjk_character(value) for value in title)
    if cjk_count >= 2 or (not title.isascii() and len(title) >= 3):
        return title in text

    for opening, closing in (("《", "》"), ("「", "」"), ("『", "』"), ('"', '"'), ("'", "'")):
        if f"{opening}{title}{closing}" in text:
            return True

    for occurrence in _title_occurrences(text, title):
        prefix = text[max(0, occurrence.start() - 40) : occurrence.start()]
        if re.search(
            r"(?:book[-\s]+title|title|书名|标题)"
            r"\s*(?:(?:is|为|是)\s*|[:：=]\s*)?[《「『\"']?$",
            prefix,
        ):
            return True

    if title.isascii() and len(title) <= 2:
        return False

    for clause in _CLAUSE_SPLIT.split(text):
        actions = (
            *tuple(_ENGLISH_PIXEL_TEXT_ACTION.finditer(clause)),
            *tuple(_CHINESE_PIXEL_TEXT_ACTION.finditer(clause)),
        )
        for occurrence in _title_occurrences(clause, title):
            if any(
                not _action_is_negated(clause, action.start())
                and min(
                    abs(action.start() - occurrence.end()),
                    abs(occurrence.start() - action.end()),
                )
                <= 64
                for action in actions
            ):
                return True
    return False


def _has_pixel_text_action_request(value: Any) -> bool:
    """Detect controlled action/object pairs in either order within one clause."""
    for raw_text in _iter_strings(value):
        for clause in _CLAUSE_SPLIT.split(_normalize(raw_text)):
            english_objects = tuple(_ENGLISH_PIXEL_TEXT_OBJECT.finditer(clause))
            chinese_objects = tuple(_CHINESE_PIXEL_TEXT_OBJECT.finditer(clause))
            if not english_objects and not chinese_objects:
                continue
            actions = (
                *tuple(_ENGLISH_PIXEL_TEXT_ACTION.finditer(clause)),
                *tuple(_CHINESE_PIXEL_TEXT_ACTION.finditer(clause)),
            )
            for action in actions:
                if _action_is_negated(clause, action.start()):
                    continue
                objects = tuple(
                    item
                    for item in (*english_objects, *chinese_objects)
                    if not _text_object_is_negated(clause, item.start())
                )
                if any(
                    min(abs(action.start() - item.end()), abs(item.start() - action.end()))
                    <= 64
                    for item in objects
                ):
                    return True
    return False


def _pixel_genome(genome: dict[str, Any]) -> dict[str, Any]:
    """Return only design fields that directly govern background pixels."""
    return {field: genome[field] for field in _PIXEL_GENOME_FIELDS}


def _positive_generation_inputs(
    project: dict[str, Any],
    genome: dict[str, Any],
    selection: dict[str, Any],
    output_spec: dict[str, Any],
) -> dict[str, Any]:
    return {
        "project_truth": {
            "purpose": project.get("purpose", "unspecified"),
            "primary_readers": project.get("primary_readers", "unspecified"),
        },
        "design_genome": _pixel_genome(genome),
        "output_spec": {
            key: value
            for key, value in output_spec.items()
            if key
            not in {
                "negative_constraints",
                "editable_text_overlay",
                "editable_text_values",
                "integrated_text",
                "editable_text_backup",
                "text_rendering_mode",
                "prompt_id",
            }
        },
        "reference_mappings": [
            {
                key: value
                for key, value in reference.items()
                if key
                in {
                    "existing_baseline",
                    "adjustment_instruction",
                    "preserve_elements",
                    "required_changes",
                }
            }
            for reference in selection["selected_references"]
        ],
    }


def _reject_readable_text_in_generation_instructions(
    project: dict[str, Any],
    genome: dict[str, Any],
    selection: dict[str, Any],
    output_spec: dict[str, Any],
) -> None:
    positive_inputs = _positive_generation_inputs(
        project, genome, selection, output_spec
    )
    if _has_pixel_text_action_request(positive_inputs):
        raise ValueError(
            "positive generated-pixel instructions contain a controlled "
            "readable-text request via a readable-text object/action pair"
        )


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _reference_transfer_block(selection: dict[str, Any]) -> str:
    lines = []
    for reference in selection["selected_references"]:
        closed_mapping = {field: reference[field] for field in _MAPPING_FIELDS}
        lines.append(_json_text(closed_mapping))
    return "\n".join(lines)


def _positive_reference_mappings(selection: dict[str, Any]) -> dict[str, Any]:
    return {
        "reference_mappings": [
            {
                key: reference[key]
                for key in (
                    "existing_baseline",
                    "adjustment_instruction",
                    "preserve_elements",
                    "required_changes",
                )
            }
            for reference in selection["selected_references"]
        ]
    }


def validate_selection_prompt_safety(
    project: dict[str, Any], selection: dict[str, Any]
) -> None:
    """Preflight draft or approved reference prose before human approval."""
    _validate_schema(project, "project-config", "project")
    _validate_selection_shape(selection)
    transfer_block = _reference_transfer_block(selection)
    if _contains_explicit_project_title(transfer_block, project["title"]):
        raise ValueError(
            "final project title cannot appear anywhere in REFERENCE_TRANSFERS"
        )
    if _has_pixel_text_action_request(_positive_reference_mappings(selection)):
        raise ValueError(
            "positive reference mapping instructions contain a controlled "
            "readable-text request via a readable-text object/action pair"
        )


def _validate_generation_values(
    project_root: Path,
    selection: dict[str, Any],
    prompt: dict[str, Any],
    recompiled_prompt: dict[str, Any],
    generation_payload: dict[str, Any],
    generation_authorization: dict[str, Any],
) -> None:
    """Validate a generation payload and its exact project-local authorization."""
    if not all(
        isinstance(value, dict)
        for value in (
            selection,
            prompt,
            recompiled_prompt,
            generation_payload,
            generation_authorization,
        )
    ):
        raise ValueError(
            "generation bundle requires selection, prompt, recompiled prompt, "
            "payload, and authorization"
        )
    _validate_approved_selection_shape(selection)
    _validate_schema(prompt, "book-component-prompt", "prompt")
    _validate_schema(recompiled_prompt, "book-component-prompt", "recompiled prompt")
    _validate_schema(
        generation_payload,
        "book-project-image-generation-payload",
        "generation payload",
    )
    _validate_schema(
        generation_authorization,
        "book-project-image-generation-authorization",
        "generation authorization",
    )
    if prompt != recompiled_prompt:
        raise ValueError("committed prompt must exactly match production recompile")
    if prompt["selection_id"] != selection["selection_id"]:
        raise ValueError("prompt selection_id must match approved selection")
    if prompt["component_type"] != selection["component_type"]:
        raise ValueError("prompt component_type must match approved selection")
    transfer_block = prompt["compiled_blocks"]["REFERENCE_TRANSFERS"]
    try:
        transfer_records = [
            json.loads(line) for line in transfer_block.splitlines() if line.strip()
        ]
    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError("REFERENCE_TRANSFERS must contain closed JSON mappings") from error
    transfer_record_ids = [record.get("record_id") for record in transfer_records]
    approved_record_ids = [
        reference["record_id"] for reference in selection["selected_references"]
    ]
    if transfer_record_ids != approved_record_ids:
        raise ValueError("prompt must retain the exact approved record_ids in order")
    if generation_payload["background_prompt"] != prompt["background_prompt"]:
        raise ValueError("generation payload must use the exact compiled background_prompt")
    for field, expected in (
        ("selection_id", selection["selection_id"]),
        ("prompt_id", prompt["prompt_id"]),
        ("component_type", selection["component_type"]),
    ):
        if generation_authorization[field] != expected:
            raise ValueError(f"generation authorization {field} binding mismatch")
    output_relative = Path(generation_authorization["output_path"])
    if (
        output_relative.is_absolute()
        or ".." in output_relative.parts
        or not output_relative.parts
        or output_relative.parts[0] != "generated"
    ):
        raise ValueError(
            "generation authorization output must be a project generated/ path"
        )

    references = generation_payload["referenced_image_paths"]
    authorized = generation_authorization["referenced_images"]
    if references != [item["relative_path"] for item in authorized]:
        raise ValueError("generation references must exactly match the authorized list")
    supplied_root = Path(os.path.abspath(project_root))
    try:
        root_stat = os.lstat(supplied_root)
    except OSError as error:
        raise ValueError("PROJECT_ROOT must be an existing directory") from error
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        raise ValueError("PROJECT_ROOT must be a real directory without links")
    root = Path(os.path.realpath(supplied_root))
    for reference, evidence in zip(references, authorized):
        relative = Path(reference)
        normalized_parts = {part.casefold() for part in relative.parts}
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or "overlays" in normalized_parts
        ):
            raise ValueError(
                "generation reference must be a project-relative non-overlay path"
            )
        safe_reference = safe_relative_file(root, reference)
        reference_fd = _open_regular_file(safe_reference)
        try:
            if os.fstat(reference_fd).st_nlink != 1:
                raise ValueError("authorized generation reference must not be a hardlink")
        finally:
            os.close(reference_fd)
        metadata = read_image_metadata(safe_reference)
        if sha256_file(safe_reference) != evidence["sha256"]:
            raise ValueError("authorized generation reference SHA-256 mismatch")
        if metadata["mime_type"] != evidence["mime_type"]:
            raise ValueError("authorized generation reference MIME mismatch")


def _negative_constraints(
    output_spec: dict[str, Any], *, integrated: bool = False
) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    mandatory = (
        _INTEGRATED_NEGATIVE_CONSTRAINTS
        if integrated
        else _MANDATORY_NEGATIVE_CONSTRAINTS
    )
    for value in (*mandatory, *output_spec["negative_constraints"]):
        normalized = _normalize(value)
        if integrated and normalized in _INTEGRATED_CONTRADICTORY_NEGATIVES:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(value.strip())
    return result


def compile_component_prompt(
    project: dict[str, Any],
    genome: dict[str, Any],
    selection: dict[str, Any],
    output_spec: dict[str, Any],
) -> dict[str, Any]:
    """Compile an approved mapping into a legacy or integrated cover prompt."""
    _validate_schema(project, "project-config", "project")
    _validate_schema(genome, "design-genome", "genome")
    _validate_approved_selection_shape(selection)
    validate_selection_prompt_safety(project, selection)
    _validate_output_spec(output_spec)
    integrated_plan = validate_integrated_typography(
        project, selection["component_type"], output_spec
    )
    if project["project_id"] != genome["project_id"]:
        raise ValueError("project and genome project_id must match")
    selected_ids = {
        reference["record_id"] for reference in selection["selected_references"]
    }
    if not selected_ids.issubset(set(genome["reference_ids"])):
        raise ValueError("selected record IDs must be bound by genome reference_ids")

    if integrated_plan is not None:
        positive_inputs = _positive_generation_inputs(
            project, genome, selection, output_spec
        )
        if any(
            contains_machine_identifier(value)
            for value in _iter_strings(positive_inputs)
        ):
            raise ValueError(
                "machine identifier is forbidden in positive cover instructions"
            )
    negative_constraints = _negative_constraints(
        output_spec, integrated=integrated_plan is not None
    )
    project_truth = {
        "project_id": project["project_id"],
        "mode": project["mode"],
        "primary_category": project["primary_category"],
        "purpose": project.get("purpose", "unspecified"),
        "primary_readers": project.get("primary_readers", "unspecified"),
        "title_handling": (
            "render only the exact registered project text in INTEGRATED_TEXT"
            if integrated_plan is not None
            else "real title remains metadata for an editable layout layer; do not render it"
        ),
    }
    genome_for_generation = _pixel_genome(genome)
    output_for_generation = {
        "component_type": selection["component_type"],
        "aspect_ratio": output_spec["aspect_ratio"],
        "editable_text_overlay": output_spec["editable_text_overlay"],
        "deliverable": (
            "cover image with exact registered typography; keep an editable backup"
            if integrated_plan is not None
            else "background image only; typography is added later as editable layers"
        ),
    }

    block_values = {
        "PROJECT_TRUTH": _json_text(project_truth),
        "COMPONENT_ROLE": output_spec["component_role"].strip(),
        "DESIGN_GENOME": _json_text(genome_for_generation),
        "REFERENCE_TRANSFERS": _reference_transfer_block(selection),
        "COMPOSITION": output_spec["composition"].strip(),
        "IMAGE_CONTENT": output_spec["image_content"].strip(),
        "COLOR_LIGHT_MATERIAL": output_spec["color_light_material"].strip(),
        "EDITABLE_TEXT_SAFE_ZONES": output_spec["editable_text_safe_zones"].strip(),
        "PRINT_AND_CROP": output_spec["print_and_crop"].strip(),
        "NEGATIVE": "; ".join(negative_constraints),
        "OUTPUT_SPEC": _json_text(output_for_generation),
    }
    block_order = EXPECTED_BLOCK_ORDER
    if integrated_plan is not None:
        block_values["INTEGRATED_TEXT"] = _json_text(
            {
                "instruction": "render these strings exactly once on their registered surfaces",
                "entries": integrated_plan.entries_as_dicts(),
            }
        )
        block_order = INTEGRATED_BLOCK_ORDER
    compiled_blocks = {name: block_values[name] for name in block_order}
    background_prompt = "\n\n".join(
        f"{name}\n{compiled_blocks[name]}" for name in block_order
    )
    title_guard_prompt = "\n\n".join(
        f"{name}\n{compiled_blocks[name]}"
        for name in block_order
        if name != "INTEGRATED_TEXT"
    )
    if _contains_explicit_project_title(title_guard_prompt, project["title"]):
        raise ValueError(
            "final project title cannot appear anywhere in the generated-pixel prompt"
        )
    _reject_readable_text_in_generation_instructions(
        project, genome, selection, output_spec
    )

    prompt: dict[str, Any] = {
        "schema_version": "1.0",
        "prompt_id": output_spec["prompt_id"],
        "component_type": selection["component_type"],
        "selection_id": selection["selection_id"],
        "compiled_blocks": compiled_blocks,
        "background_prompt": background_prompt,
        "generation_constraints": {
            "readable_text": (
                "exact-project-text" if integrated_plan is not None else "none"
            ),
            "logo": "none",
            "watermark": "none",
            "aspect_ratio": output_spec["aspect_ratio"],
        },
        "editable_text_overlay": dict(output_spec["editable_text_values"]),
        "negative_constraints": negative_constraints,
    }
    if integrated_plan is not None:
        prompt.update(
            {
                "text_rendering_mode": INTEGRATED_MODE,
                "integrated_text": integrated_plan.entries_as_dicts(),
                "editable_text_backup": integrated_plan.backup_dict(),
            }
        )
    _validate_schema(prompt, "book-component-prompt", "compiled prompt")
    return prompt


__all__ = [
    "EXPECTED_BLOCK_ORDER",
    "INTEGRATED_BLOCK_ORDER",
    "compile_component_prompt",
    "validate_selection",
    "validate_selection_prompt_safety",
]
