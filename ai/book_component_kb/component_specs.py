from __future__ import annotations

from typing import Any


COMPONENT_SPECS: dict[str, dict[str, Any]] = {
    "cover": {
        "record_prefix": "COV-CN-",
        "category_specs": (
            ("by-visual-strategy", "visual_strategy"),
            ("by-composition", "composition"),
            ("by-title-zone", "title_zone"),
            ("by-publication-year", "publication_year"),
        ),
        "retrieval_fields": ("visual_strategy", "composition", "title_zone"),
        "require_contiguous_books": True,
    },
    "chapter-opener": {
        "record_prefix": "CHO-CN-",
        "category_specs": (
            ("by-opening-mode", "opening_mode"),
            ("by-visual-strategy", "visual_strategy"),
            ("by-chapter-title-zone", "chapter_title_zone"),
            ("by-image-role", "image_role"),
            ("by-publication-year", "publication_year"),
        ),
        "retrieval_fields": (
            "opening_mode",
            "visual_strategy",
            "chapter_number_zone",
            "chapter_title_zone",
            "image_role",
            "text_image_relationship",
            "whitespace",
        ),
        "require_contiguous_books": False,
    },
}


def component_spec(component: str) -> dict[str, Any]:
    try:
        return COMPONENT_SPECS[component]
    except KeyError as error:
        raise ValueError(f"Unsupported component library: {component}") from error


def derived_names(component: str) -> tuple[str, ...]:
    category_specs = component_spec(component)["category_specs"]
    return (
        *(f"categories/{name}.json" for name, _ in category_specs),
        "catalog.json",
        "retrieval-index.json",
    )


__all__ = ["COMPONENT_SPECS", "component_spec", "derived_names"]
