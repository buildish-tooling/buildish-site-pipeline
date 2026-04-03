# Copyright 2026 The Apache Software Foundation

"""Implementation of the `watch` CLI command."""

from __future__ import annotations

import signal
import shutil
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import FrameType
from typing import Iterator

from watchfiles import DefaultFilter, watch

from apache_buildish_site_pipeline.evaluation import EvaluationMode, EvaluationRequest, run_evaluation
from apache_buildish_site_pipeline.models import DocumentFormat, PipelineDiagnosticEntry, load_stage_manifest
from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity, PlanningTarget, StageCommand
from apache_buildish_site_pipeline.models.planning_stage_contract import StageRunReportV1
from apache_buildish_site_pipeline.planning import evaluate_planning
from apache_buildish_site_pipeline.staging.execution import (
    finalize_stage_publication,
    materialize_stage_tree,
    validate_materialized_stage_tree,
    validate_visible_stage_target_path,
)

from ..cli_contract import ApplicationExitCode, CommandResult, WatchInvocation
from ..cli_errors import InvocationError, RetainedStageError, SitePipelineCliError, StageIntegrityError
from ..cli_reporting import emit_report, render_text_report, revalidate_report_request
from .shared import load_workspace_inputs
from .stage_report import build_stage_run_report

_WATCH_FAILURE_DIAGNOSTIC_CODE = "watchCycleFailure"
_WATCH_DEBOUNCE_MS = 250
_WATCH_STEP_MS = 50
_WATCH_RUST_TIMEOUT_MS = 250
_WATCH_SHUTDOWN_SIGNALS = (signal.SIGINT, signal.SIGTERM)


@dataclass(frozen=True, slots=True)
class TrustedStageState:
    """A previously published stage tree that passed manifest validation."""

    stage_root: Path
    manifest_path: Path


@dataclass(frozen=True, slots=True)
class WatchCycleOutcome:
    """One completed watch cycle plus the next roots to watch."""

    report: StageRunReportV1
    trusted_stage: TrustedStageState | None
    watch_roots: tuple[Path, ...]


@dataclass(slots=True)
class _WatchShutdownController:
    """Shared stop controller for graceful watch shutdown after steady state."""

    stop_event: threading.Event
    shutdown_requested: bool = False

    def request_shutdown(self) -> None:
        self.shutdown_requested = True
        self.stop_event.set()


class _WatchEventStream:
    """Coalescing wrapper around watchfiles with pipeline-output filtering."""

    def __init__(
        self,
        *,
        watch_roots: tuple[Path, ...],
        stage_root: Path,
        work_root: Path,
        report_output: Path | None,
        stop_event: threading.Event,
    ) -> None:
        self._stage_root = stage_root.resolve(strict=False)
        self._work_root = work_root.resolve(strict=False)
        self._report_output = report_output.resolve(strict=False) if report_output is not None else None
        self._stop_event = stop_event
        self._default_filter = DefaultFilter()
        self._raw_events = watch(
            *(str(path) for path in watch_roots),
            watch_filter=self._watch_filter,
            debounce=_WATCH_DEBOUNCE_MS,
            step=_WATCH_STEP_MS,
            stop_event=stop_event,
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
            dirty_paths.extend(Path(changed_path).resolve(strict=False) for _, changed_path in raw_changes)

    def close(self) -> None:
        close = getattr(self._raw_events, "close", None)
        if callable(close):
            close()

    def _watch_filter(self, change, changed_path: str) -> bool:
        return self._default_filter(change, changed_path) and not _is_pipeline_owned_path(
            path=Path(changed_path),
            stage_root=self._stage_root,
            work_root=self._work_root,
            report_output=self._report_output,
        )


def run_watch(invocation: WatchInvocation, *, stdout) -> CommandResult:
    """Run the initial watch cycle and continue rebuilding on watched changes."""

    trusted_stage = _load_trusted_stage(invocation.layout.stage_root)
    cycle_number = 1
    outcome = _run_watch_cycle(
        invocation=invocation,
        cycle_number=cycle_number,
        trusted_stage=trusted_stage,
        prior_watch_roots=_derive_watch_roots(repo_root=invocation.layout.repo_root, planning_roots=()),
    )
    _emit_cycle_report(invocation=invocation, report=outcome.report, stdout=stdout)

    if not outcome.report.summary.stage_usable:
        raise StageIntegrityError("Initial watch cycle failed before any trustworthy stage existed")

    trusted_stage = outcome.trusted_stage
    last_report = outcome.report
    current_watch_roots = outcome.watch_roots
    with _graceful_watch_shutdown() as shutdown_controller:
        with _open_watch_event_stream(
            watch_roots=current_watch_roots,
            stage_root=invocation.layout.stage_root,
            work_root=invocation.layout.work_root,
            report_output=invocation.report_request.output_path,
            stop_event=shutdown_controller.stop_event,
        ) as event_stream:
            while True:
                pending_dirty_paths = event_stream.collect_dirty_paths(wait_for_first=True)
                if pending_dirty_paths is None:
                    return _watch_success_result(last_report)

                cycle_number, trusted_stage, current_watch_roots, last_report = _run_follow_up_cycle(
                    invocation=invocation,
                    cycle_number=cycle_number,
                    trusted_stage=trusted_stage,
                    last_watch_roots=current_watch_roots,
                    stdout=stdout,
                )
                if shutdown_controller.shutdown_requested:
                    return _watch_success_result(last_report)

                while True:
                    pending_dirty_paths = event_stream.collect_dirty_paths(wait_for_first=False)
                    if pending_dirty_paths is None:
                        return _watch_success_result(last_report)
                    if not pending_dirty_paths:
                        break
                    cycle_number, trusted_stage, current_watch_roots, last_report = _run_follow_up_cycle(
                        invocation=invocation,
                        cycle_number=cycle_number,
                        trusted_stage=trusted_stage,
                        last_watch_roots=current_watch_roots,
                        stdout=stdout,
                    )


def _run_follow_up_cycle(
    *,
    invocation: WatchInvocation,
    cycle_number: int,
    trusted_stage: TrustedStageState | None,
    last_watch_roots: tuple[Path, ...],
    stdout,
) -> tuple[int, TrustedStageState | None, tuple[Path, ...], StageRunReportV1]:
    """Run one later watch cycle and enforce stage-integrity rules."""

    next_cycle_number = cycle_number + 1
    outcome = _run_watch_cycle(
        invocation=invocation,
        cycle_number=next_cycle_number,
        trusted_stage=trusted_stage,
        prior_watch_roots=last_watch_roots,
    )
    _emit_cycle_report(invocation=invocation, report=outcome.report, stdout=stdout)

    if not outcome.report.summary.stage_usable:
        raise StageIntegrityError(f"Watch cycle {next_cycle_number} left no trustworthy stage to serve")
    return next_cycle_number, outcome.trusted_stage, outcome.watch_roots, outcome.report


def _watch_success_result(report: StageRunReportV1) -> CommandResult:
    """Build the final success result for an orderly watch shutdown."""

    return CommandResult(
        exit_code=ApplicationExitCode.SUCCESS,
        report=report,
        text_output=render_text_report(report),
    )


def _run_watch_cycle(
    *,
    invocation: WatchInvocation,
    cycle_number: int,
    trusted_stage: TrustedStageState | None,
    prior_watch_roots: tuple[Path, ...],
) -> WatchCycleOutcome:
    try:
        loaded_inputs = load_workspace_inputs(invocation.layout.repo_root)
        planning = evaluate_planning(
            target=PlanningTarget.WATCH,
            catalog=loaded_inputs.catalog,
            provider_snapshot=loaded_inputs.provider_snapshot,
            workspace_root=invocation.layout.repo_root,
            component_documents=loaded_inputs.component_documents,
            stage_root=invocation.layout.stage_root,
            work_root=invocation.layout.work_root,
            report_output=invocation.report_request.output_path,
        )
        evaluation = run_evaluation(
            request=EvaluationRequest(
                mode=EvaluationMode.WATCH,
                fail_on_severity=invocation.fail_on_severity,
            ),
            planning=planning,
        )
    except (InvocationError, SitePipelineCliError) as exc:
        return _failed_cycle_outcome(
            cycle_number=cycle_number,
            trusted_stage=trusted_stage,
            prior_watch_roots=prior_watch_roots,
            diagnostics=(_build_cycle_failure_diagnostic(str(exc)),),
        )

    planning_roots = planning.watch_plan.roots if planning.watch_plan is not None else prior_watch_roots
    watch_roots = _derive_watch_roots(repo_root=invocation.layout.repo_root, planning_roots=planning_roots)
    if not evaluation.stage_gate.allowed or evaluation.build_plan is None:
        return WatchCycleOutcome(
            report=build_stage_run_report(
                command=StageCommand.WATCH,
                evaluation=evaluation,
                diagnostics=tuple(evaluation.diagnostics),
                succeeded=False,
                wrote_stage=False,
                stage_usable=trusted_stage is not None,
                stage_root_path=trusted_stage.stage_root if trusted_stage is not None else None,
                manifest_path=trusted_stage.manifest_path if trusted_stage is not None else None,
                cycle=cycle_number,
            ),
            trusted_stage=trusted_stage,
            watch_roots=watch_roots,
        )

    cycle_root = invocation.layout.work_root / "watch" / f"cycle-{cycle_number:06d}"
    candidate_stage_root = cycle_root / "stage"
    try:
        materialize_stage_tree(
            stage_root=candidate_stage_root,
            build_plan=evaluation.build_plan,
            diagnostics=tuple(evaluation.diagnostics),
            provider_snapshot=loaded_inputs.provider_snapshot,
        )
    except StageIntegrityError as exc:
        return _failed_cycle_outcome(
            cycle_number=cycle_number,
            trusted_stage=trusted_stage,
            prior_watch_roots=watch_roots,
            evaluation=evaluation,
            diagnostics=tuple(evaluation.diagnostics) + (_build_cycle_failure_diagnostic(str(exc)),),
        )

    try:
        publication = finalize_stage_publication(
            candidate_stage_root=candidate_stage_root,
            stage_root=invocation.layout.stage_root,
            allow_replace_existing=invocation.layout.stage_root.exists(),
        )
    except RetainedStageError as exc:
        return _failed_cycle_outcome(
            cycle_number=cycle_number,
            trusted_stage=trusted_stage,
            prior_watch_roots=watch_roots,
            evaluation=evaluation,
            diagnostics=tuple(evaluation.diagnostics) + (_build_cycle_failure_diagnostic(str(exc)),),
        )
    finally:
        shutil.rmtree(cycle_root, ignore_errors=True)

    next_trusted_stage = TrustedStageState(
        stage_root=publication.stage_root,
        manifest_path=publication.manifest_path,
    )
    return WatchCycleOutcome(
        report=build_stage_run_report(
            command=StageCommand.WATCH,
            evaluation=evaluation,
            succeeded=True,
            wrote_stage=True,
            stage_usable=True,
            stage_root_path=publication.stage_root,
            manifest_path=publication.manifest_path,
            cycle=cycle_number,
        ),
        trusted_stage=next_trusted_stage,
        watch_roots=watch_roots,
    )


def _failed_cycle_outcome(
    *,
    cycle_number: int,
    trusted_stage: TrustedStageState | None,
    prior_watch_roots: tuple[Path, ...],
    diagnostics: tuple[PipelineDiagnosticEntry, ...],
    evaluation=None,
) -> WatchCycleOutcome:
    return WatchCycleOutcome(
        report=build_stage_run_report(
            command=StageCommand.WATCH,
            evaluation=evaluation,
            diagnostics=diagnostics,
            succeeded=False,
            wrote_stage=False,
            stage_usable=trusted_stage is not None,
            stage_root_path=trusted_stage.stage_root if trusted_stage is not None else None,
            manifest_path=trusted_stage.manifest_path if trusted_stage is not None else None,
            cycle=cycle_number,
        ),
        trusted_stage=trusted_stage,
        watch_roots=prior_watch_roots,
    )


def _emit_cycle_report(*, invocation: WatchInvocation, report, stdout) -> None:
    if invocation.report_request.output_path is None:
        return
    request = revalidate_report_request(
        cwd=invocation.layout.repo_root,
        request=invocation.report_request,
        forbidden_roots=(invocation.layout.stage_root, invocation.layout.work_root),
    )
    emit_report(
        request=request,
        report=report,
        text_output=render_text_report(report),
        stdout=stdout,
    )


@contextmanager
def _open_watch_event_stream(
    *,
    watch_roots: tuple[Path, ...],
    stage_root: Path,
    work_root: Path,
    report_output: Path | None,
    stop_event: threading.Event,
) -> Iterator[_WatchEventStream]:
    """Open one watchfiles-backed event stream for the steady-state loop."""

    event_stream = _WatchEventStream(
        watch_roots=watch_roots,
        stage_root=stage_root,
        work_root=work_root,
        report_output=report_output,
        stop_event=stop_event,
    )
    try:
        yield event_stream
    finally:
        event_stream.close()


@contextmanager
def _graceful_watch_shutdown() -> Iterator[_WatchShutdownController]:
    """Translate later watch shutdown signals into an orderly stop request."""

    controller = _WatchShutdownController(stop_event=threading.Event())
    previous_handlers = {signum: signal.getsignal(signum) for signum in _WATCH_SHUTDOWN_SIGNALS}

    def _handle_shutdown(signum: int, frame: FrameType | None) -> None:
        del signum, frame
        controller.request_shutdown()

    try:
        for signum in _WATCH_SHUTDOWN_SIGNALS:
            signal.signal(signum, _handle_shutdown)
        yield controller
    finally:
        for signum, previous_handler in previous_handlers.items():
            signal.signal(signum, previous_handler)


def _derive_watch_roots(*, repo_root: Path, planning_roots: tuple[Path, ...]) -> tuple[Path, ...]:
    """Keep a stable workspace-level watch root so topology changes remain visible."""

    return _coalesce_dirty_paths((repo_root.resolve(strict=False), *(root.resolve(strict=False) for root in planning_roots)))


def _coalesce_dirty_paths(paths: tuple[Path, ...] | list[Path]) -> tuple[Path, ...]:
    """Deduplicate noisy changed-path bursts into the smallest ancestor set."""

    coalesced: list[Path] = []
    for path in sorted({candidate.resolve(strict=False) for candidate in paths}, key=lambda item: (len(item.parts), str(item))):
        if any(path == existing or path.is_relative_to(existing) for existing in coalesced):
            continue
        coalesced.append(path)
    return tuple(coalesced)


def _is_pipeline_owned_path(
    *,
    path: Path,
    stage_root: Path,
    work_root: Path,
    report_output: Path | None,
) -> bool:
    """Return whether a changed path belongs to watch-owned outputs or temp files."""

    normalized_path = path.resolve(strict=False)
    normalized_stage_root = stage_root.resolve(strict=False)
    normalized_work_root = work_root.resolve(strict=False)
    if normalized_path == normalized_stage_root or normalized_path.is_relative_to(normalized_stage_root):
        return True
    if normalized_path == normalized_work_root or normalized_path.is_relative_to(normalized_work_root):
        return True

    stage_parent = normalized_stage_root.parent
    stage_temp_prefix = f".{normalized_stage_root.name}."
    stage_backup_prefix = f".{normalized_stage_root.name}.backup."
    if normalized_path.parent == stage_parent and (
        normalized_path.name.startswith(stage_temp_prefix) or normalized_path.name.startswith(stage_backup_prefix)
    ):
        return True

    if report_output is None:
        return False
    normalized_report_output = report_output.resolve(strict=False)
    if normalized_path == normalized_report_output:
        return True
    return normalized_path.parent == normalized_report_output.parent and normalized_path.name.startswith(
        f".{normalized_report_output.name}.",
    )


def _load_trusted_stage(stage_root: Path) -> TrustedStageState | None:
    try:
        validate_visible_stage_target_path(stage_root)
    except StageIntegrityError:
        return None

    normalized_stage_root = stage_root.resolve(strict=False)
    try:
        if not normalized_stage_root.exists() or not normalized_stage_root.is_dir():
            return None
        validate_materialized_stage_tree(normalized_stage_root)
        manifest_path = normalized_stage_root / "manifest.json"
        if not manifest_path.exists() or not manifest_path.is_file() or manifest_path.is_symlink():
            return None
        load_stage_manifest(
            manifest_path.read_text(encoding="utf-8"),
            document_format=DocumentFormat.JSON,
            source_name=str(manifest_path),
        )
    except OSError:
        return None
    except Exception:
        return None
    return TrustedStageState(stage_root=normalized_stage_root, manifest_path=manifest_path)


def _build_cycle_failure_diagnostic(message: str) -> PipelineDiagnosticEntry:
    return PipelineDiagnosticEntry(
        severity=DiagnosticSeverity.ERROR,
        code=_WATCH_FAILURE_DIAGNOSTIC_CODE,
        message=message,
    )