# Copyright 2026 The Apache Software Foundation

"""Publication and route validation over resolved planning output."""

from __future__ import annotations

from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity

from . import diagnostic_codes
from .collector import DiagnosticCollector
from .types import PublicationIndex, PublishedTarget

from apache_buildish_site_pipeline.planning.types import PlanningEvaluation


def build_publication_index(planning: PlanningEvaluation) -> PublicationIndex:
    """Project resolved component publication targets into a normalized index."""

    targets = []
    for component in planning.site.components:
        publication = component.publication
        targets.extend(
            [
                PublishedTarget(component.slug, f"component:{component.slug}", publication.origin.key, publication.component_path),
                PublishedTarget(component.slug, f"development:{component.slug}", publication.origin.key, publication.development_path),
                PublishedTarget(component.slug, f"docs:{component.slug}", publication.origin.key, publication.docs_path),
                PublishedTarget(component.slug, f"assets:{component.slug}", publication.origin.key, publication.assets_path),
            ]
        )
    return PublicationIndex(targets=tuple(targets))


def validate_publication(planning: PlanningEvaluation, collector: DiagnosticCollector) -> PublicationIndex:
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