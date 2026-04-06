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

"""Internal runtime types for contextual evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from apache_buildish_site_pipeline.models.enums import CheckFailureThreshold, RunStatus
from apache_buildish_site_pipeline.models.emitted.planning_stage_contract import (
    CheckSummary,
    PipelineDiagnosticEntry,
)

from apache_buildish_site_pipeline.planning.types import PlanningEvaluation
from apache_buildish_site_pipeline.staging.types import EffectiveBuildPlan


class EvaluationMode(StrEnum):
    """Shared evaluation mode for check/build/watch flows."""

    CHECK = "check"
    BUILD = "build"
    WATCH = "watch"


@dataclass(frozen=True, slots=True)
class EvaluationRequest:
    """Immutable request for one contextual evaluation run."""

    mode: EvaluationMode
    fail_on_severity: CheckFailureThreshold = CheckFailureThreshold.ERROR


@dataclass(frozen=True, slots=True)
class DiagnosticCounts:
    """Precomputed diagnostic counts for summaries and gates."""

    error_count: int
    warning_count: int
    info_count: int


@dataclass(frozen=True, slots=True)
class BlockingCondition:
    """One operator-readable reason why staging may not proceed."""

    code: str
    message: str
    component_slug: str | None = None
    artifact_key: str | None = None
    target_id: str | None = None


@dataclass(frozen=True, slots=True)
class PublishedTarget:
    """Normalized public route target used for route validation."""

    component_slug: str
    target_id: str
    origin_key: str
    path: str


@dataclass(frozen=True, slots=True)
class PublicationIndex:
    """Derived publication targets for evaluation."""

    targets: tuple[PublishedTarget, ...]


@dataclass(frozen=True, slots=True)
class RouteInventory:
    """Derived route and redirect inventory counts for safety checks."""

    route_count: int
    redirect_count: int


@dataclass(frozen=True, slots=True)
class ScannedPage:
    """One page-like file discovered beneath a selected input root."""

    input_id: str
    component_slug: str | None
    artifact_key: str | None
    relative_path: str
    translation_key: str | None


@dataclass(frozen=True, slots=True)
class PageScanResult:
    """Summary of read-only page scanning over selected local inputs."""

    pages: tuple[ScannedPage, ...]


@dataclass(frozen=True, slots=True)
class EvaluationArtifacts:
    """Derived contextual indexes that later phases may reuse."""

    publication_index: PublicationIndex
    route_inventory: RouteInventory
    page_scan: PageScanResult


@dataclass(frozen=True, slots=True)
class StageGateDecision:
    """Explicit answer to whether staging may proceed."""

    allowed: bool
    blocking_conditions: tuple[BlockingCondition, ...]


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    """Whole contextual evaluation result."""

    request: EvaluationRequest
    planning: PlanningEvaluation
    diagnostics: tuple[PipelineDiagnosticEntry, ...]
    counts: DiagnosticCounts
    run_status: RunStatus
    stage_gate: StageGateDecision
    build_plan: EffectiveBuildPlan | None
    artifacts: EvaluationArtifacts
    check_summary: CheckSummary
