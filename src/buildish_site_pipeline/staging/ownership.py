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

"""Owned-unit planning and output-root validation for staging."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from ..cli.errors import StageIntegrityError
from ..planning.types import ResolvedVendorAsset, SelectedVersionContext
from .publication_paths import (
    public_path_for_context,
    stage_root_for_public_path,
    target_id_for_context,
)
from .types import EffectiveBuildPlan


class OwnedUnitKind(StrEnum):
    """Top-level unit categories staged by the first-wave coordinator."""

    SITE_PAGES = "site-pages"
    SITE_ASSETS = "site-assets"
    VENDOR_ASSETS = "vendor-assets"
    COMPONENT = "component"


@dataclass(frozen=True, slots=True)
class OwnedContextInput:
    """One selected version context attached to one component-owned unit."""

    context_id: str
    context: SelectedVersionContext
    content_stage_root: Path
    static_stage_root: Path


@dataclass(frozen=True, slots=True)
class OwnedUnit:
    """One independently staged subtree with one logical owner."""

    unit_id: str
    owner_id: str
    kind: OwnedUnitKind
    content_stage_roots: tuple[Path, ...] = ()
    static_stage_roots: tuple[Path, ...] = ()
    site_pages_source: Path | None = None
    site_assets_source: Path | None = None
    vendor_assets: tuple[ResolvedVendorAsset, ...] = ()
    component_slug: str | None = None
    component_pages_source: Path | None = None
    component_assets_source: Path | None = None
    contexts: tuple[OwnedContextInput, ...] = ()

def _unique_stage_roots(*roots: Path) -> tuple[Path, ...]:
    """Return one stable tuple of stage roots without duplicates."""

    unique_roots: list[Path] = []
    for root in roots:
        if root in unique_roots:
            continue
        unique_roots.append(root)
    return tuple(unique_roots)


def build_owned_units(build_plan: EffectiveBuildPlan) -> tuple[OwnedUnit, ...]:
    """Produce the first-wave owned units from one validated build plan."""

    units: list[OwnedUnit] = []
    publications_by_component = {
        component.slug: component.publication for component in build_plan.site.components
    }
    if build_plan.site.site_pages_root is not None:
        units.append(
            OwnedUnit(
                unit_id="site-pages",
                owner_id="site-content",
                kind=OwnedUnitKind.SITE_PAGES,
                content_stage_roots=(Path("content") / "site",),
                site_pages_source=build_plan.site.site_pages_root,
            ),
        )
    if build_plan.site.site_assets_root is not None:
        units.append(
            OwnedUnit(
                unit_id="site-assets",
                owner_id="site-static",
                kind=OwnedUnitKind.SITE_ASSETS,
                static_stage_roots=(Path("static") / "site",),
                site_assets_source=build_plan.site.site_assets_root,
            ),
        )
    if build_plan.site.vendor_assets:
        units.append(
            OwnedUnit(
                unit_id="vendor-assets",
                owner_id="site-static",
                kind=OwnedUnitKind.VENDOR_ASSETS,
                static_stage_roots=(Path("static") / "site" / "vendor",),
                vendor_assets=tuple(build_plan.site.vendor_assets),
            ),
        )

    contexts_by_component: dict[str, list[OwnedContextInput]] = {}
    for context in build_plan.selected_versions:
        publication = publications_by_component.get(context.component_slug)
        if publication is None:
            raise StageIntegrityError(
                f"Missing publication policy for selected context component: {context.component_slug}"
            )
        public_path = public_path_for_context(publication, context)
        contexts_by_component.setdefault(context.component_slug, []).append(
            OwnedContextInput(
                context_id=target_id_for_context(context),
                context=context,
                content_stage_root=stage_root_for_public_path("content", public_path),
                static_stage_root=stage_root_for_public_path("static", public_path),
            ),
        )

    for component in build_plan.site.components:
        component_contexts = tuple(contexts_by_component.get(component.slug, ()))
        component_content_root = stage_root_for_public_path(
            "content", component.publication.component_path
        )
        component_static_root = stage_root_for_public_path(
            "static", component.publication.assets_path
        )
        if (
            component.pages_root is None
            and component.assets_root is None
            and not component_contexts
        ):
            continue
        context_content_roots = tuple(
            context.content_stage_root for context in component_contexts
        )
        context_static_roots = tuple(
            context.static_stage_root for context in component_contexts
        )
        units.append(
            OwnedUnit(
                unit_id=f"component:{component.slug}",
                owner_id=f"component:{component.slug}",
                kind=OwnedUnitKind.COMPONENT,
                content_stage_roots=_unique_stage_roots(
                    component_content_root,
                    *context_content_roots,
                ),
                static_stage_roots=_unique_stage_roots(
                    component_static_root,
                    *context_static_roots,
                ),
                component_slug=component.slug,
                component_pages_source=component.pages_root,
                component_assets_source=component.assets_root,
                contexts=component_contexts,
            ),
        )

    _validate_output_ownership(tuple(units))
    return tuple(units)


def _validate_output_ownership(units: tuple[OwnedUnit, ...]) -> None:
    claims: list[tuple[str, str, str, str]] = []
    for unit in units:
        for root in (*unit.content_stage_roots, *unit.static_stage_roots):
            path = str(root)
            claims.append((path, path.casefold(), unit.owner_id, unit.unit_id))
    sorted_claims = sorted(claims, key=lambda claim: claim[0])
    for index, (path, casefold_path, owner_id, unit_id) in enumerate(sorted_claims):
        for (
            other_path,
            other_casefold_path,
            other_owner_id,
            other_unit_id,
        ) in sorted_claims[index + 1 :]:
            overlapping_paths = (
                other_path == path
                or other_path.startswith(f"{path}/")
                or path.startswith(f"{other_path}/")
            )
            casefold_collision = (
                other_casefold_path == casefold_path
                or other_casefold_path.startswith(f"{casefold_path}/")
                or casefold_path.startswith(f"{other_casefold_path}/")
            )
            if not overlapping_paths and not casefold_collision:
                continue
            if (
                unit_id == other_unit_id
                and owner_id == other_owner_id
                and path == other_path
            ):
                continue
            if owner_id == other_owner_id and overlapping_paths:
                continue
            detail = (
                "case-insensitive path collision"
                if casefold_collision and not overlapping_paths
                else "ambiguous stage output ownership"
            )
            raise StageIntegrityError(
                f"{detail} between {unit_id!r} and {other_unit_id!r}: {path!r} vs {other_path!r}",
            )
