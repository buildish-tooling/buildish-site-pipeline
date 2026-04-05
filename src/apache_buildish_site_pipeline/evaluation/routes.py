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

"""Shared route and redirect validation over resolved planning output."""

from __future__ import annotations

from apache_buildish_site_pipeline.models.enums import (
    DiagnosticSeverity,
    RecordKind,
    WithdrawalBehavior,
)

from . import diagnostic_codes
from .collector import DiagnosticCollector
from .publication import public_path_for_context, target_id_for_context
from .reference_index import (
    KnownRoute,
    build_reference_index,
    resolve_internal_reference,
    route_from_published_target,
)
from .types import PublicationIndex, RouteInventory

from apache_buildish_site_pipeline.planning.types import (
    PlanningEvaluation,
    ResolvedComponentConfig,
    SelectedVersionContext,
)


def validate_routes(
    planning: PlanningEvaluation,
    publication_index: PublicationIndex,
    collector: DiagnosticCollector,
) -> RouteInventory:
    """Validate shared route occupancy and redirect targets for the resolved plan."""

    component_by_slug = {
        component.slug: component for component in planning.site.components
    }
    routes_by_lookup_key: dict[tuple[str, str], KnownRoute] = {}
    targets_by_reference: dict[str, KnownRoute] = {}
    redirect_edges: dict[tuple[str, str], tuple[str, str]] = {}

    for target in publication_index.targets:
        route = route_from_published_target(target)
        routes_by_lookup_key[_route_lookup_key(route.origin_key, route.path)] = route
        if target.target_id.startswith("component:"):
            targets_by_reference[target.target_id] = route

    for context in planning.selected_versions.contexts:
        component = component_by_slug[context.component_slug]
        route = KnownRoute(
            route_id=target_id_for_context(context),
            origin_key=component.publication.origin.key,
            path=public_path_for_context(component.publication, context),
            component_slug=context.component_slug,
            route_kind="context",
        )
        _register_route(
            route=route,
            collector=collector,
            routes_by_lookup_key=routes_by_lookup_key,
            target_id=route.route_id,
        )
        reference = _reference_string_for_context(context)
        if reference is not None:
            targets_by_reference[reference] = route

    for component in planning.site.components:
        _validate_canonical_path(
            component=component,
            routes_by_lookup_key=routes_by_lookup_key,
            collector=collector,
        )
        _register_aliases(
            component=component,
            collector=collector,
            routes_by_lookup_key=routes_by_lookup_key,
        )

    for component in planning.site.components:
        _register_redirect_sources(
            component=component,
            collector=collector,
            routes_by_lookup_key=routes_by_lookup_key,
        )

    reference_index = build_reference_index(
        routes_by_lookup_key=routes_by_lookup_key,
        targets_by_reference=targets_by_reference,
    )
    for component in planning.site.components:
        _validate_component_redirect_targets(
            component=component,
            collector=collector,
            reference_index=reference_index,
            redirect_edges=redirect_edges,
        )
    for context in planning.selected_versions.contexts:
        _validate_context_redirect_target(
            context=context,
            component_by_slug=component_by_slug,
            collector=collector,
            reference_index=reference_index,
            redirect_edges=redirect_edges,
        )
    _validate_redirect_loops(
        redirect_edges=redirect_edges,
        routes_by_lookup_key=routes_by_lookup_key,
        collector=collector,
    )
    return RouteInventory(
        route_count=(
            len(publication_index.targets)
            + len(planning.selected_versions.contexts)
            + sum(
                len(component.publication.aliases)
                for component in planning.site.components
            )
        ),
        redirect_count=(
            sum(
                len(component.publication.redirects)
                for component in planning.site.components
            )
            + sum(
                1
                for context in planning.selected_versions.contexts
                if context.withdrawal_behavior is WithdrawalBehavior.REDIRECT
                and context.redirect_target is not None
            )
        ),
    )


def _validate_canonical_path(
    *,
    component: ResolvedComponentConfig,
    routes_by_lookup_key: dict[tuple[str, str], KnownRoute],
    collector: DiagnosticCollector,
) -> None:
    canonical_path = component.publication.canonical_path
    if canonical_path is None:
        return
    route = routes_by_lookup_key.get(
        _route_lookup_key(component.publication.origin.key, canonical_path)
    )
    if (
        route is not None
        and route.component_slug == component.slug
        and route.route_kind != "redirect"
    ):
        return
    collector.add(
        severity=DiagnosticSeverity.ERROR,
        code=diagnostic_codes.PUBLICATION_CANONICAL_INVALID,
        message=(
            f"Canonical path {canonical_path} for component {component.slug} does not resolve "
            "to one of the component's publishable routes"
        ),
        component_slug=component.slug,
        details={"canonicalPath": canonical_path},
    )


def _register_aliases(
    *,
    component: ResolvedComponentConfig,
    collector: DiagnosticCollector,
    routes_by_lookup_key: dict[tuple[str, str], KnownRoute],
) -> None:
    for index, alias in enumerate(component.publication.aliases):
        route = KnownRoute(
            route_id=f"alias:{component.slug}:{index}",
            origin_key=alias.origin or component.publication.origin.key,
            path=alias.path,
            component_slug=component.slug,
            route_kind="alias",
        )
        _register_route(
            route=route, collector=collector, routes_by_lookup_key=routes_by_lookup_key
        )


def _register_redirect_sources(
    *,
    component: ResolvedComponentConfig,
    collector: DiagnosticCollector,
    routes_by_lookup_key: dict[tuple[str, str], KnownRoute],
) -> None:
    for index, redirect in enumerate(component.publication.redirects):
        route = KnownRoute(
            route_id=f"redirect:{component.slug}:{index}",
            origin_key=redirect.from_origin or component.publication.origin.key,
            path=redirect.from_path,
            component_slug=component.slug,
            route_kind="redirect",
        )
        _register_route(
            route=route, collector=collector, routes_by_lookup_key=routes_by_lookup_key
        )


def _register_route(
    *,
    route: KnownRoute,
    collector: DiagnosticCollector,
    routes_by_lookup_key: dict[tuple[str, str], KnownRoute],
    target_id: str | None = None,
) -> None:
    lookup_key = _route_lookup_key(route.origin_key, route.path)
    other_route = routes_by_lookup_key.get(lookup_key)
    if other_route is None:
        routes_by_lookup_key[lookup_key] = route
        return
    if _allows_shared_context_route(existing=other_route, candidate=route):
        return
    collector.add(
        severity=DiagnosticSeverity.ERROR,
        code=diagnostic_codes.PUBLICATION_ROUTE_COLLISION,
        message=(
            f"Route {route.route_id} collides with {other_route.route_id} "
            f"on {route.origin_key}:{route.path}"
        ),
        component_slug=route.component_slug,
        target_id=target_id,
        details={"otherTargetId": other_route.route_id, "path": route.path},
    )


def _allows_shared_context_route(
    *, existing: KnownRoute, candidate: KnownRoute
) -> bool:
    if existing.component_slug != candidate.component_slug:
        return False
    if candidate.route_kind != "context":
        return False
    return existing.route_kind in {"published", "context"}


def _validate_component_redirect_targets(
    *,
    component: ResolvedComponentConfig,
    collector: DiagnosticCollector,
    reference_index,
    redirect_edges: dict[tuple[str, str], tuple[str, str]],
) -> None:
    for index, redirect in enumerate(component.publication.redirects):
        source_origin_key = redirect.from_origin or component.publication.origin.key
        _validate_redirect_target(
            reference=str(redirect.target),
            source_origin_key=source_origin_key,
            source_path=redirect.from_path,
            component_slug=component.slug,
            redirect_id=f"redirect:{component.slug}:{index}",
            collector=collector,
            reference_index=reference_index,
            redirect_edges=redirect_edges,
        )


def _validate_context_redirect_target(
    *,
    context: SelectedVersionContext,
    component_by_slug: dict[str, ResolvedComponentConfig],
    collector: DiagnosticCollector,
    reference_index,
    redirect_edges: dict[tuple[str, str], tuple[str, str]],
) -> None:
    if (
        context.withdrawal_behavior is not WithdrawalBehavior.REDIRECT
        or context.redirect_target is None
    ):
        return
    component = component_by_slug[context.component_slug]
    source_path = public_path_for_context(component.publication, context)
    _validate_redirect_target(
        reference=str(context.redirect_target),
        source_origin_key=component.publication.origin.key,
        source_path=source_path,
        component_slug=context.component_slug,
        redirect_id=f"withdrawal:{target_id_for_context(context)}",
        collector=collector,
        reference_index=reference_index,
        redirect_edges=redirect_edges,
        artifact_key=context.artifact_key,
        target_id=target_id_for_context(context),
    )


def _validate_redirect_target(
    *,
    reference: str,
    source_origin_key: str,
    source_path: str,
    component_slug: str,
    redirect_id: str,
    collector: DiagnosticCollector,
    reference_index,
    redirect_edges: dict[tuple[str, str], tuple[str, str]],
    artifact_key: str | None = None,
    target_id: str | None = None,
) -> None:
    if reference.startswith(("http://", "https://")):
        return
    resolved_target = resolve_internal_reference(
        reference=reference,
        source_origin_key=source_origin_key,
        reference_index=reference_index,
    )
    if resolved_target is None:
        collector.add(
            severity=DiagnosticSeverity.ERROR,
            code=diagnostic_codes.REDIRECT_TARGET_UNKNOWN,
            message=(
                f"Redirect {redirect_id} points to unknown internal target {reference} "
                f"from {source_origin_key}:{source_path}"
            ),
            component_slug=component_slug,
            artifact_key=artifact_key,
            target_id=target_id,
            details={
                "redirectId": redirect_id,
                "target": reference,
                "fromPath": source_path,
            },
        )
        return
    redirect_edges[_route_lookup_key(source_origin_key, source_path)] = (
        _route_lookup_key(
            resolved_target.origin_key,
            resolved_target.path,
        )
    )


def _validate_redirect_loops(
    *,
    redirect_edges: dict[tuple[str, str], tuple[str, str]],
    routes_by_lookup_key: dict[tuple[str, str], KnownRoute],
    collector: DiagnosticCollector,
) -> None:
    visited: set[tuple[str, str]] = set()
    reported_cycles: set[frozenset[tuple[str, str]]] = set()

    for node in redirect_edges:
        if node in visited:
            continue
        cycle = _find_cycle(start=node, redirect_edges=redirect_edges, visited=visited)
        if cycle is None:
            continue
        cycle_key = frozenset(cycle)
        if cycle_key in reported_cycles:
            continue
        reported_cycles.add(cycle_key)
        cycle_labels = [
            f"{origin}:{routes_by_lookup_key[(origin, path)].path}"
            for origin, path in cycle
        ]
        collector.add(
            severity=DiagnosticSeverity.ERROR,
            code=diagnostic_codes.REDIRECT_LOOP,
            message=f"Redirect loop detected: {' -> '.join(cycle_labels)}",
            details={"cycle": cycle_labels},
        )


def _find_cycle(
    *,
    start: tuple[str, str],
    redirect_edges: dict[tuple[str, str], tuple[str, str]],
    visited: set[tuple[str, str]],
) -> tuple[tuple[str, str], ...] | None:
    path_index: dict[tuple[str, str], int] = {}
    chain: list[tuple[str, str]] = []
    node: tuple[str, str] | None = start
    while node is not None:
        if node in path_index:
            return tuple(chain[path_index[node] :])
        if node in visited:
            return None
        visited.add(node)
        path_index[node] = len(chain)
        chain.append(node)
        node = redirect_edges.get(node)
    return None


def _reference_string_for_context(context: SelectedVersionContext) -> str | None:
    if context.kind is RecordKind.LINE_HEAD:
        return f"line:{context.component_slug}/{context.artifact_key}@{context.release_line}"
    if context.kind is RecordKind.RELEASED:
        return (
            f"release:{context.component_slug}/{context.artifact_key}@{context.version}"
        )
    return None


def _route_lookup_key(origin_key: str, path: str) -> tuple[str, str]:
    return (origin_key, path.lower())
