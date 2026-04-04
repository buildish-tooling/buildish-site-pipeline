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

"""Implementation of the `build` CLI command."""

from __future__ import annotations

from apache_buildish_site_pipeline.evaluation import EvaluationMode, EvaluationRequest, run_evaluation
from apache_buildish_site_pipeline.models.enums import PlanningTarget, StageCommand
from apache_buildish_site_pipeline.planning import evaluate_planning
from apache_buildish_site_pipeline.staging.coordinator import publish_stage

from ..cli.contract import ApplicationExitCode, BuildInvocation, CommandResult
from ..cli.reporting import render_text_report
from .shared import load_workspace_inputs
from .stage_report import build_stage_run_report


def run_build(invocation: BuildInvocation) -> CommandResult:
    """Execute one `build` command."""

    loaded_inputs = load_workspace_inputs(invocation.layout.workspace_root, invocation.layout.catalog_path)
    planning = evaluate_planning(
        target=PlanningTarget.BUILD,
        catalog=loaded_inputs.catalog,
        provider_snapshot=loaded_inputs.provider_snapshot,
        workspace_root=invocation.layout.workspace_root,
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
        report = build_stage_run_report(
            command=StageCommand.BUILD,
            evaluation=evaluation,
            succeeded=False,
            wrote_stage=False,
            stage_usable=False,
            stage_root_path=None,
            manifest_path=None,
            workspace_root=invocation.layout.workspace_root,
            private_roots=(invocation.layout.work_root, invocation.layout.stage_root),
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
    report = build_stage_run_report(
        command=StageCommand.BUILD,
        evaluation=evaluation,
        succeeded=True,
        wrote_stage=True,
        stage_usable=True,
        stage_root_path=publication.stage_root,
        manifest_path=publication.manifest_path,
        workspace_root=invocation.layout.workspace_root,
        private_roots=(invocation.layout.work_root, invocation.layout.stage_root),
    )
    return CommandResult(exit_code=ApplicationExitCode.SUCCESS, report=report, text_output=render_text_report(report))