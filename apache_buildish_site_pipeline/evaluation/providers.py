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

"""Provider-context validation over selected version contexts."""

from __future__ import annotations

from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity
from apache_buildish_site_pipeline.models.enums import RecordKind
from apache_buildish_site_pipeline.planning.types import IndexedProviderRecord, PlanningEvaluation, SelectedVersionContext

from . import diagnostic_codes
from .collector import DiagnosticCollector


def validate_providers(planning: PlanningEvaluation, collector: DiagnosticCollector) -> None:
    """Validate selected provider contexts remain deterministic."""

    for context in planning.selected_versions.contexts:
        matching_records = _matching_records(planning=planning, context=context)
        if len(matching_records) <= 1 and context.deterministic:
            continue
        collector.add(
            severity=DiagnosticSeverity.ERROR,
            code=diagnostic_codes.PROVIDER_CONTEXT_AMBIGUOUS,
            message=(
                f"Selected version context {context.kind.value} for "
                f"{context.component_slug}:{context.artifact_key} matches multiple normalized provider records"
            ),
            component_slug=context.component_slug,
            artifact_key=context.artifact_key,
            target_id=context.kind.value,
            details={
                "kind": context.kind.value,
                "version": context.version,
                "namedRefKey": context.named_ref_key,
                "releaseLine": context.release_line,
                "ref": context.ref,
                "matchingRecords": [
                    {
                        "provider": record.provider,
                        "externalId": record.external_id,
                        "version": record.version,
                        "namedRefKey": record.named_ref_key,
                        "ref": record.ref,
                    }
                    for record in matching_records
                ],
            },
        )


def _matching_records(*, planning: PlanningEvaluation, context: SelectedVersionContext) -> tuple[IndexedProviderRecord, ...]:
    provider_context = planning.provider_index.contexts_by_artifact.get((context.component_slug, context.artifact_key))
    if provider_context is None:
        return ()
    if context.kind is RecordKind.DEVELOPMENT:
        if context.ref is None:
            return ()
        return tuple(record for record in provider_context.development_records if record.ref == context.ref)
    if context.kind is RecordKind.LINE_HEAD:
        return provider_context.line_heads_by_release_line.get(context.release_line or "", ())
    if context.kind is RecordKind.RELEASED:
        return provider_context.released_by_version.get(context.version or "", ())
    if context.kind is RecordKind.NAMED_REF:
        if context.named_ref_key is not None:
            return provider_context.named_refs_by_key.get(context.named_ref_key, ())
        if context.ref is not None:
            return provider_context.refs_by_ref.get(context.ref, ())
        return ()
    if context.kind is RecordKind.CANDIDATE:
        return provider_context.candidates_by_version.get(context.version or "", ())