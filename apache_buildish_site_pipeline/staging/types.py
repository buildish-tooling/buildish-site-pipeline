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

"""Internal staging runtime types shared with planning."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from apache_buildish_site_pipeline.models import ProviderSnapshotV1
from apache_buildish_site_pipeline.models.enums import PlanningTarget
from apache_buildish_site_pipeline.models.planning_stage_contract import PipelineDiagnosticEntry, StageManifestV1, StageCommand

from apache_buildish_site_pipeline.planning.types import ResolvedLocalInput, ResolvedSiteConfig, SelectedVersionContext
from apache_buildish_site_pipeline.staging.worker_protocol import UnitContributionManifestWire


@dataclass(frozen=True, slots=True)
class EffectiveBuildPlan:
    """Immutable validated plan handed to later staging layers."""

    target: PlanningTarget
    workspace_root: Path
    site: ResolvedSiteConfig
    selected_versions: tuple[SelectedVersionContext, ...]
    planned_inputs: tuple[ResolvedLocalInput, ...]
    watch_roots: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class OperatorPolicy:
    """Operator-controlled runtime policy for staging execution."""

    pool_size: int = 1

    def normalized_pool_size(self) -> int:
        """Return a safe worker count for the first-wave serial coordinator."""

        return max(1, self.pool_size)


@dataclass(frozen=True, slots=True)
class StageDestination:
    """Publication target and private assembly options for one stage build."""

    stage_root: Path
    assembly_root: Path | None = None
    allow_replace_existing: bool = False


@dataclass(frozen=True, slots=True)
class BuildRequest:
    """All runtime inputs required to materialize one build/watch stage tree."""

    command: StageCommand
    build_plan: EffectiveBuildPlan
    diagnostics: tuple[PipelineDiagnosticEntry, ...]
    provider_snapshot: ProviderSnapshotV1
    destination: StageDestination
    operator_policy: OperatorPolicy = field(default_factory=OperatorPolicy)
    included_unit_ids: frozenset[str] | None = None
    seed_stage_root: Path | None = None
    seed_stage_removals: tuple[str, ...] = ()
    retained_unit_manifests: tuple[UnitContributionManifestWire, ...] = ()


@dataclass(frozen=True, slots=True)
class WorkRootLayout:
    """Directory layout for a single private staging run."""

    work_root: Path
    next_stage_root: Path
    content_root: Path
    static_root: Path
    data_root: Path
    fragments_root: Path
    units_root: Path


@dataclass(frozen=True, slots=True)
class BuildRunOutcome:
    """Coordinator result returned before optional visible-stage publication."""

    command: StageCommand
    layout: WorkRootLayout
    manifest: StageManifestV1
    worker_count: int
    built_unit_ids: tuple[str, ...]