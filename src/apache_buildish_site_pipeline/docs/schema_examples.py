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

"""Shared generated example builders used by schema export metadata."""

from __future__ import annotations

from apache_buildish_site_pipeline.models.enums import DocumentFormat
from apache_buildish_site_pipeline.models.loading import (
    load_component_metadata_document,
    load_provider_snapshot_document,
    load_site_catalog_document,
)


def catalog_example_document() -> object:
    """Return a realistic authored catalog example used in generated docs."""

    return load_site_catalog_document(
        (
            "schemaVersion: 1\n"
            "defaults:\n"
            "  docsRoot: docs\n"
            "  publication:\n"
            "    origin: docs\n"
            "site: {}\n"
            "origins:\n"
            "  docs:\n"
            "    baseUrl: https://docs.example.org\n"
            "sources:\n"
            "  runtime:\n"
            "    localDir: components/runtime\n"
            "components:\n"
            "  - slug: spark\n"
            "    weight: 100\n"
            "    content:\n"
            "      source: runtime\n"
            "    publication:\n"
            "      mountPath: /spark/\n"
            "    artifacts:\n"
            "      - key: runtime\n"
            "        source: runtime\n"
            "        versioning:\n"
            "          developmentRef: main\n"
            "          tagPattern: ^v.*$\n"
            "        publicationSelection:\n"
            "          development: true\n"
            "          lineHeads:\n"
            "            mode: allAuthored\n"
            "          releases:\n"
            "            mode: latestPerLine\n"
            "        lifecycle:\n"
            "          releaseLines:\n"
            "            - key: '4.0'\n"
            "              maintenanceRef: maintenance/4.0\n"
            "              latest: '4.0.0'\n"
            "          releases:\n"
            "            - version: '4.0.0'\n"
        ),
        document_format=DocumentFormat.YAML,
        source_name="site/catalog.yaml",
    )


def component_metadata_example_document() -> object:
    """Return a realistic component metadata example used in generated docs."""

    return load_component_metadata_document(
        (
            "schemaVersion: 1\n"
            "component:\n"
            "  slug: spark\n"
            "  displayName: Apache Spark\n"
            "content:\n"
            "  pagesRoot: site/pages\n"
            "  docsRoot: docs\n"
            "lifecycle:\n"
            "  latestStable: 4.0.0\n"
            "  supportStatusVocabulary:\n"
            "    active:\n"
            "      displayName: Active\n"
            "      order: 10\n"
        ),
        document_format=DocumentFormat.YAML,
        source_name="site/component.yaml",
    )


def provider_snapshot_example_document() -> object:
    """Return a realistic provider snapshot example used in generated docs."""

    return load_provider_snapshot_document(
        (
            '{"schemaVersion":1,'
            '"providers":[{"key":"github-releases","type":"github","displayName":"GitHub Releases","baseUrl":"https://github.com/apache/spark","fetchedAt":"2026-04-03T18:00:00Z"}],'
            '"records":[{"provider":"github-releases","kind":"released","componentSlug":"spark","artifactKey":"runtime","externalId":"spark-4.0.0","version":"4.0.0","externalUrl":"https://github.com/apache/spark/releases/tag/v4.0.0","publishedAt":"2026-04-03T18:00:00Z","assets":[{"name":"spark-4.0.0-src.tgz","url":"https://downloads.apache.org/spark/spark-4.0.0-src.tgz","checksums":{"sha256":"abc123"}}]}]}'
        ),
        document_format=DocumentFormat.JSON,
        source_name="providers.json",
    )


def materialization_report_example_document() -> object:
    """Return a representative planning report example used in generated docs."""

    from apache_buildish_site_pipeline.models.emitted.planning_stage_contract import (
        ResolvedMaterializationReportV1,
    )

    return ResolvedMaterializationReportV1.model_validate(
        {
            "schemaVersion": 1,
            "generatedAt": "2026-04-06T08:30:00Z",
            "target": "build",
            "entries": [
                {
                    "sourceKey": "apache-spark",
                    "inputKind": "released",
                    "componentSlug": "spark",
                    "artifactKey": "runtime",
                    "version": "4.0.0",
                    "tag": "v4.0.0",
                    "expectedLocalPath": ".buildish/materialized/apache-spark/v4.0.0",
                    "status": "present",
                    "watchEligible": False,
                    "reason": "Release docs are staged from the release tag checkout.",
                }
            ],
            "diagnostics": [],
        }
    )


def check_report_example_document() -> object:
    """Return a representative validation report example used in generated docs."""

    from apache_buildish_site_pipeline.models.emitted.planning_stage_contract import (
        CheckReportV1,
    )

    return CheckReportV1.model_validate(
        {
            "schemaVersion": 1,
            "generatedAt": "2026-04-06T08:35:00Z",
            "command": "check",
            "summary": {
                "status": "warnings",
                "passed": True,
                "failOnSeverity": "error",
                "errorCount": 0,
                "warningCount": 1,
                "infoCount": 0,
            },
            "diagnostics": [
                {
                    "severity": "warning",
                    "code": "catalog.redirectReasonMissing",
                    "message": "Redirect /spark/docs/current/ has no reader-facing reason.",
                    "componentSlug": "spark",
                    "targetId": "/spark/docs/current/",
                }
            ],
        }
    )


def stage_run_report_example_document() -> object:
    """Return a representative stage run report example used in generated docs."""

    from apache_buildish_site_pipeline.models.emitted.planning_stage_contract import (
        StageRunReportV1,
    )

    return StageRunReportV1.model_validate(
        {
            "schemaVersion": 1,
            "generatedAt": "2026-04-06T08:40:00Z",
            "command": "build",
            "summary": {
                "status": "clean",
                "succeeded": True,
                "wroteStage": True,
                "stageUsable": True,
                "errorCount": 0,
                "warningCount": 0,
                "infoCount": 2,
            },
            "stageRootPath": ".buildish/stage/current",
            "manifestPath": ".buildish/stage/current/manifest.json",
            "diagnostics": [],
        }
    )


def stage_manifest_example_document() -> object:
    """Return a representative stage manifest example used in generated docs."""

    from apache_buildish_site_pipeline.models.emitted.planning_stage_contract import (
        StageManifestV1,
    )

    return StageManifestV1.model_validate(
        {
            "schemaVersion": 1,
            "stageLayoutVersion": 1,
            "generatedAt": "2026-04-06T08:40:00Z",
            "command": "build",
            "frontMatterFormat": "yaml",
            "aggregateFormat": "json",
            "roots": {"content": "content", "static": "static", "data": "data"},
            "dataFiles": {
                "components": "data/components.json",
                "artifacts": "data/artifacts.json",
                "routes": "data/routes.json",
                "redirects": "data/redirects.json",
                "releases": "data/releases.json",
                "refs": "data/refs.json",
                "contentIndex": "data/content-index.json",
            },
        }
    )


def front_matter_namespace_example_document() -> object:
    """Return a representative staged front matter example used in generated docs."""

    from apache_buildish_site_pipeline.models.emitted.staged_front_matter import (
        PipelineFrontMatterNamespace,
    )

    return PipelineFrontMatterNamespace.model_validate(
        {
            "component": {
                "slug": "spark",
                "displayName": "Apache Spark",
                "latestStable": "4.0.0",
                "publication": {
                    "origin": {
                        "key": "archive",
                        "baseUrl": "https://archive.apache.org/dist/spark",
                        "hostname": "archive.apache.org",
                    },
                    "paths": {
                        "component": "/spark/",
                        "development": "/spark/main/",
                        "docs": "/spark/docs/",
                        "assets": "/spark/assets/",
                    },
                    "urls": {
                        "component": "https://archive.apache.org/dist/spark/",
                        "development": "https://archive.apache.org/dist/spark/main/",
                        "docs": "https://archive.apache.org/dist/spark/docs/",
                        "assets": "https://archive.apache.org/dist/spark/assets/",
                    },
                },
            },
            "page": {
                "kind": "docsPage",
                "section": "documentation",
                "artifactKey": "runtime",
                "path": "/spark/4.0.0/docs/getting-started/",
                "url": "https://archive.apache.org/dist/spark/4.0.0/docs/getting-started/",
                "componentPath": "/spark/",
                "componentUrl": "https://archive.apache.org/dist/spark/",
                "version": {"kind": "released", "label": "4.0.0", "tag": "v4.0.0"},
            },
        }
    )


def unit_contributions_example_document() -> object:
    """Return a representative unit contribution map example used in generated docs."""

    from apache_buildish_site_pipeline.staging.incremental_metadata import (
        PersistedUnitContributionsV1,
    )

    return PersistedUnitContributionsV1.model_validate(
        {
            "schemaVersion": 1,
            "units": [
                {
                    "unitId": "component:spark:runtime",
                    "pages": [
                        {
                            "stageRelativePath": "content/spark/4.0.0/docs/getting-started/index.md",
                            "componentSlug": "spark",
                            "artifactKey": "runtime",
                            "section": "documentation",
                            "pageKind": "docsPage",
                            "publicPath": "/spark/4.0.0/docs/getting-started/",
                            "componentPath": "/spark/",
                            "originKey": "archive",
                            "versionKind": "released",
                            "version": "4.0.0",
                            "title": "Getting Started",
                            "sourcePath": "docs/runtime/getting-started.md",
                        }
                    ],
                }
            ],
        }
    )


def output_ownership_example_document() -> object:
    """Return a representative output ownership example used in generated docs."""

    from apache_buildish_site_pipeline.staging.incremental_metadata import (
        OutputOwnershipMapV1,
    )

    return OutputOwnershipMapV1.model_validate(
        {
            "schemaVersion": 1,
            "claims": [
                {
                    "ownerId": "artifact:spark/runtime",
                    "unitId": "component:spark:runtime",
                    "pathKind": "directory",
                    "stageRelativePath": "content/spark/4.0.0",
                },
                {
                    "ownerId": "coordinator",
                    "pathKind": "file",
                    "stageRelativePath": "data/components.json",
                },
            ],
        }
    )


def aggregate_dependencies_example_document() -> object:
    """Return a representative aggregate dependency example used in generated docs."""

    from apache_buildish_site_pipeline.staging.incremental_metadata import (
        AggregateDependencyMapV1,
    )

    return AggregateDependencyMapV1.model_validate(
        {
            "schemaVersion": 1,
            "entries": [
                {
                    "stageRelativePath": "data/components.json",
                    "dependentUnitIds": ["component:spark:runtime", "component:spark:site"],
                }
            ],
        }
    )
