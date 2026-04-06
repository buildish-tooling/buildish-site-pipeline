---
title: "Pipeline model glossary"
description: "This glossary defines the terms used across the flexible publication and provider-integration docs."
weight: 28
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

## Component

The user-facing product, project area, or documentation space. A component is a
stable identity and publication unit, but not necessarily the unit of versioning
truth.

## Artifact

An independently versioned release unit within a component. Artifacts may share a
repository, or come from different repositories, and may have different tag
patterns, release lines, and maintenance refs.

## Source

A repository or checkout from which content, tags, refs, or metadata are read.
A component or artifact may reference one or more sources.

## Origin

A publication host or base URL, such as `https://spark.example.org`. The final
publication location is modeled as `origin + path`.

## Publication path

The path portion of a published URL under an origin, such as `/` or
`/projects/spark/`.

## Route

A resolved published location, effectively the combination of origin and path.

## Canonical route

The preferred published route for a target. This is the route renderers, feeds,
and search-oriented metadata should usually use by default.

## Alias route

An additional non-redirecting route for the same published target.

## Redirect route

A route that forwards to another route or URL instead of directly publishing the
target content.

## Redirect inventory

Pipeline-emitted aggregate metadata describing resolved redirects in a
deployment-neutral form so server-specific config can be generated from it.

## Development ref

The moving mainline ref for an artifact, usually something like `main` or
`trunk`.

## Named ref

A moving ref intentionally exposed beyond development, such as a feature branch,
preview branch, or other project-defined ref.

## Release line

A named grouping of exact releases, such as `1.x` or `1.1.x`. Release lines may
be hierarchical.

## Line head

The moving ref associated with a release line, such as `releases/1.1.x`.

## Exact release

An immutable published version such as `4.0.0` or tag `v4.0.0`.

## Release candidate

An in-flight candidate for an exact release, often associated with a vote
or review process.

## Maturity

An optional label describing release flavor or stage, such as `alpha`, `beta`,
`rc`, or `preview`. This is distinct from support posture.

## Support status

An optional project-defined label describing support posture, such as `active`,
`bugfix-only`, `security-fix-only`, or `eol`.

## Support window

Structured lifecycle metadata such as release date, end-of-support date,
end-of-life date, maintenance phase, or support-policy URL.

## Locale

A language or language-region identifier such as `en`, `fr`, or `pt-br` used as
an optional publication dimension.

## Translation set

A group of pages representing the same conceptual content across locales.

## Compatibility assertion

A structured claim that one component, artifact, release line, or exact release
is compatible with another under some stated scope.

## Mount

A publication rule that attaches a generated or imported documentation subtree to
one public path under a component or artifact publication root.

## Generated subtree

Documentation output produced by another tool, such as Javadoc, Scaladoc,
Sphinx, or OpenAPI generation.

## Imported subtree

A documentation tree copied into the staged site from another build output,
bundle, or external source.

## Provider

An external system that supplies normalized release metadata, such as ATR or a
Git-hosting release API.

## Provider snapshot

A versioned, normalized input file consumed by the pipeline from one or more
providers.

## Front matter

Page-local metadata attached to staged Markdown content. It should contain only
the information needed to render the current page and nearby navigation.

## Aggregate metadata

Pipeline-emitted metadata files under `data/` used for global queries, listings,
navigation structures, and release inventories.

## Asset

Optional file-level detail attached to a release or candidate, such as an
archive, signature, checksum, SBOM, or provenance file. Assets are usually not
top-level pipeline identities.
