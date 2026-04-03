---
weight: 31
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

# Model implementation guide

This document tells implementers how to build the external model layer for the
pipeline using Pydantic.

It is intentionally prescriptive. The goal is that a junior engineer can follow
it directly without inventing local rules for validation, security, module
layout, or test coverage.

This document complements:

- `pipeline-model-schema-reference.md` as the source of truth for model names,
  fields, and wire-level types
- `security-and-trust-model.md` as the source of truth for path, URL, trust,
  and resource-limit requirements
- `validation-and-check.md` for diagnostic behavior and operator-facing failure
  handling

## Scope

This guide is only about **external schema models** and their deserialization,
validation, and serialization.

It covers:

- authored YAML input models,
- provider snapshot input models,
- planning and report models,
- staged front matter models,
- staged aggregate metadata models, and
- reusable scalar, enum, and validation helper types that those models need.

It does **not** cover:

- internal runtime/execution state,
- coordinator or worker control-flow objects,
- filesystem mutation logic,
- watch-cycle state management, or
- renderer-specific behavior.

## Decisions already made

Implementers should treat the following as fixed decisions:

1. The root package is `apache_buildish_site_pipeline.models`.
2. Model modules are grouped by the section structure of
   `pipeline-model-schema-reference.md`.
3. Pydantic is used from the first implementation wave.
4. Invalid YAML or JSON input must never produce a successfully deserialized
   model instance.
5. Validation rules are applied in the model layer when they are local and
   deterministic.
6. Validation rules that need shared helper logic belong in
   `apache_buildish_site_pipeline.models.validation`.
7. Production models are not implemented with a general builder pattern.
8. Test fixture builders are allowed in tests when they improve readability.

## Required package layout

The initial package layout should be:

- `apache_buildish_site_pipeline/models/__init__.py`
- `apache_buildish_site_pipeline/models/base.py`
- `apache_buildish_site_pipeline/models/enums.py`
- `apache_buildish_site_pipeline/models/scalars.py`
- `apache_buildish_site_pipeline/models/authored_input.py`
- `apache_buildish_site_pipeline/models/provider_input.py`
- `apache_buildish_site_pipeline/models/planning_stage_contract.py`
- `apache_buildish_site_pipeline/models/staged_front_matter.py`
- `apache_buildish_site_pipeline/models/staged_aggregate_metadata.py`
- `apache_buildish_site_pipeline/models/loading.py`
- `apache_buildish_site_pipeline/models/validation/__init__.py`
- `apache_buildish_site_pipeline/models/validation/common.py`
- `apache_buildish_site_pipeline/models/validation/paths.py`
- `apache_buildish_site_pipeline/models/validation/urls.py`
- `apache_buildish_site_pipeline/models/validation/references.py`
- `apache_buildish_site_pipeline/models/validation/extensions.py`

If `authored_input.py` becomes too large, it may later split into multiple
modules such as `authored_input_catalog.py` and `authored_input_component.py`.
Do not split early unless file size or readability actually demands it.

## Mapping from schema-reference sections to modules

Use this mapping directly.

| Schema-reference section | Implementation module |
| --- | --- |
| Authored input types | `authored_input.py` |
| Provider input types | `provider_input.py` |
| Planning and stage-contract types | `planning_stage_contract.py` |
| Staged front matter types | `staged_front_matter.py` |
| Staged aggregate metadata types | `staged_aggregate_metadata.py` |
| Shared enums | `enums.py` |
| Scalar and helper types | `scalars.py` plus `validation/*` |

Do not invent a second grouping scheme by feature or command. The schema section
layout is the primary organizing principle.

## Base-model conventions

All production schema models should inherit from one shared base class defined in
`base.py`.

That shared base should enforce these defaults:

1. unknown fields are forbidden by default,
2. instances are treated as immutable after construction,
3. serialization uses wire-format field names,
4. validation errors are not suppressed or converted into partial objects, and
5. JSON serialization is deterministic enough for stable tests.

Collection-typed fields must use safe default factories rather than mutable
module-level defaults.

Recommended policy details:

- Python attribute names should use `snake_case`.
- Wire-format field names must use `camelCase` exactly as documented in
  `pipeline-model-schema-reference.md`.
- External YAML and JSON documents must be validated against the wire-format
  names, not against ad hoc alternative spellings.
- Tests must prove that misspelled or unknown fields are rejected.

## Field naming and alias rules

The implementation should keep Python readable without drifting from the schema.

Required rule:

- Python code uses `snake_case` field names.
- Serialized YAML/JSON uses the schema's `camelCase` field names.

That means implementers should define explicit aliases or a shared alias policy
for every field that appears in serialized input or output.

Do not accept these shortcuts:

- accepting both `snake_case` and `camelCase` from external authored files,
- silently rewriting misspelled field names, or
- allowing unknown fields "for forward compatibility" in v1.

The correct behavior for unknown or wrongly cased external fields is validation
failure.

## Parsing and deserialization entry points

Do not deserialize authored YAML or provider JSON by calling Pydantic model
constructors directly at random call sites.

Instead, create explicit document-loading entry points in `loading.py`.

The first implementation wave should expose at least these entry points:

- `load_component_repository_document(...)`
- `load_catalog_document(...)`
- `load_provider_snapshot(...)`
- `load_resolved_materialization_report(...)`
- `load_check_report(...)`
- `load_stage_run_report(...)`
- `load_stage_manifest(...)`

Those loaders should perform this order of work:

1. decode bytes using UTF-8 when bytes are provided,
2. parse YAML or JSON using safe parsing only,
3. reject duplicate mapping keys in authored YAML and duplicate object keys in
   JSON,
4. require the document root to be the expected container type,
5. inspect `schemaVersion` when the document type defines one,
6. dispatch to the correct version-specific model,
7. run Pydantic validation,
8. return a fully validated model instance or raise a structured validation
   failure,
9. never return a partial or best-effort object.

### Duplicate-key policy

Duplicate keys in YAML and duplicate object keys in JSON must be treated as
invalid input.

Do not rely on whichever duplicate happens to "win" in the parser. That is
error-prone and can hide authored mistakes or security-sensitive shadowing.

### Schema-version policy

Every root document with a documented `schemaVersion` should have:

- one loader function that reads the raw version first,
- one version-specific Pydantic model for each supported schema version, and
- an explicit unsupported-version failure path.

For the first implementation wave, version-specific models may use a concrete
literal schema version internally, but the dispatch hook should still exist from
day one.

## Scalar and helper types

Do not model all schema-reference scalar types as plain `str` everywhere.

Create reusable scalar types or reusable constrained field aliases for at least:

- `Identifier`
- `Slug`
- `ArtifactKey`
- `OriginKey`
- `SourceKey`
- `ProviderKey`
- `VersionString`
- `RefString`
- `ReferenceString`
- `RepoRelativePath`
- `LocalPathString`
- `MountSourceRef`
- `PublicPath`
- `StageRelativePath`
- `UrlString`
- `HostnameString`
- `TimestampString`

These types should share one normalization and validation rule per scalar kind.
Do not re-implement slug or path validation separately in each model.

## What belongs in Pydantic validators versus separate validation helpers

Use this split consistently.

### Pydantic field or model validators should handle

- type shape,
- required versus optional fields,
- enum membership,
- local scalar normalization,
- cross-field constraints that only depend on the object being validated,
- list uniqueness within the current object,
- obvious self-contradictions, and
- security checks that do not require external state.

### Separate validation helpers in `models.validation` should handle

- reusable path rules,
- reusable URL rules,
- reusable reference-string parsing and validation,
- reusable extension-object size checks,
- reusable collection-uniqueness helpers,
- reusable normalization helpers, and
- logic shared across multiple models.

### Do not put these into Pydantic model validators

- filesystem existence checks,
- route resolution that depends on a separately computed route inventory,
- network access,
- provider fetches,
- workspace scanning,
- watch-root derivation, or
- any validation that depends on mutable runtime state outside the document.

Those belong in later contextual validation layers, not in raw model
deserialization.

## Security-critical validation requirements

This section is mandatory. If a junior engineer follows only one section
carefully, it should be this one.

### Path-bearing fields

For path-bearing fields such as `RepoRelativePath`, `LocalPathString`,
`StageRelativePath`, `PublicPath`, and mount-related path references, the model
layer must:

- normalize paths before later consumers use them,
- reject paths containing traversal that would escape the intended root,
- reject NUL-like malformed path payloads,
- reject absolute paths for types that are declared repository-relative or stage-
  relative,
- preserve the distinction between local-only path fields and public path fields,
  and
- never serialize machine-local paths into public staged aggregate models unless
  the schema explicitly calls for a local path field such as report-only output.

The model layer is not the place that proves a path exists on disk, but it is
the place that must reject obviously unsafe path syntax.

Filesystem-dependent trust decisions such as symlink resolution belong in later
contextual validation layers that have real root-path context.

### URL-bearing fields

For `UrlString` and any redirect, canonical, or origin field that contains a
URL, the model layer must:

- reject unsupported schemes such as `javascript:` and `data:`,
- allow only the schemes explicitly permitted by the contract,
- keep internal-reference syntax distinct from absolute-URL syntax, and
- leave any local-operator-only development overrides outside repo-authored and
  provider-authored input.

If a field is an internal reference rather than a URL, model it as such. Do not
smuggle internal references through generic URL strings.

### Redirects and internal references

The schema design already implies typed internal reference strings such as:

- `route:/docs/latest/`
- `component:spark`
- `artifact:spark/runtime`
- `line:spark/runtime@4.x`
- `release:spark/runtime@4.0.0`

Implement reusable reference parsing and validation helpers for those forms.

The model layer should at minimum:

- validate reference grammar,
- reject malformed type prefixes,
- reject empty target payloads, and
- preserve the parsed string exactly if it is valid.

Context-dependent resolution against known routes or known components belongs in
later validation layers, not in basic deserialization.

### Reserved namespaces and contract-owned fields

The staged front matter contract reserves the top-level `pipeline` namespace for
pipeline-owned output.

That means:

- authored input must not be allowed to define pipeline-owned staged namespaces,
- staged front matter models must treat that namespace as contract-owned rather
  than free-form metadata, and
- tests must prove authored attempts to claim contract-owned namespaces are
  rejected.

### ExtensionsObject fields

`ExtensionsObject` is allowed only in explicitly documented extension slots such
as mount `metadata` and diagnostic `details`.

Implementers must not use it as a loophole for untyped arbitrary data anywhere
else.

Required rules:

- only the documented fields may use an extension-object type,
- extension-object values must be JSON-serializable structured data,
- size limits must be checked after deterministic JSON serialization,
- hard security ceilings from `security-and-trust-model.md` are mandatory,
- safe operational defaults may be locally overridden only by local operator
  policy, not by repo-authored or provider-authored input.

### Diagnostic details special rule

`PipelineDiagnosticEntry.details` has a special reduction rule.

If the serialized `details` payload would exceed the documented hard ceiling, the
implementation must:

- keep the diagnostic entry itself,
- replace only `details` with a bounded summary object,
- include measured and allowed sizes,
- never emit malformed JSON, and
- never rely on `details` as the sole carrier of operator-essential meaning.

This is a case where a dedicated factory function or classmethod is preferable to
raw direct construction.

## Extra-field, coercion, and normalization policy

The model layer should be strict by default.

Required behavior:

- reject unknown fields,
- reject wrong container types,
- reject invalid enum values,
- reject malformed scalar values,
- reject illegal duplicate identifiers inside one document when uniqueness is
  required,
- do not silently trim or rewrite structural values such as keys, slugs, refs,
  paths, URLs, or enum-like strings.

Human-facing labels such as display names may preserve human-authored spacing and
capitalization when the schema allows it.

For structural values, prefer explicit failure over silent cleanup.

## When a builder pattern is acceptable

Do **not** create a generic builder pattern for production schema models.

Use these patterns instead:

- direct Pydantic construction for already validated data,
- loader functions for external documents,
- focused `classmethod` or helper factories when extra derived behavior is
  required,
- fixture builders only in tests.

A builder-like factory is acceptable only when it prevents unsafe duplication of
important logic, for example:

- diagnostic-detail size reduction,
- report models that consistently inject `generatedAt`,
- stage manifest creation that sets required fixed-format fields safely.

Do not use a builder just because a model has many fields.

Do not use `model_construct()` or other validation-bypassing shortcuts in
production parsing paths.

## Required implementation order

Implementers should follow this order.

### Phase 0: package skeleton and common primitives

1. Create the `apache_buildish_site_pipeline.models` package.
2. Add `base.py`, `enums.py`, `scalars.py`, `loading.py`, and the
   `validation/` subpackage.
3. Implement the shared base model.
4. Implement shared enum types.
5. Implement shared scalar types and reusable validation helpers.
6. Add unit tests for scalar types and validation helpers first.

### Phase 1: authored input models

Implement all types from the authored-input section of the schema reference.

Start with the root documents first:

- `ComponentRepositoryDocument`
- `CatalogDocument`

Then implement the nested authored types they depend on.

Add dedicated loader functions for authored YAML documents before moving on.

### Phase 2: provider input models

Implement:

- `ProviderSnapshot`
- `ProviderDescriptor`
- `ProviderRecord`
- `ProviderAsset`

Add JSON loader coverage and size-limit validation coverage.

### Phase 3: planning and stage-contract models

Implement:

- `ResolvedMaterializationReport`
- `ResolvedMaterializationEntry`
- `CheckReport`
- `CheckSummary`
- `StageRunReport`
- `StageRunSummary`
- `StageManifest`
- `StageRoots`
- `StageDataFiles`
- `PipelineDiagnosticEntry`

Implement report-specific helper factories where they prevent duplication of
fixed fields or reduction rules.

### Phase 4: staged front matter models

Implement all types from the staged front matter section.

Add serialization tests proving the wire format stays camelCase and stable.

### Phase 5: staged aggregate metadata models

Implement all types from the staged aggregate metadata section.

Add tests that prove public aggregate models do not accidentally expose
machine-local fields.

## Required tests per module family

Every model family must have both positive and negative tests.

The test layout should mirror the model layout:

- `tests/models/test_scalars.py`
- `tests/models/test_loading.py`
- `tests/models/test_authored_input.py`
- `tests/models/test_provider_input.py`
- `tests/models/test_planning_stage_contract.py`
- `tests/models/test_staged_front_matter.py`
- `tests/models/test_staged_aggregate_metadata.py`
- `tests/models/validation/test_paths.py`
- `tests/models/validation/test_urls.py`
- `tests/models/validation/test_references.py`
- `tests/models/validation/test_extensions.py`

### Scalar and validator tests

For each reusable scalar or helper validator, test:

- valid examples,
- obvious invalid examples,
- boundary cases,
- security-sensitive bad inputs,
- deterministic normalization behavior if normalization is allowed.

### Root-document tests

For each root document type with `schemaVersion`, test:

- minimal valid document,
- fully populated valid document,
- unsupported `schemaVersion`,
- missing `schemaVersion`,
- wrong top-level container type,
- duplicate YAML keys,
- unknown fields,
- invalid nested objects.

### Nested-model tests

For nested models, test:

- missing required fields,
- illegal cross-field combinations,
- uniqueness violations,
- malformed path values,
- malformed URL or reference values,
- rejection of wrong-case or unknown external field names.

### Output-model serialization tests

For reports, manifests, front matter, and aggregate metadata, test:

- serialization uses `camelCase`,
- optional fields appear or omit exactly as intended,
- JSON remains well-formed,
- round-trip parse/serialize behavior stays stable where applicable,
- no machine-local-only fields leak into public aggregate outputs.

### Security-specific tests

Add explicit tests for:

- path traversal attempts,
- absolute paths where repo-relative or stage-relative values are required,
- dangerous URL schemes,
- malformed internal references,
- oversized mount metadata,
- oversized diagnostic details reduction,
- rejection of unknown extension-object fields outside approved slots,
- rejection of repo-authored attempts to influence local operator override
  policy.

## Documented model-family checklist

Before a schema-reference section is considered implemented, confirm all of the
following:

- every type from that section exists in the mapped module,
- every documented field exists with the documented wire name,
- enums are implemented as constrained pipeline-defined values,
- shared scalars are reused rather than copied as raw strings,
- root documents have loader entry points,
- negative tests exist for validation failures,
- security-sensitive fields have explicit tests,
- serialization tests exist for output-facing models.

## Specific guidance for the first implementation wave

These conventions reduce future mistakes.

### Use version-specific root models

For example, a v1 catalog document should be represented by a version-specific
model even if only version 1 exists today.

That keeps future schema-version dispatch from becoming a breaking refactor.

### Prefer explicit enums over unconstrained strings

Any pipeline-defined status, mode, kind, or command from the schema reference
should be implemented as an enum-like constrained type, not a raw free-form
string.

Prefer string-valued enums for wire-facing enum types so serialized values match
the documented schema values directly.

### Prefer `Literal[...]` for fixed wire values

Fields that have one documented allowed value in v1 should be modeled as a fixed
literal rather than as an unconstrained string.

Examples include:

- `CheckReport.command = check`
- `StageManifest.frontMatterFormat = yaml`
- `StageManifest.aggregateFormat = json`

That prevents accidental emission of schema-invalid values.

### Prefer explicit model fields over `dict[str, Any]`

Only use opaque extension-object shapes where the schema explicitly says so.
Elsewhere, create real nested models.

### Keep validation pure

Model construction and validation must not perform I/O, mutate global state, or
depend on the current filesystem contents.

That keeps tests fast, deterministic, and safe.

### Use factory methods sparingly and deliberately

Factories are good when they centralize tricky logic. They are bad when they hide
basic required fields or silently invent defaults that the schema did not define.

## Self-review checklist before merging model code

Use this checklist during implementation reviews.

### Architecture and package layout

- [x] the package is `apache_buildish_site_pipeline.models`, not `model`
- [x] modules are grouped by schema-reference section
- [x] runtime/execution state has not been mixed into schema modules
- [x] shared scalar and enum types exist centrally

### Validation and correctness

- [x] root-document loaders exist and are the only supported external parse path
- [x] duplicate YAML keys are rejected
- [x] unsupported schema versions fail clearly
- [x] unknown fields fail clearly
- [x] no partial object is returned on invalid input
- [x] cross-field constraints are tested
- [x] uniqueness constraints are tested

### Security

- [x] path-bearing fields reject obviously unsafe syntax
- [x] dangerous URL schemes are rejected
- [x] internal-reference grammar is validated
- [x] extension-object slots are limited to documented fields only
- [x] mount metadata size ceilings are enforced
- [x] diagnostic-detail reduction follows the documented rule
- [x] public aggregate models avoid machine-local implementation details
- [x] local operator override policy is not sourced from repo/provider input

### Serialization and compatibility

- [x] wire-format field names are `camelCase`
- [x] Python attribute names stay `snake_case`
- [x] output models have round-trip or serialization stability tests
- [x] required fixed-value fields are set consistently

## Bottom line

If implementers follow this guide, the result should be:

- one coherent `apache_buildish_site_pipeline.models` package,
- strict and predictable deserialization,
- no accidental acceptance of malformed authored input,
- reusable security-sensitive validators,
- test coverage for both happy and unhappy paths, and
- output-facing models that stay aligned with the published schema reference.