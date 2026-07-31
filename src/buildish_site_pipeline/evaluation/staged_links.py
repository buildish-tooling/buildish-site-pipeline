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

"""Validate authored internal page links against resolved staged public routes."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from urllib.parse import urljoin, urlsplit

from buildish_site_pipeline.models.enums import DiagnosticSeverity, LinkCheckMode
from buildish_site_pipeline.page_support import (
    SUPPORTED_PAGE_EXTENSIONS,
    strips_suffix_in_pretty_route,
)
from buildish_site_pipeline.public_paths import normalize_public_path
from buildish_site_pipeline.planning.types import (
    PlanningEvaluation,
    ResolvedLinkCheckPolicy,
)
from buildish_site_pipeline.staging.front_matter import public_page_path

from . import diagnostic_codes
from .collector import DiagnosticCollector
from .types import ExtractedLinkReference, InventoryPage, PageInventory


def validate_staged_links(
    *,
    planning: PlanningEvaluation,
    page_inventory: PageInventory,
    collector: DiagnosticCollector,
) -> None:
    """Warn when authored internal page links do not resolve to any known page route."""

    policy = planning.site.link_checks
    if policy is None or not policy.enabled:
        return

    known_paths = {
        _page_public_path(page, mode=policy.mode) for page in page_inventory.pages
    }
    seen_occurrences: set[tuple[str, int, str, str]] = set()
    for page in page_inventory.pages:
        for reference in page.extracted_links:
            href = reference.href
            resolved = _resolve_link_target(page=page, href=href, policy=policy)
            if resolved is None or resolved in known_paths:
                continue
            occurrence_key = (
                str(page.source_path.resolve(strict=False)),
                reference.occurrence_index,
                href,
                resolved,
            )
            if occurrence_key in seen_occurrences:
                continue
            seen_occurrences.add(occurrence_key)
            collector.add(
                severity=DiagnosticSeverity.WARNING,
                code=diagnostic_codes.PAGE_LINK_TARGET_MISSING,
                message=(
                    f"{_diagnostic_source_location(page.relative_path, reference)}: "
                    f"internal page link {href!r} resolves to missing staged page {resolved}"
                ),
                component_slug=page.component_slug,
                artifact_key=page.artifact_key,
                details={
                    "inputId": page.input_id,
                    "sourcePath": str(page.source_path),
                    "sourceRelativePath": page.relative_path,
                    "occurrenceIndex": reference.occurrence_index,
                    "sourceLine": reference.source_line,
                    "sourceColumn": reference.source_column,
                    "approximateLineColumn": reference.approximate_line_column,
                    "sourceRoute": _page_public_path(page, mode=policy.mode),
                    "href": href,
                    "resolvedPath": resolved,
                    "mode": policy.mode.value,
                },
            )


def _resolve_link_target(
    *, page: InventoryPage, href: str, policy: ResolvedLinkCheckPolicy
) -> str | None:
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
    if relative_path.stem in {"index", "_index"}:
        html_relative = relative_path.parent.joinpath("index.html").as_posix().strip("/")
    else:
        html_relative = relative_path.with_suffix(".html").as_posix().strip("/")
    normalized_base = "/" + base_public_path.strip("/") if base_public_path.strip("/") else "/"
    if not html_relative:
        return f"{normalized_base.rstrip('/')}/index.html" if normalized_base != "/" else "/index.html"
    return f"{normalized_base.rstrip('/')}/{html_relative}" if normalized_base != "/" else f"/{html_relative}"


def _resolution_base_path(*, page: InventoryPage, mode: LinkCheckMode) -> str:
    current_path = _page_public_path(page, mode=mode)
    if mode is LinkCheckMode.DIRECTORY and _uses_directory_root_resolution(
        Path(page.routed_relative_path)
    ):
        return current_path if current_path == "/" else f"{current_path.rstrip('/')}/"
    return current_path


def _uses_directory_root_resolution(relative_path: Path) -> bool:
    return relative_path.stem in {"index", "_index"} or strips_suffix_in_pretty_route(
        relative_path
    )


def _looks_like_page_target(path: str) -> bool:
    if path.endswith("/"):
        return True
    suffix = PurePosixPath(path).suffix.lower()
    return suffix == "" or suffix in SUPPORTED_PAGE_EXTENSIONS


def _matches_internal_prefix(path: str, internal_prefixes: tuple[str, ...]) -> bool:
    for prefix in internal_prefixes:
        normalized_prefix = _normalize_public_path(prefix)
        if path == normalized_prefix or path.startswith(f"{normalized_prefix}/"):
            return True
    return False


def _normalize_public_path(path: str) -> str:
    return normalize_public_path(path, trailing_slash=False)


def _diagnostic_source_location(relative_path: str, reference: ExtractedLinkReference) -> str:
    if reference.source_line is None:
        return relative_path
    prefix = "~" if reference.approximate_line_column else ""
    if reference.source_column is None:
        return f"{relative_path}:{prefix}{reference.source_line}"
    return (
        f"{relative_path}:{prefix}{reference.source_line}:"
        f"{prefix}{reference.source_column}"
    )
