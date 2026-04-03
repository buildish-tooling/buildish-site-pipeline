# Copyright 2026 The Apache Software Foundation

"""Contextual internal-reference indexing for shared evaluation."""

from __future__ import annotations

from dataclasses import dataclass

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


def build_reference_index(
    *,
    routes_by_lookup_key: dict[tuple[str, str], KnownRoute],
    targets_by_reference: dict[str, KnownRoute],
) -> ReferenceIndex:
    """Freeze the computed contextual reference lookups."""

    return ReferenceIndex(
        routes_by_lookup_key=dict(routes_by_lookup_key),
        targets_by_reference=dict(targets_by_reference),
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
