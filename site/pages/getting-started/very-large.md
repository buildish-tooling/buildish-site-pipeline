---
title: Very-large sites
description: "This page is for publication systems that span many repositories, multiple product families, and strong permalink, trust-boundary, and localization needs."
weight: 15
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

## Who this is for

- many repositories or doc sources
- multiple product families under one staged contract
- localization, mounted content, and generated refs may all be in play

## Start from a working large-site model

A very-large site is not a different schema. It is a large-site catalog with
more independent sources, product groups, locales, mounts, and deployment
targets operating through the same staged contract. Start from the
[Large sites](../large/) packet, then add one dimension at a time.

A representative source layout might include:

```text
site/
  catalog.yaml
  provider-snapshot.json
components/
  spark/
    docs/
      en/
      de/
  spark-operator/
    docs/
      en/
      de/
generated/
  api-reference/
vendor/
  shared-brand/
```

Localization remains authored policy. For example, shared defaults can require
every localized route to carry its locale prefix:

```yaml
defaults:
  localization:
    supportedLocales: [en, de]
    defaultLocale: en
    fallbackLocale: en
    routeMode: prefixAll
```

Translated pages use the same `translationKey` while keeping their own authored
content:

```text
docs/en/guide.md  -> translationKey: guide
docs/de/guide.md  -> translationKey: guide
```

The pipeline validates that the locale, route shape, and translation linkage
agree. It emits the cross-page relationship in `data/translations.json`; the
renderer decides how to present a language switcher.

## Use a gated operating flow

Run planning and validation before publishing a new stage:

```bash
site-pipeline plan --for build --report-format json --report-schema-version 1
site-pipeline check --report-format json --report-schema-version 1
site-pipeline build
```

Treat each step as a separate decision:

1. Planning inventories the selected local inputs and reports whether they are
   present, missing, stale, or unresolved.
2. Consumer-owned SCM or cache tooling materializes missing inputs.
3. `check` validates paths, links, provider records, translations, references,
   and route ownership without publishing a stage.
4. `build` publishes one completed staged contract for renderers and deployment
   adapters.

## Inspect the cross-site outputs

At this scale, sample representative pages and inspect the aggregate inventory:

```text
site/.stage/
  manifest.json
  content/
  data/
    components.json
    compatibility.json
    content-index.json
    diagnostics.json
    redirects.json
    routes.json
    translations.json
  static/
```

Use `manifest.json` to discover which aggregate files are present. Do not make
renderers or deployment adapters infer routes, versions, translations, or
compatibility from checkout layout.

## Failure and recovery expectations

- Missing or stale inputs stay visible in the planning report; acquisition
  remains outside Site Pipeline.
- Unknown compatibility targets, duplicate translation locales, inconsistent
  translation routes, and route collisions block staging.
- A failed build must not replace the last completed stage.
- Deployment adapters should reject route or redirect entries belonging to an
  origin they do not own.
- Provider input can enrich lifecycle state but cannot redefine component
  identity or public routes.

## Read these first

1. [Integrate provider, compatibility, and translation data](../../how-to/integrate-provider-compatibility-and-translation-data/)
2. [Scale Site Pipeline operations](../../how-to/scale-site-pipeline-operations/)
3. [Create HTTP server configuration](../../how-to/http-server-config-how-to/)

## What you should treat as first-class concerns

- route ownership and long-lived permalink stability
- trust boundaries between authored inputs, provider data, and deployment config
- translation linkage and mounted/generated content boundaries
- operational controls for planning, caches, and large inventories

## Growth transition

There is no next size band. Growth means making ownership and operating limits
more explicit: split planning by deployment unit where appropriate, monitor
inventory sizes and build time, keep source acquisition replaceable, and test
each renderer and deployment adapter against the staged contract.

## Deeper unreleased development reference

- [Architecture overview](../../architecture/architecture-overview/)
- [staged output contract](../../development/reference/staged-output-contract/)
- [security and trust model](../../development/reference/security-and-trust-model/)
- [pipeline model schema reference](../../development/reference/pipeline-model-schema-reference/)

These contracts describe unreleased development behavior and have not yet been
published as release documentation.
