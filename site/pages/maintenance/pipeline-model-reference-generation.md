---
title: Pipeline model reference generation
description: "This page defines the intended direction for how Site Pipeline documents its catalog and component models."
weight: 25
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

Today the repository already generates JSON Schema from the Pydantic models, but
the checked-in schema reference Markdown is still maintained separately. That is
not sustainable once the field descriptions, examples, and ownership guidance
become more useful and more detailed.

The target state is simple:

- the Python model layer is the single source of truth for type and field docs
- JSON Schema is generated from that source
- the schema reference Markdown is generated from that same source
- hand-written docs stay focused on concepts, ownership boundaries, workflows,
  and examples that span several model types

## Requirements

Any final implementation should satisfy these requirements:

- field descriptions explain intent, not just field names or types
- model docs explain ownership, defaults, inheritance, and related fields
- examples exist for the most important authored shapes
- generated output stays deterministic in CI
- maintainers do not have to edit the same field description in two places
- generated reference docs remain readable by humans, not just schema tooling

## Option A: generate JSON Schema and Markdown directly from Pydantic metadata

This is the most direct improvement path.

- strengthen model docstrings
- strengthen `Field(description=...)`
- add examples via `json_schema_extra`
- add a Markdown generator alongside the existing schema export

Pros:

- one source of truth for field-level docs
- low conceptual overhead
- easiest path from the current implementation

Cons:

- relationships between fields can still be awkward unless we enrich metadata
- purely generated docs can read mechanically if the source prose is weak

## Option B: generate the reference core, keep narrative wrappers hand-written

This is the best editorial balance.

The generated part would cover:

- model names
- field tables
- descriptions
- defaults
- examples
- enum values and shape constraints

Hand-written wrapper pages would explain:

- the component-owned versus consumer-owned split
- precedence such as `defaults < group < component < artifact`
- how `docsRoot`, artifacts, and `/development/` versus `/latest/` routes relate
- migration examples and authoring patterns

Pros:

- one source of truth for schema facts
- good reader experience for the important concepts
- less pressure to force long narrative text into field annotations

Cons:

- still requires a small amount of deliberate editorial structure

## Option C: generate Markdown from emitted JSON Schema only

This is the most schema-centric option.

Pros:

- very strict single source
- easy to reason about mechanically
- potentially reusable with other tooling

Cons:

- the prose quality tends to be worse
- relationships and ownership explanations are harder to express well
- examples become clumsy unless the schema is heavily annotated anyway

This is a valid fallback, but it should not be the preferred direction for
human-facing reference docs.

## Option D: add richer documentation metadata in the model layer

This option builds on A or B.

In addition to ordinary descriptions, the models would expose extra metadata
such as:

- ownership: component-owned, consumer-owned, derived, or provider-derived
- related fields
- inheritance or override sources
- warnings or validation notes
- example snippets or example references
- reference-oriented rich-text content that can be rendered consistently into
  generated Markdown

Pros:

- highest-quality generated reference docs
- clearer explanation of how fields relate to each other
- enough structure to emit richer schema reference pages later

Cons:

- more design work up front
- needs a small internal convention so maintainers know where each kind of doc
  metadata belongs

## Recommended direction

The recommended plan is:

1. start with Option B as the documentation shape
2. implement it on top of Option D-style metadata where useful
3. use Option A as the first implementation step if that gets us moving faster

In practical terms, that means:

- make the Pydantic models the source of truth
- improve docstrings, field descriptions, and examples first
- generate both JSON Schema and the schema reference from that metadata
- keep concept-heavy pages hand-written and link them from the generated
  reference

## Concrete implementation plan

The implementation should treat Option B as the output shape and Option D as the
underlying metadata design.

That means the generated reference should own schema facts such as field names,
types, defaults, examples, ownership notes, validation notes, and related-field
links, while hand-written pages continue to explain cross-model concepts,
authoring workflows, precedence rules, and migration guidance.

The implementation should be intentionally split into larger phases to reduce
churn. The goal is to establish the metadata contract and rendering mechanics
first, then update model docs once against that stable structure.

## Rich-text and formatting model

The richer documentation metadata should use a small internal rich-text model,
but it should be authored using a constrained Markdown-like syntax so the input
feels familiar to maintainers.

The intended flow is:

1. maintainers author bounded formatting in familiar Markdown-like text
2. the generator parses that text into an internal rich-text representation
3. renderers emit deterministic output for the schema reference and any future
   derived formats

This keeps authoring ergonomic without making raw arbitrary Markdown the actual
source-of-truth contract.

### Supported first-slice formatting

The first implementation should support at least:

- ordinary paragraphs
- inline code
- bold
- italics
- unordered and ordered lists
- fenced code blocks with a language tag
- cross-reference links that resolve to generated anchors or known narrative
  pages

### Cross-reference link approach

Cross-reference links should look familiar to authors, but they should resolve
through symbolic targets instead of hard-coded relative URLs.

For example, the authoring syntax can still look Markdown-like while using a
stable target vocabulary such as model, field, enum, page, or section
references. The generator should then resolve those symbolic targets into final
anchors.

That means inputs such as:

- `[component list](type:SiteCatalogDocumentV1#components)` for an internal
  symbolic target
- `[project site](https://buildish.apache.org/)` for an external URL

should both be valid in the authored metadata.

That keeps links readable in source while avoiding brittle manually-authored
paths.

The parser should treat those as different link classes:

- internal symbolic references that must resolve against the generated target
  registry
- external URLs that must pass a small allow-list of safe schemes such as
  `https`

Unsafe or unsupported link schemes should be rejected during generation rather
than passed through silently.

### Deliberate first-version limits

The first version should explicitly avoid:

- arbitrary raw HTML in model-layer docs
- fully generic Markdown with no validation rules
- hand-authored Markdown tables inside model metadata

Markdown tables may still be worth adding later, but they should not block the
initial implementation. If table-like output becomes important, it is safer to
add it as a deliberate extension once the basic metadata contract is stable.

### Relationship to JSON Schema output

The JSON Schema output should continue to be generated from the same model-layer
source, but not every rich-text feature needs to appear literally in the schema
documents.

The practical rule should be:

- schema-facing metadata remains suitable for schema tooling
- richer reference-only metadata is available to the Markdown reference
  generator
- both outputs still come from the same model-layer source of truth

This avoids forcing the JSON Schema payload to carry every documentation feature
verbatim while still preventing duplicate authoring.

In particular, link metadata should render differently per output target:

- generated Markdown reference pages should emit proper resolved Markdown links
- generated JSON Schema should remain readable even when consumers do not render
  Markdown links in descriptions

In practice, that means schema descriptions should prefer readable prose such as
`See SiteCatalogDocumentV1.components.` or `External reference:
https://buildish.apache.org/.` rather than depending on schema viewers to render
Markdown link syntax.

If richer machine-readable link output is needed in the schema documents later,
the generator may also emit a project-specific extension field that carries the
resolved link metadata alongside the ordinary human-readable description text.

### Examples in JSON Schema output

The project already has enough model knowledge to generate proper JSON Schema
examples for the main authored document shapes, and that should be part of the
first useful rollout.

That example support should focus first on:

- top-level authored catalog and component document shapes
- common nested authored objects that maintainers are expected to write by hand
- examples that show realistic defaults, ownership boundaries, and field
  interactions

It does not need to force example payloads for every internal, derived, or
purely machine-oriented model in the first version.

The main rule should be that generated examples are:

- valid against the emitted schema
- realistic enough to teach authoring intent
- deterministic in CI
- sourced from the same model-layer metadata rather than duplicated elsewhere

## Phased implementation plan

### Phase 1: define the metadata contract and rendering mechanics

- define where plain schema descriptions, examples, ownership notes, related
  fields, and richer reference-only notes live in the model layer
- define the supported Markdown-like authoring subset and reject unsupported
  syntax deterministically
- introduce the internal rich-text representation used by the generators
- extend the existing generation flow so JSON Schema and Markdown reference
  output both derive from the same source
- make anchor generation and cross-reference resolution deterministic in CI

### Phase 2: pilot the system on representative model areas

- apply the new metadata structure to one or two important model families first
- validate authoring ergonomics, rendered readability, and link stability
- adjust the metadata conventions before broad rollout

### Phase 3: strengthen model docs against the new contract

- rewrite unhelpful field descriptions
- add missing model docstrings
- add examples for the main authored shapes
- add ownership and relationship notes using the new metadata structure
- add rich reference snippets where they improve the generated reference

### Phase 4: reduce or remove the hand-maintained duplicate reference

- replace duplicated hand-maintained schema details with generated output
- keep only the narrative pages that genuinely add cross-model explanation
- ensure links from narrative docs into generated reference sections are stable

## Non-goals

This work should not try to force every piece of project documentation into the
model layer.

The model layer should own schema facts. Concept pages, tutorials, and broad
architecture explanations should remain hand-written.
