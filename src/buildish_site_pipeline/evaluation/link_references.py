# Copyright 2026 The Buildish Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Extract structured authored link references without retaining whole page bodies."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from mistletoe import Document
from mistletoe.block_token import BlockCode, BlockToken, CodeFence
from mistletoe.span_token import AutoLink, InlineCode, Link, SpanToken

from .types import ExtractedLinkReference

_MARKDOWN_SUFFIXES = {".md", ".mdx"}
_ASCIIDOC_SUFFIXES = {".adoc", ".asciidoc"}
_HTML_HREF_PATTERN = re.compile(
    r"href\s*=\s*(?P<quote>[\"'])(?P<href>.*?)(?P=quote)",
    re.IGNORECASE,
)
_ASCIIDOC_LINK_PATTERN = re.compile(r"(?:^|[^A-Za-z0-9_])link:(?P<href>[^\[]+)\[[^\]]*\]")


@dataclass(slots=True)
class _LocatedHrefCandidate:
    href: str
    offset: int
    used: bool = False


def extract_link_references(
    *, source_path: Path, text: str, source_line_offset: int = 0
) -> tuple[ExtractedLinkReference, ...]:
    """Extract authored link occurrences with optional source locations."""

    suffix = source_path.suffix.lower()
    if suffix in _MARKDOWN_SUFFIXES:
        return _with_occurrence_indexes(
            _markdown_links(text=text, source_line_offset=source_line_offset)
        )
    if suffix in _ASCIIDOC_SUFFIXES:
        return _with_occurrence_indexes(
            _regex_links(
                text=text,
                source_line_offset=source_line_offset,
                pattern=_ASCIIDOC_LINK_PATTERN,
                href_group="href",
            )
        )
    return _with_occurrence_indexes(
        _regex_links(
            text=text,
            source_line_offset=source_line_offset,
            pattern=_HTML_HREF_PATTERN,
            href_group="href",
        )
    )


def _markdown_links(*, text: str, source_line_offset: int) -> tuple[ExtractedLinkReference, ...]:
    document = Document(text)
    lines = text.splitlines(keepends=True)
    leaf_blocks = tuple(_leaf_blocks(document))
    references: list[ExtractedLinkReference] = []
    for index, block in enumerate(leaf_blocks):
        if isinstance(block, (BlockCode, CodeFence)):
            continue
        start_line = getattr(block, "line_number", 1) or 1
        next_start_line = len(lines) + 1
        if index + 1 < len(leaf_blocks):
            next_start_line = getattr(leaf_blocks[index + 1], "line_number", len(lines) + 1)
        block_text = "".join(lines[start_line - 1 : next_start_line - 1])
        references.extend(
            _markdown_block_links(
                block=block,
                block_text=block_text,
                source_line_offset=source_line_offset + start_line - 1,
            )
        )
    return tuple(references)


def _leaf_blocks(node: BlockToken) -> Iterator[BlockToken]:
    children = tuple(cast(Iterable[object], getattr(node, "children", ()) or ()))
    block_children = tuple(child for child in children if isinstance(child, BlockToken))
    if block_children:
        for child in block_children:
            yield from _leaf_blocks(child)
        return
    if children:
        yield node


def _markdown_block_links(
    *, block: BlockToken, block_text: str, source_line_offset: int
) -> tuple[ExtractedLinkReference, ...]:
    masked_text = _mask_inline_code(block_text)
    references = list(
        _regex_links(
            text=masked_text,
            source_line_offset=source_line_offset,
            pattern=_HTML_HREF_PATTERN,
            href_group="href",
        )
    )
    markdown_candidates = list(_iter_markdown_link_candidates(masked_text))
    autolink_cursor = 0
    for href, is_autolink in _token_targets(block):
        if is_autolink:
            candidate = _find_autolink_candidate(masked_text, href, autolink_cursor)
            if candidate is not None:
                autolink_cursor = candidate.offset + len(href) + 2
                references.append(
                    _reference_from_offset(
                        text=masked_text,
                        href=href,
                        offset=candidate.offset,
                        source_line_offset=source_line_offset,
                        approximate_line_column=False,
                    )
                )
                continue
        else:
            candidate = _consume_candidate(markdown_candidates, href)
            if candidate is not None:
                references.append(
                    _reference_from_offset(
                        text=masked_text,
                        href=href,
                        offset=candidate.offset,
                        source_line_offset=source_line_offset,
                        approximate_line_column=False,
                    )
                )
                continue
        references.append(
            ExtractedLinkReference(
                href=href,
                occurrence_index=-1,
                source_line=source_line_offset + 1,
                source_column=None,
                approximate_line_column=True,
            )
        )
    return tuple(
        sorted(
            references,
            key=lambda reference: (
                reference.source_line or 0,
                reference.source_column or 0,
                reference.href,
            ),
        )
    )


def _token_targets(block: BlockToken) -> Iterator[tuple[str, bool]]:
    for child in cast(Iterable[object], getattr(block, "children", ()) or ()):  # pragma: no branch
        yield from _walk_span_targets(child)


def _walk_span_targets(node: object) -> Iterator[tuple[str, bool]]:
    if isinstance(node, InlineCode):
        return
    if isinstance(node, (Link, AutoLink)):
        target = getattr(node, "target", None)
        if isinstance(target, str) and target:
            yield target, isinstance(node, AutoLink)
        return
    if not isinstance(node, SpanToken):
        return
    for child in cast(Iterable[object], getattr(node, "children", ()) or ()):  # pragma: no branch
        yield from _walk_span_targets(child)


def _consume_candidate(
    candidates: list[_LocatedHrefCandidate], href: str
) -> _LocatedHrefCandidate | None:
    for candidate in candidates:
        if candidate.used or candidate.href != href:
            continue
        candidate.used = True
        return candidate
    return None


def _find_autolink_candidate(
    text: str, href: str, start_offset: int
) -> _LocatedHrefCandidate | None:
    offset = text.find(f"<{href}>", start_offset)
    if offset == -1:
        return None
    return _LocatedHrefCandidate(href=href, offset=offset + 1)


def _iter_markdown_link_candidates(text: str) -> Iterator[_LocatedHrefCandidate]:
    index = 0
    while index < len(text):
        if text[index] != "[":
            index += 1
            continue
        if index > 0 and text[index - 1] == "!":
            index += 1
            continue
        label_end = _find_closing_bracket(text, index)
        if label_end == -1:
            index += 1
            continue
        destination = _parse_inline_link_destination(text, label_end + 1)
        if destination is None:
            index = label_end + 1
            continue
        href, href_offset, closing_paren = destination
        if href:
            yield _LocatedHrefCandidate(href=href, offset=href_offset)
        index = closing_paren + 1


def _find_closing_bracket(text: str, start_offset: int) -> int:
    depth = 0
    index = start_offset + 1
    while index < len(text):
        if text[index] == "\\":
            index += 2
            continue
        if text[index] == "[":
            depth += 1
        elif text[index] == "]":
            if depth == 0:
                return index
            depth -= 1
        index += 1
    return -1


def _parse_inline_link_destination(
    text: str, start_offset: int
) -> tuple[str, int, int] | None:
    index = start_offset
    while index < len(text) and text[index] in " \t":
        index += 1
    if index >= len(text) or text[index] != "(":
        return None
    index += 1
    while index < len(text) and text[index] in " \t":
        index += 1
    if index >= len(text):
        return None
    if text[index] == "<":
        href_start = index + 1
        href_end = text.find(">", href_start)
        if href_end == -1:
            return None
        closing_paren = _find_closing_paren(text, href_end + 1)
        if closing_paren == -1:
            return None
        return text[href_start:href_end], href_start, closing_paren
    href_start = index
    nested_parentheses = 0
    while index < len(text):
        if text[index] == "\\":
            index += 2
            continue
        if text[index] == "(":
            nested_parentheses += 1
            index += 1
            continue
        if text[index] == ")":
            if nested_parentheses == 0:
                return text[href_start:index].strip(), href_start, index
            nested_parentheses -= 1
            index += 1
            continue
        if text[index] in " \t":
            href_end = index
            closing_paren = _find_closing_paren(text, index)
            if closing_paren == -1:
                return None
            return text[href_start:href_end], href_start, closing_paren
        index += 1
    return None


def _find_closing_paren(text: str, start_offset: int) -> int:
    index = start_offset
    while index < len(text):
        if text[index] == "\\":
            index += 2
            continue
        if text[index] == ")":
            return index
        index += 1
    return -1


def _mask_inline_code(text: str) -> str:
    masked = list(text)
    index = 0
    while index < len(text):
        if text[index] != "`":
            index += 1
            continue
        delimiter_width = 1
        while index + delimiter_width < len(text) and text[index + delimiter_width] == "`":
            delimiter_width += 1
        delimiter = "`" * delimiter_width
        closing_offset = text.find(delimiter, index + delimiter_width)
        if closing_offset == -1:
            index += delimiter_width
            continue
        for masked_index in range(index, closing_offset + delimiter_width):
            if masked[masked_index] != "\n":
                masked[masked_index] = " "
        index = closing_offset + delimiter_width
    return "".join(masked)


def _regex_links(
    *, text: str, source_line_offset: int, pattern: re.Pattern[str], href_group: str
) -> tuple[ExtractedLinkReference, ...]:
    references: list[ExtractedLinkReference] = []
    for match in pattern.finditer(text):
        href = match.group(href_group).strip()
        if not href:
            continue
        references.append(
            _reference_from_offset(
                text=text,
                href=href,
                offset=match.start(href_group),
                source_line_offset=source_line_offset,
                approximate_line_column=False,
            )
        )
    return tuple(references)


def _with_occurrence_indexes(
    references: tuple[ExtractedLinkReference, ...]
) -> tuple[ExtractedLinkReference, ...]:
    return tuple(
        ExtractedLinkReference(
            href=reference.href,
            occurrence_index=occurrence_index,
            source_line=reference.source_line,
            source_column=reference.source_column,
            approximate_line_column=reference.approximate_line_column,
        )
        for occurrence_index, reference in enumerate(references)
    )


def _reference_from_offset(
    *,
    text: str,
    href: str,
    offset: int,
    source_line_offset: int,
    approximate_line_column: bool,
) -> ExtractedLinkReference:
    source_line, source_column = _offset_to_line_column(text=text, offset=offset)
    return ExtractedLinkReference(
        href=href,
        occurrence_index=-1,
        source_line=source_line + source_line_offset,
        source_column=source_column,
        approximate_line_column=approximate_line_column,
    )


def _offset_to_line_column(*, text: str, offset: int) -> tuple[int, int]:
    source_line = text.count("\n", 0, offset) + 1
    line_start = text.rfind("\n", 0, offset)
    source_column = offset + 1 if line_start == -1 else offset - line_start
    return source_line, source_column