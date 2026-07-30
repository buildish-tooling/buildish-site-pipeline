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

"""Internal runtime types for contextual evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Self

from buildish_site_pipeline.models.enums import (
    CheckFailureThreshold,
    DiagnosticSeverity,
    RunStatus,
)
from buildish_site_pipeline.models.emitted.planning_stage_contract import (
    CheckSummary,
    PipelineDiagnosticEntry,
)

from buildish_site_pipeline.planning.types import PlanningEvaluation
from buildish_site_pipeline.staging.types import EffectiveBuildPlan


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
class ExtractedLinkReference:
    """One authored link occurrence extracted from a page body for later checks."""

    href: str
    occurrence_index: int
    source_line: int | None
    source_column: int | None
    approximate_line_column: bool | None


@dataclass(frozen=True, slots=True)
class InventoryPage:
    """One discovered authored page plus the routing facts later checks reuse."""

    input_id: str
    component_slug: str | None
    artifact_key: str | None
    relative_path: str
    routed_relative_path: str
    source_path: Path
    base_public_path: str
    translation_key: str | None
    extracted_links: tuple[ExtractedLinkReference, ...]


@dataclass(frozen=True, slots=True)
class PageInventory:
    """Shared read-only page inventory for contextual evaluation checks."""

    pages: tuple[InventoryPage, ...]


ScannedPage = InventoryPage
PageScanResult = PageInventory


@dataclass(frozen=True, slots=True)
class EvaluationArtifacts:
    """Derived contextual indexes that later phases may reuse."""

    publication_index: PublicationIndex
    route_inventory: RouteInventory
    page_inventory: PageInventory


@dataclass(frozen=True, slots=True)
class StageGateDecision:
    """Explicit answer to whether staging may proceed."""

    allowed: bool
    blocking_conditions: tuple[BlockingCondition, ...]


@dataclass(frozen=True, slots=True)
class StageReadinessResult:
    """Explicit evaluation-to-staging handoff once diagnostics are finalized."""

    gate: StageGateDecision
    build_plan: EffectiveBuildPlan | None

    def __post_init__(self) -> None:
        """Reject contradictory states where gating and plan availability disagree."""

        if self.gate.allowed != (self.build_plan is not None):
            raise ValueError(
                "Stage-gate allowance must agree with build-plan availability"
            )
        if self.gate.allowed and self.gate.blocking_conditions:
            raise ValueError("Allowed stage gates may not carry blocking conditions")

    @classmethod
    def blocked(cls, *, blocking_conditions: tuple[BlockingCondition, ...]) -> Self:
        """Build a blocked handoff with no staging candidate."""

        return cls(
            gate=StageGateDecision(
                allowed=False,
                blocking_conditions=blocking_conditions,
            ),
            build_plan=None,
        )

    @classmethod
    def available(cls, *, build_plan: EffectiveBuildPlan) -> Self:
        """Build a ready handoff with one staging candidate."""

        return cls(
            gate=StageGateDecision(allowed=True, blocking_conditions=()),
            build_plan=build_plan,
        )

    @classmethod
    def from_diagnostics(
        cls,
        *,
        diagnostics: tuple[PipelineDiagnosticEntry, ...],
        build_plan_candidate: EffectiveBuildPlan | None,
    ) -> Self:
        """Normalize finalized diagnostics into one stage handoff contract."""

        blocking_conditions = tuple(
            BlockingCondition(
                code=diagnostic.code,
                message=diagnostic.message,
                component_slug=diagnostic.component_slug,
                artifact_key=diagnostic.artifact_key,
                target_id=diagnostic.target_id,
            )
            for diagnostic in diagnostics
            if diagnostic.severity is DiagnosticSeverity.ERROR
        )
        if build_plan_candidate is None or blocking_conditions:
            return cls.blocked(blocking_conditions=blocking_conditions)
        return cls.available(build_plan=build_plan_candidate)


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
