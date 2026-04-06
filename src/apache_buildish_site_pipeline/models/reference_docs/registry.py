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

"""Typed registries used by generated reference documentation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelSectionDefinition:
    """Grouping rule for one generated model-reference section."""

    title: str
    description: str
    module_prefixes: tuple[str, ...]

    def matches(self, module_name: str) -> bool:
        return any(module_name.startswith(prefix) for prefix in self.module_prefixes)


@dataclass(frozen=True, slots=True)
class ScalarReferenceEntry:
    """Reference-doc description for one exported scalar alias."""

    name: str
    base_type: str
    description: str


MODEL_SECTION_DEFINITIONS = (
    ModelSectionDefinition(
        title="Authored input types",
        description="Consumer-owned and component-owned authored contract models.",
        module_prefixes=("apache_buildish_site_pipeline.models.authored.",),
    ),
    ModelSectionDefinition(
        title="Provider input types",
        description="Normalized provider snapshot contracts consumed by the pipeline.",
        module_prefixes=("apache_buildish_site_pipeline.models.provider.",),
    ),
    ModelSectionDefinition(
        title="Planning and stage-contract types",
        description="Pipeline-emitted planning, diagnostics, and stage-manifest contracts.",
        module_prefixes=("apache_buildish_site_pipeline.models.emitted.planning_stage_contract",),
    ),
    ModelSectionDefinition(
        title="Staged front matter types",
        description="Front matter and page-level metadata emitted into staged content.",
        module_prefixes=("apache_buildish_site_pipeline.models.emitted.staged_front_matter",),
    ),
    ModelSectionDefinition(
        title="Staged aggregate metadata types",
        description="Public aggregate JSON contracts emitted under `data/`.",
        module_prefixes=("apache_buildish_site_pipeline.models.emitted.aggregates",),
    ),
    ModelSectionDefinition(
        title="Incremental bookkeeping types",
        description="Pipeline-internal emitted bookkeeping contracts stored under `data/_pipeline/`.",
        module_prefixes=(
            "apache_buildish_site_pipeline.staging.incremental_metadata",
            "apache_buildish_site_pipeline.staging.worker_protocol",
        ),
    ),
)


SCALAR_REFERENCE_ENTRIES = (
    ScalarReferenceEntry("NonEmptyString", "String", "Non-empty free-form string."),
    ScalarReferenceEntry("NonNegativeInteger", "Integer", "Integer value greater than or equal to zero."),
    ScalarReferenceEntry("PositiveInteger", "Integer", "Integer value greater than zero."),
    ScalarReferenceEntry("Identifier", "String", "Non-empty symbolic key."),
    ScalarReferenceEntry("Slug", "String", "Stable component identifier."),
    ScalarReferenceEntry("ArtifactKey", "String", "Stable artifact identifier unique within a component."),
    ScalarReferenceEntry("OriginKey", "Identifier", "Key for a publication origin."),
    ScalarReferenceEntry("SourceKey", "String", "Key for a source or repository entry."),
    ScalarReferenceEntry("ProviderKey", "String", "Key for a provider descriptor."),
    ScalarReferenceEntry("VersionString", "String", "Exact version string such as `4.0.0`."),
    ScalarReferenceEntry("RefString", "String", "Moving ref name such as `main` or `releases/4.x`."),
    ScalarReferenceEntry(
        "ReferenceString",
        "String",
        "Typed internal reference string such as `route:/docs/latest/` or `artifact:spark/runtime`.",
    ),
    ScalarReferenceEntry("RegexString", "String", "Regex pattern stored as text."),
    ScalarReferenceEntry("SchemaVersion", "Integer", "Positive schema version integer."),
    ScalarReferenceEntry("TimestampString", "Datetime", "RFC 3339 / ISO 8601 timestamp value."),
    ScalarReferenceEntry(
        "LocalPathString",
        "String",
        "Consumer-local filesystem path that follows host operating-system path rules.",
    ),
    ScalarReferenceEntry(
        "RepoRelativePath",
        "String",
        "Repository-relative normalized POSIX path that must use forward slashes.",
    ),
    ScalarReferenceEntry(
        "StageRelativePath",
        "String",
        "Stage-root-relative normalized POSIX path that must use forward slashes.",
    ),
    ScalarReferenceEntry("MountSourceRef", "String", "Stable mount source reference such as a path or bundle key."),
    ScalarReferenceEntry("PublicPath", "String", "Resolved normalized POSIX public path such as `/docs/latest/`."),
    ScalarReferenceEntry("HostnameString", "String", "Hostname derived from an origin URL."),
    ScalarReferenceEntry("UrlString", "String", "Absolute public URL."),
    ScalarReferenceEntry("ProviderBaseUrl", "String", "Validated public provider base URL."),
    ScalarReferenceEntry(
        "ExtensionsObject",
        "Object",
        "Opaque structured metadata allowed only in explicitly documented extension slots.",
    ),
)