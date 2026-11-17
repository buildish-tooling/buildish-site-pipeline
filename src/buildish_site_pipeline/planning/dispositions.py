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

"""Resolve release publication behavior and allowed local inventory gaps."""

from dataclasses import replace
from buildish_site_pipeline.content_scope import context_exclusions

from buildish_site_pipeline.models.enums import (
    ContextAction,
    DiagnosticSeverity,
    MaterializationStatus,
    PublicationState,
    RecordKind,
)
from buildish_site_pipeline.models.emitted.execution import (
    ContextDisposition,
    SnapshotInput,
)
from buildish_site_pipeline.models.emitted.planning_stage_contract import (
    PipelineDiagnosticEntry,
)
from .types import ResolvedSiteConfig, SelectedVersionContext, SelectedVersionSet


def resolve_dispositions(
    *,
    site: ResolvedSiteConfig,
    selected: SelectedVersionSet,
    snapshot_inputs: tuple[SnapshotInput, ...],
) -> tuple[
    SelectedVersionSet,
    tuple[SelectedVersionContext, ...],
    tuple[ContextDisposition, ...],
    tuple[PipelineDiagnosticEntry, ...],
]:
    """Keep desired identities while excluding original trees that cannot publish."""
    absent = {
        entry.component_slug
        for entry in snapshot_inputs
        if entry.component_slug is not None
        and entry.status is MaterializationStatus.MISSING
        and not entry.required
    }
    diagnostics = [
        PipelineDiagnosticEntry(
            severity=DiagnosticSeverity.INFO,
            code="provider-snapshot-missing",
            message="Provider inventory is absent; materialization is needed"
            if entry.required
            else "Optional provider inventory is absent; local release preview may be incomplete",
            component_slug=entry.component_slug,
            details={
                "expectedLocalPath": entry.expected_local_path,
                "required": entry.required,
            },
        )
        for entry in snapshot_inputs
        if entry.status is MaterializationStatus.MISSING
    ]
    artifacts = {
        (component.slug, artifact.key): artifact
        for component in site.components
        for artifact in component.artifacts
    }
    desired = []
    effective = []
    dispositions = []
    for context in selected.contexts:
        exclusions = list(
            context_exclusions(
                context.kind.value, versioned=context.artifact_key is not None
            )
        )
        if context.kind is RecordKind.DEVELOPMENT and context.artifact_key is not None:
            owner = artifacts[(context.component_slug, context.artifact_key)]
            if owner.lifecycle:
                exclusions.extend(
                    f"maintenance/{line.key}"
                    for line in owner.lifecycle.release_lines or ()
                )
            exclusions.extend(
                f"refs/{ref.key}" for ref in owner.versioning.named_refs or ()
            )
        context = replace(context, source_exclusions=tuple(exclusions))
        if context.kind is not RecordKind.RELEASED:
            effective.append(context)
            desired.append(context)
            continue
        if context.artifact_key is None or context.version is None:
            raise ValueError("A released context needs an artifact and exact version")
        artifact = artifacts[(context.component_slug, context.artifact_key)]
        authored = (
            next(
                (
                    item
                    for item in artifact.lifecycle.releases or ()
                    if item.version == context.version
                ),
                None,
            )
            if artifact.lifecycle
            else None
        )
        action = ContextAction.DOCS
        reason = None
        if context.publication_state is PublicationState.HIDDEN:
            action, reason = ContextAction.OMIT, "hidden"
        elif context.publication_state in {
            PublicationState.WITHDRAWN,
            PublicationState.TOMBSTONED,
        }:
            action = (
                ContextAction(context.withdrawal_behavior.value)
                if context.withdrawal_behavior
                else ContextAction.OMIT
            )
            reason = context.publication_state.value
        elif context.component_slug in absent and context.provider_record is None:
            expected = context.docs_root / "releases" / str(context.version)
            if (
                expected.resolve(strict=False).is_relative_to(
                    context.source_binding.local_dir
                )
                and not expected.exists()
            ):
                action, reason = ContextAction.OMIT, "snapshot-absent"
        verified = context.provider_record is not None or authored is not None
        artifact_key, version = context.artifact_key, context.version
        context = replace(context, action=action, identity_verified=verified)
        desired.append(context)
        dispositions.append(
            ContextDisposition(
                component_slug=context.component_slug,
                artifact_key=artifact_key,
                version=version,
                action=action,
                publication_state=context.publication_state,
                reason=reason,
            )
        )
        if action is not ContextAction.OMIT:
            effective.append(context)
        if reason:
            diagnostics.append(
                PipelineDiagnosticEntry(
                    severity=DiagnosticSeverity.INFO,
                    code="release-docs-unavailable",
                    component_slug=context.component_slug,
                    artifact_key=context.artifact_key,
                    target_id=context.version,
                    message=f"Original docs for release {context.version} are not staged ({reason})",
                    details={"reason": reason, "action": action.value},
                )
            )
        if context.component_slug in absent and not verified:
            diagnostics.append(
                PipelineDiagnosticEntry(
                    severity=DiagnosticSeverity.INFO,
                    code="release-identity-unverified",
                    component_slug=context.component_slug,
                    artifact_key=context.artifact_key,
                    target_id=context.version,
                    message=f"Release {context.version} cannot be verified without its optional inventory",
                )
            )
    return (
        SelectedVersionSet(
            contexts=tuple(effective), deterministic=selected.deterministic
        ),
        tuple(desired),
        tuple(dispositions),
        tuple(diagnostics),
    )
