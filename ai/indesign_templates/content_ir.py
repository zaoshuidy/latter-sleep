"""Semantic BookContentIR converter.

Parses HTML and Markdown into the closed ``book-content-ir`` contract using
only the Python standard library. CSS coordinates, absolute positioning, and
any web-layout information are intentionally discarded: the IR carries meaning
(text, role, image location), never geometry.

Public API:

- ``parse_html(source: str) -> dict``
- ``parse_markdown(source: str) -> dict``
- ``source_digest(source: str) -> str``

Every parsed result is validated against ``book-content-ir.schema.json``
before it is returned; an invalid internal result raises ``ValueError`` with
the concrete schema messages joined in.

Semantics of nested mapped containers
-------------------------------------

Mapped tags (h1-h3, p, blockquote, aside, time, address, figcaption) may be
nested in valid HTML, e.g. ``<blockquote><p>引文</p></blockquote>``. The
parser keeps the outermost role: the inner text is merged into the outer
frame so the quote/note/signature role is never lost. Block-level inner
containers (h1-h3, p, blockquote, aside, address, figcaption) start a new
unit, so consecutive merged units are separated by a single space; inline
``<time>`` merges without added spacing, matching HTML text flow.

``<img>`` inside a mapped container is buffered into that frame and emitted
after the frame's own block, so block order follows document order:
``<p>前<img alt="图">后</p>`` yields ``[body("前后"), image("图")]``. Inside
the passive ``<figure>`` (which is never a frame), images emit immediately.

Unknown tags are passive containers: known children still parse, the wrapper
itself never creates a block, and its bare text is dropped.
"""

from __future__ import annotations

import hashlib
import re
from html.parser import HTMLParser
from typing import Any

from ai.contracts import validate_data

SCHEMA_NAME = "book-content-ir"

# Tags that must never reach a book pipeline, even when empty.
REJECTED_TAGS = frozenset({"script", "style", "iframe", "object", "embed"})

# Shared role ladder for HTML h1-h3 and Markdown #/##/### so the two syntaxes
# cannot drift apart.
_LEVEL_ROLES = {
    1: "book-title",
    2: "chapter-title",
    3: "section-title",
}

# Semantic HTML tags mapped to IR block roles. ``figure`` stays passive and is
# deliberately absent: it groups children but never produces a block itself.
HTML_MAPPING = {
    "h1": _LEVEL_ROLES[1],
    "h2": _LEVEL_ROLES[2],
    "h3": _LEVEL_ROLES[3],
    "p": "body",
    "blockquote": "quote",
    "aside": "note",
    "time": "date",
    "address": "signature",
    "figcaption": "caption",
}

# Block-level mapped tags: merging a closed frame into its parent separates
# the units with a space. Inline tags (``time``) merge without spacing.
_BLOCK_TAGS = frozenset({"h1", "h2", "h3", "p", "blockquote", "aside", "address", "figcaption"})

_IMAGE_TAG = "img"

_MARKDOWN_HEADINGS = _LEVEL_ROLES

_HEADING_PATTERN = re.compile(r"^(#{1,3})[ \t]+(.+)$")

__all__ = ["parse_html", "parse_markdown", "source_digest"]


def source_digest(source: str) -> str:
    """Return the lowercase hex SHA-256 of the UTF-8 encoded source string."""
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _normalized(text: str) -> str:
    """Collapse every run of whitespace (including newlines and NBSP) to one space."""
    return " ".join(text.split())


def _validated(payload: dict[str, Any]) -> dict[str, Any]:
    """Raise ValueError with schema details when the payload violates the IR contract."""
    errors = validate_data(payload, SCHEMA_NAME)
    if errors:
        raise ValueError("invalid book content IR: " + "; ".join(errors))
    return payload


class _ContentHTMLParser(HTMLParser):
    """Standard-library HTML parser that emits only semantic IR blocks.

    Frames mirror open mapped containers. Each frame holds ``parts``: text
    chunks and pending sub-blocks (images). Closing a frame emits its own
    block, or merges its content into the open parent frame when one exists.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[dict[str, Any]] = []
        self._content_stack: list[dict[str, Any]] = []

    def close(self) -> None:
        # Flush frames left open at EOF so a missing end tag never loses text.
        while self._content_stack:
            self._close_frame(self._content_stack.pop())
        super().close()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in REJECTED_TAGS:
            raise ValueError(f"rejected HTML tag <{tag}>")
        if tag == _IMAGE_TAG:
            self._emit_image(attrs)
            return
        if tag in HTML_MAPPING:
            self._content_stack.append(
                {"type": HTML_MAPPING[tag], "tag": tag, "parts": []}
            )

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # ``<img ... />`` style markup must still produce an image block.
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in HTML_MAPPING and self._content_stack:
            self._close_frame(self._content_stack.pop())
        # Unknown and passive containers (figure, section, div, spans, ...) end
        # without creating any block; their own text is dropped.

    def handle_data(self, data: str) -> None:
        if self._content_stack:
            self._content_stack[-1]["parts"].append(data)

    def _emit_image(self, attrs: list[tuple[str, str | None]]) -> None:
        attributes: dict[str, str] = {}
        alt = ""
        for name, value in attrs:
            name = name.lower()
            if name == "src" and value is not None:
                attributes["src"] = value
            elif name == "alt" and value is not None:
                alt = value
        image = {"type": "image", "text": alt, "attributes": attributes}
        if self._content_stack:
            # Buffer into the open frame so document order is preserved and
            # the image block follows its containing block.
            self._content_stack[-1]["parts"].append(image)
        else:
            self.blocks.append(image)

    def _close_frame(self, frame: dict[str, Any]) -> None:
        text_parts = [part for part in frame["parts"] if isinstance(part, str)]
        pending = [part for part in frame["parts"] if not isinstance(part, str)]
        text = _normalized("".join(text_parts))
        if self._content_stack:
            parent = self._content_stack[-1]
            if text:
                if frame["tag"] in _BLOCK_TAGS and _has_text(parent["parts"]):
                    parent["parts"].append(" ")
                parent["parts"].append(text)
            parent["parts"].extend(pending)
        else:
            if text:
                self.blocks.append({"type": frame["type"], "text": text, "attributes": {}})
            self.blocks.extend(pending)


def _has_text(parts: list[Any]) -> bool:
    return any(isinstance(part, str) and part.strip() for part in parts)


def parse_html(source: str) -> dict[str, Any]:
    parser = _ContentHTMLParser()
    parser.feed(source)
    parser.close()
    return _validated(
        {
            "schema_version": "1.0",
            "source_type": "html",
            "source_sha256": source_digest(source),
            "blocks": parser.blocks,
        }
    )


def _heading_of(line: str) -> tuple[str, str] | None:
    match = _HEADING_PATTERN.match(line)
    if match is None:
        return None
    level = len(match.group(1))
    # Heading text goes through the same whitespace normalization as every
    # other text path, so "# 第一  章" yields "第一 章" (single spaces).
    return _MARKDOWN_HEADINGS[level], _normalized(match.group(2))


def _quote_content(line: str) -> str:
    """Drop the leading ``>`` and one optional space, then strip the line."""
    rest = line[1:]
    if rest.startswith(" "):
        rest = rest[1:]
    return rest.strip()


def parse_markdown(source: str) -> dict[str, Any]:
    """Parse the supported Markdown subset: #/##/### headings, ``>`` quotes and
    blank-line-separated paragraphs. Dates, signatures and images are never
    guessed."""
    blocks: list[dict[str, Any]] = []
    lines = source.splitlines()
    index = 0
    count = len(lines)
    while index < count:
        line = lines[index].lstrip()
        if not line:
            index += 1
            continue

        heading = _heading_of(line)
        if heading is not None:
            block_type, text = heading
            if text:
                blocks.append({"type": block_type, "text": text, "attributes": {}})
            index += 1
            continue

        if line.startswith(">"):
            parts: list[str] = []
            while index < count:
                current = lines[index].lstrip()
                if not current.startswith(">"):
                    break
                parts.append(_quote_content(current))
                index += 1
            text = _normalized(" ".join(parts))
            if text:
                blocks.append({"type": "quote", "text": text, "attributes": {}})
            continue

        parts = [line.strip()]
        index += 1
        while index < count:
            next_line = lines[index].lstrip()
            if not next_line or _heading_of(next_line) is not None or next_line.startswith(">"):
                break
            parts.append(next_line.strip())
            index += 1
        text = _normalized(" ".join(parts))
        if text:
            blocks.append({"type": "body", "text": text, "attributes": {}})

    return _validated(
        {
            "schema_version": "1.0",
            "source_type": "markdown",
            "source_sha256": source_digest(source),
            "blocks": blocks,
        }
    )