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

"""Artifact-scoped recommendation targets and stage-backed landing destinations."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from ...docs.documentation import PipelineDerivedModel
from ..enums import ContextAction, PublicationState
from ..scalars import NonEmptyString, PublicPath, UrlString, VersionString


class DocsAvailability(PipelineDerivedModel):
    """An owned root documentation page in the assembled stage, not remote availability."""

    kind: Literal["docs"] = "docs"
    path: PublicPath
    url: UrlString


class NoticeAvailability(PipelineDerivedModel):
    """A generated withdrawal notice, not original documentation."""

    kind: Literal["notice"] = "notice"
    path: PublicPath
    url: UrlString


class RedirectAvailability(PipelineDerivedModel):
    """An emitted withdrawal redirect instruction, not attested destination content."""

    kind: Literal["redirect"] = "redirect"
    path: PublicPath
    url: UrlString
    to_url: UrlString


class UnavailableDesignation(PipelineDerivedModel):
    """A recommendation without an eligible landing destination in this stage."""

    kind: Literal["unavailable"] = "unavailable"
    reason: Literal[
        "not-selected",
        "hidden",
        "withdrawn",
        "tombstoned",
        "snapshot-absent",
        "omitted",
        "no-landing-page",
    ]


DesignationAvailability = Annotated[
    DocsAvailability
    | NoticeAvailability
    | RedirectAvailability
    | UnavailableDesignation,
    Field(discriminator="kind"),
]


class ReleaseDesignationTarget(PipelineDerivedModel):
    """An exact released recommendation scoped by its containing component/artifact row."""

    version: VersionString
    selected: bool
    publication_state: PublicationState | None = None
    action: ContextAction | None = None
    availability: DesignationAvailability

    @model_validator(mode="after")
    def ensure_disposition_consistency(self) -> Self:
        if self.selected != (self.action is not None):
            raise ValueError("Only selected designation targets have an action")
        available = self.availability
        if not self.selected:
            if (
                not isinstance(available, UnavailableDesignation)
                or available.reason != "not-selected"
            ):
                raise ValueError("Unselected targets must be unavailable/not-selected")
            return self
        if available.kind != "unavailable" and available.kind != self.action:
            raise ValueError("Designation availability must match its action")
        if isinstance(available, UnavailableDesignation):
            if self.action is ContextAction.DOCS:
                valid = available.reason == "no-landing-page"
            elif self.action is ContextAction.OMIT:
                valid = available.reason in {
                    "hidden",
                    "withdrawn",
                    "tombstoned",
                    "snapshot-absent",
                    "omitted",
                }
            else:
                valid = False
            if not valid:
                raise ValueError("Unavailable reason must match selected action")
        if (
            self.publication_state is PublicationState.HIDDEN
            and self.action is not ContextAction.OMIT
        ):
            raise ValueError("Hidden targets must be omitted")
        withdrawn = self.publication_state in {
            PublicationState.WITHDRAWN,
            PublicationState.TOMBSTONED,
        }
        if withdrawn and self.action is ContextAction.DOCS:
            raise ValueError("Withdrawn targets cannot expose original docs")
        if (
            self.action in {ContextAction.NOTICE, ContextAction.REDIRECT}
            and not withdrawn
        ):
            raise ValueError("Notice/redirect requires withdrawn or tombstoned state")
        return self


class ReleaseLineDesignation(PipelineDerivedModel):
    """One explicit line recommendation; multiple lines may share the same target."""

    key: NonEmptyString
    target: ReleaseDesignationTarget


class ReleaseDesignations(PipelineDerivedModel):
    """Explicit recommendations and availability; no inferred latest or full inventory."""

    snapshot_status: Literal["present", "missing", "not-configured"] = Field(
        description="Status of the configured component snapshot input, not inventory completeness."
    )
    latest_stable: ReleaseDesignationTarget | None = None
    lines: list[ReleaseLineDesignation]

    @model_validator(mode="after")
    def ensure_unique_lines(self) -> Self:
        keys = [line.key for line in self.lines]
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate designation line key")
        return self
