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

"""Coordinator-owned destination claims for pages, copied files and reservations."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from ..cli.errors import StageIntegrityError
from ..models.enums import ContextAction
from ..models.emitted.staged_front_matter import PipelineComponentFrontMatter
from ..planning.types import ResolvedSiteConfig, SelectedVersionContext
from ..public_paths import join_public_path, normalize_public_path
from .front_matter import detect_locale, is_page_path, public_page_path
from .ownership import source_root_for_context
from .publication_paths import (
    can_share_context_route,
    public_path_for_context,
    stage_root_for_public_path,
    target_id_for_context,
)
from .source_tree import iter_source_tree_files
from .worker_protocol import (
    LocalizationWire,
    StagedPageContributionWire,
    WorkerSpecWire,
)
from ..planning.types import ResolvedLocalizationPolicy

_MAX_DESTINATION_CLAIMS = 100_000


@dataclass(frozen=True, slots=True)
class DestinationClaim:
    """One producer's concrete file or reserved public surface."""

    producer: str
    source: str
    public_path: str
    origin: str | None = None
    stage_path: Path | None = None
    page: bool = False
    locale: str | None = None
    kind: str = "file"
    artifact_key: str | None = None
    unit_id: str | None = None
    context: SelectedVersionContext | None = None
    artifact_routing: str = "shared"

    @property
    def output_path(self) -> str:
        path = normalize_public_path(self.public_path, trailing_slash=False)
        if (
            self.page or self.kind in {"alias", "redirect"}
        ) and not path.lower().endswith((".html", ".htm")):
            return join_public_path(path, "index.html", trailing_slash=False)
        return path


def _tree_claims(
    source: Path | None,
    stage: Path,
    public: str,
    producer: str,
    *,
    origin: str | None = None,
    pages: bool = False,
    localization: ResolvedLocalizationPolicy | LocalizationWire | None = None,
    exclusions: tuple[str, ...] = (".git",),
    snapshots: tuple[str, ...] = (),
    artifact_key: str | None = None,
    unit_id: str | None = None,
) -> Iterable[DestinationClaim]:
    if source is None:
        return
    for source_path, relative in iter_source_tree_files(
        source_root=source,
        exclusions=exclusions,
        snapshot_paths=snapshots,
    ):
        page = pages and is_page_path(source_path)
        locale, _, routed = (
            detect_locale(relative, localization) if page else (None, False, relative)
        )
        path = (
            public_page_path(public, routed)
            if page
            else join_public_path(public, relative.as_posix(), trailing_slash=False)
        )
        yield DestinationClaim(
            producer,
            str(source_path),
            path,
            origin,
            stage / relative,
            page,
            locale,
            artifact_key=artifact_key,
            unit_id=unit_id,
        )


def collect_destination_claims(
    site: ResolvedSiteConfig,
    contexts: Iterable[SelectedVersionContext],
    snapshot_paths: tuple[Path, ...] = (),
) -> tuple[DestinationClaim, ...]:
    """Enumerate actual owned inputs without trusting worker or retained labels."""
    snapshots = tuple(str(path) for path in snapshot_paths)
    claims: list[DestinationClaim] = []

    def add(items: Iterable[DestinationClaim]) -> None:
        for item in items:
            if len(claims) >= _MAX_DESTINATION_CLAIMS:
                raise StageIntegrityError(
                    "Destination claim inventory exceeds its safety ceiling; validation is incomplete"
                )
            claims.append(item)

    add(
        _tree_claims(
            site.site_pages_root,
            Path("content/site"),
            "/site/",
            "site-pages",
            pages=True,
            snapshots=snapshots,
        )
    )
    add(
        _tree_claims(
            site.site_assets_root,
            Path("static/site"),
            "/site/",
            "site-assets",
            snapshots=snapshots,
        )
    )
    for asset in site.vendor_assets:
        add(
            _tree_claims(
                asset.source_path,
                Path("static/site/vendor") / asset.key,
                f"/site/vendor/{asset.key}/",
                f"vendor:{asset.key}",
                snapshots=snapshots,
            )
        )
    components = {component.slug: component for component in site.components}
    for component in site.components:
        publication = component.publication
        origin = publication.origin.key
        unit_id = f"component:{component.slug}"
        add(
            _tree_claims(
                component.pages_root,
                stage_root_for_public_path("content", publication.component_path),
                publication.component_path,
                f"{unit_id}:pages",
                origin=origin,
                pages=True,
                localization=component.localization,
                snapshots=snapshots,
                unit_id=unit_id,
            )
        )
        add(
            _tree_claims(
                component.assets_root,
                stage_root_for_public_path("static", publication.assets_path),
                publication.assets_path,
                f"{unit_id}:assets",
                origin=origin,
                snapshots=snapshots,
            )
        )
        for alias in publication.aliases:
            add(
                (
                    DestinationClaim(
                        f"alias:{component.slug}:{alias.path}",
                        str(component.metadata_file),
                        str(alias.path),
                        alias.origin or origin,
                        kind="alias",
                    ),
                )
            )
        for redirect in publication.redirects:
            add(
                (
                    DestinationClaim(
                        f"redirect:{component.slug}:{redirect.from_path}",
                        str(component.metadata_file),
                        str(redirect.from_path),
                        redirect.from_origin or origin,
                        kind="redirect",
                    ),
                )
            )
        mount_groups = [(unit_id, component.authored.mounts or ())]
        mount_groups.extend(
            (f"artifact:{component.slug}:{artifact.key}", artifact.binding.mounts or ())
            for artifact in component.artifacts
            if artifact.binding is not None
        )
        for owner, mounts in mount_groups:
            for index, mount in enumerate(mounts):
                add(
                    (
                        DestinationClaim(
                            f"mount:{owner}:{index}",
                            str(mount.source),
                            str(mount.mount_path),
                            origin,
                            kind="mount",
                        ),
                    )
                )
    for context in contexts:
        component = components[context.component_slug]
        public = public_path_for_context(component.publication, context)
        origin = component.publication.origin.key
        producer = target_id_for_context(context)
        unit_id = f"component:{component.slug}"
        add(
            (
                DestinationClaim(
                    producer,
                    str(context.docs_root),
                    public,
                    origin,
                    kind="redirect"
                    if context.action is ContextAction.REDIRECT
                    else "context",
                    context=context,
                    artifact_routing=component.publication.artifact_routing,
                ),
            )
        )
        content_root = stage_root_for_public_path("content", public)
        if context.action is ContextAction.NOTICE:
            add(
                (
                    DestinationClaim(
                        producer,
                        "generated withdrawal notice",
                        normalize_public_path(public, trailing_slash=False),
                        origin,
                        content_root / "index.md",
                        page=True,
                        artifact_key=context.artifact_key,
                        unit_id=unit_id,
                    ),
                )
            )
        elif context.action is ContextAction.DOCS:
            add(
                _tree_claims(
                    source_root_for_context(context.docs_root, context),
                    content_root,
                    public,
                    producer,
                    origin=origin,
                    pages=True,
                    localization=component.localization,
                    exclusions=context.source_exclusions,
                    snapshots=snapshots,
                    artifact_key=context.artifact_key,
                    unit_id=unit_id,
                )
            )
            add(
                _tree_claims(
                    source_root_for_context(context.assets_root, context),
                    stage_root_for_public_path("static", public),
                    public,
                    producer + ":assets",
                    origin=origin,
                    exclusions=context.source_exclusions,
                    snapshots=snapshots,
                )
            )
    return tuple(claims)


def _conflict(
    first: DestinationClaim, second: DestinationClaim, path: str
) -> StageIntegrityError:
    return StageIntegrityError(
        f"Destination conflict at {path}: {first.producer} ({first.source}) and {second.producer} ({second.source})"
    )


def validate_destination_claims(claims: Iterable[DestinationClaim]) -> None:
    """Reject ambiguous files, rendered URLs and reserved mount subtrees."""
    claims = tuple(claims)
    files = [claim for claim in claims if claim.stage_path is not None]
    routes = [claim for claim in claims if claim.kind in {"alias", "redirect"}]
    contexts: dict[tuple[str | None, str], list[DestinationClaim]] = {}
    for claim in claims:
        if claim.context is None:
            continue
        context_key = (
            claim.origin,
            normalize_public_path(claim.public_path, trailing_slash=False).lower(),
        )
        previous = contexts.setdefault(context_key, [])
        for other in previous:
            if other.context is not None and not can_share_context_route(
                claim.artifact_routing, other.context, claim.context
            ):
                raise _conflict(other, claim, claim.public_path)
        previous.append(claim)
    stage_paths: dict[str, DestinationClaim] = {}
    for claim in files:
        if claim.stage_path is None:
            continue
        key = claim.stage_path.as_posix().casefold()
        if key in stage_paths:
            raise _conflict(stage_paths[key], claim, key)
        stage_paths[key] = claim
    for key, claim in stage_paths.items():
        for parent in PurePosixPath(key).parents:
            if str(parent) in stage_paths:
                raise _conflict(stage_paths[str(parent)], claim, key)

    # A page is a container in pretty URLs, but renders to an actual index file.
    # Compare rendered filenames to catch content/static file-vs-directory claims.
    outputs: dict[str, list[DestinationClaim]] = {}
    for claim in (*files, *routes):
        outputs.setdefault(claim.output_path.casefold(), []).append(claim)
    for path, group in outputs.items():
        candidates = list(group)
        for parent in PurePosixPath(path).parents:
            candidates.extend(outputs.get(str(parent), ()))
        for claim in group:
            for other in candidates:
                if other is claim or not _same_origin(other, claim):
                    continue
                if (
                    other.page
                    and claim.page
                    and other.locale
                    and claim.locale
                    and other.locale != claim.locale
                ):
                    continue
                raise _conflict(other, claim, path)
    reservations = [claim for claim in claims if claim.kind == "mount"]
    for index, mount in enumerate(reservations):
        root = normalize_public_path(mount.public_path, trailing_slash=False).casefold()
        for other in (
            *files,
            *routes,
            *reservations[index + 1 :],
            *(claim for claim in claims if claim.kind == "context"),
        ):
            if not _same_origin(mount, other):
                continue
            path = normalize_public_path(
                other.public_path, trailing_slash=False
            ).casefold()
            if (
                _within(path, root)
                or (other.kind in {"mount", "redirect"} and _within(root, path))
                or (
                    other.stage_path is not None
                    and _within(root, other.output_path.casefold())
                )
            ):
                raise _conflict(mount, other, path)


def _within(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip("/") + "/")


def _same_origin(first: DestinationClaim, second: DestinationClaim) -> bool:
    return (
        first.origin is None or second.origin is None or first.origin == second.origin
    )


def reconcile_candidate_files(
    root: Path,
    claims: tuple[DestinationClaim, ...],
    pages: Iterable[StagedPageContributionWire],
) -> None:
    """Directory ownership cannot vouch for unmanifested retained descendants."""
    expected = {
        claim.stage_path: claim for claim in claims if claim.stage_path is not None
    }
    actual: set[Path] = set()
    for tree in ("content", "static"):
        for _, relative in iter_source_tree_files(
            source_root=root / tree, exclusions=()
        ):
            path = Path(tree) / relative
            if path not in expected:
                raise StageIntegrityError(
                    f"Unexpected candidate file without a current producer: {path}"
                )
            actual.add(path)
    missing = expected.keys() - actual
    if missing:
        raise StageIntegrityError(f"Missing claimed candidate file: {min(missing)}")
    seen: set[Path] = set()
    for page in pages:
        path = Path(page.stage_relative_path)
        claim = expected.get(path)
        if path in seen:
            raise StageIntegrityError(
                f"Duplicate page contribution destination: {path}"
            )
        if (
            claim is None
            or not claim.page
            or claim.artifact_key != page.artifact_key
            or claim.public_path != page.public_path
        ):
            raise StageIntegrityError(
                f"Page contribution does not match its owned destination claim: {path}"
            )
        seen.add(path)
    missing_pages = {
        path
        for path, claim in expected.items()
        if claim.page and claim.unit_id is not None
    } - seen
    if missing_pages:
        raise StageIntegrityError(
            f"Missing owned page contribution: {min(missing_pages)}"
        )


def validate_component_worker_claims(spec: WorkerSpecWire) -> None:
    """Guard same-unit writes using current producers, including seeded outputs."""
    claims: list[DestinationClaim] = []
    publication = spec.component_publication
    if publication is not None:
        claims.extend(
            _tree_claims(
                Path(spec.component_pages_source)
                if spec.component_pages_source
                else None,
                Path(spec.component_pages_stage_root or ""),
                publication.path,
                "component-pages",
                pages=True,
                localization=spec.localization,
                snapshots=spec.snapshot_paths,
            )
        )
    assets_public = (
        PipelineComponentFrontMatter.model_validate(
            spec.component_front_matter
        ).publication.paths.assets
        if spec.component_front_matter is not None
        else "/"
    )
    claims.extend(
        _tree_claims(
            Path(spec.component_assets_source)
            if spec.component_assets_source
            else None,
            Path(spec.component_assets_stage_root or ""),
            assets_public,
            "component-assets",
            snapshots=spec.snapshot_paths,
        )
    )
    for context in spec.contexts:
        content = Path(context.content_stage_root)
        if context.action == "notice":
            claims.append(
                DestinationClaim(
                    context.context_id,
                    "generated withdrawal notice",
                    context.publication.path,
                    stage_path=content / "index.md",
                    page=True,
                )
            )
        elif context.action == "docs":
            claims.extend(
                _tree_claims(
                    Path(context.source_docs_root)
                    if context.source_docs_root
                    else None,
                    content,
                    context.publication.path,
                    context.context_id,
                    pages=True,
                    localization=spec.localization,
                    exclusions=context.source_exclusions,
                    snapshots=spec.snapshot_paths,
                )
            )
            claims.extend(
                _tree_claims(
                    Path(context.source_assets_root)
                    if context.source_assets_root
                    else None,
                    Path(context.static_stage_root),
                    context.publication.path,
                    context.context_id + ":assets",
                    exclusions=context.source_exclusions,
                    snapshots=spec.snapshot_paths,
                )
            )
    validate_destination_claims(claims)
