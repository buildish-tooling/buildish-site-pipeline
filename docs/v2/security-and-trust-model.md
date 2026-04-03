---
weight: 16
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

# Security and trust model

This document defines the baseline security posture for the v2 model.

The Site Pipeline stages and normalizes content. It does not make untrusted
content safe by accident. Safety depends on explicit validation, careful staged
metadata design, renderer escaping, and clear treatment of mounted active
content.

## Core principles

The baseline rules are:

- metadata strings are untrusted text unless a field explicitly says otherwise
- path-bearing inputs must stay within declared source or materialization roots
- aggregate outputs must avoid machine-local implementation details
- imported active HTML/JS content is trusted code, not inert content
- renderers must escape metadata by default

## Path and filesystem safety

Path-bearing inputs include authored content roots, metadata files, local source
roots, mount sources, and materialized local trees.

The pipeline should:

- normalize every path before use
- resolve symlinks before trust decisions are made
- reject any path that escapes its declared root after normalization
- reject archive extraction or bundle expansion that would write outside an owned
  destination
- avoid publishing symlink escapes into the staged tree

This protects against accidental workspace leakage and straightforward path
traversal mistakes.

## Metadata and XSS safety

The model intentionally allows many human-facing string fields, including titles,
labels, descriptions, notes, and provider extensions.

The safety rule is simple:

- those values are data, not trusted HTML

That means:

- the pipeline preserves them as structured text
- renderers HTML-escape them by default
- templates should treat raw HTML rendering as an explicit opt-in outside the
  core pipeline contract

## URL and redirect safety

Redirects and other URL-bearing fields need validation in addition to schema
shape checks.

The pipeline should:

- require internal redirect targets to resolve to known internal routes
- reject unsupported URL schemes such as `javascript:` and `data:`
- treat external redirect destinations as explicit policy decisions
- prefer `https` for public external destinations

Local development tooling may allow additional schemes by consumer-owned policy,
but that is outside the default pipeline contract.

## Mounted content trust classes

Mounted content falls into three broad classes:

- pipeline-rendered markup and pages
- inert static assets such as images, archives, or downloadable files
- imported active site trees containing HTML, CSS, or JavaScript

The first two are normal publication inputs.

Imported active site trees are different. They are trusted code with the ability
to execute in the browser and influence same-origin behavior.

Consumers publishing imported active site trees should decide deliberately:

- whether the subtree shares the main origin
- whether it needs path or host isolation
- which CSP, cookie, and storage policies apply at deployment time

The pipeline can stage and describe those mounts, but it should not pretend they
are inert.

## Aggregate-output minimization

Public staged outputs should prefer stable identifiers, public paths, and public
URLs over machine-local details.

Aggregate metadata should avoid exposing:

- absolute local filesystem paths
- cache-internal directory layout
- other machine-local implementation details

## Resource-exhaustion and abuse resistance

The pipeline should remain defensive against oversized or abusive inputs.

That includes practical limits for:

- provider snapshot size and record count
- redirect and route inventory size
- mounted metadata payload size
- extension payload size
- watched directory scope
- number of staged version contexts in one pass

Failure behavior should be explicit and fail fast when limits are exceeded.

## Responsibility split

Security is shared across layers:

- the pipeline validates, normalizes, and rejects unsafe structural inputs
- renderers escape metadata and handle safe HTML rendering policy
- deployment adapters and site operators enforce origin isolation, CSP, and
  server policy for active mounted content

## Read next

- [flexible-component-publication.md](flexible-component-publication.md) for the
  publication model and validation rules
- [staged-output-contract.md](staged-output-contract.md) for the staged-tree
  contract
- [source-resolution-and-materialization.md](source-resolution-and-materialization.md)
  for local input and cache boundaries