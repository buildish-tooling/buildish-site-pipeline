# Copyright 2026 The Apache Software Foundation

"""Implementation of the `plan` CLI command."""

from __future__ import annotations

from apache_buildish_site_pipeline.planning import build_resolved_materialization_report, evaluate_planning

from ..cli_contract import ApplicationExitCode, CommandResult, PlanInvocation
from ..cli_reporting import render_text_report
from .shared import load_workspace_inputs


def run_plan(invocation: PlanInvocation) -> CommandResult:
    """Execute one `plan` command."""

    loaded_inputs = load_workspace_inputs(invocation.layout.repo_root)
    planning = evaluate_planning(
        target=invocation.planning_target,
        catalog=loaded_inputs.catalog,
        provider_snapshot=loaded_inputs.provider_snapshot,
        workspace_root=invocation.layout.repo_root,
        component_documents=loaded_inputs.component_documents,
        stage_root=invocation.layout.stage_root,
        work_root=invocation.layout.work_root,
        report_output=invocation.report_request.output_path,
    )
    report = build_resolved_materialization_report(planning)
    exit_code = ApplicationExitCode.DOMAIN_FAILURE if report.diagnostics else ApplicationExitCode.SUCCESS
    return CommandResult(exit_code=exit_code, report=report, text_output=render_text_report(report))