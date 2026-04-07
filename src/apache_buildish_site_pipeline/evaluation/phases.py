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

"""Ordered evaluation phases that populate reusable validation artifacts."""

from __future__ import annotations

from apache_buildish_site_pipeline.planning.types import PlanningEvaluation

from .collector import DiagnosticCollector
from .inputs import validate_inputs
from .limits import validate_limits
from .localization import validate_localization
from .page_scan import validate_page_scan
from .providers import validate_providers
from .publication import validate_publication
from .reference_index import validate_references
from .routes import validate_routes
from .staged_links import validate_staged_links
from .types import EvaluationArtifacts


def collect_evaluation_artifacts(
    *, planning: PlanningEvaluation, collector: DiagnosticCollector
) -> EvaluationArtifacts:
    """Run the reusable validation phases and return their derived artifacts.

    The caller remains responsible for build-plan availability checks and final
    result assembly. This helper only runs the ordered read-only validation
    phases that contribute diagnostics and reusable inventories.
    """

    publication_index = validate_publication(planning, collector)
    validate_references(
        planning=planning,
        publication_targets=publication_index.targets,
        collector=collector,
    )
    route_inventory = validate_routes(planning, publication_index, collector)
    page_inventory = validate_page_scan(planning, collector)
    validate_localization(
        planning=planning,
        page_scan=page_inventory,
        collector=collector,
    )
    validate_staged_links(
        planning=planning,
        page_inventory=page_inventory,
        collector=collector,
    )
    validate_providers(planning, collector)
    validate_inputs(planning, collector)
    validate_limits(
        planning=planning,
        route_inventory=route_inventory,
        page_inventory=page_inventory,
        collector=collector,
    )
    return EvaluationArtifacts(
        publication_index=publication_index,
        route_inventory=route_inventory,
        page_inventory=page_inventory,
    )