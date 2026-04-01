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

"""Operational and security-minded scale checks over evaluation inputs."""

from __future__ import annotations

from pathlib import Path

from buildish_site_pipeline.models.enums import DiagnosticSeverity
from buildish_site_pipeline.planning.types import PlanningEvaluation
from buildish_site_pipeline.resource_limits import DEFAULT_PROVIDER_SNAPSHOT_BYTES

from . import diagnostic_codes
from .collector import DiagnosticCollector
from .types import PageInventory, RouteInventory

_ROUTE_INVENTORY_LIMIT = 100_000
_REDIRECT_INVENTORY_LIMIT = 100_000
_CONTENT_INDEX_LIMIT = 100_000
_WATCH_FILESYSTEM_ENTRY_LIMIT = 100_000
_SELECTED_VERSION_CONTEXT_LIMIT = 512


def content_index_limit() -> int:
    """Return the effective page-inventory ceiling for the current run."""

    return _CONTENT_INDEX_LIMIT


def validate_limits(
    *,
    planning: PlanningEvaluation,
    route_inventory: RouteInventory,
    page_inventory: PageInventory,
    collector: DiagnosticCollector,
) -> None:
    """Apply documented operational ceilings to the resolved evaluation inputs."""

    _check_limit(
        collector=collector,
        metric="routeInventoryCount",
        measured=route_inventory.route_count,
        allowed=_ROUTE_INVENTORY_LIMIT,
        message="Resolved route inventory exceeds the documented default safety ceiling",
    )
    _check_limit(
        collector=collector,
        metric="redirectInventoryCount",
        measured=route_inventory.redirect_count,
        allowed=_REDIRECT_INVENTORY_LIMIT,
        message="Resolved redirect inventory exceeds the documented default safety ceiling",
    )
    _check_limit(
        collector=collector,
        metric="contentIndexCount",
        measured=len(page_inventory.pages),
        allowed=_CONTENT_INDEX_LIMIT,
        message="Scanned page inventory exceeds the documented default safety ceiling",
    )
    _check_limit(
        collector=collector,
        metric="selectedVersionContextCount",
        measured=len(planning.selected_versions.contexts),
        allowed=_SELECTED_VERSION_CONTEXT_LIMIT,
        message="Selected version-context inventory exceeds the documented default safety ceiling",
    )
    _check_limit(
        collector=collector,
        metric="providerSnapshotBytes",
        measured=planning.provider_index.snapshot_bytes,
        allowed=DEFAULT_PROVIDER_SNAPSHOT_BYTES,
        message="Provider snapshot size exceeds the documented default safety ceiling",
    )
    if planning.watch_plan is not None:
        _check_limit(
            collector=collector,
            metric="watchFilesystemEntryCount",
            measured=_count_watch_entries(
                planning,
                limit=_WATCH_FILESYSTEM_ENTRY_LIMIT,
            ),
            allowed=_WATCH_FILESYSTEM_ENTRY_LIMIT,
            message="Watch startup filesystem breadth exceeds the documented default safety ceiling",
        )


def _check_limit(
    *,
    collector: DiagnosticCollector,
    metric: str,
    measured: int,
    allowed: int,
    message: str,
) -> None:
    if measured <= allowed:
        return
    collector.add(
        severity=DiagnosticSeverity.ERROR,
        code=diagnostic_codes.OPERATIONAL_LIMIT_EXCEEDED,
        message=message,
        details={
            "metric": metric,
            "measured": measured,
            "allowed": allowed,
            "thresholdSource": "documentedDefault",
        },
    )


def _count_watch_entries(
    planning: PlanningEvaluation,
    *,
    limit: int | None = None,
) -> int:
    """Count watch entries, stopping once ``limit + 1`` proves an excess."""

    if planning.watch_plan is None:
        raise ValueError("Watch-entry counting requires one watch plan")
    total = 0
    seen_dirs: set[Path] = set()
    for root in planning.watch_plan.roots:
        remaining = None if limit is None else limit - total
        total += _count_entries_beneath(root, seen_dirs, limit=remaining)
        if limit is not None and total > limit:
            return total
    return total


def _count_entries_beneath(
    root: Path,
    seen_dirs: set[Path],
    *,
    limit: int | None,
) -> int:
    count = 0
    root_real = root.resolve(strict=False)
    stack = [root]
    while stack:
        directory = stack.pop()
        directory_real = directory.resolve(strict=False)
        if directory_real in seen_dirs:
            continue
        seen_dirs.add(directory_real)
        for entry in directory.iterdir():
            count += 1
            if limit is not None and count > limit:
                return count
            if entry.is_dir() and entry.resolve(strict=False).is_relative_to(root_real):
                stack.append(entry)
    return count
