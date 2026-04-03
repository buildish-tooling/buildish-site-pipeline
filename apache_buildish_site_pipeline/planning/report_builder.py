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

"""Projection of planning evaluation into the public planning report model."""

from __future__ import annotations

from datetime import datetime, timezone

from apache_buildish_site_pipeline.models.planning_stage_contract import (
    ResolvedMaterializationEntry,
    ResolvedMaterializationReportV1,
)

from .types import PlanningEvaluation


def build_resolved_materialization_report(evaluation: PlanningEvaluation) -> ResolvedMaterializationReportV1:
    """Convert an in-memory planning evaluation into the public report model."""

    return ResolvedMaterializationReportV1(
        schema_version=1,
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        target=evaluation.target,
        entries=[
            ResolvedMaterializationEntry(
                source_key=local_input.identity.source_key,
                input_kind=local_input.identity.input_kind,
                component_slug=local_input.identity.component_slug,
                artifact_key=local_input.identity.artifact_key,
                release_line=local_input.identity.release_line,
                version=local_input.identity.version,
                ref=local_input.identity.ref,
                tag=local_input.identity.tag,
                commit_sha=local_input.identity.commit_sha,
                expected_local_path=str(local_input.expected_local_path),
                status=local_input.readiness.status,
                provenance=local_input.provenance,
                watch_eligible=local_input.watch_eligible,
                reason=local_input.readiness.reason.value if local_input.readiness.reason is not None else None,
            )
            for local_input in evaluation.local_inputs
        ],
        diagnostics=[*evaluation.diagnostics, *(evaluation.watch_plan.diagnostics if evaluation.watch_plan else ())],
    )