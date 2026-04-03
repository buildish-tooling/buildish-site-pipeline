# Copyright 2026 The Apache Software Foundation

"""Stage materialization and publication helpers for build and watch."""

from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from apache_buildish_site_pipeline.models import ProviderSnapshotV1
from apache_buildish_site_pipeline.models.aggregates import (
    ArtifactsDataEntry,
    ComponentsDataEntry,
    ProvidersDataEntry,
    RedirectAggregateEntry,
    RouteAggregateEntry,
)
from apache_buildish_site_pipeline.models.enums import RecordKind, StageCommand
from apache_buildish_site_pipeline.models.planning_stage_contract import (
    PipelineDiagnosticEntry,
    StageDataFiles,
    StageManifestV1,
    StageRoots,
)
from apache_buildish_site_pipeline.models.staged_front_matter import (
    ArtifactFrontMatterSummary,
    ResolvedOrigin,
    ResolvedPathSet,
    ResolvedPublication,
    ResolvedUrlSet,
)

from ..cli_errors import RetainedStageError, StageIntegrityError
from ..planning.types import ResolvedComponentConfig, ResolvedPublicationPolicy, SelectedVersionContext
from .types import EffectiveBuildPlan


@dataclass(frozen=True, slots=True)
class StagePublicationResult:
    """Paths of one successfully published stage tree."""

    stage_root: Path
    manifest_path: Path


def publish_stage(
    *,
    build_plan: EffectiveBuildPlan,
    diagnostics: tuple[PipelineDiagnosticEntry, ...],
    provider_snapshot: ProviderSnapshotV1,
    stage_root: Path,
    assembly_root: Path | None = None,
    allow_replace_existing: bool = False,
) -> StagePublicationResult:
    """Materialize and publish one finalized stage tree."""

    validate_visible_stage_target_path(stage_root)
    normalized_stage_root = stage_root.resolve(strict=False)
    parent_path = normalized_stage_root.parent
    parent_path.mkdir(parents=True, exist_ok=True)

    temp_root = (
        assembly_root.resolve(strict=False)
        if assembly_root is not None
        else Path(tempfile.mkdtemp(prefix=f".{normalized_stage_root.name}.", dir=parent_path))
    )
    try:
        materialize_stage_tree(
            stage_root=temp_root,
            build_plan=build_plan,
            diagnostics=diagnostics,
            provider_snapshot=provider_snapshot,
        )
        return finalize_stage_publication(
            candidate_stage_root=temp_root,
            stage_root=normalized_stage_root,
            allow_replace_existing=allow_replace_existing,
        )
    except Exception:
        shutil.rmtree(temp_root, ignore_errors=True)
        raise


def materialize_stage_tree(
    *,
    stage_root: Path,
    build_plan: EffectiveBuildPlan,
    diagnostics: tuple[PipelineDiagnosticEntry, ...],
    provider_snapshot: ProviderSnapshotV1,
) -> StageManifestV1:
    """Materialize one complete candidate stage tree into a private directory."""

    if stage_root.exists():
        if stage_root.is_symlink():
            raise StageIntegrityError(f"Candidate stage root must not be a symlink: {stage_root}")
        if not stage_root.is_dir():
            raise StageIntegrityError(f"Candidate stage root must be a directory: {stage_root}")
        if any(stage_root.iterdir()):
            raise StageIntegrityError(f"Candidate stage root must be absent or empty: {stage_root}")
    stage_root.mkdir(parents=True, exist_ok=True)

    return _materialize_stage(
        stage_root=stage_root,
        build_plan=build_plan,
        diagnostics=diagnostics,
        provider_snapshot=provider_snapshot,
    )


def finalize_stage_publication(
    *,
    candidate_stage_root: Path,
    stage_root: Path,
    allow_replace_existing: bool = False,
) -> StagePublicationResult:
    """Publish a previously materialized candidate stage tree atomically."""

    validate_visible_stage_target_path(stage_root)
    normalized_candidate_root = candidate_stage_root.resolve(strict=False)
    normalized_stage_root = stage_root.resolve(strict=False)
    _validate_candidate_stage_root(normalized_candidate_root)
    _validate_publication_filesystems(
        candidate_stage_root=normalized_candidate_root,
        stage_root=normalized_stage_root,
    )
    if allow_replace_existing:
        _validate_replaceable_stage_root(normalized_stage_root)
        return _replace_stage_root(
            candidate_stage_root=normalized_candidate_root,
            stage_root=normalized_stage_root,
        )

    _validate_initial_stage_root(normalized_stage_root)
    if normalized_stage_root.exists():
        normalized_stage_root.rmdir()
    os.replace(normalized_candidate_root, normalized_stage_root)
    return StagePublicationResult(
        stage_root=normalized_stage_root,
        manifest_path=normalized_stage_root / "manifest.json",
    )


def _validate_initial_stage_root(stage_root: Path) -> None:
    if stage_root.exists() and stage_root.is_symlink():
        raise StageIntegrityError(f"Stage root must not be a symlink: {stage_root}")
    if stage_root.exists() and not stage_root.is_dir():
        raise StageIntegrityError(f"Stage root must be a directory: {stage_root}")
    if not stage_root.exists():
        return
    if any(stage_root.iterdir()):
        raise StageIntegrityError(
            f"Stage root must be absent or empty for the initial build implementation: {stage_root}",
        )


def _validate_replaceable_stage_root(stage_root: Path) -> None:
    if stage_root.exists() and stage_root.is_symlink():
        raise StageIntegrityError(f"Stage root must not be a symlink: {stage_root}")
    if stage_root.exists() and not stage_root.is_dir():
        raise StageIntegrityError(f"Stage root must be a directory: {stage_root}")


def _validate_candidate_stage_root(stage_root: Path) -> None:
    if not stage_root.exists() or not stage_root.is_dir() or stage_root.is_symlink():
        raise StageIntegrityError(f"Candidate stage root is not a normal directory: {stage_root}")
    manifest_path = stage_root / "manifest.json"
    if not manifest_path.exists() or not manifest_path.is_file():
        raise StageIntegrityError(f"Candidate stage root is missing manifest.json: {stage_root}")


def validate_visible_stage_target_path(stage_root: Path) -> None:
    """Reject visible stage targets that resolve through symlinked parents."""

    absolute_stage_root = stage_root if stage_root.is_absolute() else stage_root.absolute()
    parent_path = absolute_stage_root.parent
    if _contains_symlink(parent_path):
        raise StageIntegrityError(f"Stage root parent directory resolves through a symlink: {parent_path}")
    if absolute_stage_root.exists() and absolute_stage_root.is_symlink():
        raise StageIntegrityError(f"Stage root must not be a symlink: {absolute_stage_root}")


def _validate_publication_filesystems(*, candidate_stage_root: Path, stage_root: Path) -> None:
    """Reject publication paths that would require cross-filesystem finalization."""

    stage_parent = stage_root.parent
    if not stage_parent.exists() or not stage_parent.is_dir():
        raise StageIntegrityError(f"Stage root parent directory does not exist: {stage_parent}")

    target_device = _stat_device_id(stage_parent)
    candidate_device = _stat_device_id(candidate_stage_root)
    if candidate_device != target_device:
        raise StageIntegrityError(
            "Candidate stage root and visible stage root must live on the same filesystem "
            f"for atomic publication: {candidate_stage_root} -> {stage_root}",
        )

    if stage_root.exists() and _stat_device_id(stage_root) != target_device:
        raise StageIntegrityError(
            "Existing stage root and its parent must live on the same filesystem "
            f"for safe replacement publication: {stage_root}",
        )


def _stat_device_id(path: Path) -> int:
    """Return one filesystem device id for publication precondition checks."""

    return path.stat().st_dev


def _contains_symlink(path: Path) -> bool:
    """Return whether any existing path segment resolves through a symlink."""

    current = Path(path.anchor) if path.is_absolute() else Path()
    for part in path.parts:
        if current == Path(path.anchor) and part == path.anchor:
            continue
        current = current / part if current != Path() else Path(part)
        if current.exists() and current.is_symlink():
            return True
    return False


def _replace_stage_root(*, candidate_stage_root: Path, stage_root: Path) -> StagePublicationResult:
    parent_path = stage_root.parent
    parent_path.mkdir(parents=True, exist_ok=True)
    backup_root = Path(tempfile.mkdtemp(prefix=f".{stage_root.name}.backup.", dir=parent_path))
    shutil.rmtree(backup_root, ignore_errors=True)

    previous_stage_moved = False
    try:
        if stage_root.exists():
            os.replace(stage_root, backup_root)
            previous_stage_moved = True
        os.replace(candidate_stage_root, stage_root)
    except OSError as exc:
        if previous_stage_moved and backup_root.exists() and not stage_root.exists():
            try:
                os.replace(backup_root, stage_root)
            except OSError as rollback_exc:
                raise StageIntegrityError(
                    f"Could not finalize stage publication or roll back safely for {stage_root}: {rollback_exc}",
                ) from rollback_exc
            raise RetainedStageError(
                f"Could not finalize the newly materialized stage; retained the prior stage at {stage_root}",
            ) from exc
        raise StageIntegrityError(f"Could not finalize stage publication for {stage_root}: {exc}") from exc
    finally:
        if backup_root.exists():
            shutil.rmtree(backup_root, ignore_errors=True)

    return StagePublicationResult(
        stage_root=stage_root,
        manifest_path=stage_root / "manifest.json",
    )


def _materialize_stage(
    *,
    stage_root: Path,
    build_plan: EffectiveBuildPlan,
    diagnostics: tuple[PipelineDiagnosticEntry, ...],
    provider_snapshot: ProviderSnapshotV1,
) -> StageManifestV1:
    content_root = stage_root / "content"
    static_root = stage_root / "static"
    data_root = stage_root / "data"
    content_root.mkdir(parents=True, exist_ok=True)
    static_root.mkdir(parents=True, exist_ok=True)
    data_root.mkdir(parents=True, exist_ok=True)

    _copy_optional_tree(build_plan.site.site_pages_root, content_root / "site")
    _copy_optional_tree(build_plan.site.site_assets_root, static_root / "site")
    for vendor_asset in build_plan.site.vendor_assets:
        _copy_optional_tree(vendor_asset.source_path, static_root / "site" / "vendor" / vendor_asset.key)

    for component in build_plan.site.components:
        _copy_optional_tree(component.pages_root, content_root / "components" / component.slug / "pages")
        _copy_optional_tree(component.assets_root, static_root / "components" / component.slug / "assets")
    for context in build_plan.selected_versions:
        _copy_optional_tree(
            context.docs_root,
            content_root / "components" / context.component_slug / "contexts" / _context_subpath(context),
        )
        _copy_optional_tree(
            context.assets_root,
            static_root / "components" / context.component_slug / "contexts" / _context_subpath(context) / "assets",
        )

    data_files = _write_aggregate_files(
        stage_root=stage_root,
        build_plan=build_plan,
        diagnostics=diagnostics,
        provider_snapshot=provider_snapshot,
    )
    manifest = StageManifestV1(
        schema_version=1,
        stage_layout_version=1,
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        command=StageCommand.BUILD,
        front_matter_format="yaml",
        aggregate_format="json",
        roots=StageRoots(content="content", static="static", data="data"),
        data_files=data_files,
    )
    _write_json_file(stage_root / "manifest.json", manifest)
    return manifest


def _write_aggregate_files(*, stage_root: Path, build_plan: EffectiveBuildPlan, diagnostics, provider_snapshot) -> StageDataFiles:
    data_root = stage_root / "data"
    _write_json_file(data_root / "components.json", _build_components_entries(build_plan.site.components))
    _write_json_file(data_root / "artifacts.json", _build_artifacts_entries(build_plan.site.components))
    _write_json_file(
        data_root / "routes.json",
        _build_route_entries(build_plan.site.components, build_plan.selected_versions),
    )
    _write_json_file(data_root / "redirects.json", _build_redirect_entries(build_plan.site.components))

    providers_path = None
    if provider_snapshot.providers:
        providers_path = data_root / "providers.json"
        _write_json_file(providers_path, _build_provider_entries(provider_snapshot))

    diagnostics_path = None
    if diagnostics:
        diagnostics_path = data_root / "diagnostics.json"
        _write_json_file(diagnostics_path, list(diagnostics))

    return StageDataFiles(
        components="data/components.json",
        artifacts="data/artifacts.json",
        routes="data/routes.json",
        redirects="data/redirects.json",
        providers=str(providers_path.relative_to(stage_root)) if providers_path is not None else None,
        diagnostics=str(diagnostics_path.relative_to(stage_root)) if diagnostics_path is not None else None,
    )


def _build_components_entries(components: tuple[ResolvedComponentConfig, ...]) -> list[ComponentsDataEntry]:
    entries = []
    for component in components:
        entries.append(
            ComponentsDataEntry(
                slug=component.slug,
                display_name=component.authored.display_name,
                group=component.authored.group,
                origin_key=component.publication.origin.key,
                publication=_resolved_publication(component.publication),
                provider_keys=None,
                artifacts=[
                    ArtifactFrontMatterSummary(
                        key=artifact.key,
                        display_name=artifact.authored.display_name,
                    )
                    for artifact in component.artifacts
                ]
                or None,
            ),
        )
    return entries


def _build_artifacts_entries(components: tuple[ResolvedComponentConfig, ...]) -> list[ArtifactsDataEntry]:
    entries = []
    for component in components:
        for artifact in component.artifacts:
            entries.append(
                ArtifactsDataEntry(
                    component_slug=component.slug,
                    key=artifact.key,
                    display_name=artifact.authored.display_name,
                    source_key=artifact.source_binding.key,
                    docs_root=artifact.authored.docs_root,
                    versioning=artifact.versioning,
                ),
            )
    return entries


def _build_route_entries(
    components: tuple[ResolvedComponentConfig, ...],
    contexts: tuple[SelectedVersionContext, ...],
) -> list[RouteAggregateEntry]:
    component_by_slug = {component.slug: component for component in components}
    entries = []
    for component in components:
        publication = component.publication
        entries.extend(
            [
                _route_entry(component.slug, publication, publication.component_path, section="component", target_id=f"component:{component.slug}"),
                _route_entry(component.slug, publication, publication.development_path, section="development", target_id=f"development:{component.slug}"),
                _route_entry(component.slug, publication, publication.docs_path, section="docs", target_id=f"docs:{component.slug}"),
                _route_entry(component.slug, publication, publication.assets_path, section="assets", target_id=f"assets:{component.slug}"),
            ],
        )
    for context in contexts:
        publication = component_by_slug[context.component_slug].publication
        entries.append(
            _route_entry(
                context.component_slug,
                publication,
                _public_path_for_context(publication, context),
                artifact_key=context.artifact_key,
                section=context.kind.value,
                target_id=_target_id_for_context(context),
            ),
        )
    return entries


def _build_redirect_entries(components: tuple[ResolvedComponentConfig, ...]) -> list[RedirectAggregateEntry]:
    entries = []
    for component in components:
        for redirect in component.publication.redirects:
            origin = component.publication.origin
            to_url = redirect.target if str(redirect.target).startswith("http") else f"{origin.base_url.rstrip('/')}{redirect.target}"
            entries.append(
                RedirectAggregateEntry(
                    from_url=f"{origin.base_url.rstrip('/')}{redirect.from_path}",
                    to_url=to_url,
                    status=redirect.status or 302,
                    reason=redirect.reason,
                    source_kind="catalog",
                ),
            )
    return entries


def _build_provider_entries(provider_snapshot: ProviderSnapshotV1) -> list[ProvidersDataEntry]:
    return [
        ProvidersDataEntry(
            key=provider.key,
            type=str(provider.type),
            display_name=provider.display_name,
            base_url=provider.base_url,
            fetched_at=provider.fetched_at,
        )
        for provider in provider_snapshot.providers
    ]


def _resolved_publication(publication: ResolvedPublicationPolicy) -> ResolvedPublication:
    return ResolvedPublication(
        origin=ResolvedOrigin(
            key=publication.origin.key,
            base_url=publication.origin.base_url,
            hostname=publication.origin.hostname,
        ),
        paths=ResolvedPathSet(
            component=publication.component_path,
            development=publication.development_path,
            docs=publication.docs_path,
            assets=publication.assets_path,
        ),
        urls=ResolvedUrlSet(
            component=publication.component_url,
            development=publication.development_url,
            docs=publication.docs_url,
            assets=publication.assets_url,
        ),
    )


def _route_entry(component_slug, publication, path_value, *, artifact_key=None, section=None, target_id=None):
    return RouteAggregateEntry(
        origin_key=publication.origin.key,
        base_url=publication.origin.base_url,
        path=path_value,
        url=f"{publication.origin.base_url.rstrip('/')}{path_value}",
        component_slug=component_slug,
        artifact_key=artifact_key,
        section=section,
        canonical=path_value == publication.canonical_path if publication.canonical_path is not None else None,
        route_kind=section,
        target_id=target_id,
    )


def _public_path_for_context(publication: ResolvedPublicationPolicy, context: SelectedVersionContext) -> str:
    docs_path = publication.docs_path.rstrip("/")
    if context.kind is RecordKind.DEVELOPMENT:
        return publication.development_path
    if context.kind is RecordKind.LINE_HEAD:
        return f"{docs_path}/{context.release_line}/"
    if context.kind is RecordKind.RELEASED:
        return f"{docs_path}/releases/{context.version}/"
    if context.kind is RecordKind.CANDIDATE:
        return f"{docs_path}/candidates/{context.version}/"
    return f"{docs_path}/refs/{context.named_ref_key or context.ref}/"


def _target_id_for_context(context: SelectedVersionContext) -> str:
    if context.kind is RecordKind.DEVELOPMENT:
        return f"development:{context.component_slug}:{context.artifact_key}"
    if context.kind is RecordKind.LINE_HEAD:
        return f"line-head:{context.component_slug}:{context.artifact_key}:{context.release_line}"
    if context.kind is RecordKind.RELEASED:
        return f"released:{context.component_slug}:{context.artifact_key}:{context.version}"
    if context.kind is RecordKind.CANDIDATE:
        return f"candidate:{context.component_slug}:{context.artifact_key}:{context.version}"
    return f"named-ref:{context.component_slug}:{context.artifact_key}:{context.named_ref_key or context.ref}"


def _context_subpath(context: SelectedVersionContext) -> Path:
    if context.kind is RecordKind.DEVELOPMENT:
        return Path("development")
    if context.kind is RecordKind.LINE_HEAD:
        return Path("line-heads") / str(context.release_line)
    if context.kind is RecordKind.RELEASED:
        return Path("releases") / str(context.version)
    if context.kind is RecordKind.CANDIDATE:
        return Path("candidates") / str(context.version)
    return Path("refs") / str(context.named_ref_key or context.ref)


def _copy_optional_tree(source_path: Path | None, destination_path: Path) -> None:
    if source_path is None or not source_path.exists():
        return
    _copy_tree(source_path, destination_path)


def _copy_tree(source_root: Path, destination_root: Path) -> None:
    if source_root.is_symlink():
        raise StageIntegrityError(f"Stage input root must not be a symlink: {source_root}")
    if source_root.is_file():
        destination_root.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_root, destination_root)
        return
    destination_root.mkdir(parents=True, exist_ok=True)
    for source_path in source_root.rglob("*"):
        if source_path.is_symlink():
            raise StageIntegrityError(f"Stage input must not contain symlinks: {source_path}")
        relative_path = source_path.relative_to(source_root)
        destination_path = destination_root / relative_path
        if source_path.is_dir():
            destination_path.mkdir(parents=True, exist_ok=True)
            continue
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)


def _write_json_file(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(value, "model_dump_json"):
        serialized = value.model_dump_json(indent=2, exclude_none=True)
    else:
        serialized = "[\n" + ",\n".join(entry.model_dump_json(indent=2, exclude_none=True) for entry in value) + "\n]"
    path.write_text(f"{serialized}\n", encoding="utf-8")