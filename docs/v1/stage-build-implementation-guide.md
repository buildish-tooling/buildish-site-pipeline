---
weight: 33
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

# Stage/build implementation guide

This document tells implementers how to build the internal staging engine that
turns validated pipeline inputs into staged content, aggregate metadata, and a
finalized `manifest.json`.

It is intentionally prescriptive. The goal is that a junior engineer can follow
it directly without inventing local rules for runtime model design, worker
communication, output ownership, private work areas, or finalization safety.

This guide complements:

- `planning-and-input-resolution-implementation-guide.md` for effective config
  resolution, selected local-input inventory, and immutable build-plan
  construction
- `evaluation-and-validation-implementation-guide.md` for contextual validation,
  diagnostics, and stage-gating before mutation begins
- `build-architecture.md` for the high-level coordinator/worker shape
- `watch-incremental-staging-plan.md` for watch-cycle guardrails and publication
  safety
- `cli-api-implementation-guide.md` for the public command boundary and exit-code
  handling
- `staged-output-contract.md` for the stable staged-tree contract
- `security-and-trust-model.md` for path-safety, trust, and abuse-resistance
  rules
- `model-implementation-guide.md` for external schema models and report/manifest
  serialization
- `pipeline-model-schema-reference.md` for the final typed stage and report
  outputs

## Scope

This guide is about the internal build/staging engine.

It covers:

- the package layout below the CLI layer,
- internal runtime and wire-model types,
- coordinator versus worker responsibilities,
- owned-unit planning and output ownership,
- private work-area layout,
- message versus temp-file handoff rules between Python worker processes,
- aggregate recomputation,
- finalized-stage publication preconditions, and
- tests for the stage/build implementation.

It does **not** define:

- the stable public CLI syntax,
- the external schema-model package,
- the materialization/fetch strategy for missing inputs, or
- renderer-specific behavior.

## Fixed decisions

Implementers should treat the following as already decided:

1. `check`, `build`, and each `watch` cycle share one resolve/validate/stage
   pipeline until stage mutation begins.
2. The external Pydantic models are for authored/provider/report/staged-contract
   documents, not for runtime coordinator state.
3. The coordinator is the only writer of shared aggregate outputs,
   `manifest.json`, and visible-stage publication steps.
4. Workers may write only to their owned private output roots inside a private
   run or cycle work area.
5. `manifest.json` is the commit point for a finalized stage and must be written
   last.
6. Large page bodies, asset blobs, parsed ASTs, or other size-variable payloads
   must not be sent through worker pipes.
7. Worker communication is an internal same-version protocol only. It is not a
   public API and must not be persisted as a compatibility promise.
8. Report files live outside the stage root; stage publication and report
   publication are distinct write paths.
9. Output ownership ambiguity, path escapes, symlinked final targets, or
   same-filesystem uncertainty are hard stop conditions for publication.
10. When site-owned content and component-owned content target the same final
    staged path in the first implementation wave, treat that as a collision error,
    not a precedence rule.

## Required package layout

The first implementation wave should create one dedicated internal package for
the staging engine.

Required layout:

- `apache_buildish_site_pipeline/staging/__init__.py`
- `apache_buildish_site_pipeline/staging/types.py`
- `apache_buildish_site_pipeline/staging/ownership.py`
- `apache_buildish_site_pipeline/staging/workdirs.py`
- `apache_buildish_site_pipeline/staging/coordinator.py`
- `apache_buildish_site_pipeline/staging/worker_protocol.py`
- `apache_buildish_site_pipeline/staging/worker_entrypoint.py`
- `apache_buildish_site_pipeline/staging/aggregates.py`
- `apache_buildish_site_pipeline/staging/publication.py`
- `apache_buildish_site_pipeline/staging/fs_guard.py`
- `apache_buildish_site_pipeline/staging/front_matter.py`
- `apache_buildish_site_pipeline/staging/manifest_builder.py`
- `apache_buildish_site_pipeline/staging/units/__init__.py`
- `apache_buildish_site_pipeline/staging/units/site_pages.py`
- `apache_buildish_site_pipeline/staging/units/site_assets.py`
- `apache_buildish_site_pipeline/staging/units/vendor_assets.py`
- `apache_buildish_site_pipeline/staging/units/component.py`

Optional later modules may extend that package, but the first wave should keep
the split explicit and boring.

## Runtime-type policy

Do **not** place runtime coordinator state under
`apache_buildish_site_pipeline.models`.

Use this split:

- external schema documents -> `apache_buildish_site_pipeline.models`
- internal staging runtime and worker protocol types ->
  `apache_buildish_site_pipeline.staging`

### Recommended implementation technology

Use stdlib dataclasses for internal runtime types.

Recommended defaults:

- immutable runtime value types use `@dataclass(frozen=True, slots=True)`
- small mutable coordinator state uses `@dataclass(slots=True)`
- internal enums use string-valued enums when values must appear in logs or JSON
  fragments
- avoid `dict[str, Any]` as the primary runtime contract between modules

Pydantic is the right tool for external document validation. It is not the
default tool for runtime coordinator graphs.

### Path-type rule

Keep local filesystem roots as `pathlib.Path` in coordinator-only runtime types.

For any type that crosses a worker process boundary or is written to an internal
JSON fragment file, use normalized string paths instead:

- absolute local paths as normalized UTF-8 strings when they refer to local input
  or work roots,
- stage-relative paths as forward-slash relative strings,
- never OS-specific opaque path objects in wire payloads.

That keeps the process boundary explicit and testable.

## Internal model families

The staging package should define five families of internal types.

### 1. Build/run request types

These are coordinator-owned immutable inputs for one staging pass.

Required types:

- `BuildRequest`
- `BuildMode`
- `EffectiveBuildPlan`
- `PlannedInput`
- `OperatorPolicy`
- `StageDestination`
- `RunWorkspace`
- `UnitWorkspace`

Minimum responsibilities:

- capture whether the run is `build` or one `watch` cycle,
- capture the validated effective plan derived from authored config, provider
  data, and resolved local inputs,
- carry operator-controlled execution policy such as pool size and safe-default
  overrides,
- carry the finalized stage destination and private work-root locations.

`RunWorkspace` and `UnitWorkspace` should be explicit runtime types in
`workdirs.py`. Do not spread work-area path construction across ad hoc string
concatenation inside workers and coordinator code.

`UnitWorkspace` should at least expose:

- one private staged-content root,
- one private staged-static root when the unit owns static outputs,
- one private fragment root, and
- one private temp root for atomic fragment-file writes.

`EffectiveBuildPlan` should be the one immutable runtime document that the rest
of the staging engine consumes.

It should already contain:

- the selected site-level roots,
- the selected component/version contexts,
- the resolved local paths for planned inputs,
- any needed publication/routing facts already validated enough for staging to
  proceed, and
- watch-root planning facts when the command mode is `watch`.

It should **not** contain live file handles, parser objects, or mutable caches.

### 2. Ownership and dependency types

These types define who may write which staged paths and which aggregates depend
on which owned units.

Required types:

- `OwnedUnitId`
- `OwnedUnitKind`
- `OwnedUnitPlan`
- `OwnedOutputRoots`
- `OutputOwnershipMap`
- `AggregateKind`
- `AggregateDependencyMap`

Every finalized staged path must have exactly one owner.

First-wave owned units should be:

- one site-pages unit,
- one site-assets unit,
- one vendor-assets unit when configured,
- one component unit per staged component slug, covering that component's
  selected version contexts for the current run.

This is a refinement of the higher-level split in `build-architecture.md`, not a
contradiction of it. The same coordinator/worker separation still applies; this
guide just makes the first-wave owned-unit boundaries more explicit.

All aggregate datasets remain coordinator-owned in the first wave.

### 3. Worker wire/message types

These are the small structured payloads that cross Python worker process
boundaries.

Required types:

- `WorkerSpecWire`
- `WorkerResultWire`
- `WorkerFailureWire`
- `WorkerOutputStats`
- `ContributionFileRefs`

These types must be:

- immutable,
- JSON-compatible by design,
- small and bounded,
- free of raw content blobs,
- version-locked to one running codebase revision.

`WorkerSpecWire` should contain only what the worker needs to locate inputs and
write its private outputs, for example:

- unit identity and kind,
- normalized source-root paths,
- normalized private output-root paths,
- normalized private fragment-root path,
- small config values,
- already-resolved publication facts needed by that unit,
- local policy flags needed for deterministic staging.

`WorkerResultWire` should contain only compact summary data, for example:

- unit identity,
- success/failure status,
- output counters,
- relative paths to contribution fragment files,
- relative paths to staged owned roots written by the worker,
- compact diagnostics when small enough.

### 4. File-based fragment types

These are internal JSON documents written into the private work area when worker
outputs are too large, too variable, or too useful after the worker exits to send
through a process pipe.

Required types:

- `UnitContributionManifest`
- `ComponentAggregateFragment`
- `ArtifactAggregateFragment`
- `VersionContextAggregateFragment`
- `PageRecordFragment`
- `RouteCandidateFragment`
- `RedirectCandidateFragment`
- `TranslationSetFragment`
- `CompatibilityFragment`
- `MountFragment`
- `ProviderUsageFragment`
- `ContentIndexFragment`
- `DiagnosticsFragment`

These documents are not public API. They are internal scratch artifacts.

They must:

- use UTF-8 JSON,
- live only beneath the private run or cycle work area,
- never be published as final staged outputs directly,
- be written via same-directory temporary files followed by atomic replace within
  the private work area,
- be treated as untrusted until the coordinator validates ownership and expected
  location.

### 5. Publication and outcome types

These types describe a prepared next stage and the result of publication.

Required types:

- `PreparedAggregates`
- `PreparedStage`
- `PublicationPlan`
- `PublicationPreconditions`
- `PublicationOutcome`
- `LastKnownGoodState`

`PreparedStage` should represent a complete private next-stage candidate, not a
partially published visible stage.

`PublicationOutcome` should be the internal input to final `StageRunSummary`
construction.

`LastKnownGoodState` is coordinator-owned watch state. It should be serialized as
UTF-8 JSON under the pipeline-owned watch work area and must not be passed to or
from workers.

## One-table mapping of internal type families to transport

Use this mapping consistently.

| Type family | Example types | Crosses worker boundary? | Transport | Notes |
| --- | --- | --- | --- | --- |
| Coordinator-only immutable runtime types | `BuildRequest`, `EffectiveBuildPlan`, `PublicationPlan` | no | in-memory only | may use `Path` |
| Ownership/dependency types | `OwnedUnitPlan`, `OutputOwnershipMap` | no | in-memory only | may be snapshotted in tests |
| Worker wire types | `WorkerSpecWire`, `WorkerResultWire` | yes | process-pool message/pipe boundary | must stay small and JSON-compatible |
| Worker large result fragments | `UnitContributionManifest`, `RouteCandidateFragment` | indirect | UTF-8 JSON files in private work area | coordinator loads after worker success |
| Final staged/report models | `StageManifest`, `StageRunReport`, `PipelineDiagnosticEntry` | no public worker boundary by default | final stage/report files | use external Pydantic models |

## Worker transport policy

The first implementation wave should use one request and one result per worker
task.

Do **not** invent a long-lived custom streaming protocol between coordinator and
worker processes in v1.

Recommended execution shape:

- coordinator submits one `WorkerSpecWire`
- worker reads its own inputs from disk
- worker writes its owned private subtree and fragment files
- worker returns one `WorkerResultWire`

### Pipes/messages versus temp files

Use the worker message boundary only for small control-plane data.

Good message payloads:

- identifiers,
- normalized paths,
- booleans and enums,
- small counters,
- a small diagnostic list,
- references to fragment files.

Use temp files inside the private work area for any payload whose size can grow
with page count, asset count, or content size.

That includes:

- route candidates,
- redirect candidates,
- content-index candidates,
- page-record inventories,
- larger diagnostic sets,
- any contribution list that could become large in real sites.

### Pickle policy

The implementation may use Python process pools internally, but it must define
the boundary in terms of explicit wire types, not arbitrary pickled object graphs.

That means:

- worker entrypoints accept one explicit wire object,
- worker results return one explicit wire object,
- closures, lambdas, open file handles, parser instances, and hidden global state
  do not cross the boundary,
- no pickled runtime objects are written to disk as temporary files.

Tests should prove that every worker wire type is JSON-round-trippable even if
the chosen process-pool implementation uses Python pickling internally.

### Start-method rule

Prefer a clean-process start method such as `spawn` for worker pools.

Do not rely on implicit forked global state when the worker correctness depends
on clean locks, clean file descriptors, or predictable import-time initialization.

### Timeout rule

Do not wait indefinitely on worker shutdown or result collection.

Use bounded waits, fail safely, and treat hung worker cleanup as an execution
failure rather than letting the coordinator block forever.

## Required work-area layout

Both one-off `build` and each `watch` cycle should use a private work area on the
same filesystem as the finalized stage root.

Recommended layout:

- `<work-root>/runs/run-000001/`
- `<work-root>/runs/run-000001/next-stage/`
- `<work-root>/runs/run-000001/unit-fragments/<unit-id>/`
- `<work-root>/runs/run-000001/tmp/`
- `<work-root>/last-known-good.json` for watch state only

`next-stage/` is the fully private assembled stage candidate.

Workers may write only into their owned subtrees beneath `next-stage/` and their
owned fragment directories beneath `unit-fragments/<unit-id>/`.

In practice that means workers write beneath owned subtrees of:

- `next-stage/content/...`
- `next-stage/static/...`

Workers do not write `next-stage/data/...` or `next-stage/manifest.json`.

The coordinator owns:

- creation and cleanup of the run directory,
- aggregate files beneath `next-stage/data/`,
- `manifest.json` beneath `next-stage/`,
- same-directory finalization temp files in the visible stage root,
- any retained watch-state metadata.

## Stage-destination safety rules

Treat the caller-selected stage destination as operator-controlled but still
untrusted until validated.

Required rules:

1. normalize every path before use,
2. resolve symlinks before trust decisions,
3. reject any destination that escapes the owned stage root after normalization,
4. reject final write targets whose final path resolves through a symlink,
5. reject publication plans that require cross-filesystem finalization,
6. reject case-only output collisions,
7. reject route collisions and final-path ownership collisions,
8. never delete or overwrite unknown non-pipeline files outside the owned
   contract paths.

### Dedicated-stage-root rule

The safest first-wave assumption is that the selected stage root is dedicated to
pipeline output.

If the stage root already exists but does not look like a pipeline-owned stage
root, fail rather than trying to merge with unrelated files.

For the first wave, "looks like a pipeline-owned stage root" should mean one of:

- the stage root does not exist yet,
- the stage root exists and is empty, or
- the stage root already contains a valid pipeline-owned `manifest.json` and only
  pipeline-owned contract paths beneath it.

If the implementation later supports richer coexistence rules, they must remain
explicit and heavily tested.

## Output ownership and collision policy

The ownership map must be created before any worker starts.

Required first-wave policy:

- one finalized path has exactly one owner,
- site-owned and component-owned outputs may not overlap,
- case-only distinct paths are treated as collisions,
- route collisions are validation or publication failures,
- aggregate files are coordinator-owned only,
- deletion of removed outputs must follow recorded ownership, not directory-wide
  guesswork.

Do **not** implement hidden precedence rules such as "site content wins" or
"component content wins" in the first wave.

Collision means fail the build or fail the watch cycle before publication.

## Coordinator responsibilities

The coordinator is the single entry point for one staging pass.

Required responsibilities:

- accept `BuildRequest` and `EffectiveBuildPlan`
- derive first-wave owned units and the ownership map
- validate stage destination and work-root preconditions
- create one private run workspace
- build worker specs
- execute worker tasks serially or through a bounded process pool
- collect worker results and load contribution fragments
- fail the run before publication if any worker failed
- recompute coordinator-owned aggregates
- create the final private `StageManifest`
- revalidate publication preconditions immediately before visible writes
- publish the stage safely
- build final `StageRunReport` inputs from publication outcome and diagnostics

The coordinator should also own any human-readable or machine-readable summary
construction that depends on the whole run.

## Worker responsibilities

Each worker stages exactly one owned unit.

Required worker properties:

- deterministic for the given input snapshot,
- synchronous internally by default,
- no writes outside its owned private roots,
- no dependence on mutable globals,
- no direct writes to shared aggregate files,
- no direct writes to the visible stage root,
- no direct printing to stdout/stderr as part of normal operation.

Each worker should:

1. validate its own input paths again before reading,
2. load source files from local disk,
3. write staged owned outputs into private roots,
4. generate internal contribution fragments for coordinator-owned aggregates,
5. emit compact diagnostics,
6. return one `WorkerResultWire`.

## Aggregate recomputation rules

Aggregates are coordinator-owned because they combine information across owned
units.

Required first-wave aggregate outputs are the staged files documented in the
contract, including at least:

- `data/components.json`
- `data/artifacts.json`
- `data/routes.json`
- `data/redirects.json`
- `data/diagnostics.json` when preserved non-fatal diagnostics exist

The broader documented aggregate set should already be reflected in the internal
types and manifest/data-file inventory logic:

- `data/releases.json`
- `data/candidates.json`
- `data/refs.json`
- `data/translations.json`
- `data/compatibility.json`
- `data/mounts.json`
- `data/providers.json`
- `data/content-index.json`

The first implementation wave may stage only the subsets whose dependency rules
are already fully defined, but it must not hard-code a manifest/data-file model
that assumes those broader files can never appear.

### Aggregate build order

The coordinator should:

1. collect all successful worker contribution fragments,
2. verify aggregate dependency completeness for the current run,
3. reject missing or ambiguous dependencies,
4. build aggregate entry models using the external typed models where available,
5. write aggregate JSON files into `next-stage/data/` via temp-file replacement
   within the private work area,
6. build `StageManifest` only after the aggregate file inventory is final.

## Front matter and staged-page rules

Workers that stage pages are responsible for page-local front matter emission,
but they must use shared helpers in `front_matter.py`.

Required rules:

- authored front matter remains authored metadata,
- pipeline-owned fields live only under the reserved `pipeline` namespace,
- authored attempts to define the reserved `pipeline` namespace remain validation
  failures,
- staged front matter must not leak machine-local source paths,
- front matter serialization uses YAML,
- aggregate metadata and `manifest.json` use JSON.

## Manifest-building rules

`manifest.json` is built only after the private next stage is complete enough to
describe authoritatively.

The manifest builder should:

- use the external `StageManifest` model,
- set fixed wire values explicitly,
- include only aggregate files that actually exist in the private next stage,
- point to stage-relative roots and data files only,
- never include machine-local work-root or source-root details.

`manifest.json` must be the last finalized visible write.

## Publication model for one-off build and watch reuse

The stage engine should separate these phases sharply:

1. assemble a complete private next-stage candidate,
2. validate that candidate and the publication preconditions,
3. publish visibly under coordinator control,
4. update any requested operator-facing reports.

That separation is mandatory even for one-off `build`.

Visible publication writes for aggregate files, public staged files, and
`manifest.json` must use same-directory temporary files followed by atomic
replace.

### Publication preconditions

Immediately before visible writes, the coordinator must re-check at least:

1. final target paths are still within the intended stage root,
2. final target paths still do not resolve through symlinks,
3. same-filesystem assumptions still hold,
4. ownership is still unambiguous,
5. all files referenced by the new `manifest.json` exist in the private next
   stage,
6. redirect, canonical, origin, mount, and trust-sensitive metadata still pass
   current validation rules,
7. public aggregates still avoid machine-local implementation details.

If any of those checks fail, fail before publication.

### Cleanup and commit-point rule

Removal of outputs that disappeared from the new private next stage must happen
before `manifest.json` is replaced visibly.

Required rules:

- cleanup scope is derived from the ownership map and the previous trustworthy
  stage state,
- cleanup must never broaden to unrelated unknown files,
- newly written visible files must be finalized before the manifest commit point,
- `manifest.json` is replaced only after stale owned paths are cleaned up and all
  referenced new paths are finalized.

If cleanup ownership is ambiguous, fail before the manifest commit point.

### In-place publication fallback rule

If the chosen visible publication strategy mutates the visible tree in place, the
implementation must prove by tests that downstream consumers never observe an
internally inconsistent stage.

If that cannot be guaranteed, fall back to a broader private-stage generation
handoff strategy rather than keep a clever but fragile in-place publisher.

### Publication outcome categories

Use one internal publication outcome model that maps cleanly to the public
`StageRunSummary` combinations:

- `publishedNewStage`
- `failedBeforePublication`
- `failedRetainPrevious`
- `failedExitRequired`

For one-off `build`, the normal categories are `publishedNewStage` and
`failedBeforePublication`.

For `watch`, reuse the same outcome model and let the CLI layer translate it to
the documented process behavior.

The mapping should preserve the public report semantics:

- `publishedNewStage` -> `wroteStage: true`, `stageUsable: true`, `manifestPath`
  present
- `failedBeforePublication` -> `wroteStage: false`; for one-off `build` there is
  no new trustworthy stage from this run
- `failedRetainPrevious` -> `wroteStage: false`, `stageUsable: true`,
  `manifestPath` may point to the retained trustworthy stage
- `failedExitRequired` -> `wroteStage: false`, `stageUsable: false`,
  `manifestPath` omitted

## Security-critical implementation rules

### Never trust fragment-file paths from workers blindly

Workers return references to fragment files, but the coordinator must still
verify that each referenced file:

- lives beneath the worker's owned fragment root,
- matches the expected file name or expected fragment type,
- exists as a regular file,
- does not resolve through a symlink escape,
- is valid JSON before use.

### Keep public outputs free of machine-local details

Public staged outputs and run reports must not expose:

- work-root paths,
- cache layout,
- temp-file names,
- private fragment paths,
- other machine-local implementation details.

If local paths are needed for operator-facing reports, use only the documented
report fields such as `stageRootPath` or `manifestPath`.

### Respect hard ceilings and safe defaults during staging

The staging layer must continue enforcing the security ceilings and safe defaults
from `security-and-trust-model.md`.

That includes at least:

- mounted metadata size ceilings,
- diagnostic `details` reduction rules,
- route/redirect/content-index/watch-root/version-count operational defaults.

If a limit is exceeded, fail before publication of a new stage.

### No hidden network or materialization behavior

The stage/build engine consumes local inputs. It does not fetch SCM state,
refresh caches, or call provider APIs as part of staging.

If a required local input is missing, stale, or unresolved, that should already
surface through planning and validation state and block publication.

### Watch-input exclusion rule

When the staging engine is reused by `watch`, the watch root set must exclude:

- the finalized stage root,
- the pipeline-owned work root,
- report output paths, and
- any same-directory temporary publication files.

Self-generated writes must not be treated as fresh authored-input changes.

## Recommended implementation order

Implementers should follow this order.

### Phase 0: package skeleton and runtime types

1. Create the `staging` package and modules listed above.
2. Define immutable request, ownership, worker-wire, and publication types.
3. Define the work-area layout model.
4. Define the ownership map and collision policy.
5. Add tests for runtime-type round-trips and ownership rules before writing real
   staging logic.

### Phase 1: serial private build pipeline

1. Implement one-off `build` using one coordinator and no worker pool yet.
2. Assemble the full next stage privately.
3. Write coordinator-owned aggregates privately.
4. Build `StageManifest` privately.
5. Publish only after preconditions pass.
6. Prove that worker-free serial builds are deterministic.

### Phase 2: process-ready owned-unit workers

1. Implement `WorkerSpecWire` and `WorkerResultWire` round-trips.
2. Add the worker entrypoint and one worker per first-wave owned-unit type.
3. Keep large contributions file-based.
4. Add bounded process-pool fan-out with configurable pool size.
5. Prove that pool size `1` and pool size `N` produce equivalent outputs.

### Phase 3: watch reuse of the same staging engine

1. Reuse the same private-stage assembly path for watch cycles.
2. Add `LastKnownGoodState` and publication-outcome reuse.
3. Ensure failed cycles retain the previous trustworthy stage when safe.
4. Keep stage/report/work-area paths excluded from watch invalidation.
5. Prove that incremental watch cycles match fresh clean builds for the same
   workspace state.

## Required test layout

The test layout should mirror the package split:

- `tests/staging/test_types.py`
- `tests/staging/test_ownership.py`
- `tests/staging/test_workdirs.py`
- `tests/staging/test_worker_protocol.py`
- `tests/staging/test_coordinator.py`
- `tests/staging/test_aggregates.py`
- `tests/staging/test_manifest_builder.py`
- `tests/staging/test_publication.py`
- `tests/staging/units/test_site_pages.py`
- `tests/staging/units/test_site_assets.py`
- `tests/staging/units/test_vendor_assets.py`
- `tests/staging/units/test_component.py`

## Required tests per concern

### Runtime-type tests

Test at least:

- dataclass immutability where expected,
- JSON round-trip of every worker wire type,
- path normalization in wire payload generation,
- rejection of runtime types that accidentally embed file handles or parser
  instances.

### Ownership and collision tests

Test at least:

- every finalized path has exactly one owner,
- site-pages versus component-path collision rejection,
- site-assets versus vendor-assets collision rejection,
- case-only path collision rejection,
- cleanup ownership for removed component outputs,
- route collision rejection.

### Worker tests

Test at least:

- worker writes only within owned private roots,
- worker does not write shared aggregates,
- worker fragment paths are under the owned fragment root,
- malformed fragment JSON is rejected by the coordinator,
- worker failure prevents publication,
- pool size `1` and `N` equivalence.

### Publication tests

Test at least:

- same-filesystem precondition enforcement,
- rejection of symlinked final targets,
- failure before publication leaves no partially trusted new stage,
- `manifest.json` is written last,
- public outputs omit machine-local paths,
- existing non-pipeline stage-root collisions fail safely,
- unknown files outside owned contract paths are not deleted blindly.

### Build/watch equivalence tests

Test at least:

- one-off `build` and initial `watch` cycle produce equivalent normalized stages,
- failed watch cycle with retained stage yields `wroteStage: false` and
  `stageUsable: true`,
- unrecoverable stage-integrity failure yields `stageUsable: false`,
- rebuild after metadata-only route/redirect/origin change matches a fresh clean
  build,
- self-generated work/report/stage writes do not retrigger watch input.

## Review checklist before merging staging code

### Structure

- [ ] runtime types live under `apache_buildish_site_pipeline.staging`, not
      `models`
- [ ] coordinator-owned logic and worker-owned logic are separated clearly
- [ ] one explicit worker protocol exists
- [ ] large contributions use fragment files rather than message payloads

### Correctness

- [ ] one immutable `EffectiveBuildPlan` feeds the staging engine
- [ ] ownership is explicit before workers start
- [ ] aggregates are coordinator-owned only
- [ ] `manifest.json` is built from the finalized private next stage
- [ ] `manifest.json` is the last visible finalized write
- [ ] pool size changes do not change normalized outputs

### Security

- [ ] every path is normalized before use
- [ ] symlinks are resolved before trust decisions
- [ ] final write targets do not resolve through symlinks
- [ ] cross-filesystem publication is rejected
- [ ] worker fragment references are revalidated by the coordinator
- [ ] machine-local details do not leak into public outputs
- [ ] unknown files are not deleted blindly from the stage root

### Watch reuse

- [ ] watch reuses the same staging engine rather than a second path
- [ ] failed cycles distinguish retain-previous from exit-required
- [ ] stage/work/report outputs are excluded from watch invalidation

## Bottom line

If implementers follow this guide, the result should be:

- one clear staging package below the CLI layer,
- one explicit split between runtime types and external schema models,
- one narrow worker protocol with small pipe messages and larger temp-file
  fragments,
- one ownership model that rejects ambiguous publication,
- one private-stage assembly path reused by one-off `build` and later `watch`,
- and one publication path that prioritizes integrity and security over cleverness.