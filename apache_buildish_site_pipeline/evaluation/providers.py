# Copyright 2026 The Apache Software Foundation

"""Provider-context validation over selected version contexts."""

from __future__ import annotations

from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity

from . import diagnostic_codes
from .collector import DiagnosticCollector

from apache_buildish_site_pipeline.planning.types import PlanningEvaluation


def validate_providers(planning: PlanningEvaluation, collector: DiagnosticCollector) -> None:
    """Validate selected provider contexts remain deterministic."""

    if planning.selected_versions.deterministic:
        return
    for context in planning.selected_versions.contexts:
        if context.deterministic:
            continue
        collector.add(
            severity=DiagnosticSeverity.ERROR,
            code=diagnostic_codes.PROVIDER_CONTEXT_AMBIGUOUS,
            message=(
                f"Selected version context {context.kind.value} for "
                f"{context.component_slug}:{context.artifact_key} is not deterministic"
            ),
            component_slug=context.component_slug,
            artifact_key=context.artifact_key,
            target_id=context.kind.value,
        )