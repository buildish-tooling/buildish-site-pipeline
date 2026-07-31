---
title: "Pipeline file contract index"
description: "Generated contract-file tables for authored, provider, and emitted Site Pipeline schemas."
---

<!--
Copyright 2026 The Buildish Authors

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
| `site/component.yaml` | [ComponentMetadataDocumentV1](../pipeline-authored-input-reference/#componentmetadatadocumentv1) | [`component-v1.schema.json`](/components/site-pipeline/schemas/component-v1.schema.json) | Stable component identity, repository content roots, and shared lifecycle hints. |
| `site/catalog.yaml` | [SiteCatalogDocumentV1](../pipeline-authored-input-reference/#sitecatalogdocumentv1) | [`catalog-v1.schema.json`](/components/site-pipeline/schemas/catalog-v1.schema.json) | Catalog of components, defaults, sources, origins, and publication rules for one site. |

### Provider input contracts

Provider-derived snapshot contracts that the pipeline reads.

| Contract file | Root type(s) | Schema file | Summary |
| --- | --- | --- | --- |
| `site/provider-snapshot.json` | [ProviderSnapshotDocumentV1](../pipeline-provider-input-reference/#providersnapshotdocumentv1) | [`provider-snapshot-v1.schema.json`](/components/site-pipeline/schemas/provider-snapshot-v1.schema.json) | Normalized provider inventory of releases, candidates, refs, and downloadable assets. |

### Pipeline-emitted file contracts

Stable files that the pipeline writes into staged or published output trees.

| Contract file | Root type(s) | Schema file | Summary |
| --- | --- | --- | --- |
| `data/_pipeline/aggregate-dependencies.json` | [AggregateDependencyMapV1](../pipeline-incremental-bookkeeping-reference/#aggregatedependencymapv1) | [`aggregate-dependencies-v1.schema.json`](/components/site-pipeline/schemas/aggregate-dependencies-v1.schema.json) | Coordinator aggregate files and the units that can invalidate them. |
| `data/_pipeline/output-ownership.json` | [OutputOwnershipMapV1](../pipeline-incremental-bookkeeping-reference/#outputownershipmapv1) | [`output-ownership-v1.schema.json`](/components/site-pipeline/schemas/output-ownership-v1.schema.json) | Ownership map for staged files and directories retained across rebuilds. |
| `data/_pipeline/unit-contributions.json` | [PersistedUnitContributionsV1](../pipeline-incremental-bookkeeping-reference/#persistedunitcontributionsv1) | [`unit-contributions-v1.schema.json`](/components/site-pipeline/schemas/unit-contributions-v1.schema.json) | Per-unit page contribution manifests retained in the visible stage. |
| `data/artifacts.json` | [ArtifactsDataEntry](../pipeline-staged-aggregate-metadata-reference/#artifactsdataentry) | [`artifacts-data-v1.schema.json`](/components/site-pipeline/schemas/artifacts-data-v1.schema.json) | Published artifact inventory with version discovery rules, lifecycle hints, and latest-version summaries. |
| `data/candidates.json` | [CandidateAggregateEntry](../pipeline-staged-aggregate-metadata-reference/#candidateaggregateentry) | [`candidates-data-v1.schema.json`](/components/site-pipeline/schemas/candidates-data-v1.schema.json) | Published release-candidate inventory with vote status and downloadable assets. |
| `data/compatibility.json` | [CompatibilityAggregateEntry](../pipeline-staged-aggregate-metadata-reference/#compatibilityaggregateentry) | [`compatibility-data-v1.schema.json`](/components/site-pipeline/schemas/compatibility-data-v1.schema.json) | Declared compatibility relationships between published identities. |
| `data/components.json` | [ComponentsDataEntry](../pipeline-staged-aggregate-metadata-reference/#componentsdataentry) | [`components-data-v1.schema.json`](/components/site-pipeline/schemas/components-data-v1.schema.json) | Published component inventory with resolved routes, origins, and artifact summaries. |
| `data/content-index.json` | [ContentIndexEntry](../pipeline-staged-aggregate-metadata-reference/#contentindexentry) | [`content-index-data-v1.schema.json`](/components/site-pipeline/schemas/content-index-data-v1.schema.json) | Search and navigation index for staged pages with titles, ancestry, and version metadata. |
| `data/diagnostics.json` | [PipelineDiagnosticEntry](../pipeline-planning-and-stage-contract-reference/#pipelinediagnosticentry) | [`diagnostics-data-v1.schema.json`](/components/site-pipeline/schemas/diagnostics-data-v1.schema.json) | Structured diagnostics emitted during planning, checking, or staging. |
| `data/mounts.json` | [MountAggregateEntry](../pipeline-staged-aggregate-metadata-reference/#mountaggregateentry) | [`mounts-data-v1.schema.json`](/components/site-pipeline/schemas/mounts-data-v1.schema.json) | Mounted content and asset subtrees published under resolved public paths. |
| `data/providers.json` | [ProvidersDataEntry](../pipeline-staged-aggregate-metadata-reference/#providersdataentry) | [`providers-data-v1.schema.json`](/components/site-pipeline/schemas/providers-data-v1.schema.json) | Loaded provider inventory with display names, base URLs, and fetch timestamps. |
| `data/redirects.json` | [RedirectAggregateEntry](../pipeline-staged-aggregate-metadata-reference/#redirectaggregateentry) | [`redirects-data-v1.schema.json`](/components/site-pipeline/schemas/redirects-data-v1.schema.json) | Flat inventory of published redirects and their resolved destination URLs. |
| `data/refs.json` | [RefAggregateEntry](../pipeline-staged-aggregate-metadata-reference/#refaggregateentry) | [`refs-data-v1.schema.json`](/components/site-pipeline/schemas/refs-data-v1.schema.json) | Published development, line-head, and named-ref inventory for version navigation. |
| `data/releases.json` | [ReleaseAggregateEntry](../pipeline-staged-aggregate-metadata-reference/#releaseaggregateentry) | [`releases-data-v1.schema.json`](/components/site-pipeline/schemas/releases-data-v1.schema.json) | Published released-version inventory with lifecycle, support, and asset metadata. |
| `data/routes.json` | [RouteAggregateEntry](../pipeline-staged-aggregate-metadata-reference/#routeaggregateentry) | [`routes-data-v1.schema.json`](/components/site-pipeline/schemas/routes-data-v1.schema.json) | Flat inventory of published routes with resolved URLs, labels, and ownership metadata. |
| `data/translations.json` | [TranslationSetAggregateEntry](../pipeline-staged-aggregate-metadata-reference/#translationsetaggregateentry) | [`translations-data-v1.schema.json`](/components/site-pipeline/schemas/translations-data-v1.schema.json) | Translation sibling groups keyed by one shared translation identifier. |
| `manifest.json` | [StageManifestV1](../pipeline-planning-and-stage-contract-reference/#stagemanifestv1) | [`stage-manifest-v1.schema.json`](/components/site-pipeline/schemas/stage-manifest-v1.schema.json) | Entry point for a stage tree, including roots, formats, and aggregate file locations. |

### Pipeline-emitted non-file root contracts

Schema-root report and namespace types that do not correspond to one stable checked-in file path.

| Root type(s) | Schema file | Summary |
| --- | --- | --- |
| [CliFailureReportV1](../pipeline-planning-and-stage-contract-reference/#clifailurereportv1) | [`cli-failure-report-v1.schema.json`](/components/site-pipeline/schemas/cli-failure-report-v1.schema.json) | Versioned CLI failure envelope emitted in place of a requested JSON command report. |
| [CheckReportV1](../pipeline-planning-and-stage-contract-reference/#checkreportv1) | [`check-report-v1.schema.json`](/components/site-pipeline/schemas/check-report-v1.schema.json) | Validation result for one `site-pipeline check` invocation. |
| [PipelineFrontMatterNamespace](../pipeline-staged-front-matter-reference/#pipelinefrontmatternamespace) | [`front-matter-namespace-v1.schema.json`](/components/site-pipeline/schemas/front-matter-namespace-v1.schema.json) | Reserved front matter namespace containing pipeline-derived component and page metadata. |
| [ResolvedMaterializationReportV1](../pipeline-planning-and-stage-contract-reference/#resolvedmaterializationreportv1) | [`materialization-report-v1.schema.json`](/components/site-pipeline/schemas/materialization-report-v1.schema.json) | Planning inventory of required local inputs and their current materialization status. |
| [StageRunReportV1](../pipeline-planning-and-stage-contract-reference/#stagerunreportv1) | [`stage-run-report-v1.schema.json`](/components/site-pipeline/schemas/stage-run-report-v1.schema.json) | Execution result for one `build` run or completed watch cycle. |

