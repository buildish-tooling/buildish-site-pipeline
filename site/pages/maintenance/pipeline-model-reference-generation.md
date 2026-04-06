---
title: Pipeline model reference generation
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

# Pipeline model reference generation

This page defines the intended direction for how Site Pipeline documents its
catalog and component models.

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
- how `docsRoot`, artifacts, and `/latest/` relate
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

## Phased implementation plan

### Phase 1: strengthen model docs

- rewrite unhelpful field descriptions
- add missing model docstrings
- add examples for the main authored shapes
- add ownership and relationship notes where the model layer already supports it

### Phase 2: generate the schema reference

- extend the existing schema export flow
- emit Markdown reference pages from the same model metadata
- make generation deterministic and easy to run in CI

### Phase 3: reduce or remove the hand-maintained duplicate reference

- replace duplicated hand-maintained schema details with generated output
- keep only the narrative pages that genuinely add cross-model explanation
- ensure links from narrative docs into generated reference sections are stable

## Non-goals

This work should not try to force every piece of project documentation into the
model layer.

The model layer should own schema facts. Concept pages, tutorials, and broad
architecture explanations should remain hand-written.