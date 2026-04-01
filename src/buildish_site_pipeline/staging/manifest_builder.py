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

"""Manifest-last assembly entry point for finalized stage data."""

from __future__ import annotations

from typing import Any

from buildish_site_pipeline.models.emitted.planning_stage_contract import (
    StageCommand,
    StageManifestV1,
)
from buildish_site_pipeline.models.provider.provider_snapshot import (
    ProviderSnapshotDocumentV1,
)

from .aggregates import finalize_pages_and_write_aggregates
from .ownership import OwnedUnit
from .types import EffectiveBuildPlan, WorkRootLayout
from .worker_protocol import UnitContributionManifestWire, WorkerResultWire


def build_stage_manifest(
    *,
    layout: WorkRootLayout,
    command: StageCommand,
    build_plan: EffectiveBuildPlan,
    diagnostics: tuple[Any, ...],
    provider_snapshot: ProviderSnapshotDocumentV1,
    worker_results: tuple[WorkerResultWire, ...],
    retained_unit_manifests: tuple[UnitContributionManifestWire, ...] = (),
    owned_units: tuple[OwnedUnit, ...] | None = None,
) -> StageManifestV1:
    """Write all aggregate data files and emit the stage manifest last."""

    return finalize_pages_and_write_aggregates(
        layout=layout,
        command=command,
        build_plan=build_plan,
        diagnostics=diagnostics,
        provider_snapshot=provider_snapshot,
        worker_results=worker_results,
        retained_unit_manifests=retained_unit_manifests,
        owned_units=owned_units,
    )
