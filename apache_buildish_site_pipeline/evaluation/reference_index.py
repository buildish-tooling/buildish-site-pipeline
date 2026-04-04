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

"""Contextual internal-reference indexing for shared evaluation."""

from __future__ import annotations

from dataclasses import dataclass

from apache_buildish_site_pipeline.models.catalog import CompatibilityAssertionConfig, ReleaseLineConfig
from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity, ReleaseSelectionMode
from apache_buildish_site_pipeline.planning.types import PlanningEvaluation, ResolvedArtifactConfig, ResolvedComponentConfig

from . import diagnostic_codes
from .collector import DiagnosticCollector
from .types import PublishedTarget


@dataclass(frozen=True, slots=True)
class KnownRoute:
    """One normalized public route that internal references may resolve to."""

    route_id: str
    origin_key: str
    path: str
    component_slug: str | None
    route_kind: str


@dataclass(frozen=True, slots=True)
class ReferenceIndex:
    """Lookup tables for internal references and route-path targets."""

    routes_by_lookup_key: dict[tuple[str, str], KnownRoute]
    targets_by_reference: dict[str, KnownRoute]
    known_components: frozenset[str]
    artifacts_by_component: dict[str, frozenset[str]]
    release_lines_by_artifact: dict[tuple[str, str], frozenset[str]]
    releases_by_artifact: dict[tuple[str, str], frozenset[str]]
    named_refs_by_artifact: dict[tuple[str, str], frozenset[str]]
    routes_by_path: dict[str, tuple[KnownRoute, ...]]


def build_reference_index(
    *,
    routes_by_lookup_key: dict[tuple[str, str], KnownRoute],
    targets_by_reference: dict[str, KnownRoute],
    known_components: frozenset[str] | None = None,
    artifacts_by_component: dict[str, frozenset[str]] | None = None,
    release_lines_by_artifact: dict[tuple[str, str], frozenset[str]] | None = None,
    releases_by_artifact: dict[tuple[str, str], frozenset[str]] | None = None,
    named_refs_by_artifact: dict[tuple[str, str], frozenset[str]] | None = None,
    routes_by_path: dict[str, tuple[KnownRoute, ...]] | None = None,
) -> ReferenceIndex:
    """Freeze the computed contextual reference lookups."""

    return ReferenceIndex(
        routes_by_lookup_key=dict(routes_by_lookup_key),
        targets_by_reference=dict(targets_by_reference),
        known_components=known_components or frozenset(),
        artifacts_by_component=dict(artifacts_by_component or {}),
        release_lines_by_artifact=dict(release_lines_by_artifact or {}),
        releases_by_artifact=dict(releases_by_artifact or {}),
        named_refs_by_artifact=dict(named_refs_by_artifact or {}),
        routes_by_path=dict(routes_by_path or {}),
    )


def route_from_published_target(target: PublishedTarget) -> KnownRoute:
    """Project one published target into a known route entry."""

    return KnownRoute(
        route_id=target.target_id,
        origin_key=target.origin_key,
        path=target.path,
        component_slug=target.component_slug,
        route_kind="published",
    )


def resolve_internal_reference(
    *,
    reference: str,
    source_origin_key: str,
    reference_index: ReferenceIndex,
) -> KnownRoute | None:
    """Resolve one already-validated internal reference string against known routes."""

    prefix, separator, payload = reference.partition(":")
    if separator == "":
        return None
    if prefix == "route":
        lookup_key = (source_origin_key, payload.lower())
        return reference_index.routes_by_lookup_key.get(lookup_key)
    return reference_index.targets_by_reference.get(reference)


def validate_references(
    *,
    planning: PlanningEvaluation,
    publication_targets: tuple[PublishedTarget, ...],
    collector: DiagnosticCollector,
) -> None:
    """Validate contextual reference existence and authored identity consistency."""

    reference_index = _build_context_reference_index(planning=planning, publication_targets=publication_targets)
    for component in planning.site.components:
        _validate_component_artifacts(component=component, collector=collector)
        _validate_compatibility_references(
            component_slug=component.slug,
            artifact_key=None,
            compatibility=getattr(component.authored, "compatibility", ()) or (),
            reference_index=reference_index,
            collector=collector,
        )
        for artifact in component.artifacts:
            _validate_release_lines(component_slug=component.slug, artifact=artifact, collector=collector)
            _validate_selection_references(
                component_slug=component.slug,
                artifact=artifact,
                planning=planning,
                collector=collector,
            )
            _validate_compatibility_references(
                component_slug=component.slug,
                artifact_key=artifact.key,
                compatibility=getattr(artifact.authored, "compatibility", ()) or (),
                reference_index=reference_index,
                collector=collector,
            )


def _build_context_reference_index(
    *,
    planning: PlanningEvaluation,
    publication_targets: tuple[PublishedTarget, ...],
) -> ReferenceIndex:
    routes_by_lookup_key: dict[tuple[str, str], KnownRoute] = {}
    targets_by_reference: dict[str, KnownRoute] = {}
    routes_by_path: dict[str, list[KnownRoute]] = {}
    artifacts_by_component: dict[str, frozenset[str]] = {}
    release_lines_by_artifact: dict[tuple[str, str], frozenset[str]] = {}
    releases_by_artifact: dict[tuple[str, str], frozenset[str]] = {}
    named_refs_by_artifact: dict[tuple[str, str], frozenset[str]] = {}

    for target in publication_targets:
        route = route_from_published_target(target)
        routes_by_lookup_key[(route.origin_key, route.path.lower())] = route
        if target.target_id.startswith("component:"):
            targets_by_reference[target.target_id] = route
        routes_by_path.setdefault(route.path.lower(), []).append(route)
    for context in planning.selected_versions.contexts:
        route = KnownRoute(
            route_id=f"{context.component_slug}/{context.artifact_key}/{context.kind.value}",
            origin_key="",
            path="",
            component_slug=context.component_slug,
            route_kind=context.kind.value,
        )
        if context.release_line is not None:
            targets_by_reference[f"line:{context.component_slug}/{context.artifact_key}@{context.release_line}"] = route
        if context.version is not None:
            targets_by_reference[f"release:{context.component_slug}/{context.artifact_key}@{context.version}"] = route

    for component in planning.site.components:
        artifacts_by_component[component.slug] = frozenset(artifact.key for artifact in component.artifacts)
        for artifact in component.artifacts:
            artifact_identity = (component.slug, artifact.key)
            release_lines_by_artifact[artifact_identity] = frozenset(line.key for line in artifact.lifecycle.release_lines or ()) if artifact.lifecycle else frozenset()
            known_releases = {release.version for release in artifact.lifecycle.releases or ()} if artifact.lifecycle else set()
            provider_context = planning.provider_index.contexts_by_artifact.get(artifact_identity)
            if provider_context is not None:
                known_releases.update(provider_context.released_by_version)
            releases_by_artifact[artifact_identity] = frozenset(known_releases)
            named_refs_by_artifact[artifact_identity] = frozenset(named_ref.key for named_ref in artifact.versioning.named_refs or ())

    return build_reference_index(
        routes_by_lookup_key=routes_by_lookup_key,
        targets_by_reference=targets_by_reference,
        known_components=frozenset(component.slug for component in planning.site.components),
        artifacts_by_component=artifacts_by_component,
        release_lines_by_artifact=release_lines_by_artifact,
        releases_by_artifact=releases_by_artifact,
        named_refs_by_artifact=named_refs_by_artifact,
        routes_by_path={path: tuple(routes) for path, routes in routes_by_path.items()},
    )


def _validate_component_artifacts(*, component: ResolvedComponentConfig, collector: DiagnosticCollector) -> None:
    seen: set[str] = set()
    duplicate_keys: set[str] = set()
    for artifact in component.artifacts:
        if artifact.key in seen:
            duplicate_keys.add(artifact.key)
        seen.add(artifact.key)
    for artifact_key in sorted(duplicate_keys):
        _add_reference_error(
            collector=collector,
            component_slug=component.slug,
            artifact_key=artifact_key,
            message=f"Component {component.slug} defines duplicate artifact key {artifact_key}",
            details={"artifactKey": artifact_key},
        )


def _validate_release_lines(*, component_slug: str, artifact: ResolvedArtifactConfig, collector: DiagnosticCollector) -> None:
    release_lines = tuple(artifact.lifecycle.release_lines or ()) if artifact.lifecycle else ()
    known_lines = {line.key for line in release_lines}
    for line in release_lines:
        parent_line = getattr(line, "parent", None)
        if parent_line is not None and parent_line not in known_lines:
            _add_reference_error(
                collector=collector,
                component_slug=component_slug,
                artifact_key=artifact.key,
                message=(
                    f"Release line {line.key} for {component_slug}/{artifact.key} references unknown parent line "
                    f"{parent_line}"
                ),
                details={"line": line.key, "parentLine": parent_line},
            )
        if _has_line_cycle(start_key=line.key, release_lines=release_lines):
            _add_reference_error(
                collector=collector,
                component_slug=component_slug,
                artifact_key=artifact.key,
                message=f"Release line {line.key} for {component_slug}/{artifact.key} participates in a parent cycle",
                details={"line": line.key},
            )


def _validate_selection_references(
    *,
    component_slug: str,
    artifact: ResolvedArtifactConfig,
    planning: PlanningEvaluation,
    collector: DiagnosticCollector,
) -> None:
    selection = artifact.publication_selection
    if selection is None:
        return
    artifact_identity = (component_slug, artifact.key)
    known_releases = {release.version for release in artifact.lifecycle.releases or ()} if artifact.lifecycle else set()
    provider_context = planning.provider_index.contexts_by_artifact.get(artifact_identity)
    if provider_context is not None:
        known_releases.update(provider_context.released_by_version)
    known_lines = {line.key for line in artifact.lifecycle.release_lines or ()} if artifact.lifecycle else set()
    known_named_refs = {named_ref.key for named_ref in artifact.versioning.named_refs or ()}

    if selection.releases is not None and selection.releases.mode is ReleaseSelectionMode.EXPLICIT:
        for version in selection.releases.versions or ():
            if version in known_releases:
                continue
            _add_reference_error(
                collector=collector,
                component_slug=component_slug,
                artifact_key=artifact.key,
                message=(
                    f"Publication selection for {component_slug}/{artifact.key} references unknown exact release version "
                    f"{version}"
                ),
                details={"version": version},
            )
    for named_ref_key in selection.named_refs or ():
        if named_ref_key in known_named_refs:
            continue
        _add_reference_error(
            collector=collector,
            component_slug=component_slug,
            artifact_key=artifact.key,
            message=f"Publication selection for {component_slug}/{artifact.key} references unknown named ref {named_ref_key}",
            details={"namedRefKey": named_ref_key},
        )
    for release in artifact.lifecycle.releases or () if artifact.lifecycle else ():
        if release.release_line is None or release.release_line in known_lines:
            continue
        _add_reference_error(
            collector=collector,
            component_slug=component_slug,
            artifact_key=artifact.key,
            message=(
                f"Authored release {release.version} for {component_slug}/{artifact.key} references unknown release line "
                f"{release.release_line}"
            ),
            details={"version": release.version, "releaseLine": release.release_line},
        )


def _validate_compatibility_references(
    *,
    component_slug: str,
    artifact_key: str | None,
    compatibility: tuple[CompatibilityAssertionConfig, ...] | None,
    reference_index: ReferenceIndex,
    collector: DiagnosticCollector,
) -> None:
    for assertion in compatibility or ():
        _validate_compatibility_reference(
            component_slug=component_slug,
            artifact_key=artifact_key,
            field_name="subjectRef",
            reference=assertion.subject_ref,
            reference_index=reference_index,
            collector=collector,
        )
        _validate_compatibility_reference(
            component_slug=component_slug,
            artifact_key=artifact_key,
            field_name="targetRef",
            reference=assertion.target_ref,
            reference_index=reference_index,
            collector=collector,
        )


def _validate_compatibility_reference(
    *,
    component_slug: str,
    artifact_key: str | None,
    field_name: str,
    reference: str,
    reference_index: ReferenceIndex,
    collector: DiagnosticCollector,
) -> None:
    if _reference_exists(reference=reference, reference_index=reference_index):
        return
    collector.add(
        severity=DiagnosticSeverity.ERROR,
        code=diagnostic_codes.COMPATIBILITY_REFERENCE_UNKNOWN,
        message=(
            f"Compatibility assertion for {component_slug}"
            f"{f'/{artifact_key}' if artifact_key else ''} references unknown {field_name} {reference}"
        ),
        component_slug=component_slug,
        artifact_key=artifact_key,
        details={"field": field_name, "reference": reference},
    )


def _reference_exists(*, reference: str, reference_index: ReferenceIndex) -> bool:
    prefix, _, payload = reference.partition(":")
    if prefix == "component":
        return payload in reference_index.known_components
    if prefix == "artifact":
        component_slug, artifact_key = payload.split("/", maxsplit=1)
        return artifact_key in reference_index.artifacts_by_component.get(component_slug, frozenset())
    if prefix == "line":
        artifact_payload, line_key = payload.split("@", maxsplit=1)
        component_slug, artifact_key = artifact_payload.split("/", maxsplit=1)
        return line_key in reference_index.release_lines_by_artifact.get((component_slug, artifact_key), frozenset())
    if prefix == "release":
        artifact_payload, version = payload.split("@", maxsplit=1)
        component_slug, artifact_key = artifact_payload.split("/", maxsplit=1)
        return version in reference_index.releases_by_artifact.get((component_slug, artifact_key), frozenset())
    if prefix == "route":
        return len(reference_index.routes_by_path.get(payload.lower(), ())) == 1
    return reference in reference_index.targets_by_reference


def _add_reference_error(
    *,
    collector: DiagnosticCollector,
    component_slug: str,
    artifact_key: str,
    message: str,
    details: dict[str, object],
) -> None:
    collector.add(
        severity=DiagnosticSeverity.ERROR,
        code=diagnostic_codes.REFERENCE_CONFIGURATION_INVALID,
        message=message,
        component_slug=component_slug,
        artifact_key=artifact_key,
        details=details,
    )


def _has_line_cycle(*, start_key: str, release_lines: tuple[ReleaseLineConfig, ...]) -> bool:
    parents_by_key = {line.key: getattr(line, "parent", None) for line in release_lines}
    seen: set[str] = set()
    current: str | None = start_key
    while current is not None:
        if current in seen:
            return True
        seen.add(current)
        current = parents_by_key.get(current)
    return False
