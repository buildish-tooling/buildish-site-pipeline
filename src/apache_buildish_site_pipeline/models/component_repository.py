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

"""Component-owned authored metadata documents."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base import SitePipelineBaseModel
from .scalars import Identifier, NonEmptyString, RepoRelativePath, Slug, VersionString


class ComponentIdentity(SitePipelineBaseModel):
    """Stable identity for a component repository."""

    slug: Slug = Field(description="Stable component identifier used by consumer catalogs and staged metadata.")
    display_name: NonEmptyString | None = Field(default=None, description="Human-readable component name shown in rendered navigation and listings.")


class ContentRoots(SitePipelineBaseModel):
    """Repository-relative locations of authored component content."""

    pages_root: RepoRelativePath | None = Field(default=None, description="Repository-relative root for non-versioned component-owned pages.")
    docs_root: RepoRelativePath | None = Field(default=None, description="Repository-relative root for versioned or development docs content.")
    assets_root: RepoRelativePath | None = Field(default=None, description="Repository-relative root for component-owned static assets.")


class SupportStatusDefinition(SitePipelineBaseModel):
    """Definition of one support-status vocabulary entry."""

    display_name: NonEmptyString
    order: int | None = None
    description: NonEmptyString | None = None
    default_maintenance_phase: NonEmptyString | None = None


class ComponentLifecycleHints(SitePipelineBaseModel):
    """Optional high-level lifecycle defaults for a component."""

    latest_stable: VersionString | None = Field(default=None, description="Latest stable version for the component when one overall release line is enough.")
    support_status_vocabulary: dict[Identifier, SupportStatusDefinition] | None = Field(default=None, description="Optional support-status vocabulary shared by artifacts in this repository.")


class ComponentRepositoryDocumentV1(SitePipelineBaseModel):
    """Component-owned metadata from ``site/component.yaml``."""

    schema_version: Literal[1] = Field(description="Schema version for the component metadata file.")
    component: ComponentIdentity = Field(description="Stable identity for the component repository.")
    content: ContentRoots | None = Field(default=None, description="Repository-relative authored content roots owned by this component.")
    lifecycle: ComponentLifecycleHints | None = Field(default=None, description="Optional high-level lifecycle hints shared across the component repository.")