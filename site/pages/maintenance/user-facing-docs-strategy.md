---
title: User-facing documentation strategy
weight: 20
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

# User-facing documentation strategy

This document describes the target shape of the public documentation site for
Apache Buildish Site Pipeline.

The current documentation set already has stronger structure than before, but it
is still weighted toward implementation, architecture, and contract readers.
This strategy defines how to turn that base into a user-facing site that quickly
explains what the pipeline is, what it is not, and where each reader should go
next.

## Buildish context

Site Pipeline will become a component within the broader Apache Buildish project.
That means the docs must work at two levels:

- as a standalone documentation site for readers evaluating or adopting Site
  Pipeline directly
- as a component-level documentation site that fits naturally into a larger
  Buildish information architecture later

The docs should therefore avoid pretending that Site Pipeline is the whole
product. They should explain its responsibility boundary clearly and leave room
for future Buildish-level overview, workflow, and integration pages.

## Primary goals

A reader landing on the docs should be able to answer quickly:

1. What is Apache Buildish Site Pipeline?
2. What does it own?
3. What does it explicitly not own?
4. Is it a fit for my site?
5. What should I read next?

## Canonical positioning

The docs root should treat the following as the durable plain-language position.

Site Pipeline is a reusable staging pipeline for documentation sites. It loads
consumer-owned catalog and component metadata, validates publication intent,
normalizes authored and optional provider inputs, and emits a staged site tree
plus machine-readable metadata for downstream renderers and deployment adapters.

The docs should state just as plainly what it is not:

- not a renderer
- not a theme system
- not a CMS
- not a hosting platform
- not a generic website builder
- not a replacement for consumer-owned publication and release policy

## Reader journeys

The user-facing site should optimize for these entry paths:

1. evaluate whether Site Pipeline is the right tool
2. build a first working tiny or small site
3. grow from simple authored docs to versions, redirects, mounts, and grouped
   publication
4. integrate Site Pipeline with an existing renderer or deployment layer
5. look up exact schema, contract, and trust-model details
6. maintain or extend the Site Pipeline implementation itself

## Target information architecture

The documentation set should use these top-level reader-facing sections:

- `getting-started/` for tutorials and size-band entry points
- `concepts/` for mental models, boundaries, and plain-language explanation
- `how-to/` for task-oriented procedures
- `reference/` for schemas, contracts, glossary material, and normative rules
- `architecture/` for deeper design and system-shape explanation
- `maintenance/` for maintainer-only implementation guidance

The missing layer today is `concepts/`. Without it, readers have to jump from
brief onboarding pages into either how-to tasks or deep architecture/reference
material too early.

## Docs root requirements

`site/pages/_index.md` should be the real product landing page, not just a
section index. It should include, in this order:

1. a one-paragraph definition of Site Pipeline
2. a short "what it is" list
3. a short "what it is not" list
4. good-fit and poor-fit signals
5. a "choose your path" section with reader-intent links
6. a five-minute mental model of inputs, planning, staging, and consumers
7. a "what this looks like" section linking to concrete examples
8. natural next steps for first-time readers

The root page should never require readers to infer the project boundary from
architecture prose buried deeper in the site.

## Getting-started requirements

The current size-band pages are a useful index, but they are still too abstract.
Each getting-started guide should eventually include:

- what this size band looks like in practice
- a small repo or content-layout example
- the minimum files and metadata involved
- what command the reader runs
- what staged output the reader should expect to see
- what concepts matter at this size
- what can be ignored for now
- what changes when the site grows beyond this band

The guides should show real-looking structures early instead of relying mostly
on abstract explanation.

## Content design rules

For user-facing docs, prefer these rules:

- explain intent before detail
- show examples before deep abstraction
- separate tutorial, concept, how-to, and reference writing styles
- end each page with a natural next step
- be explicit about responsibility boundaries and trust boundaries
- prefer concrete file trees, config fragments, and staged-output examples over
  vague descriptions

## Required example packet for user-facing pages

Every tutorial, concept page, or how-to that introduces new pipeline behavior
should try to include a small reusable example packet:

- the relevant workspace tree
- the authored `site/components.yaml` fragment
- the authored page or content fragment when page behavior matters
- the CLI command the reader runs
- the first staged path the reader should inspect
- one front-matter or aggregate-file excerpt that proves the behavior happened

This is the quickest way to keep the docs concrete and to stop readers from
guessing how the model maps onto real files.

## Canonical examples

The site should maintain one canonical example thread that appears across the
docs in progressively richer forms. Readers should not have to remap the model
from scratch on each page.

At minimum the example thread should support:

- tiny single-component authored docs
- small versioned docs with redirects
- medium publication with imported or generated docs
- large or very-large publication with grouped components and provider data

Each richer example should extend the previous one instead of replacing it, so a
reader can recognize the same component, mount paths, and stage outputs across
multiple sections.

## Rollout plan

Deliver the user-facing site in phases:

1. keep `site/pages/_index.md` focused on product definition and reader routing
2. keep `site/pages/concepts/` as the plain-language mental-model layer
3. expand the getting-started guides with real-looking examples and expected
   outputs
4. align how-to pages with the new concept pages and canonical examples
5. review reference pages for better entry links and reader context

The current rollout should use the same `spark` tiny-site example across the
landing page, concept pages, tiny guide, and staged-output inspection guide.

## Definition of success

The user-facing site is in good shape when a new reader can:

- understand what Site Pipeline is from the docs root alone
- determine quickly whether it fits their site
- find the right next page without searching
- build a tiny or small first setup without guessing about expected outputs
- understand the staged-output boundary before reading deep reference docs

## Read next

- [code-maintenance.md](code-maintenance.md) for durable maintainer guidance
- [../architecture/architecture-overview.md](../architecture/architecture-overview.md)
  for the current architectural explanation that the user-facing site should
  gradually expose more accessibly
- [api contract](/docs/reference/api-contract/) for the stable
  command and output boundary that user-facing pages should point toward