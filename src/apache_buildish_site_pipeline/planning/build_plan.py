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

"""Bridge from planning evaluation to an immutable build-plan candidate."""

from __future__ import annotations

from apache_buildish_site_pipeline.models.enums import (
    MaterializationStatus,
    PlanningTarget,
)

from apache_buildish_site_pipeline.staging.types import EffectiveBuildPlan

from .types import (
    PlanToBuildBridge,
    ResolvedLocalInput,
    ResolvedSiteConfig,
    SelectedVersionSet,
    WatchInputPlan,
)


def build_effective_build_plan(
    *,
    target: PlanningTarget,
    site: ResolvedSiteConfig,
    selected_versions: SelectedVersionSet,
    local_inputs: tuple[ResolvedLocalInput, ...],
    watch_plan: WatchInputPlan | None,
) -> tuple[PlanToBuildBridge, EffectiveBuildPlan | None]:
    """Build the staging handoff document when planning is usable."""

    blocking_inputs = tuple(
        local_input.identity
        for local_input in local_inputs
        if local_input.readiness.status is not MaterializationStatus.PRESENT
    )
    watch_ready = target is PlanningTarget.BUILD or (
        watch_plan is not None and len(watch_plan.roots) > 0
    )
    bridge = PlanToBuildBridge(
        ready=selected_versions.deterministic and not blocking_inputs and watch_ready,
        blocking_inputs=blocking_inputs,
        deterministic=selected_versions.deterministic,
        watch_ready=watch_ready,
    )
    if not bridge.ready:
        return bridge, None
    return (
        bridge,
        EffectiveBuildPlan(
            target=target,
            workspace_root=site.workspace_root,
            site=site,
            selected_versions=selected_versions.contexts,
            planned_inputs=local_inputs,
            watch_roots=watch_plan.roots if watch_plan is not None else (),
        ),
    )
