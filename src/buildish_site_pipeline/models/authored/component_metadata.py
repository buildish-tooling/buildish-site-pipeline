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

"""Component-owned authored metadata documents."""

from __future__ import annotations

from typing import ClassVar, Literal, Self

from pydantic import Field, model_validator

from ...docs.documentation import (
    ComponentOwnedAuthoredModel as SitePipelineBaseModel,
    ContractDocumentation,
    SchemaExample,
    SchemaExportSpecification,
)
from ...docs.reference_docs import (
    ReferenceDocumentation,
    ReferenceMarkdown,
    ReferenceSection,
)
from ...docs.schema_examples import component_metadata_example_document
from ..scalars import (
    ArtifactKey,
    Identifier,
    NonEmptyString,
    RepoRelativePath,
    Slug,
    UrlString,
)
from .artifacts import ArtifactVersioningConfig, SupportStatusDefinition, SupportWindow


class ComponentIdentity(SitePipelineBaseModel):
    """Stable identity for a component repository."""

    slug: Slug = Field(
        description="Stable component identifier used by consumer catalogs and staged metadata."
    )
    display_name: NonEmptyString | None = Field(
        default=None,
        description="Human-readable component name shown in rendered navigation and listings.",
    )


class ContentRoots(SitePipelineBaseModel):
    """Repository-relative locations of authored component content."""

    pages_root: RepoRelativePath | None = Field(
        default=None,
        description="Repository-relative root for non-versioned component-owned pages.",
    )
    docs_root: RepoRelativePath | None = Field(
        default=None,
        description="Repository-relative root for versioned or development docs content.",
    )
    assets_root: RepoRelativePath | None = Field(
        default=None,
        description="Repository-relative root for component-owned static assets.",
    )


class ComponentLifecycleHints(SitePipelineBaseModel):
    """Optional lifecycle defaults shared across all artifacts in a component repository."""

    support_status_vocabulary: dict[Identifier, SupportStatusDefinition] | None = Field(
        default=None,
        description="Optional support-status vocabulary shared by artifacts in this repository.",
    )


class ArtifactSupportPolicy(SitePipelineBaseModel):
    """Reusable static support defaults owned by an artifact."""

    support_status_vocabulary: dict[Identifier, SupportStatusDefinition] | None = Field(
        default=None,
        description="Reusable artifact-specific support-status vocabulary layered over component defaults.",
    )
    support_policy_url: UrlString | None = Field(
        default=None, description="Canonical support policy URL for this artifact."
    )
    default_support_window: SupportWindow | None = Field(
        default=None,
        description="Fallback support window when a release or line supplies no narrower window.",
    )


class ComponentArtifactDefinition(SitePipelineBaseModel):
    """Stable artifact identity and repository-relative content layout."""

    key: ArtifactKey = Field(
        description="Stable artifact identity referenced by inventories and optional catalog bindings."
    )
    display_name: NonEmptyString | None = Field(
        default=None, description="Canonical human-readable artifact label."
    )
    docs_root: RepoRelativePath | None = Field(
        default=None,
        description="Repository-relative artifact docs root, inheriting component content roots when omitted.",
    )
    assets_root: RepoRelativePath | None = Field(
        default=None,
        description="Repository-relative artifact asset root, inheriting component content roots when omitted.",
    )
    versioning: ArtifactVersioningConfig = Field(
        default_factory=ArtifactVersioningConfig,
        description="Static development, maintenance, tag, and named-ref stream definitions; materialized inventories require no tag-discovery pattern.",
    )
    lifecycle: ArtifactSupportPolicy | None = Field(
        default=None,
        description="Reusable static artifact support defaults; release decisions belong in the snapshot.",
    )


class ComponentMetadataDocumentV1(SitePipelineBaseModel):
    """Component-owned metadata from ``site/component.yaml``."""

    contract_documentation: ClassVar[ContractDocumentation] = ContractDocumentation(
        category="authored",
        ownership="component-owned",
        summary="Stable component identity, repository content roots, and shared lifecycle hints.",
        file_path="site/component.yaml",
        reference=ReferenceDocumentation(
            summary=ReferenceMarkdown(
                "Canonical component metadata that defines stable identity, repository content roots, and optional lifecycle defaults shared across a component repository."
            ),
            sections=(
                ReferenceSection(
                    title="Content roots",
                    body=ReferenceMarkdown(
                        "Use `pagesRoot` for unversioned component pages and `docsRoot` for versioned or development docs content."
                    ),
                ),
            ),
        ),
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="component-v1.schema.json",
        title="Site Pipeline Component Metadata v1",
        examples=(
            SchemaExample(
                summary="Component metadata with identity, content roots, and lifecycle hints.",
                value_builder=component_metadata_example_document,
                render_format="yaml",
            ),
        ),
    )

    schema_version: Literal[1] = Field(
        description="Schema version for the component metadata file."
    )
    component: ComponentIdentity = Field(
        description="Stable identity for the component repository."
    )
    content: ContentRoots | None = Field(
        default=None,
        description="Repository-relative authored content roots owned by this component.",
    )
    lifecycle: ComponentLifecycleHints | None = Field(
        default=None,
        description="Optional high-level lifecycle hints shared across the component repository.",
    )

    artifacts: list[ComponentArtifactDefinition] | None = Field(
        default=None,
        description="Component-owned artifact identities, streams, content roots, and support defaults.",
    )

    @model_validator(mode="after")
    def ensure_artifact_keys_are_unique(self) -> Self:
        keys = [artifact.key for artifact in self.artifacts or ()]
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate component artifact key")
        return self
