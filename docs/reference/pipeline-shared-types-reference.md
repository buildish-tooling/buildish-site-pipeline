---
title: "Pipeline shared types reference"
description: "Generated scalar alias and enum reference for Site Pipeline contracts."
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

This page defines the shared scalar aliases and enums that appear across the generated contract pages.

Back to the [reference overview](../pipeline-model-schema-reference/).

## Scalar aliases

| Type | Base type | Description |
| --- | --- | --- |
| <a id="nonemptystring"></a>`NonEmptyString` | `String` | Non-empty free-form string. |
| <a id="nonnegativeinteger"></a>`NonNegativeInteger` | `Integer` | Integer value greater than or equal to zero. |
| <a id="positiveinteger"></a>`PositiveInteger` | `Integer` | Integer value greater than zero. |
| <a id="identifier"></a>`Identifier` | `String` | Non-empty symbolic key. |
| <a id="slug"></a>`Slug` | `String` | Stable component identifier. |
| <a id="artifactkey"></a>`ArtifactKey` | `String` | Stable artifact identifier unique within a component. |
| <a id="originkey"></a>`OriginKey` | `Identifier` | Key for a publication origin. |
| <a id="sourcekey"></a>`SourceKey` | `String` | Key for a source or repository entry. |
| <a id="providerkey"></a>`ProviderKey` | `String` | Key for a provider descriptor. |
| <a id="versionstring"></a>`VersionString` | `String` | Exact version string such as `4.0.0`. |
| <a id="refstring"></a>`RefString` | `String` | Moving ref name such as `main` or `releases/4.x`. |
| <a id="referencestring"></a>`ReferenceString` | `String` | Typed internal reference string such as `route:/docs/development/` or `artifact:spark/runtime`. |
| <a id="regexstring"></a>`RegexString` | `String` | Regex pattern stored as text. |
| <a id="schemaversion"></a>`SchemaVersion` | `Integer` | Positive schema version integer. |
| <a id="timestampstring"></a>`TimestampString` | `Datetime` | RFC 3339 / ISO 8601 timestamp value. |
| <a id="localpathstring"></a>`LocalPathString` | `String` | Consumer-local filesystem path that follows host operating-system path rules. |
| <a id="reporelativepath"></a>`RepoRelativePath` | `String` | Repository-relative normalized POSIX path that must use forward slashes. |
| <a id="stagerelativepath"></a>`StageRelativePath` | `String` | Stage-root-relative normalized POSIX path that must use forward slashes. |
| <a id="mountsourceref"></a>`MountSourceRef` | `String` | Stable mount source reference such as a path or bundle key. |
| <a id="publicpath"></a>`PublicPath` | `String` | Resolved normalized POSIX public path such as `/docs/development/`. |
| <a id="hostnamestring"></a>`HostnameString` | `String` | Hostname derived from an origin URL. |
| <a id="urlstring"></a>`UrlString` | `String` | Absolute public URL. |
| <a id="providerbaseurl"></a>`ProviderBaseUrl` | `String` | Validated public provider base URL. |
| <a id="extensionsobject"></a>`ExtensionsObject` | `Object` | Opaque structured metadata allowed only in explicitly documented extension slots. |


## Shared enums

| Type | Values | Description |
| --- | --- | --- |
| <a id="candidateselectionmode"></a>`CandidateSelectionMode` | `none`, `latest`, `explicit` | Strategy used to select a candidate version. |
| <a id="checkfailurethreshold"></a>`CheckFailureThreshold` | `error`, `warning` | Lowest severity that causes ``check`` to fail. |
| <a id="diagnosticseverity"></a>`DiagnosticSeverity` | `info`, `warning`, `error` | Severity level for pipeline diagnostics. |
| <a id="indexbehavior"></a>`IndexBehavior` | `full`, `metadataOnly`, `none` | Renderer hint for version/ref index visibility. |
| <a id="lineheadselectionmode"></a>`LineHeadSelectionMode` | `none`, `allAuthored`, `explicit` | Strategy used to derive a release-line head record. |
| <a id="linkcheckmode"></a>`LinkCheckMode` | `directory`, `file-html` | Supported staged public-path resolution strategies for internal page links. |
| <a id="materializationinputkind"></a>`MaterializationInputKind` | `sitePages`, `siteAssets`, `vendorAssets`, `development`, `namedRef`, `lineHead`, `candidate`, `released` | Planning/build/watch local-input category. |
| <a id="materializationstatus"></a>`MaterializationStatus` | `present`, `missing`, `stale`, `unresolved` | Readiness state of a required local input. |
| <a id="planningtarget"></a>`PlanningTarget` | `build`, `watch` | Planning intent for later staging behavior. |
| <a id="publicationstate"></a>`PublicationState` | `published`, `hidden`, `withdrawn`, `tombstoned` | Observed provider-side publication state. |
| <a id="recordkind"></a>`RecordKind` | `development`, `released`, `candidate`, `namedRef`, `lineHead` | Normalized provider record lifecycle kind. |
| <a id="releaseselectionmode"></a>`ReleaseSelectionMode` | `latestPerLine`, `latestN`, `allKnown`, `explicit` | Strategy used to select a released version. |
| <a id="routemode"></a>`RouteMode` | `none`, `prefixAll` | Locale routing strategy for a published route set. |
| <a id="runstatus"></a>`RunStatus` | `clean`, `warnings`, `errors` | Overall diagnostic class for a run or cycle. |
| <a id="stagecommand"></a>`StageCommand` | `build`, `watch` | Stable stage-producing command modes. |
| <a id="trustclass"></a>`TrustClass` | `passive`, `active` | Trust posture of a mounted content subtree. |
| <a id="withdrawalbehavior"></a>`WithdrawalBehavior` | `notice`, `redirect`, `omit` | Author-directed behavior for a withdrawn release. |


