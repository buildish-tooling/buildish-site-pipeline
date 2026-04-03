---
weight: 15
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

# Planning and input-resolution implementation guide

This document tells implementers how to build the internal planning and input
resolution layer that turns authored configuration, optional provider snapshots,
and local filesystem facts into:

- a machine-readable `ResolvedMaterializationReport`, and
- one immutable `PlanningEvaluation` result for shared evaluation, and
- when planning prerequisites are sufficient, the immutable
  `EffectiveBuildPlan` candidate later handed to staging.

It is intentionally prescriptive. The goal is that a junior engineer can follow
it directly without inventing local rules for effective-config resolution,
provider authority, version-context selection, local-input readiness, or watch
eligibility.

This guide complements:

- `source-resolution-and-materialization.md` for the architectural planning and
  materialization boundary
- `flexible-component-publication.md` for publication, lifecycle, routing, and
  provider-authority rules
- `provider-snapshot-schema.md` for provider input shape
- `provider-to-staged-metadata-mapping.md` for provider-to-public-output mapping
- `pipeline-model-schema-reference.md` for `ResolvedMaterializationReport` and
  `ResolvedMaterializationEntry`
- `model-implementation-guide.md` for external schema-model loading and parsing
- `evaluation-and-validation-implementation-guide.md` for the non-mutating
  contextual validation layer that consumes the resolved plan
- `stage-build-implementation-guide.md` for the staging engine that consumes the
  final immutable build plan
- `security-and-trust-model.md` for path-safety, trust-boundary, and limit rules

## Scope

This guide is about planning and input resolution only.

It covers:

- loading authored and provider models through the model-layer loaders,
- effective authored configuration resolution,
- provider snapshot indexing and authority boundaries,
- publication-selection resolution,
- version-context selection,
- local-input inventory derivation,
- local-input readiness classification,
- watch-eligibility derivation,
- construction of the immutable `PlanningEvaluation` result and optional
  `EffectiveBuildPlan` candidate, and
- planning-focused tests.

It does **not** cover:

- command-line parsing or report-file writing,
- contextual validation and diagnostic aggregation,
- stage mutation or aggregate publication,
- watch-loop orchestration, or
- SCM fetching, cache mutation, or other materialization work.

## Fixed decisions

Implementers should treat the following as already decided:

1. `site-pipeline plan` is a report-only command. It resolves required local
   inputs but does not fetch or materialize them.
2. The planning layer must not perform SCM fetches, provider API calls, cache
   mutation, or stage-root writes.
3. Effective authored configuration resolution follows one explicit rule:
   `defaults` < `group` < `component` < `artifact`.
4. Scalar fields use nearest-defined-value wins; maps merge by key; arrays
   replace rather than concatenate; explicitly empty arrays/maps clear inherited
   values.
5. Provider snapshots are authoritative for externally observed release state,
   timestamps, vote status, external URLs, and asset inventories.
6. Authored metadata remains authoritative for routing, publication selection,
   named-ref publishability, exact-release publication behavior, and final route
   ownership.
7. No local provider-override file exists in the first implementation wave.
8. `plan --for watch` must emit an explicit `watchEligible` value for every
   planning entry.
9. `stale` must never be guessed from ad hoc filesystem mtimes alone.
10. The planning layer must produce the same local-input universe that `build`
    and `watch` actually consume: top-level site pages, site assets, vendor
    assets, and selected component/version-context trees.

## Required package layout

Create one dedicated internal package for planning and input resolution.

Required layout:

- `apache_buildish_site_pipeline/planning/__init__.py`
- `apache_buildish_site_pipeline/planning/types.py`
- `apache_buildish_site_pipeline/planning/effective_config.py`
- `apache_buildish_site_pipeline/planning/provider_index.py`
- `apache_buildish_site_pipeline/planning/selection.py`
- `apache_buildish_site_pipeline/planning/input_inventory.py`
- `apache_buildish_site_pipeline/planning/readiness.py`
- `apache_buildish_site_pipeline/planning/watch_roots.py`
- `apache_buildish_site_pipeline/planning/build_plan.py`
- `apache_buildish_site_pipeline/planning/report_builder.py`

Keep this package separate from:

- `apache_buildish_site_pipeline.models`, which owns external document models,
- `apache_buildish_site_pipeline.evaluation`, which owns contextual validation,
  and
- `apache_buildish_site_pipeline.staging`, which owns stage mutation and
  publication.

## Responsibility split

Use this split consistently.

### `models`

- parse YAML/JSON safely
- validate external document shape
- reject duplicate keys, unknown fields, and malformed scalar values

### `planning`

- resolve effective authored config
- index normalized provider snapshot records
- choose version contexts to stage
- derive required local inputs and readiness states
- derive watch-eligible inputs and watch roots
- build `ResolvedMaterializationReport`
- build `PlanningEvaluation`
- build `staging.types.EffectiveBuildPlan` only when planning prerequisites are
  sufficient

### `evaluation`

- perform cross-document, cross-route, cross-provider, and rooted filesystem
  validation
- collect diagnostics
- decide whether staging may proceed

### `staging`

- mutate private stage work areas
- write staged outputs
- publish a trustworthy finalized stage

## Planning outputs

The planning layer has one public output and two internal runtime products.

### External output

The public planning output is the external typed model:

- `ResolvedMaterializationReport`

Use the model-layer type from `planning_stage_contract.py`. Do not hand-roll
report dictionaries.

### Internal runtime products

The always-present internal output is the immutable runtime document:

- `PlanningEvaluation`

`PlanningEvaluation` is what the shared evaluation layer should consume for
`check`, `build`, and `watch`.

The optional stage-capable planning output is:

- `staging.types.EffectiveBuildPlan`

The planning package may define helper runtime types, but the final stage-capable
plan handed onward to staging should be the single `EffectiveBuildPlan` type
already called for by the staging guide.

## Required internal type families

Define internal dataclass-based runtime types in `planning/types.py`.

### 1. Effective authored projection types

Required types:

- `ResolvedSiteConfig`
- `ResolvedGroupConfig`
- `ResolvedComponentConfig`
- `ResolvedArtifactConfig`
- `ResolvedPublicationPolicy`
- `ResolvedSourceBinding`

These are immutable projections of authored config after inheritance and default
resolution.

They should contain only resolved fields the rest of planning needs. Do not drag
raw Pydantic model graphs through the whole pipeline once the projection step is
complete.

### 2. Provider index types

Required types:

- `ProviderSnapshotIndex`
- `ProviderRecordKey`
- `IndexedProviderRecord`
- `ProviderContextIndex`

These runtime types index normalized provider records by the dimensions planning
and validation need, such as:

- provider key,
- `(componentSlug, artifactKey)`,
- record kind,
- version,
- ref,
- release line,
- external ID.

### 3. Selected version-context types

Required types:

- `VersionContextKind`
- `SelectedVersionContext`
- `SelectedVersionSet`

Every selected context should carry enough information to identify:

- component slug,
- artifact key,
- context kind such as development, line head, released, candidate, or named ref,
- route-facing display identity,
- source-facing identity such as `ref`, `tag`, or exact version,
- provider enrichment references when present,
- whether the context is mutable enough to be watch-eligible.

### 4. Local-input inventory types

Required types:

- `InputKind`
- `LocalInputIdentity`
- `ResolvedLocalInput`
- `MaterializationStatusReason`
- `InputReadiness`
- `WatchInputPlan`

These types represent the exact local inputs required for one build target.

### 5. Planning result types

Required types:

- `PlanningTargetRuntime`
- `PlanningEvaluation`
- `PlanToBuildBridge`

`PlanningEvaluation` should be the internal result for one planning pass. It
should include:

- the target (`build` or `watch`),
- the resolved authored projections,
- the indexed provider snapshot view,
- the selected version contexts,
- the resolved local-input inventory,
- the derived watch-root facts,
- any planning-phase diagnostics already known, and
- an optional prebuilt `EffectiveBuildPlan` candidate when planning prerequisites
  are already sufficient.

## Effective authored configuration resolution

Implement the authored-resolution algorithm once in `effective_config.py`.

### Precedence rule

Apply this order consistently:

1. `defaults`
2. `group`
3. `component`
4. `artifact`

Do not re-implement inheritance differently for publication, localization,
selection, support-status vocabularies, or source bindings.

### Merge semantics

Use the documented rules:

- scalars -> nearest defined value wins
- maps/objects -> merge by key; nearer scope wins per key
- arrays/lists -> replace, do not concatenate
- absent field -> inherit
- explicit empty array/map -> clear inherited value

### Resolution safety rules

Required rules:

1. do not mutate the original model instances,
2. do not resolve by serializing to ad hoc dicts and merging untyped data,
3. do not infer routing from `slug` when routing fields are absent,
4. do not let provider data override authored publication policy,
5. treat unknown group references, source references, origin references, or
   artifact references as contextual validation failures later, not silent
   omissions.

## Provider snapshot indexing and authority split

Load provider snapshots only through the model-layer loader, then build a compact
runtime index in `provider_index.py`.

### First-wave provider rules

1. At most one normalized provider snapshot document is needed in the first wave.
2. Apply the security doc's hard ceilings and safe defaults while loading and
   indexing.
3. Reject duplicate `(provider, externalId)` pairs when `externalId` exists.
4. Reject unknown provider keys referenced by records.
5. Reject records that point to unknown components or artifact keys.

### Authority split

Implement this split explicitly:

- provider-authored facts win for:
  - discovered releases,
  - release candidates and vote status,
  - externally observed ref state,
  - timestamps,
  - public external URLs,
  - release/candidate asset inventories
- consumer-authored facts win for:
  - publication selection,
  - named refs that are intentionally publishable,
  - exact-release `publicationState`, `withdrawalBehavior`, and `redirectTarget`,
  - origin/path ownership,
  - component and artifact identity

Do not silently let provider data redefine route ownership or publishability.

### No passthrough rule

The provider index should keep only the normalized fields needed for planning,
evaluation, and later aggregate emission.

Do not preserve provider-specific passthrough payloads as generic bags in runtime
planning objects.

## Version-context selection algorithm

Implement selection in `selection.py`.

### Policy source order

Resolve the effective publication-selection policy in this order:

1. artifact `publicationSelection`, if present
2. component `publicationSelection`, if present
3. built-in default behavior

### Built-in default

The default selection must be:

- include development docs
- include all authored line heads
- include the latest stable release per release line
- include only explicitly selected authored named refs
- exclude release candidates unless explicitly requested

### Selection rules by context kind

#### Development

- selected when effective policy enables development
- source identity comes from the resolved development ref binding
- provider data may enrich the context but may not create it when no authored
  development source exists

#### Line heads

- selected according to the effective line-head policy
- line identity comes from authored release-line definitions
- source identity comes from the resolved maintenance-ref or line-head source
- do not invent release lines from provider data alone

#### Exact releases

- selected according to the effective release policy
- the authoritative selected version set comes from authored lifecycle data plus
  provider-discovered releases, merged by version identity
- if the chosen mode needs a "latest stable per line" answer, use authored
  lifecycle/latest-line facts where present; do not guess by string sorting when
  the underlying model does not make the answer deterministic

#### Named refs

- only authored named refs are eligible for intentional publication in the first
  wave
- provider records may enrich an authored named ref and may carry `namedRefKey`
- provider records must not create ad hoc publishable named refs outside authored
  policy

#### Candidates

- excluded by default
- included only when effective policy requests them
- exact candidate selection must remain deterministic when several provider
  candidates exist for one version; use explicit authored policy or a clearly
  documented provider sort rule, then validate the result

### Withdrawal and publication-state rule

Selection must preserve authored exact-release publication behavior.

That means a selected released context may still carry authored behavior such as:

- `published`
- `hidden`
- `withdrawn`
- `tombstoned`

and authored withdrawal behavior such as:

- `notice`
- `redirect`
- `omit`

Do not collapse release-state selection and route/publication behavior into one
step.

## Local-input inventory derivation

Implement required local-input derivation in `input_inventory.py`.

The local-input universe must include:

- one entry per configured site pages root,
- one entry per configured site assets root,
- one entry per configured vendor asset tree,
- one entry per selected component/version context.

### `sourceKey` rule

Every entry should have a stable identity.

Use:

- the configured source key when one exists,
- otherwise a deterministic synthetic internal key derived from owned input kind,
  component, artifact, and context kind.

Do not use raw local absolute paths as the primary identity key.

### Expected local path rule

Each entry must carry one normalized expected local path string suitable for the
public planning report.

That path must be:

- deterministic,
- rooted in the resolved local input binding,
- normalized before comparison,
- checked for escapes and symlink surprises before use.

## Readiness classification

Implement readiness classification in `readiness.py`.

The public status vocabulary is:

- `present`
- `missing`
- `stale`
- `unresolved`

### First-wave classification rules

#### `present`

Use `present` only when:

- the expected local path exists,
- it resolves within the intended declared root,
- it has the expected basic type for the input kind, and
- there is no explicit evidence that the local input is stale or mismatched.

#### `missing`

Use `missing` when:

- the required local input path does not exist, or
- a configured required local subtree is absent entirely.

#### `stale`

Use `stale` only when the implementation has explicit evidence that the local
input no longer matches the required source identity.

Good stale evidence includes:

- a local materialization marker that records `ref`, `tag`, `version`, or
  `commitSha` and does not match the selected context,
- a generated snapshot manifest that declares an older source identity than the
  selected one,
- a versioned cache record that points to a different selected context than the
  one now required.

Do **not** classify an input as `stale` from:

- plain mtime drift,
- directory age,
- "looks old" heuristics,
- provider `updatedAt` timestamps alone without a local identity mismatch.

#### `unresolved`

Use `unresolved` when planning cannot determine a trustworthy required local
input path or identity, for example:

- a selected context has no resolvable local binding,
- authored config references an unknown source,
- the local materialization metadata is contradictory,
- the implementation cannot determine which of several local trees should satisfy
  the required input.

When in doubt between `stale` and `unresolved`, prefer `unresolved` unless the
staleness proof is explicit.

## Watch eligibility and watch roots

Implement watch eligibility in `watch_roots.py`.

### `watchEligible` rules

Use explicit rules, not guesses.

Inputs should normally be `watchEligible: true` only when they are:

- mutable workspace-backed roots,
- actively edited local development trees,
- mutable local vendor trees the consumer expects watch mode to track.

Inputs should normally be `watchEligible: false` when they are:

- immutable snapshots,
- cached historical releases,
- archive-expansion outputs that are not edited in place,
- generated trees whose refresh is external to pipeline watch mode.

### Watch-root exclusion rules

Derived watch roots must exclude:

- the finalized stage root,
- the pipeline-owned work root,
- requested report-output files,
- same-directory temporary publication files,
- unrelated parent directories that would broaden the watch scope far beyond the
  actual mutable inputs.

Self-generated pipeline writes must not be added back into the watch plan.

## Path-safety rules for planning

Planning is non-mutating, but it still makes trust decisions about local paths.

Required rules:

1. normalize every path before use,
2. resolve symlinks before trust decisions,
3. reject any path that escapes its declared root after normalization,
4. reject contradictory or ambiguous local bindings,
5. do not let repo-authored or provider-authored input choose local operator work
   roots,
6. do not expose internal cache layout or internal-only provider endpoints in the
   public planning report.

## Building the optional `EffectiveBuildPlan` candidate

Implement the bridge from `PlanningEvaluation` to
`staging.types.EffectiveBuildPlan` in `build_plan.py`.

### Build-plan gating rule

Only create an `EffectiveBuildPlan` candidate when planning has enough resolved
input information to describe a trustworthy staging attempt.

That means:

- required local inputs are not `missing`, `stale`, or `unresolved`,
- selected version contexts are deterministic,
- source bindings are resolved enough for staging to read local files,
- watch-root facts are computed when the target is `watch`.

If those conditions are not met, planning may still emit a public planning report,
and it must still emit `PlanningEvaluation`, but it must not fabricate an
`EffectiveBuildPlan` candidate.

### Required `EffectiveBuildPlan` contents

The built plan should include at least:

- resolved site-level input roots,
- resolved component and artifact context projections,
- selected version contexts,
- normalized local input paths,
- resolved publication facts already known before contextual validation,
- provider context references needed later for staged metadata,
- watch-root facts for watch-capable execution.

Do not include:

- raw SCM clients,
- open file handles,
- parser instances,
- mutable caches,
- hidden closures or lambdas.

## Public planning-report construction

Implement report construction in `report_builder.py`.

Required rules:

1. build the report using the external `ResolvedMaterializationReport` model,
2. set `target` to the requested planning target, not the literal command name,
3. include every resolved required local input as one entry,
4. include explicit `watchEligible` on every entry when `target = watch`,
5. include structured diagnostics when planning discovered them,
6. keep local-path output operator-meaningful but free of internal cache and temp
   implementation details when possible.

## Security-critical planning rules

### No hidden materialization behavior

The planning layer must not:

- fetch from Git or other SCMs,
- call provider APIs,
- refresh caches,
- generate snapshots,
- mutate local input trees.

It may only inspect already available authored input, already available provider
snapshot input, and already available local filesystem state.

### Keep operator policy local

Safe-default overrides such as planning scale ceilings, watch-root breadth, or
provider snapshot size overrides must remain local operator policy.

They must not come from:

- repo-authored metadata,
- provider snapshot data, or
- page front matter.

### No accidental route inference from provider data

Provider data is enrichment, not route truth.

Do not derive public origins, public paths, or publishability solely from provider
records.

## Recommended implementation order

Implementers should follow this order.

### Phase 0: internal planning types and report builder

1. Create the `planning` package and runtime types.
2. Implement `report_builder.py` against fixture-based `PlanningEvaluation`
   objects.
3. Add tests for report-shape correctness and `watchEligible` requirements.

### Phase 1: effective authored resolution

1. Implement `effective_config.py`.
2. Prove the precedence and merge semantics with focused tests.
3. Add tests for explicit empty-array/map clearing behavior.

### Phase 2: provider indexing and selected-context resolution

1. Implement `provider_index.py`.
2. Implement `selection.py`.
3. Add tests for authored-vs-provider authority boundaries.
4. Add tests for deterministic candidate and named-ref handling.

### Phase 3: local-input inventory and readiness

1. Implement `input_inventory.py`.
2. Implement `readiness.py`.
3. Add tests for `present`, `missing`, `stale`, and `unresolved` classification.
4. Prove that `stale` is never emitted from mtime-only heuristics.

### Phase 4: watch-root derivation and build-plan bridge

1. Implement `watch_roots.py`.
2. Implement `build_plan.py`.
3. Add tests for watch-root exclusion of stage/work/report paths.
4. Add tests proving that `EffectiveBuildPlan` candidates are only built from
   ready inputs.

## Required tests

Recommended test layout:

- `tests/planning/test_effective_config.py`
- `tests/planning/test_provider_index.py`
- `tests/planning/test_selection.py`
- `tests/planning/test_input_inventory.py`
- `tests/planning/test_readiness.py`
- `tests/planning/test_watch_roots.py`
- `tests/planning/test_build_plan.py`
- `tests/planning/test_report_builder.py`

### Effective-config tests

Test at least:

- defaults/group/component/artifact precedence,
- scalar nearest-value wins,
- map merge behavior,
- array replacement behavior,
- explicit empty-array/map clearing,
- no route inference from slug-only identity.

### Provider-index tests

Test at least:

- duplicate `(provider, externalId)` rejection,
- unknown component/artifact provider references,
- provider/authored authority split,
- no provider passthrough baggage retained in runtime planning types,
- ceiling/default enforcement for oversized provider snapshots.

### Selection tests

Test at least:

- artifact policy overriding component policy,
- built-in default behavior,
- named refs only from authored policy,
- release candidates excluded by default,
- exact-release publication state preserved separately from selection,
- deterministic release selection without unsafe guesswork.

### Readiness tests

Test at least:

- `present`, `missing`, `stale`, and `unresolved` mapping,
- `stale` only from explicit mismatch evidence,
- no mtime-only stale detection,
- path normalization and symlink-escape rejection,
- ambiguous local-binding detection.

### Watch-root tests

Test at least:

- mutable workspace roots are watch-eligible,
- immutable snapshot roots are not watch-eligible,
- stage/work/report paths are excluded,
- `plan --for watch` requires explicit `watchEligible` on every entry.

## Review checklist before merging planning code

### Structure

- [ ] the planning package is separate from `models`, `evaluation`, and `staging`
- [ ] one central effective-config resolution algorithm exists
- [ ] one central selection algorithm exists
- [ ] the planning layer produces `ResolvedMaterializationReport` and
      `PlanningEvaluation`
- [ ] `EffectiveBuildPlan` candidates are produced only when planning
      prerequisites are sufficient

### Correctness

- [ ] `defaults` < `group` < `component` < `artifact` is implemented consistently
- [ ] arrays replace rather than concatenate
- [ ] selected contexts match authored publication-selection policy
- [ ] the reported local-input universe matches what `build` and `watch` consume
- [ ] `target = watch` planning entries all include `watchEligible`
- [ ] `EffectiveBuildPlan` candidates are only built when readiness is
      sufficient

### Security

- [ ] planning performs no hidden fetches or cache mutation
- [ ] local paths are normalized and rooted before trust decisions
- [ ] symlink escapes are rejected
- [ ] provider data does not redefine route ownership or publishability
- [ ] operator policy stays local and is not repo/provider driven
- [ ] public planning output does not leak private implementation details

## Bottom line

If implementers follow this guide, the result should be:

- one explicit planning package,
- one deterministic effective-config and selection path,
- one disciplined split between authored policy and provider enrichment,
- one trustworthy local-input inventory with explicit readiness states,
- one watch-root derivation path that does not self-trigger, and
- one immutable planning result that `check`, `build`, and `watch` can share,
  with an `EffectiveBuildPlan` candidate only when planning prerequisites are
  sufficient.