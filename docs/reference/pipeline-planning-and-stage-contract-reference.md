---
title: "Planning and stage-contract types"
description: "Pipeline-emitted planning, diagnostics, and stage-manifest contracts."
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

Pipeline-emitted planning, diagnostics, and stage-manifest contracts.

Back to the [reference overview](../pipeline-model-schema-reference/).

## Type index

- [CheckReportV1](#checkreportv1) — Machine-readable result of ``site-pipeline check``.
- [CheckSummary](#checksummary) — Outcome counts and pass/fail decision for one `check` run.
- [PipelineDiagnosticEntry](#pipelinediagnosticentry) — Structured diagnostic emitted during planning, checking, or staging.
- [ReducedDiagnosticDetailsSummary](#reduceddiagnosticdetailssummary) — Compact placeholder used when full diagnostic details were too large to keep.
- [ResolvedMaterializationEntry](#resolvedmaterializationentry) — One local checkout or fetched input that the planner expects to exist.
- [ResolvedMaterializationReportV1](#resolvedmaterializationreportv1) — Machine-readable planning report for required local inputs.
- [StageDataFiles](#stagedatafiles) — Stage-relative paths of aggregate metadata files currently present in one stage tree.
- [StageManifestV1](#stagemanifestv1) — Authoritative entry-point document for a staged output tree.
- [StageRoots](#stageroots) — Named top-level directories inside a stage tree.
- [StageRunReportV1](#stagerunreportv1) — Machine-readable result of ``build`` or one completed watch cycle.
- [StageRunSummary](#stagerunsummary) — Outcome counts and usability flags for one stage-producing run or watch cycle.

<a id="checkreportv1"></a>
### CheckReportV1

Machine-readable result of `site-pipeline check`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="checkreportv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | Schema version for the check report. |
| <a id="checkreportv1-generatedat"></a>`generatedAt` | [TimestampString](../pipeline-shared-types-reference/#timestampstring) | yes | Timestamp when the check report was generated. |
| <a id="checkreportv1-command"></a>`command` | Literal['check'] | yes | Command name that produced this report; always `check` for this contract. |
| <a id="checkreportv1-summary"></a>`summary` | [CheckSummary](#checksummary) | yes | Outcome summary with pass/fail state and diagnostic counts for the run. |
| <a id="checkreportv1-diagnostics"></a>`diagnostics` | list[[PipelineDiagnosticEntry](#pipelinediagnosticentry)] | yes | Structured diagnostics emitted during the check run. |

#### Example: Validation report with one warning that does not fail the run.

```json
{
  "schemaVersion": 1,
  "generatedAt": "2026-04-06T08:35:00Z",
  "command": "check",
  "summary": {
    "status": "warnings",
    "passed": true,
    "failOnSeverity": "error",
    "errorCount": 0,
    "warningCount": 1,
    "infoCount": 0
  },
  "diagnostics": [
    {
      "severity": "warning",
      "code": "catalog.redirectReasonMissing",
      "message": "Redirect /spark/docs/current/ has no reader-facing reason.",
      "componentSlug": "spark",
      "targetId": "/spark/docs/current/"
    }
  ]
}
```

<a id="checksummary"></a>
### CheckSummary

Outcome counts and pass/fail decision for one `check` run.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="checksummary-status"></a>`status` | [RunStatus](../pipeline-shared-types-reference/#runstatus) | yes | Overall diagnostic status for the run after counts were evaluated. |
| <a id="checksummary-passed"></a>`passed` | bool | yes | Whether the check run satisfied the configured failure threshold and should be treated as passing. |
| <a id="checksummary-failonseverity"></a>`failOnSeverity` | [CheckFailureThreshold](../pipeline-shared-types-reference/#checkfailurethreshold) | yes | Configured severity threshold that decides whether warnings already fail the run or only errors do. |
| <a id="checksummary-errorcount"></a>`errorCount` | [NonNegativeInteger](../pipeline-shared-types-reference/#nonnegativeinteger) | yes | Number of error diagnostics emitted during the run. |
| <a id="checksummary-warningcount"></a>`warningCount` | [NonNegativeInteger](../pipeline-shared-types-reference/#nonnegativeinteger) | yes | Number of warning diagnostics emitted during the run. |
| <a id="checksummary-infocount"></a>`infoCount` | [NonNegativeInteger](../pipeline-shared-types-reference/#nonnegativeinteger) | yes | Number of informational diagnostics emitted during the run. |

<a id="pipelinediagnosticentry"></a>
### PipelineDiagnosticEntry

Structured diagnostic emitted during planning, checking, or staging.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="pipelinediagnosticentry-severity"></a>`severity` | [DiagnosticSeverity](../pipeline-shared-types-reference/#diagnosticseverity) | yes | Diagnostic severity level that callers can use for gating and presentation. |
| <a id="pipelinediagnosticentry-code"></a>`code` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Stable machine-readable diagnostic code. |
| <a id="pipelinediagnosticentry-message"></a>`message` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Primary human-readable diagnostic message. |
| <a id="pipelinediagnosticentry-componentslug"></a>`componentSlug` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Component slug associated with the diagnostic when a specific component is directly affected. |
| <a id="pipelinediagnosticentry-artifactkey"></a>`artifactKey` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Artifact key associated with the diagnostic when a specific artifact is directly affected. |
| <a id="pipelinediagnosticentry-targetid"></a>`targetId` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Additional target identifier, such as a path, ref, or release key, that helps callers locate the problem precisely. |
| <a id="pipelinediagnosticentry-details"></a>`details` | [ReducedDiagnosticDetailsSummary](#reduceddiagnosticdetailssummary) \| [ExtensionsObject](../pipeline-shared-types-reference/#extensionsobject) | no | Structured detail payload for the diagnostic, or a bounded summary when the original detail payload was too large. |

#### Selected field examples

- `code`: Example: `"catalog.invalidRedirectTarget"`
- `message`: Example: `"Redirect target route:/spark/missing/ could not be resolved."`
- `componentSlug`: Example: `"spark"`
- `artifactKey`: Example: `"runtime"`
- `targetId`: Example: `"/spark/docs/current/"`

<a id="reduceddiagnosticdetailssummary"></a>
### ReducedDiagnosticDetailsSummary

Compact placeholder used when full diagnostic details were too large to keep.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="reduceddiagnosticdetailssummary-omitted"></a>`omitted` | Literal[True] | yes | Always `true`, signalling that the original diagnostic details were intentionally omitted. |
| <a id="reduceddiagnosticdetailssummary-reason"></a>`reason` | Literal['sizeLimitExceeded'] | yes | Reason why the original diagnostic details were replaced by this bounded summary. |
| <a id="reduceddiagnosticdetailssummary-actualbytes"></a>`actualBytes` | [PositiveInteger](../pipeline-shared-types-reference/#positiveinteger) | yes | Actual serialized size of the original diagnostic details payload in bytes. |
| <a id="reduceddiagnosticdetailssummary-limitbytes"></a>`limitBytes` | [PositiveInteger](../pipeline-shared-types-reference/#positiveinteger) | yes | Configured byte limit that the original diagnostic details exceeded. |
| <a id="reduceddiagnosticdetailssummary-summary"></a>`summary` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Short human-readable summary of the omitted details payload. |
| <a id="reduceddiagnosticdetailssummary-fingerprint"></a>`fingerprint` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Stable fingerprint that lets tooling correlate repeated oversized payloads without storing the full payload. |

#### Selected field examples

- `actualBytes`: Example: `524288`
- `limitBytes`: Example: `65536`

<a id="resolvedmaterializationentry"></a>
### ResolvedMaterializationEntry

One local checkout or fetched input that the planner expects to exist.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="resolvedmaterializationentry-sourcekey"></a>`sourceKey` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Named source binding that produced this materialization requirement. |
| <a id="resolvedmaterializationentry-inputkind"></a>`inputKind` | [MaterializationInputKind](../pipeline-shared-types-reference/#materializationinputkind) | yes | Kind of materialized input, such as a component checkout, artifact checkout, or provider-derived fetch target. |
| <a id="resolvedmaterializationentry-componentslug"></a>`componentSlug` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Component slug for the materialized input when the requirement is tied to a specific component. |
| <a id="resolvedmaterializationentry-artifactkey"></a>`artifactKey` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Artifact key for the materialized input when the requirement is tied to one independently versioned artifact. |
| <a id="resolvedmaterializationentry-releaseline"></a>`releaseLine` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Release-line key when the required local input is scoped to one maintenance line. |
| <a id="resolvedmaterializationentry-version"></a>`version` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Exact version when the required local input is scoped to one released version. |
| <a id="resolvedmaterializationentry-ref"></a>`ref` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Exact source-control ref when the planner resolved this input from a branch or named ref. |
| <a id="resolvedmaterializationentry-tag"></a>`tag` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Exact tag name when the planner resolved this input from a tagged release. |
| <a id="resolvedmaterializationentry-commitsha"></a>`commitSha` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Resolved commit SHA for the required input when one was discovered. |
| <a id="resolvedmaterializationentry-expectedlocalpath"></a>`expectedLocalPath` | [LocalPathString](../pipeline-shared-types-reference/#localpathstring) | yes | Local filesystem path where the planner expects this input to be present or materialized. |
| <a id="resolvedmaterializationentry-status"></a>`status` | [MaterializationStatus](../pipeline-shared-types-reference/#materializationstatus) | yes | Current materialization status, such as already present, missing, or needing refresh. |
| <a id="resolvedmaterializationentry-provenance"></a>`provenance` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Short explanation of how the planner derived this materialization requirement. |
| <a id="resolvedmaterializationentry-watcheligible"></a>`watchEligible` | bool | no | Whether watch mode can safely monitor this input for incremental restaging. |
| <a id="resolvedmaterializationentry-reason"></a>`reason` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable explanation of why this input is required or why its current status matters. |

#### Selected field examples

- `sourceKey`: Example: `"apache-spark"`
- `componentSlug`: Example: `"spark"`
- `artifactKey`: Example: `"runtime"`
- `releaseLine`: Example: `"4.0"`
- `version`: Example: `"4.0.0"`
- `ref`: Example: `"refs/heads/main"`
- `tag`: Example: `"v4.0.0"`
- `commitSha`: Example: `"6f0fd1f7b2c4a6d8e9f00123456789abcdef0123"`
- `expectedLocalPath`: Example: `".buildish/materialized/apache-spark/main"`

<a id="resolvedmaterializationreportv1"></a>
### ResolvedMaterializationReportV1

Machine-readable planning report for required local inputs.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="resolvedmaterializationreportv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | Schema version for the materialization planning report. |
| <a id="resolvedmaterializationreportv1-generatedat"></a>`generatedAt` | [TimestampString](../pipeline-shared-types-reference/#timestampstring) | yes | Timestamp when this planning report was generated. |
| <a id="resolvedmaterializationreportv1-target"></a>`target` | [PlanningTarget](../pipeline-shared-types-reference/#planningtarget) | yes | Planning target that this report was generated for, such as build or watch preparation. |
| <a id="resolvedmaterializationreportv1-entries"></a>`entries` | list[[ResolvedMaterializationEntry](#resolvedmaterializationentry)] | yes | Required local inputs together with their expected locations and current materialization status. |
| <a id="resolvedmaterializationreportv1-diagnostics"></a>`diagnostics` | list[[PipelineDiagnosticEntry](#pipelinediagnosticentry)] | no | Structured diagnostics emitted while resolving required local inputs for this planning target. |

#### Example: Planning report with one required release checkout.

```json
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
      "watchEligible": false,
      "reason": "Release docs are staged from the release tag checkout."
    }
  ],
  "diagnostics": []
}
```

<a id="stagedatafiles"></a>
### StageDataFiles

Stage-relative paths of aggregate metadata files currently present in one stage tree.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stagedatafiles-components"></a>`components` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | yes | Stage-relative path of the published component aggregate file. |
| <a id="stagedatafiles-artifacts"></a>`artifacts` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | yes | Stage-relative path of the published artifact aggregate file. |
| <a id="stagedatafiles-routes"></a>`routes` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | yes | Stage-relative path of the published route aggregate file. |
| <a id="stagedatafiles-redirects"></a>`redirects` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | yes | Stage-relative path of the published redirect aggregate file. |
| <a id="stagedatafiles-releases"></a>`releases` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | no | Stage-relative path of the published release aggregate file when release metadata is present. |
| <a id="stagedatafiles-candidates"></a>`candidates` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | no | Stage-relative path of the published candidate aggregate file when release-candidate metadata is present. |
| <a id="stagedatafiles-refs"></a>`refs` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | no | Stage-relative path of the published ref aggregate file when development, line-head, or named-ref metadata is present. |
| <a id="stagedatafiles-translations"></a>`translations` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | no | Stage-relative path of the published translation aggregate file when localized page groups are present. |
| <a id="stagedatafiles-compatibility"></a>`compatibility` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | no | Stage-relative path of the published compatibility aggregate file when compatibility assertions are present. |
| <a id="stagedatafiles-mounts"></a>`mounts` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | no | Stage-relative path of the published mount aggregate file when mounted subtrees are present. |
| <a id="stagedatafiles-providers"></a>`providers` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | no | Stage-relative path of the provider aggregate file when provider metadata is present in the stage. |
| <a id="stagedatafiles-contentindex"></a>`contentIndex` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | no | Stage-relative path of the content-index aggregate file when the stage includes a generated page index. |
| <a id="stagedatafiles-diagnostics"></a>`diagnostics` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | no | Stage-relative path of the diagnostics aggregate file when diagnostics were published into the stage. |
| <a id="stagedatafiles-unitcontributions"></a>`unitContributions` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | no | Stage-relative path of the persisted unit-contribution manifest file when it is present. |
| <a id="stagedatafiles-outputownership"></a>`outputOwnership` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | no | Stage-relative path of the output-ownership map when incremental rebuild metadata is present. |
| <a id="stagedatafiles-aggregatedependencies"></a>`aggregateDependencies` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | no | Stage-relative path of the aggregate-dependency map when incremental rebuild metadata is present. |

#### Selected field examples

- `components`: Example: `"data/components.json"`
- `artifacts`: Example: `"data/artifacts.json"`
- `routes`: Example: `"data/routes.json"`
- `redirects`: Example: `"data/redirects.json"`
- `releases`: Example: `"data/releases.json"`
- `candidates`: Example: `"data/candidates.json"`
- `refs`: Example: `"data/refs.json"`
- `translations`: Example: `"data/translations.json"`
- `compatibility`: Example: `"data/compatibility.json"`
- `mounts`: Example: `"data/mounts.json"`
- `providers`: Example: `"data/providers.json"`
- `contentIndex`: Example: `"data/content-index.json"`
- `diagnostics`: Example: `"data/diagnostics.json"`
- `unitContributions`: Example: `"data/unit-contributions.json"`
- `outputOwnership`: Example: `"data/output-ownership.json"`
- `aggregateDependencies`: Example: `"data/aggregate-dependencies.json"`

<a id="stagemanifestv1"></a>
### StageManifestV1

Authoritative entry-point document for a staged output tree.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: `manifest.json`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stagemanifestv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | Schema version for the stage manifest. |
| <a id="stagemanifestv1-stagelayoutversion"></a>`stageLayoutVersion` | [SchemaVersion](../pipeline-shared-types-reference/#schemaversion) | yes | Version of the stage directory layout contract that this manifest follows. |
| <a id="stagemanifestv1-generatedat"></a>`generatedAt` | [TimestampString](../pipeline-shared-types-reference/#timestampstring) | yes | Timestamp when the manifest was generated. |
| <a id="stagemanifestv1-command"></a>`command` | [StageCommand](../pipeline-shared-types-reference/#stagecommand) | yes | Stage-producing command that created the stage tree represented by this manifest. |
| <a id="stagemanifestv1-frontmatterformat"></a>`frontMatterFormat` | Literal['yaml'] | yes | Front matter serialization format used for staged content files. |
| <a id="stagemanifestv1-aggregateformat"></a>`aggregateFormat` | Literal['json'] | yes | Serialization format used for aggregate metadata files in the stage data directory. |
| <a id="stagemanifestv1-roots"></a>`roots` | [StageRoots](#stageroots) | yes | Top-level stage directories used for content, static assets, and aggregate data. |
| <a id="stagemanifestv1-datafiles"></a>`dataFiles` | [StageDataFiles](#stagedatafiles) | yes | Stage-relative paths of aggregate metadata files currently present in the stage. |

#### Example: Stage manifest that points at content, static, and aggregate roots.

```json
{
  "schemaVersion": 1,
  "stageLayoutVersion": 1,
  "generatedAt": "2026-04-06T08:40:00Z",
  "command": "build",
  "frontMatterFormat": "yaml",
  "aggregateFormat": "json",
  "roots": {
    "content": "content",
    "static": "static",
    "data": "data"
  },
  "dataFiles": {
    "components": "data/components.json",
    "artifacts": "data/artifacts.json",
    "routes": "data/routes.json",
    "redirects": "data/redirects.json",
    "releases": "data/releases.json",
    "refs": "data/refs.json",
    "contentIndex": "data/content-index.json"
  }
}
```

<a id="stageroots"></a>
### StageRoots

Named top-level directories inside a stage tree.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stageroots-content"></a>`content` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | yes | Stage-relative directory that contains rendered pages and content files. |
| <a id="stageroots-static"></a>`static` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | yes | Stage-relative directory that contains copied static assets. |
| <a id="stageroots-data"></a>`data` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | yes | Stage-relative directory that contains aggregate metadata files. |

#### Selected field examples

- `content`: Example: `"content"`
- `static`: Example: `"static"`
- `data`: Example: `"data"`

<a id="stagerunreportv1"></a>
### StageRunReportV1

Machine-readable result of `build` or one completed watch cycle.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stagerunreportv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | Schema version for the stage run report. |
| <a id="stagerunreportv1-generatedat"></a>`generatedAt` | [TimestampString](../pipeline-shared-types-reference/#timestampstring) | yes | Timestamp when the stage run report was generated. |
| <a id="stagerunreportv1-command"></a>`command` | [StageCommand](../pipeline-shared-types-reference/#stagecommand) | yes | Stage-producing command that produced this report, such as `build` or `watch`. |
| <a id="stagerunreportv1-summary"></a>`summary` | [StageRunSummary](#stagerunsummary) | yes | Outcome summary with success state, stage usability, and diagnostic counts for the run. |
| <a id="stagerunreportv1-stagerootpath"></a>`stageRootPath` | [LocalPathString](../pipeline-shared-types-reference/#localpathstring) | no | Local path to the root of the stage tree, if the run produced one. |
| <a id="stagerunreportv1-manifestpath"></a>`manifestPath` | [LocalPathString](../pipeline-shared-types-reference/#localpathstring) | no | Local path to the generated stage manifest when the stage is usable. |
| <a id="stagerunreportv1-cycle"></a>`cycle` | [NonNegativeInteger](../pipeline-shared-types-reference/#nonnegativeinteger) | no | Completed watch-cycle number for watch reports; omitted for one-shot build reports. |
| <a id="stagerunreportv1-diagnostics"></a>`diagnostics` | list[[PipelineDiagnosticEntry](#pipelinediagnosticentry)] | yes | Structured diagnostics emitted during the stage-producing run. |

#### Selected field examples

- `cycle`: Example: `3`

#### Example: Successful build report with a usable stage manifest.

```json
{
  "schemaVersion": 1,
  "generatedAt": "2026-04-06T08:40:00Z",
  "command": "build",
  "summary": {
    "status": "clean",
    "succeeded": true,
    "wroteStage": true,
    "stageUsable": true,
    "errorCount": 0,
    "warningCount": 0,
    "infoCount": 2
  },
  "stageRootPath": ".buildish/stage/current",
  "manifestPath": ".buildish/stage/current/manifest.json",
  "diagnostics": []
}
```

<a id="stagerunsummary"></a>
### StageRunSummary

Outcome counts and usability flags for one stage-producing run or watch cycle.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stagerunsummary-status"></a>`status` | [RunStatus](../pipeline-shared-types-reference/#runstatus) | yes | Overall diagnostic status for the run after counts were evaluated. |
| <a id="stagerunsummary-succeeded"></a>`succeeded` | bool | yes | Whether the run finished with a usable stage and should be treated as successful. |
| <a id="stagerunsummary-wrotestage"></a>`wroteStage` | bool | yes | Whether the run actually wrote or refreshed stage output on disk. |
| <a id="stagerunsummary-stageusable"></a>`stageUsable` | bool | yes | Whether downstream tooling may safely use the stage after this run finished. |
| <a id="stagerunsummary-errorcount"></a>`errorCount` | [NonNegativeInteger](../pipeline-shared-types-reference/#nonnegativeinteger) | yes | Number of error diagnostics emitted during the run. |
| <a id="stagerunsummary-warningcount"></a>`warningCount` | [NonNegativeInteger](../pipeline-shared-types-reference/#nonnegativeinteger) | yes | Number of warning diagnostics emitted during the run. |
| <a id="stagerunsummary-infocount"></a>`infoCount` | [NonNegativeInteger](../pipeline-shared-types-reference/#nonnegativeinteger) | yes | Number of informational diagnostics emitted during the run. |

