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

"""Implementation of the `check` CLI command."""

from __future__ import annotations

from apache_buildish_site_pipeline.evaluation import (
    EvaluationMode,
    EvaluationRequest,
    build_check_report,
    run_evaluation,
)
from apache_buildish_site_pipeline.models.enums import PlanningTarget
from apache_buildish_site_pipeline.planning import evaluate_planning

from ..cli.contract import ApplicationExitCode, CheckInvocation, CommandResult
from ..cli.reporting import render_text_report
from .shared import load_workspace_inputs


def run_check(invocation: CheckInvocation) -> CommandResult:
    """Execute one `check` command."""

    loaded_inputs = load_workspace_inputs(
        invocation.layout.workspace_root, invocation.layout.catalog_path
    )
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
        request=EvaluationRequest(
            mode=EvaluationMode.CHECK,
            fail_on_severity=invocation.fail_on_severity,
        ),
        planning=planning,
    )
    report = build_check_report(evaluation)
    exit_code = (
        ApplicationExitCode.SUCCESS
        if report.summary.passed
        else ApplicationExitCode.DOMAIN_FAILURE
    )
    return CommandResult(
        exit_code=exit_code, report=report, text_output=render_text_report(report)
    )
