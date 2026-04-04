# Copyright 2026 The Apache Software Foundation

"""Owned-unit planning and output-root validation for staging."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from ..cli_errors import StageIntegrityError
from ..models.enums import RecordKind
from ..planning.types import ResolvedVendorAsset, SelectedVersionContext
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


def context_subpath(context: SelectedVersionContext) -> Path:
    """Return the stable internal stage subpath for one selected version context."""

    if context.kind == RecordKind.DEVELOPMENT:
        return Path("development")
    if context.kind == RecordKind.RELEASED:
        return Path("releases") / (context.version or "unversioned")
    if context.kind == RecordKind.LINE_HEAD:
        release_line = context.release_line or (context.provider_record.release_line if context.provider_record is not None else None) or "unknown"
        return Path("line-heads") / release_line
    if context.kind == RecordKind.NAMED_REF:
        return Path("refs") / (context.named_ref_key or context.ref or "unknown")
    if context.kind == RecordKind.CANDIDATE:
        return Path("candidates") / (context.version or context.ref or "unknown")
    raise StageIntegrityError(f"Unsupported selected context kind for staging: {context.kind}")


def build_owned_units(build_plan: EffectiveBuildPlan) -> tuple[OwnedUnit, ...]:
    """Produce the first-wave owned units from one validated build plan."""

    units: list[OwnedUnit] = []
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
        contexts_by_component.setdefault(context.component_slug, []).append(
            OwnedContextInput(
                context_id=f"{context.component_slug}:{context.artifact_key}:{context.kind}:{context.ref}",
                context=context,
                content_stage_root=Path("content") / "components" / context.component_slug / "contexts" / context_subpath(context),
                static_stage_root=Path("static") / "components" / context.component_slug / "contexts" / context_subpath(context) / "assets",
            ),
        )

    for component in build_plan.site.components:
        component_contexts = tuple(contexts_by_component.get(component.slug, ()))
        if component.pages_root is None and component.assets_root is None and not component_contexts:
            continue
        units.append(
            OwnedUnit(
                unit_id=f"component:{component.slug}",
                owner_id=f"component:{component.slug}",
                kind=OwnedUnitKind.COMPONENT,
                content_stage_roots=(Path("content") / "components" / component.slug,),
                static_stage_roots=(Path("static") / "components" / component.slug,),
                component_slug=component.slug,
                component_pages_source=component.pages_root,
                component_assets_source=component.assets_root,
                contexts=component_contexts,
            ),
        )

    _validate_output_ownership(tuple(units))
    return tuple(units)


def _validate_output_ownership(units: tuple[OwnedUnit, ...]) -> None:
    claims: list[tuple[str, str, str]] = []
    for unit in units:
        for root in (*unit.content_stage_roots, *unit.static_stage_roots):
            claims.append((str(root), unit.owner_id, unit.unit_id))
    sorted_claims = sorted(claims, key=lambda claim: claim[0])
    for index, (path, owner_id, unit_id) in enumerate(sorted_claims):
        for other_path, other_owner_id, other_unit_id in sorted_claims[index + 1 :]:
            if other_path == path or other_path.startswith(f"{path}/") or path.startswith(f"{other_path}/"):
                if owner_id != other_owner_id:
                    raise StageIntegrityError(
                        "Ambiguous stage output ownership between "
                        f"{unit_id!r} and {other_unit_id!r}: {path!r} vs {other_path!r}",
                    )