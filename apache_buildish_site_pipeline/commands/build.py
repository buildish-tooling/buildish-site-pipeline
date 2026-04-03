# Copyright 2026 The Apache Software Foundation

"""Implementation of the `build` CLI command."""

from __future__ import annotations

from datetime import datetime, timezone

from apache_buildish_site_pipeline.evaluation import EvaluationMode, EvaluationRequest, run_evaluation
from apache_buildish_site_pipeline.models.enums import PlanningTarget, StageCommand
from apache_buildish_site_pipeline.models.planning_stage_contract import StageRunReportV1, StageRunSummary
from apache_buildish_site_pipeline.planning import evaluate_planning
from apache_buildish_site_pipeline.staging.execution import publish_stage

from ..cli_contract import ApplicationExitCode, BuildInvocation, CommandResult
from ..cli_reporting import render_text_report
from .shared import load_workspace_inputs


def run_build(invocation: BuildInvocation) -> CommandResult:
    """Execute one `build` command."""

    loaded_inputs = load_workspace_inputs(invocation.layout.repo_root)
    planning = evaluate_planning(
        target=PlanningTarget.BUILD,
        catalog=loaded_inputs.catalog,
        provider_snapshot=loaded_inputs.provider_snapshot,
        workspace_root=invocation.layout.repo_root,
        component_documents=loaded_inputs.component_documents,
        stage_root=invocation.layout.stage_root,
        work_root=invocation.layout.work_root,
        report_output=invocation.report_request.output_path,
    )
    evaluation = run_evaluation(
        request=EvaluationRequest(mode=EvaluationMode.BUILD),
        planning=planning,
    )
    if not evaluation.stage_gate.allowed or evaluation.build_plan is None:
        report = _build_stage_report(
            command=StageCommand.BUILD,
            evaluation=evaluation,
            succeeded=False,
            wrote_stage=False,
            stage_usable=False,
            stage_root_path=None,
            manifest_path=None,
        )
        return CommandResult(
            exit_code=ApplicationExitCode.DOMAIN_FAILURE,
            report=report,
            text_output=render_text_report(report),
        )

    publication = publish_stage(
        build_plan=evaluation.build_plan,
        diagnostics=evaluation.diagnostics,
        provider_snapshot=loaded_inputs.provider_snapshot,
        stage_root=invocation.layout.stage_root,
    )
    report = _build_stage_report(
        command=StageCommand.BUILD,
        evaluation=evaluation,
        succeeded=True,
        wrote_stage=True,
        stage_usable=True,
        stage_root_path=publication.stage_root,
        manifest_path=publication.manifest_path,
    )
    return CommandResult(exit_code=ApplicationExitCode.SUCCESS, report=report, text_output=render_text_report(report))


def _build_stage_report(*, command, evaluation, succeeded, wrote_stage, stage_usable, stage_root_path, manifest_path):
    return StageRunReportV1(
        schema_version=1,
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        command=command,
        summary=StageRunSummary(
            status=evaluation.run_status,
            succeeded=succeeded,
            wrote_stage=wrote_stage,
            stage_usable=stage_usable,
            error_count=evaluation.counts.error_count,
            warning_count=evaluation.counts.warning_count,
            info_count=evaluation.counts.info_count,
        ),
        stage_root_path=str(stage_root_path) if stage_root_path is not None else None,
        manifest_path=str(manifest_path) if manifest_path is not None else None,
        diagnostics=list(evaluation.diagnostics),
    )