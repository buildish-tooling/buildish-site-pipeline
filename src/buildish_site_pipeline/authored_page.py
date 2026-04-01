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

"""Shared parsing rules for authored page front matter."""

from __future__ import annotations

from dataclasses import dataclass

from buildish_site_pipeline.models.loading import LoadingError, load_yaml_mapping


@dataclass(frozen=True, slots=True)
class ParsedAuthoredPage:
    """One authored page split into validated metadata and body content."""

    metadata: dict[str, object]
    content: str
    source_line_offset: int


class AuthoredPageParseError(ValueError):
    """Raised when a front-matter block cannot be parsed safely."""

    def __init__(
        self,
        message: str,
        *,
        content: str | None,
        source_line_offset: int,
    ) -> None:
        super().__init__(message)
        self.content = content
        self.source_line_offset = source_line_offset


def parse_authored_page(text: str) -> ParsedAuthoredPage:
    """Parse optional YAML front matter with either LF or CRLF line endings."""

    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        return ParsedAuthoredPage(metadata={}, content=text, source_line_offset=0)

    closing_line_index = next(
        (
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.rstrip("\r\n") in {"---", "..."}
        ),
        None,
    )
    if closing_line_index is None:
        raise AuthoredPageParseError(
            "front matter is not terminated",
            content=None,
            source_line_offset=0,
        )

    raw_metadata = "".join(lines[1:closing_line_index])
    content = "".join(lines[closing_line_index + 1 :])
    source_line_offset = closing_line_index + 1
    if raw_metadata.strip() == "":
        return ParsedAuthoredPage(
            metadata={},
            content=content,
            source_line_offset=source_line_offset,
        )
    try:
        metadata = dict(load_yaml_mapping(raw_metadata))
    except LoadingError as exc:
        raise AuthoredPageParseError(
            f"front matter is malformed: {exc}",
            content=content,
            source_line_offset=source_line_offset,
        ) from exc
    return ParsedAuthoredPage(
        metadata=metadata,
        content=content,
        source_line_offset=source_line_offset,
    )
