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

"""Finalize designation destinations from reconciled, currently owned stage evidence."""

from pathlib import Path

from ..cli.errors import StageIntegrityError
from ..models.enums import ContextAction, RecordKind
from ..models.emitted.aggregates import RedirectAggregateEntry
from ..models.emitted.release_designations import (
    ReleaseDesignations,
    ReleaseDesignationTarget,
    ReleaseLineDesignation,
    DocsAvailability,
    NoticeAvailability,
    RedirectAvailability,
    UnavailableDesignation,
)
from ..planning.types import (
    ResolvedReleaseFact,
    SelectedVersionContext,
    ResolvedComponentConfig,
)
from .destination_claims import DestinationClaim
from .front_matter import detect_locale
from .publication_paths import (
    public_path_for_context,
    stage_root_for_public_path,
    target_id_for_context,
)
from .types import EffectiveBuildPlan
from .worker_protocol import UnitContributionManifestWire, StagedPageContributionWire


def build_release_designations(
    plan: EffectiveBuildPlan,
    manifests: tuple[UnitContributionManifestWire, ...],
    claims: tuple[DestinationClaim, ...],
    redirects: list[RedirectAggregateEntry],
) -> dict[tuple[str, str], ReleaseDesignations]:
    """Resolve once after candidate files and owned contributions are reconciled."""
    components = {item.slug: item for item in plan.site.components}
    contexts = {
        (item.component_slug, item.artifact_key, item.version): item
        for item in plan.desired_versions or plan.selected_versions
        if item.kind is RecordKind.RELEASED
    }
    dispositions = {
        (item.component_slug, item.artifact_key, item.version): item
        for item in plan.context_dispositions
    }
    pages = {
        Path(page.stage_relative_path): (manifest.unit_id, page)
        for manifest in manifests
        for page in manifest.pages
    }
    claims_by_producer: dict[str, list[DestinationClaim]] = {}
    for claim in claims:
        if claim.page:
            claims_by_producer.setdefault(claim.producer, []).append(claim)
    result = {}
    for artifact in plan.release_designations:
        component = components[artifact.component_slug]
        targets = {}
        for fact in artifact.targets:
            identity = (artifact.component_slug, artifact.artifact_key, fact.version)
            context = contexts.get(identity)
            if context is None:
                targets[fact.version] = ReleaseDesignationTarget(
                    version=fact.version,
                    selected=False,
                    publication_state=fact.publication_state,
                    availability=UnavailableDesignation(reason="not-selected"),
                )
                continue
            disposition = dispositions.get(identity)
            if disposition is None:
                raise StageIntegrityError(
                    "Designation is missing its current disposition"
                )
            availability = _availability(
                component,
                context,
                claims_by_producer,
                pages,
                redirects,
                disposition.reason,
            )
            targets[fact.version] = _target(fact, context, availability)
        result[(artifact.component_slug, artifact.artifact_key)] = ReleaseDesignations(
            snapshot_status=artifact.snapshot_status,
            latest_stable=targets[artifact.latest_stable]
            if artifact.latest_stable is not None
            else None,
            lines=[
                ReleaseLineDesignation(key=key, target=targets[version])
                for key, version in artifact.lines
            ],
        )
    return result


def _target(
    fact: ResolvedReleaseFact,
    context: SelectedVersionContext,
    availability: DocsAvailability
    | NoticeAvailability
    | RedirectAvailability
    | UnavailableDesignation,
) -> ReleaseDesignationTarget:
    if context.publication_state != fact.publication_state:
        raise StageIntegrityError("Designation state differs from its selected context")
    return ReleaseDesignationTarget(
        version=fact.version,
        selected=True,
        publication_state=fact.publication_state,
        action=context.action,
        availability=availability,
    )


def _availability(
    component: ResolvedComponentConfig,
    context: SelectedVersionContext,
    claims_by_producer: dict[str, list[DestinationClaim]],
    pages: dict[Path, tuple[str, StagedPageContributionWire]],
    redirects: list[RedirectAggregateEntry],
    reason: str | None,
) -> (
    DocsAvailability
    | NoticeAvailability
    | RedirectAvailability
    | UnavailableDesignation
):
    if context.action is ContextAction.OMIT:
        return UnavailableDesignation.model_validate({"reason": reason or "omitted"})
    publication = component.publication
    path = public_path_for_context(publication, context)
    url = f"{publication.origin.base_url.rstrip('/')}{path}"
    if context.action is ContextAction.REDIRECT:
        matches = [
            entry
            for entry in redirects
            if entry.source_kind == "withdrawal" and entry.from_url == url
        ]
        if len(matches) != 1:
            raise StageIntegrityError(
                "Designation redirect has no unique resolved withdrawal instruction"
            )
        return RedirectAvailability(path=path, url=url, to_url=matches[0].to_url)
    root = stage_root_for_public_path("content", path)
    found = False
    for claim in claims_by_producer.get(target_id_for_context(context), ()):
        if claim.stage_path is None or claim.public_path.rstrip("/") != path.rstrip(
            "/"
        ):
            continue
        owned = pages.get(claim.stage_path)
        if owned is None:
            raise StageIntegrityError(
                "Designation root has no reconciled page contribution"
            )
        unit_id, page = owned
        relative = claim.stage_path.relative_to(root)
        locale, default_locale, _ = detect_locale(relative, component.localization)
        expected_kind = (
            "withdrawal-notice"
            if context.action is ContextAction.NOTICE
            else "release-page"
        )
        if (
            unit_id != claim.unit_id
            or page.component_slug != component.slug
            or page.artifact_key != context.artifact_key
            or page.origin_key != publication.origin.key
            or page.version_kind != "released"
            or page.version != context.version
            or page.page_kind != expected_kind
            or page.locale != locale
            or page.default_locale != default_locale
            or page.public_path.rstrip("/") != path.rstrip("/")
            or page.public_url != url
        ):
            raise StageIntegrityError(
                "Designation root contribution does not match its current owned context"
            )
        if locale is None or default_locale:
            found = True
    if found:
        if context.action is ContextAction.NOTICE:
            return NoticeAvailability(path=path, url=url)
        return DocsAvailability(path=path, url=url)
    if context.action is ContextAction.NOTICE:
        raise StageIntegrityError("Designation notice has no eligible reconciled root")
    return UnavailableDesignation(reason="no-landing-page")
