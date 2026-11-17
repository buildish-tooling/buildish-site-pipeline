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

"""Publication and route validation over resolved planning output."""

from __future__ import annotations

from buildish_site_pipeline.models.enums import DiagnosticSeverity

from buildish_site_pipeline.staging.publication_paths import (
    public_path_for_context as public_path_for_context,
    target_id_for_context as target_id_for_context,
    publishes_family_path,
)

from . import diagnostic_codes
from .collector import DiagnosticCollector
from .types import PublicationIndex, PublishedTarget

from buildish_site_pipeline.planning.types import (
    PlanningEvaluation,
)


def build_publication_index(planning: PlanningEvaluation) -> PublicationIndex:
    """Project resolved component publication targets into a normalized index."""

    targets = []
    for component in planning.site.components:
        publication = component.publication
        targets.extend(
            [
                PublishedTarget(
                    component.slug,
                    f"component:{component.slug}",
                    publication.origin.key,
                    publication.component_path,
                ),
                PublishedTarget(
                    component.slug,
                    f"development:{component.slug}",
                    publication.origin.key,
                    publication.development_path,
                ),
                PublishedTarget(
                    component.slug,
                    f"assets:{component.slug}",
                    publication.origin.key,
                    publication.assets_path,
                ),
            ],
        )
        if publication.docs_path != publication.development_path:
            targets.append(
                PublishedTarget(
                    component.slug,
                    f"docs:{component.slug}",
                    publication.origin.key,
                    publication.docs_path,
                )
            )
    components = {item.slug: item for item in planning.site.components}
    return PublicationIndex(targets=tuple(
        target for target in targets
        if not target.target_id.startswith(("development:", "docs:"))
        or components[target.component_slug].publication.artifact_routing == "shared"
        or publishes_family_path(
            components[target.component_slug].publication,
            (ctx for ctx in planning.selected_versions.contexts if ctx.component_slug == target.component_slug),
            target.path,
        )
    ))


def validate_publication(
    planning: PlanningEvaluation, collector: DiagnosticCollector
) -> PublicationIndex:
    """Validate publication route uniqueness for the resolved plan."""

    publication_index = build_publication_index(planning)
    seen_targets: dict[tuple[str, str], PublishedTarget] = {}
    for target in publication_index.targets:
        lookup_key = (target.origin_key, target.path.lower())
        other_target = seen_targets.get(lookup_key)
        if other_target is not None:
            collector.add(
                severity=DiagnosticSeverity.ERROR,
                code=diagnostic_codes.PUBLICATION_ROUTE_COLLISION,
                message=(
                    f"Publication target {target.target_id} collides with {other_target.target_id} "
                    f"on {target.origin_key}:{target.path}"
                ),
                component_slug=target.component_slug,
                target_id=target.target_id,
                details={"otherTargetId": other_target.target_id, "path": target.path},
            )
            continue
        seen_targets[lookup_key] = target
    return publication_index
