# Copyright 2026 The Apache Software Foundation

"""Main shared contextual evaluation entry point."""

from __future__ import annotations

from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity

from . import diagnostic_codes
from .collector import DiagnosticCollector
from .inputs import validate_inputs
from .limits import validate_limits
from .localization import validate_localization
from .page_scan import validate_page_scan
from .providers import validate_providers
from .publication import validate_publication
from .reference_index import validate_references
from .routes import validate_routes
from .summary import build_check_summary, build_run_status
from .types import (
    BlockingCondition,
    EvaluationArtifacts,
    EvaluationRequest,
    EvaluationResult,
    StageGateDecision,
)

from apache_buildish_site_pipeline.planning.types import PlanningEvaluation


def run_evaluation(*, request: EvaluationRequest, planning: PlanningEvaluation) -> EvaluationResult:
    """Run the shared contextual validation pipeline."""

    collector = DiagnosticCollector()
    publication_index = validate_publication(planning, collector)
    validate_references(planning=planning, publication_targets=publication_index.targets, collector=collector)
    route_inventory = validate_routes(planning, publication_index, collector)
    page_scan = validate_page_scan(planning, collector)
    validate_localization(planning=planning, page_scan=page_scan, collector=collector)
    validate_providers(planning, collector)
    validate_inputs(planning, collector)
    validate_limits(planning=planning, route_inventory=route_inventory, page_scan=page_scan, collector=collector)
    if planning.build_plan_candidate is None:
        collector.add(
            severity=DiagnosticSeverity.ERROR,
            code=diagnostic_codes.BUILD_PLAN_UNAVAILABLE,
            message="Planning did not produce a usable build plan candidate",
        )

    diagnostics = collector.build()
    counts = collector.counts()
    run_status = build_run_status(counts)
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
    stage_allowed = not blocking_conditions and planning.build_plan_candidate is not None
    return EvaluationResult(
        request=request,
        planning=planning,
        diagnostics=diagnostics,
        counts=counts,
        run_status=run_status,
        stage_gate=StageGateDecision(allowed=stage_allowed, blocking_conditions=blocking_conditions),
        build_plan=planning.build_plan_candidate if stage_allowed else None,
        artifacts=EvaluationArtifacts(
            publication_index=publication_index,
            route_inventory=route_inventory,
            page_scan=page_scan,
        ),
        check_summary=build_check_summary(
            counts=counts,
            fail_on_severity=request.fail_on_severity,
        ),
    )