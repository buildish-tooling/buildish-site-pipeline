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

"""Native event subscription and path filtering for the watch command."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from itertools import chain
from pathlib import Path

from watchfiles import Change, DefaultFilter, watch

from buildish_site_pipeline.staging.types import EffectiveBuildPlan

_WATCH_DEBOUNCE_MS = 250
_WATCH_STEP_MS = 50
_WATCH_RUST_TIMEOUT_MS = 250


class _WatchEventStream:
    """Coalescing wrapper around watchfiles with pipeline-output filtering."""

    def __init__(
        self,
        *,
        watch_roots: tuple[Path, ...],
        stage_root: Path,
        work_root: Path,
        report_output: Path | None,
        event_output: Path | None,
        stop_event: threading.Event,
    ) -> None:
        self._stage_root = stage_root.resolve(strict=False)
        self._work_root = work_root.resolve(strict=False)
        self._report_output = (
            report_output.resolve(strict=False) if report_output is not None else None
        )
        self._event_output = (
            event_output.resolve(strict=False) if event_output is not None else None
        )
        self._stop_event = stop_event
        self._default_filter = DefaultFilter()
        self._watch_roots = watch_roots
        self._raw_events = self._open_raw_events(watch_roots)

    @property
    def watch_roots(self) -> tuple[Path, ...]:
        """Return the roots owned by the current native watcher."""

        return self._watch_roots

    def prime(self) -> bool:
        """Advance through a timeout so native watch registration is complete."""

        return self.collect_dirty_paths(wait_for_first=False) is not None

    def replace_watch_roots(self, watch_roots: tuple[Path, ...]) -> bool:
        """Replace and prime the native watcher for a changed root set.

        Callers must reconcile the full pipeline state after this handoff. That
        reconciliation covers changes made after the preceding scan but before
        the replacement watcher completed registration.
        """

        if watch_roots == self._watch_roots:
            return not self._stop_event.is_set()
        self._close_raw_events(self._raw_events)
        self._watch_roots = watch_roots
        self._raw_events = self._open_raw_events(watch_roots)
        return self.prime()

    def _open_raw_events(
        self, watch_roots: tuple[Path, ...]
    ) -> Iterator[set[tuple[Change, str]]]:
        return watch(
            *(str(path) for path in watch_roots),
            watch_filter=self._watch_filter,
            debounce=_WATCH_DEBOUNCE_MS,
            step=_WATCH_STEP_MS,
            stop_event=self._stop_event,
            rust_timeout=_WATCH_RUST_TIMEOUT_MS,
            yield_on_timeout=True,
            raise_interrupt=False,
        )

    def collect_dirty_paths(self, *, wait_for_first: bool) -> tuple[Path, ...] | None:
        """Return one coalesced dirty set, or ``None`` when shutdown was requested."""

        if self._stop_event.is_set():
            return None

        dirty_paths: list[Path] = []
        while True:
            if self._stop_event.is_set():
                return None
            raw_changes = next(self._raw_events, None)
            if raw_changes is None:
                return None
            if not raw_changes:
                if dirty_paths:
                    return _coalesce_dirty_paths(dirty_paths)
                if not wait_for_first or self._stop_event.is_set():
                    return None if self._stop_event.is_set() else ()
                continue
            dirty_paths.extend(
                Path(changed_path).resolve(strict=False)
                for _, changed_path in raw_changes
            )

    def close(self) -> None:
        """Close the current native watcher iterator."""

        self._close_raw_events(self._raw_events)

    @staticmethod
    def _close_raw_events(
        raw_events: Iterator[set[tuple[Change, str]]],
    ) -> None:
        close = getattr(raw_events, "close", None)
        if callable(close):
            close()

    def _watch_filter(self, change: Change, changed_path: str) -> bool:
        return self._default_filter(
            change, changed_path
        ) and not _is_pipeline_owned_path(
            path=Path(changed_path),
            stage_root=self._stage_root,
            work_root=self._work_root,
            report_output=self._report_output,
            event_output=self._event_output,
        )


@contextmanager
def _open_watch_event_stream(
    *,
    watch_roots: tuple[Path, ...],
    stage_root: Path,
    work_root: Path,
    report_output: Path | None,
    event_output: Path | None,
    stop_event: threading.Event,
) -> Iterator[_WatchEventStream]:
    """Open one watchfiles-backed event stream for the steady-state loop."""

    event_stream = _WatchEventStream(
        watch_roots=watch_roots,
        stage_root=stage_root,
        work_root=work_root,
        report_output=report_output,
        event_output=event_output,
        stop_event=stop_event,
    )
    try:
        yield event_stream
    finally:
        event_stream.close()


def _derive_watch_roots(
    *,
    site_root: Path,
    catalog_path: Path,
    provider_snapshot_path: Path | None,
    planning_roots: tuple[Path, ...],
) -> tuple[Path, ...]:
    """Keep the watch scope narrow while preserving config and provider visibility."""

    return _coalesce_dirty_paths(
        (
            site_root.resolve(strict=False),
            catalog_path.resolve(strict=False),
            *(
                (provider_snapshot_path.resolve(strict=False),)
                if provider_snapshot_path is not None
                else ()
            ),
            *(root.resolve(strict=False) for root in planning_roots),
        ),
    )


def _build_plan_watch_roots(build_plan: EffectiveBuildPlan) -> tuple[Path, ...]:
    """Collect concrete local inputs that can invalidate an incremental build."""

    return tuple(
        candidate
        for candidate in (
            build_plan.site.site_pages_root,
            build_plan.site.site_assets_root,
            *(asset.source_path for asset in build_plan.site.vendor_assets),
            *(
                path
                for component in build_plan.site.components
                for path in (
                    component.metadata_file,
                    component.pages_root,
                    component.assets_root,
                    component.content_source.local_dir
                    if component.content_source is not None
                    else None,
                )
            ),
        )
        if candidate is not None
    )


def _coalesce_dirty_paths(paths: tuple[Path, ...] | list[Path]) -> tuple[Path, ...]:
    """Deduplicate noisy changed-path bursts into the smallest ancestor set."""

    coalesced: list[Path] = []
    for path in sorted(
        {candidate.resolve(strict=False) for candidate in paths},
        key=lambda item: (len(item.parts), str(item)),
    ):
        if any(
            path == existing or path.is_relative_to(existing) for existing in coalesced
        ):
            continue
        coalesced.append(path)
    return tuple(coalesced)


def _is_pipeline_owned_path(
    *,
    path: Path,
    stage_root: Path,
    work_root: Path,
    report_output: Path | None,
    event_output: Path | None,
) -> bool:
    """Return whether a path belongs to watch-owned or renderer-generated output."""

    normalized_path = path.resolve(strict=False)
    normalized_stage_root = stage_root.resolve(strict=False)
    normalized_work_root = work_root.resolve(strict=False)
    normalized_site_root = normalized_stage_root.parent
    if normalized_path == normalized_stage_root or normalized_path.is_relative_to(
        normalized_stage_root
    ):
        return True
    if normalized_path == normalized_work_root or normalized_path.is_relative_to(
        normalized_work_root
    ):
        return True
    generated_build_root = normalized_site_root / "build"
    if normalized_path == generated_build_root or normalized_path.is_relative_to(
        generated_build_root
    ):
        return True
    generated_resource_parent = normalized_site_root / "resources"
    generated_resource_root = generated_resource_parent / "_gen"
    if normalized_path == generated_resource_parent:
        return True
    if normalized_path == generated_resource_root or normalized_path.is_relative_to(
        generated_resource_root
    ):
        return True

    stage_parent = normalized_site_root
    stage_temp_prefix = f".{normalized_stage_root.name}."
    stage_backup_prefix = f".{normalized_stage_root.name}.backup."
    for candidate in chain((normalized_path,), normalized_path.parents):
        if candidate.parent == stage_parent and (
            candidate.name.startswith(stage_temp_prefix)
            or candidate.name.startswith(stage_backup_prefix)
        ):
            return True

    if report_output is not None:
        normalized_report_output = report_output.resolve(strict=False)
        if normalized_path == normalized_report_output:
            return True
        if (
            normalized_path.parent == normalized_report_output.parent
            and normalized_path.name.startswith(
                f".{normalized_report_output.name}.",
            )
        ):
            return True

    if event_output is None:
        return False
    normalized_event_output = event_output.resolve(strict=False)
    return normalized_path == normalized_event_output
