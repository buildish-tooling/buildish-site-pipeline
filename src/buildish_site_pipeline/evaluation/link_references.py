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
from bisect import bisect_right
from collections import defaultdict, deque
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from mistletoe import Document
from mistletoe.block_token import BlockCode, BlockToken, CodeFence
from mistletoe.span_token import AutoLink, InlineCode, Link, SpanToken

from buildish_site_pipeline.page_support import (
    ASCIIDOC_PAGE_EXTENSIONS,
    MARKDOWN_PAGE_EXTENSIONS,
)

from .types import ExtractedLinkReference

_HTML_HREF_PATTERN = re.compile(
    r"href\s*=\s*(?P<quote>[\"'])(?P<href>.*?)(?P=quote)",
    re.IGNORECASE,
)
_ASCIIDOC_LINK_PATTERN = re.compile(r"(?:^|[^A-Za-z0-9_])link:(?P<href>[^\[]+)\[[^\]]*\]")
_SIMPLE_REFERENCE_DEFINITION_PATTERN = re.compile(
    r"""
    ^[ ]{0,3}\[(?P<label>[^\[\]\r\n]+)\]:
    [ \t]*(?P<href>[^ \t\r\n]+)
    (?:[ \t]+(?:"[^"\r\n]*"|'[^'\r\n]*'|\([^)\r\n]*\)))?
    [ \t]*$
    """,
    re.VERBOSE,
)
_REFERENCE_DEFINITION_PREFIX_PATTERN = re.compile(
    r"^ {0,3}\[[^\[\]\r\n]+\]:"
)
_FULL_REFERENCE_LINK_PATTERN = re.compile(
    r"(?<!!)\[(?P<text>[^\[\]\r\n]+)\]\[(?P<label>[^\[\]\r\n]+)\]"
)
_MARKDOWN_BLOCK_PREFIX_PATTERN = re.compile(
    r"^ {0,3}(?:#{1,6}(?:[ \t]|$)|>|(?:[-+*]|\d{1,9}[.)])[ \t]+)"
)
_MARKDOWN_BREAK_PATTERN = re.compile(
    r"^ {0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,}|=+)[ \t]*$"
)


@dataclass(frozen=True, slots=True)
class _LocatedHrefCandidate:
    href: str
    offset: int
    approximate_line_column: bool = False


@dataclass(frozen=True, slots=True)
class _SourceLocator:
    """Translate character offsets without rescanning the source prefix."""

    line_starts: tuple[int, ...]

    @classmethod
    def for_text(cls, text: str) -> _SourceLocator:
        return cls(
            line_starts=(
                0,
                *(match.end() for match in re.finditer("\n", text)),
            )
        )

    def line_column(self, offset: int) -> tuple[int, int]:
        line_index = bisect_right(self.line_starts, offset) - 1
        return line_index + 1, offset - self.line_starts[line_index] + 1


def extract_link_references(
    *, source_path: Path, text: str, source_line_offset: int = 0
) -> tuple[ExtractedLinkReference, ...]:
    """Extract authored link occurrences with optional source locations."""

    suffix = source_path.suffix.lower()
    if suffix in MARKDOWN_PAGE_EXTENSIONS:
        return _with_occurrence_indexes(
            _markdown_links(text=text, source_line_offset=source_line_offset)
        )
    if suffix in ASCIIDOC_PAGE_EXTENSIONS:
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
    fast_candidates = _fast_inline_markdown_candidates(text)
    if fast_candidates is None:
        fast_candidates = _fast_full_reference_markdown_candidates(text)
    if fast_candidates is not None:
        locator = _SourceLocator.for_text(text)
        return tuple(
            _reference_from_offset(
                locator=locator,
                href=candidate.href,
                offset=candidate.offset,
                source_line_offset=source_line_offset,
                approximate_line_column=candidate.approximate_line_column,
            )
            for candidate in fast_candidates
        )

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


def _fast_inline_markdown_candidates(
    text: str,
) -> tuple[_LocatedHrefCandidate, ...] | None:
    """Return candidates when plain inline-link scanning is unambiguous.

    Mistletoe remains the correctness fallback for code, raw HTML, autolinks,
    references, escapes, and entity handling. Plain inline links can avoid its
    quadratic span-token search on very link-dense paragraphs.
    """

    if any(marker in text for marker in ("`", "<", "][", "\\", "&")):
        return None
    if any(
        line.startswith(("    ", "\t"))
        or line.lstrip().startswith(("~~~", "```"))
        for line in text.splitlines()
    ):
        return None
    candidates = tuple(_iter_markdown_link_candidates(text))
    expected_candidate_count = len(re.findall(r"(?<!!)\][ \t]*\(", text))
    if len(candidates) != expected_candidate_count or any(
        "\n" in candidate.href or "\r" in candidate.href
        for candidate in candidates
    ):
        return None
    return candidates


def _fast_full_reference_markdown_candidates(
    text: str,
) -> tuple[_LocatedHrefCandidate, ...] | None:
    """Return plain full-reference links without invoking Mistletoe.

    This intentionally narrow path accepts one ``[text][label]`` occurrence per
    source line and simple single-line ``[label]: target`` definitions, with
    or without a quoted or parenthesized title. More expressive reference
    syntax remains with Mistletoe so this optimization does not become a
    second general-purpose Markdown parser.
    """

    if any(marker in text for marker in ("`", "<", "\\", "&")):
        return None
    if re.search(r"(?<!!)\][ \t]*\(", text):
        return None
    lines = text.splitlines(keepends=True)
    if any(
        line.startswith(("    ", "\t"))
        or line.lstrip().startswith(("~~~", "```"))
        for line in lines
    ):
        return None

    definitions: dict[str, str] = {}
    definition_lines: set[int] = set()
    definition_allowed = True
    for line_index, line in enumerate(lines):
        line_without_ending = line.rstrip("\r\n")
        if not line_without_ending.strip():
            definition_allowed = True
            continue
        definition_match = _SIMPLE_REFERENCE_DEFINITION_PATTERN.fullmatch(
            line_without_ending
        )
        if definition_match is not None:
            if not definition_allowed:
                return None
            href = definition_match.group("href")
            if any(marker in href for marker in ("(", ")", '"', "'")):
                return None
            normalized_label = _normalize_reference_label(
                definition_match.group("label")
            )
            if not normalized_label:
                return None
            definitions.setdefault(normalized_label, href)
            definition_lines.add(line_index)
            continue
        if _REFERENCE_DEFINITION_PREFIX_PATTERN.match(line_without_ending):
            return None
        definition_allowed = False
    if not definitions:
        return None

    candidates: list[_LocatedHrefCandidate] = []
    line_offset = 0
    paragraph_offset: int | None = None
    saw_full_reference = False
    for line_index, line in enumerate(lines):
        if line_index in definition_lines:
            paragraph_offset = None
            line_offset += len(line)
            continue
        if not line.strip():
            paragraph_offset = None
            line_offset += len(line)
            continue
        if _MARKDOWN_BLOCK_PREFIX_PATTERN.match(
            line
        ) or _MARKDOWN_BREAK_PATTERN.fullmatch(line.rstrip("\r\n")):
            return None
        if paragraph_offset is None:
            paragraph_offset = line_offset
        marker_count = line.count("][")
        if marker_count == 0:
            line_offset += len(line)
            continue
        matches = tuple(_FULL_REFERENCE_LINK_PATTERN.finditer(line))
        if marker_count != 1 or len(matches) != 1:
            return None
        saw_full_reference = True
        match = matches[0]
        href = definitions.get(_normalize_reference_label(match.group("label")))
        if href is not None:
            candidates.append(
                _LocatedHrefCandidate(
                    href=href,
                    offset=paragraph_offset,
                    approximate_line_column=True,
                )
            )
        line_offset += len(line)
    return tuple(candidates) if saw_full_reference else None


def _normalize_reference_label(label: str) -> str:
    return " ".join(label.split()).casefold()


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
    locator = _SourceLocator.for_text(masked_text)
    references = list(
        _regex_links(
            text=masked_text,
            source_line_offset=source_line_offset,
            pattern=_HTML_HREF_PATTERN,
            href_group="href",
            locator=locator,
        )
    )
    markdown_candidates = _index_markdown_link_candidates(masked_text)
    autolink_cursor = 0
    for href, is_autolink in _token_targets(block):
        if is_autolink:
            candidate = _find_autolink_candidate(masked_text, href, autolink_cursor)
            if candidate is not None:
                autolink_cursor = candidate.offset + len(href) + 2
                references.append(
                    _reference_from_offset(
                        locator=locator,
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
                        locator=locator,
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
    candidates: dict[str, deque[_LocatedHrefCandidate]], href: str
) -> _LocatedHrefCandidate | None:
    matching_candidates = candidates.get(href)
    return matching_candidates.popleft() if matching_candidates else None


def _index_markdown_link_candidates(
    text: str,
) -> dict[str, deque[_LocatedHrefCandidate]]:
    candidates: defaultdict[str, deque[_LocatedHrefCandidate]] = defaultdict(deque)
    for candidate in _iter_markdown_link_candidates(text):
        candidates[candidate.href].append(candidate)
    return dict(candidates)


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
    *,
    text: str,
    source_line_offset: int,
    pattern: re.Pattern[str],
    href_group: str,
    locator: _SourceLocator | None = None,
) -> tuple[ExtractedLinkReference, ...]:
    effective_locator = locator or _SourceLocator.for_text(text)
    references: list[ExtractedLinkReference] = []
    for match in pattern.finditer(text):
        href = match.group(href_group).strip()
        if not href:
            continue
        references.append(
            _reference_from_offset(
                locator=effective_locator,
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
    locator: _SourceLocator,
    href: str,
    offset: int,
    source_line_offset: int,
    approximate_line_column: bool,
) -> ExtractedLinkReference:
    source_line, source_column = locator.line_column(offset)
    return ExtractedLinkReference(
        href=href,
        occurrence_index=-1,
        source_line=source_line + source_line_offset,
        source_column=None if approximate_line_column else source_column,
        approximate_line_column=approximate_line_column,
    )
