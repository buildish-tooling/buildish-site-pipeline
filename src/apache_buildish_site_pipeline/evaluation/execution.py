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

"""Main shared contextual evaluation entry point."""

from __future__ import annotations

from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity

from . import diagnostic_codes
from .collector import DiagnosticCollector
from .phases import collect_evaluation_artifacts
from .summary import build_check_summary, build_run_status
from .types import (
    EvaluationRequest,
    EvaluationResult,
    StageReadinessResult,
)

from apache_buildish_site_pipeline.planning.types import PlanningEvaluation


def run_evaluation(
    *, request: EvaluationRequest, planning: PlanningEvaluation
) -> EvaluationResult:
    """Run the shared contextual validation pipeline."""

    build_plan_result = planning.build_plan_result
    collector = DiagnosticCollector()
    artifacts = collect_evaluation_artifacts(planning=planning, collector=collector)
    if build_plan_result.candidate is None:
        collector.add(
            severity=DiagnosticSeverity.ERROR,
            code=diagnostic_codes.BUILD_PLAN_UNAVAILABLE,
            message="Planning did not produce a usable build plan candidate",
        )

    diagnostics = collector.build()
    counts = collector.counts()
    run_status = build_run_status(counts)
    stage_readiness = StageReadinessResult.from_diagnostics(
        diagnostics=diagnostics,
        build_plan_candidate=build_plan_result.candidate,
    )
    return EvaluationResult(
        request=request,
        planning=planning,
        diagnostics=diagnostics,
        counts=counts,
        run_status=run_status,
        stage_gate=stage_readiness.gate,
        build_plan=stage_readiness.build_plan,
        artifacts=artifacts,
        check_summary=build_check_summary(
            counts=counts,
            fail_on_severity=request.fail_on_severity,
        ),
    )
