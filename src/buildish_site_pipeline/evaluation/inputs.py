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

"""Input-readiness validation and stage-blocking diagnostics."""

from __future__ import annotations

from buildish_site_pipeline.models.enums import (
    DiagnosticSeverity,
    MaterializationStatus,
)

from . import diagnostic_codes
from .collector import DiagnosticCollector

from buildish_site_pipeline.planning.types import PlanningEvaluation


def validate_inputs(
    planning: PlanningEvaluation, collector: DiagnosticCollector
) -> None:
    """Turn planning readiness results into shared evaluation diagnostics."""

    for local_input in planning.local_inputs:
        if local_input.readiness.status is MaterializationStatus.PRESENT:
            continue
        code = {
            MaterializationStatus.MISSING: diagnostic_codes.INPUT_MISSING,
            MaterializationStatus.STALE: diagnostic_codes.INPUT_STALE,
            MaterializationStatus.UNRESOLVED: diagnostic_codes.INPUT_UNRESOLVED,
        }[local_input.readiness.status]
        collector.add(
            severity=DiagnosticSeverity.ERROR,
            code=code,
            message=(
                f"Required input {local_input.identity.input_kind.value} for "
                f"{local_input.identity.component_slug or local_input.identity.source_key} is "
                f"{local_input.readiness.status.value}"
            ),
            component_slug=local_input.identity.component_slug,
            artifact_key=local_input.identity.artifact_key,
            target_id=local_input.identity.input_kind.value,
            details={
                "expectedLocalPath": str(local_input.expected_local_path),
                "reason": local_input.readiness.reason.value
                if local_input.readiness.reason
                else None,
            },
        )
