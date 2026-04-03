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

from dataclasses import dataclass
from pathlib import Path

from apache_buildish_site_pipeline.models.enums import PlanningTarget

from apache_buildish_site_pipeline.planning.types import ResolvedLocalInput, ResolvedSiteConfig, SelectedVersionContext


@dataclass(frozen=True, slots=True)
class EffectiveBuildPlan:
    """Immutable validated plan handed to later staging layers."""

    target: PlanningTarget
    workspace_root: Path
    site: ResolvedSiteConfig
    selected_versions: tuple[SelectedVersionContext, ...]
    planned_inputs: tuple[ResolvedLocalInput, ...]
    watch_roots: tuple[Path, ...]