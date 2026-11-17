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

"""Resolve only selected and explicitly designated released facts before staging."""

from typing import Literal

from buildish_site_pipeline.models.emitted.execution import SnapshotInput
from buildish_site_pipeline.models.emitted.planning_stage_contract import (
    PipelineDiagnosticEntry,
)
from buildish_site_pipeline.models.enums import DiagnosticSeverity, RecordKind
from .errors import PlanningInputFailure
from .release_facts import resolve_release_fact
from .selection import _choose_best_record
from .types import (
    ProviderSnapshotIndex,
    ResolvedSiteConfig,
    SelectedVersionSet,
    ResolvedArtifactDesignations,
    ResolvedReleaseFact,
)


def resolve_designation_facts(
    site: ResolvedSiteConfig,
    index: ProviderSnapshotIndex,
    selected: SelectedVersionSet,
    snapshot_inputs: tuple[SnapshotInput, ...],
) -> tuple[
    tuple[ResolvedArtifactDesignations, ...],
    tuple[tuple[str, str, ResolvedReleaseFact], ...],
    tuple[PipelineDiagnosticEntry, ...],
]:
    """Keep target facts independent of desired/effective publication contexts."""
    result = []
    facts = []
    diagnostics = []
    inputs = {
        item.component_slug: item
        for item in snapshot_inputs
        if item.component_slug is not None
    }
    for component in site.components:
        status: Literal["present", "missing", "not-configured"] = "not-configured"
        if component.snapshot_path is not None:
            source = inputs.get(component.slug)
            if source is None:
                raise PlanningInputFailure(
                    f"Missing explicit snapshot input status for component {component.slug}"
                )
            if source.status.value not in {"present", "missing"}:
                raise PlanningInputFailure(
                    f"Invalid snapshot input status for component {component.slug}"
                )
            status = "present" if source.status.value == "present" else "missing"
        for artifact in component.artifacts:
            lifecycle = artifact.lifecycle
            latest = lifecycle.latest_stable if lifecycle else None
            lines = (
                tuple((line.key, line.latest) for line in lifecycle.release_lines or ())
                if lifecycle
                else ()
            )
            designated = set(version for _, version in lines)
            if latest is not None:
                designated.add(latest)
            selected_versions: set[str] = set()
            for context in selected.contexts:
                version = context.version
                if (
                    version is not None
                    and context.component_slug == component.slug
                    and context.artifact_key == artifact.key
                    and context.kind is RecordKind.RELEASED
                ):
                    selected_versions.add(version)
            context_index = index.contexts_by_artifact.get(
                (component.slug, artifact.key)
            )
            targets = []
            for version in sorted(designated | selected_versions):
                records = (
                    context_index.released_by_version.get(version, ())
                    if context_index
                    else ()
                )
                record = _choose_best_record(records) if records else None
                fact = resolve_release_fact(
                    artifact, version, record, match_count=len(records)
                )
                facts.append((component.slug, artifact.key, fact))
                if version in designated:
                    targets.append(fact)
                if not fact.deterministic:
                    diagnostics.append(
                        PipelineDiagnosticEntry(
                            severity=DiagnosticSeverity.ERROR,
                            code="provider-context-ambiguous",
                            component_slug=component.slug,
                            artifact_key=artifact.key,
                            target_id="released",
                            message=f"Released {'selected context' if version in selected_versions else 'designation'} {component.slug}:{artifact.key}@{version} matches multiple normalized provider records",
                            details={
                                "kind": "released",
                                "version": version,
                                "matchingRecords": [
                                    {
                                        "provider": item.provider,
                                        "externalId": item.external_id,
                                        "version": item.version,
                                        "namedRefKey": item.named_ref_key,
                                        "ref": item.ref,
                                    }
                                    for item in records
                                ],
                            },
                        )
                    )
                authored_state = (
                    fact.authored.publication_state if fact.authored else None
                )
                provider_state = record.publication_state if record else None
                if (
                    authored_state is not None
                    and provider_state is not None
                    and authored_state != provider_state
                ):
                    diagnostics.append(
                        PipelineDiagnosticEntry(
                            severity=DiagnosticSeverity.ERROR,
                            code="release-publication-state-conflict",
                            component_slug=component.slug,
                            artifact_key=artifact.key,
                            target_id=version,
                            message=f"Release {version} has conflicting authored and provider publication states",
                            details={
                                "authoredState": authored_state.value,
                                "providerState": provider_state.value,
                            },
                        )
                    )
            result.append(
                ResolvedArtifactDesignations(
                    component.slug, artifact.key, status, latest, lines, tuple(targets)
                )
            )
    return tuple(result), tuple(facts), tuple(diagnostics)
