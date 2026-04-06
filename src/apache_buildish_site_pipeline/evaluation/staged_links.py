# Copyright 2026 The Apache Software Foundation
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

"""Validate authored internal page links against resolved staged public routes."""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path, PurePosixPath
from typing import cast
from urllib.parse import urljoin, urlsplit

from mistletoe import Document
from mistletoe.span_token import AutoLink, Link

from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity, LinkCheckMode
from apache_buildish_site_pipeline.public_paths import normalize_public_path
from apache_buildish_site_pipeline.staging.front_matter import public_page_path

from . import diagnostic_codes
from .collector import DiagnosticCollector
from .types import InventoryPage, PageInventory

_AUTHORED_PAGE_SUFFIXES = {".md", ".mdx", ".adoc", ".asciidoc", ".html"}
_MARKDOWN_SUFFIXES = {".md", ".mdx"}
_ASCIIDOC_SUFFIXES = {".adoc", ".asciidoc"}
_HTML_HREF_PATTERN = re.compile(r"href\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE)
_ASCIIDOC_LINK_PATTERN = re.compile(r"(?:^|[^A-Za-z0-9_])link:([^\[]+)\[[^\]]*\]")


def validate_staged_links(
    *, planning, page_inventory: PageInventory, collector: DiagnosticCollector
) -> None:
    """Warn when authored internal page links do not resolve to any known page route."""

    policy = planning.site.link_checks
    if policy is None or not policy.enabled:
        return

    known_paths = {
        _page_public_path(page, mode=policy.mode) for page in page_inventory.pages
    }
    seen: set[tuple[str, str, str]] = set()

    for page in page_inventory.pages:
        if page.body_text is None:
            continue
        for href in _extract_link_targets(page):
            resolved = _resolve_link_target(page=page, href=href, policy=policy)
            if resolved is None or resolved in known_paths:
                continue
            dedupe_key = (str(page.source_path), href, resolved)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            collector.add(
                severity=DiagnosticSeverity.WARNING,
                code=diagnostic_codes.PAGE_LINK_TARGET_MISSING,
                message=(
                    f"Internal page link {href!r} in {page.relative_path} resolves to missing staged page {resolved}"
                ),
                component_slug=page.component_slug,
                artifact_key=page.artifact_key,
                details={
                    "inputId": page.input_id,
                    "sourcePath": str(page.source_path),
                    "sourceRoute": _page_public_path(page, mode=policy.mode),
                    "href": href,
                    "resolvedPath": resolved,
                    "mode": policy.mode.value,
                },
            )


def _extract_link_targets(page: InventoryPage) -> tuple[str, ...]:
    suffix = page.source_path.suffix.lower()
    if suffix in _MARKDOWN_SUFFIXES:
        return tuple(_markdown_links(page.body_text or ""))
    if suffix in _ASCIIDOC_SUFFIXES:
        return tuple(_asciidoc_links(page.body_text or ""))
    return tuple(_html_links(page.body_text or ""))


def _markdown_links(text: str) -> set[str]:
    links: set[str] = set(_html_links(text))
    document = Document(text)
    stack: list[object] = list(cast(Iterable[object], document.children or ()))
    while stack:
        node = stack.pop()
        if isinstance(node, (Link, AutoLink)):
            target = getattr(node, "target", None)
            if isinstance(target, str) and target:
                links.add(target)
        children = getattr(node, "children", None)
        if children:
            stack.extend(cast(Iterable[object], children))
    return links


def _html_links(text: str) -> set[str]:
    return {match.group(1) for match in _HTML_HREF_PATTERN.finditer(text)}


def _asciidoc_links(text: str) -> set[str]:
    return {match.group(1).strip() for match in _ASCIIDOC_LINK_PATTERN.finditer(text)}


def _resolve_link_target(*, page: InventoryPage, href: str, policy) -> str | None:
    parsed = urlsplit(href.strip())
    if parsed.scheme or parsed.netloc or not parsed.path or href.startswith("#"):
        return None
    if not _looks_like_page_target(parsed.path):
        return None
    if parsed.path.startswith("/"):
        if not policy.check_root_absolute:
            return None
        resolved = _normalize_public_path(parsed.path)
        if not _matches_internal_prefix(resolved, policy.internal_prefixes):
            return None
        return resolved
    base_path = _resolution_base_path(page=page, mode=policy.mode)
    resolved = urlsplit(urljoin(f"https://buildish.invalid{base_path}", parsed.path)).path
    return _normalize_public_path(resolved)


def _page_public_path(page: InventoryPage, *, mode: LinkCheckMode) -> str:
    relative_path = Path(page.routed_relative_path)
    if mode is LinkCheckMode.DIRECTORY:
        return _normalize_public_path(
            public_page_path(page.base_public_path, relative_path),
        )
    return _normalize_public_path(
        _file_html_public_path(page.base_public_path, relative_path),
    )


def _file_html_public_path(base_public_path: str, relative_path: Path) -> str:
    html_relative = relative_path.with_suffix(".html").as_posix().strip("/")
    normalized_base = "/" + base_public_path.strip("/") if base_public_path.strip("/") else "/"
    if not html_relative:
        return f"{normalized_base.rstrip('/')}/index.html" if normalized_base != "/" else "/index.html"
    return f"{normalized_base.rstrip('/')}/{html_relative}" if normalized_base != "/" else f"/{html_relative}"


def _resolution_base_path(*, page: InventoryPage, mode: LinkCheckMode) -> str:
    current_path = _page_public_path(page, mode=mode)
    if mode is LinkCheckMode.DIRECTORY and Path(page.routed_relative_path).stem == "index":
        return current_path if current_path == "/" else f"{current_path.rstrip('/')}/"
    return current_path


def _looks_like_page_target(path: str) -> bool:
    if path.endswith("/"):
        return True
    suffix = PurePosixPath(path).suffix.lower()
    return suffix == "" or suffix in _AUTHORED_PAGE_SUFFIXES


def _matches_internal_prefix(path: str, internal_prefixes: tuple[str, ...]) -> bool:
    for prefix in internal_prefixes:
        normalized_prefix = _normalize_public_path(prefix)
        if path == normalized_prefix or path.startswith(f"{normalized_prefix}/"):
            return True
    return False


def _normalize_public_path(path: str) -> str:
    return normalize_public_path(path, trailing_slash=False)