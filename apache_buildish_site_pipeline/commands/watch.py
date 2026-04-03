# Copyright 2026 The Apache Software Foundation

"""Implementation of the `watch` CLI command."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from watchfiles import watch

from apache_buildish_site_pipeline.evaluation import EvaluationMode, EvaluationRequest, run_evaluation
from apache_buildish_site_pipeline.models import DocumentFormat, PipelineDiagnosticEntry, load_stage_manifest
from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity, PlanningTarget, StageCommand
from apache_buildish_site_pipeline.models.planning_stage_contract import StageRunReportV1
from apache_buildish_site_pipeline.planning import evaluate_planning
from apache_buildish_site_pipeline.staging.execution import finalize_stage_publication, materialize_stage_tree

from ..cli_contract import ApplicationExitCode, CommandResult, WatchInvocation
from ..cli_errors import InvocationError, RetainedStageError, SitePipelineCliError, StageIntegrityError
from ..cli_reporting import emit_report, render_text_report, revalidate_report_request
from .shared import load_workspace_inputs
from .stage_report import build_stage_run_report

_WATCH_FAILURE_DIAGNOSTIC_CODE = "watchCycleFailure"


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


def run_watch(invocation: WatchInvocation, *, stdout) -> CommandResult:
    """Run the initial watch cycle and continue rebuilding on watched changes."""

    trusted_stage = _load_trusted_stage(invocation.layout.stage_root)
    cycle_number = 1
    outcome = _run_watch_cycle(
        invocation=invocation,
        cycle_number=cycle_number,
        trusted_stage=trusted_stage,
        prior_watch_roots=(),
    )
    _emit_cycle_report(invocation=invocation, report=outcome.report, stdout=stdout)

    if not outcome.report.summary.stage_usable:
        raise StageIntegrityError("Initial watch cycle failed before any trustworthy stage existed")
    if not outcome.watch_roots:
        raise StageIntegrityError("watch mode has no eligible roots to monitor after the initial cycle")

    trusted_stage = outcome.trusted_stage
    current_watch_roots = outcome.watch_roots
    last_report = outcome.report
    while True:
        restarted = False
        for raw_paths in _iter_watch_events(watch_roots=current_watch_roots):
            trigger_paths = _filter_trigger_paths(
                raw_paths=raw_paths,
                stage_root=invocation.layout.stage_root,
                work_root=invocation.layout.work_root,
                report_output=invocation.report_request.output_path,
            )
            if not trigger_paths:
                continue

            cycle_number += 1
            outcome = _run_watch_cycle(
                invocation=invocation,
                cycle_number=cycle_number,
                trusted_stage=trusted_stage,
                prior_watch_roots=current_watch_roots,
            )
            _emit_cycle_report(invocation=invocation, report=outcome.report, stdout=stdout)

            if not outcome.report.summary.stage_usable:
                raise StageIntegrityError(f"Watch cycle {cycle_number} left no trustworthy stage to serve")
            if not outcome.watch_roots:
                raise StageIntegrityError(f"watch mode has no eligible roots to monitor after cycle {cycle_number}")

            trusted_stage = outcome.trusted_stage
            last_report = outcome.report
            if outcome.watch_roots != current_watch_roots:
                current_watch_roots = outcome.watch_roots
                restarted = True
                break

        if not restarted:
            return CommandResult(
                exit_code=ApplicationExitCode.SUCCESS,
                report=last_report,
                text_output=render_text_report(last_report),
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

    watch_roots = planning.watch_plan.roots if planning.watch_plan is not None else prior_watch_roots
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


def _filter_trigger_paths(
    *,
    raw_paths: tuple[Path, ...],
    stage_root: Path,
    work_root: Path,
    report_output: Path | None,
) -> tuple[Path, ...]:
    excluded_roots = (stage_root.resolve(strict=False), work_root.resolve(strict=False))
    excluded_path = report_output.resolve(strict=False) if report_output is not None else None
    filtered: list[Path] = []
    for raw_path in raw_paths:
        normalized_path = raw_path.resolve(strict=False)
        if excluded_path is not None and normalized_path == excluded_path:
            continue
        if any(normalized_path.is_relative_to(root) for root in excluded_roots):
            continue
        filtered.append(normalized_path)
    return tuple(filtered)


def _iter_watch_events(*, watch_roots: tuple[Path, ...]) -> Iterator[tuple[Path, ...]]:
    for changes in watch(*(str(path) for path in watch_roots)):
        yield tuple(sorted((Path(changed_path) for _, changed_path in changes), key=str))


def _load_trusted_stage(stage_root: Path) -> TrustedStageState | None:
    normalized_stage_root = stage_root.resolve(strict=False)
    if normalized_stage_root.is_symlink() or (normalized_stage_root.exists() and not normalized_stage_root.is_dir()):
        return None
    manifest_path = normalized_stage_root / "manifest.json"
    if not manifest_path.exists() or not manifest_path.is_file():
        return None
    try:
        load_stage_manifest(
            manifest_path.read_text(encoding="utf-8"),
            document_format=DocumentFormat.JSON,
            source_name=str(manifest_path),
        )
    except Exception:
        return None
    return TrustedStageState(stage_root=normalized_stage_root, manifest_path=manifest_path)


def _build_cycle_failure_diagnostic(message: str) -> PipelineDiagnosticEntry:
    return PipelineDiagnosticEntry(
        severity=DiagnosticSeverity.ERROR,
        code=_WATCH_FAILURE_DIAGNOSTIC_CODE,
        message=message,
    )