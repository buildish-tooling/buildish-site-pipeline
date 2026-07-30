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

"""Shared page-input extension rules for validation and staging.

The pipeline does not parse Markdown or AsciiDoc syntax itself. It only needs a
small, explicit allow-list of text page extensions so validation and staging can
agree on which authored files are treated as page inputs.
"""

from __future__ import annotations

from pathlib import Path

SUPPORTED_PAGE_EXTENSIONS = frozenset(
    {".adoc", ".asciidoc", ".htm", ".html", ".md", ".markdown", ".mdx"}
)
PRETTY_ROUTE_PAGE_EXTENSIONS = frozenset(
    {".adoc", ".asciidoc", ".md", ".markdown", ".mdx"}
)


def is_supported_page_path(path: Path) -> bool:
    """Return whether one source file should be treated as a stageable page."""

    return path.suffix.lower() in SUPPORTED_PAGE_EXTENSIONS


def strips_suffix_in_pretty_route(path: Path) -> bool:
    """Return whether a page extension should disappear from routed public paths."""

    return path.suffix.lower() in PRETTY_ROUTE_PAGE_EXTENSIONS