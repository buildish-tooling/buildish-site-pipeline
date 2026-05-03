---
title: "Pipeline file contract index"
description: "Generated contract-file tables for authored, provider, and emitted Site Pipeline schemas."
---

<!--
Copyright 2026 The Apache Software Foundation

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

This page groups the published JSON Schemas by authored/provider/emitted file contract.

Back to the [reference overview](../pipeline-model-schema-reference/).

## File contract groups

### Authored input contracts

Consumer-owned and component-owned source-tree contracts that the pipeline reads.

| Contract file | Root type(s) | Schema file | Summary |
| --- | --- | --- | --- |
| `site/component.yaml` | [ComponentMetadataDocumentV1](../pipeline-authored-input-reference/#componentmetadatadocumentv1) | [`site-pipeline-component-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-component-v1.schema.json) | Stable component identity, repository content roots, and shared lifecycle hints. |
| `site/catalog.yaml` | [SiteCatalogDocumentV1](../pipeline-authored-input-reference/#sitecatalogdocumentv1) | [`site-pipeline-catalog-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-catalog-v1.schema.json) | Catalog of components, defaults, sources, origins, and publication rules for one site. |

### Provider input contracts

Provider-derived snapshot contracts that the pipeline reads.

| Contract file | Root type(s) | Schema file | Summary |
| --- | --- | --- | --- |
| `site/provider-snapshot.json` | [ProviderSnapshotDocumentV1](../pipeline-provider-input-reference/#providersnapshotdocumentv1) | [`site-pipeline-provider-snapshot-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-provider-snapshot-v1.schema.json) | Normalized provider inventory of releases, candidates, refs, and downloadable assets. |

### Pipeline-emitted file contracts

Stable files that the pipeline writes into staged or published output trees.

| Contract file | Root type(s) | Schema file | Summary |
| --- | --- | --- | --- |
| `data/_pipeline/aggregate-dependencies.json` | [AggregateDependencyMapV1](../pipeline-incremental-bookkeeping-reference/#aggregatedependencymapv1) | [`site-pipeline-aggregate-dependencies-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-aggregate-dependencies-v1.schema.json) | Coordinator aggregate files and the units that can invalidate them. |
| `data/_pipeline/output-ownership.json` | [OutputOwnershipMapV1](../pipeline-incremental-bookkeeping-reference/#outputownershipmapv1) | [`site-pipeline-output-ownership-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-output-ownership-v1.schema.json) | Ownership map for staged files and directories retained across rebuilds. |
| `data/_pipeline/unit-contributions.json` | [PersistedUnitContributionsV1](../pipeline-incremental-bookkeeping-reference/#persistedunitcontributionsv1) | [`site-pipeline-unit-contributions-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-unit-contributions-v1.schema.json) | Per-unit page contribution manifests retained in the visible stage. |
| `data/artifacts.json` | [ArtifactsDataEntry](../pipeline-staged-aggregate-metadata-reference/#artifactsdataentry) | [`site-pipeline-artifacts-data-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-artifacts-data-v1.schema.json) | Published artifact inventory with version discovery rules, lifecycle hints, and latest-version summaries. |
| `data/candidates.json` | [CandidateAggregateEntry](../pipeline-staged-aggregate-metadata-reference/#candidateaggregateentry) | [`site-pipeline-candidates-data-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-candidates-data-v1.schema.json) | Published release-candidate inventory with vote status and downloadable assets. |
| `data/compatibility.json` | [CompatibilityAggregateEntry](../pipeline-staged-aggregate-metadata-reference/#compatibilityaggregateentry) | [`site-pipeline-compatibility-data-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-compatibility-data-v1.schema.json) | Declared compatibility relationships between published identities. |
| `data/components.json` | [ComponentsDataEntry](../pipeline-staged-aggregate-metadata-reference/#componentsdataentry) | [`site-pipeline-components-data-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-components-data-v1.schema.json) | Published component inventory with resolved routes, origins, and artifact summaries. |
| `data/content-index.json` | [ContentIndexEntry](../pipeline-staged-aggregate-metadata-reference/#contentindexentry) | [`site-pipeline-content-index-data-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-content-index-data-v1.schema.json) | Search and navigation index for staged pages with titles, ancestry, and version metadata. |
| `data/diagnostics.json` | [PipelineDiagnosticEntry](../pipeline-planning-and-stage-contract-reference/#pipelinediagnosticentry) | [`site-pipeline-diagnostics-data-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-diagnostics-data-v1.schema.json) | Structured diagnostics emitted during planning, checking, or staging. |
| `data/mounts.json` | [MountAggregateEntry](../pipeline-staged-aggregate-metadata-reference/#mountaggregateentry) | [`site-pipeline-mounts-data-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-mounts-data-v1.schema.json) | Mounted content and asset subtrees published under resolved public paths. |
| `data/providers.json` | [ProvidersDataEntry](../pipeline-staged-aggregate-metadata-reference/#providersdataentry) | [`site-pipeline-providers-data-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-providers-data-v1.schema.json) | Loaded provider inventory with display names, base URLs, and fetch timestamps. |
| `data/redirects.json` | [RedirectAggregateEntry](../pipeline-staged-aggregate-metadata-reference/#redirectaggregateentry) | [`site-pipeline-redirects-data-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-redirects-data-v1.schema.json) | Flat inventory of published redirects and their resolved destination URLs. |
| `data/refs.json` | [RefAggregateEntry](../pipeline-staged-aggregate-metadata-reference/#refaggregateentry) | [`site-pipeline-refs-data-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-refs-data-v1.schema.json) | Published development, line-head, and named-ref inventory for version navigation. |
| `data/releases.json` | [ReleaseAggregateEntry](../pipeline-staged-aggregate-metadata-reference/#releaseaggregateentry) | [`site-pipeline-releases-data-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-releases-data-v1.schema.json) | Published released-version inventory with lifecycle, support, and asset metadata. |
| `data/routes.json` | [RouteAggregateEntry](../pipeline-staged-aggregate-metadata-reference/#routeaggregateentry) | [`site-pipeline-routes-data-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-routes-data-v1.schema.json) | Flat inventory of published routes with resolved URLs, labels, and ownership metadata. |
| `data/translations.json` | [TranslationSetAggregateEntry](../pipeline-staged-aggregate-metadata-reference/#translationsetaggregateentry) | [`site-pipeline-translations-data-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-translations-data-v1.schema.json) | Translation sibling groups keyed by one shared translation identifier. |
| `manifest.json` | [StageManifestV1](../pipeline-planning-and-stage-contract-reference/#stagemanifestv1) | [`site-pipeline-stage-manifest-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-stage-manifest-v1.schema.json) | Entry point for a stage tree, including roots, formats, and aggregate file locations. |

### Pipeline-emitted non-file root contracts

Schema-root report and namespace types that do not correspond to one stable checked-in file path.

| Root type(s) | Schema file | Summary |
| --- | --- | --- |
| [CheckReportV1](../pipeline-planning-and-stage-contract-reference/#checkreportv1) | [`site-pipeline-check-report-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-check-report-v1.schema.json) | Validation result for one `site-pipeline check` invocation. |
| [PipelineFrontMatterNamespace](../pipeline-staged-front-matter-reference/#pipelinefrontmatternamespace) | [`site-pipeline-front-matter-namespace-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-front-matter-namespace-v1.schema.json) | Reserved front matter namespace containing pipeline-derived component and page metadata. |
| [ResolvedMaterializationReportV1](../pipeline-planning-and-stage-contract-reference/#resolvedmaterializationreportv1) | [`site-pipeline-materialization-report-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-materialization-report-v1.schema.json) | Planning inventory of required local inputs and their current materialization status. |
| [StageRunReportV1](../pipeline-planning-and-stage-contract-reference/#stagerunreportv1) | [`site-pipeline-stage-run-report-v1.schema.json`](/components/site-pipeline/schemas/site-pipeline-stage-run-report-v1.schema.json) | Execution result for one `build` run or completed watch cycle. |

