---
title: Integrate provider, compatibility, and translation data
description: "Use this guide when authored publication policy is no longer enough by itself and the site needs provider-derived lifecycle data, compatibility metadata, or translation linkage."
weight: 21
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

## Keep ownership boundaries explicit

The clean split is:

- authored site and catalog metadata own public policy and route intent
- provider snapshots enrich lifecycle and release-state information
- compatibility metadata expresses cross-component or cross-artifact support
- translation linkage relates localized pages without redefining route policy

These are three independent dimensions. Add and validate each one separately so
a provider problem cannot be mistaken for a compatibility or localization
problem.

## 1. Add provider lifecycle data

First author the component, artifact, versioning rules, publication selection,
and lifecycle entries in `site/catalog.yaml`. Then supply matching normalized
records in `site/provider-snapshot.json`:

```json
{
  "schemaVersion": 1,
  "providers": [
    {
      "key": "github",
      "type": "githubReleases",
      "fetchedAt": "2026-04-03T00:00:00Z"
    }
  ],
  "records": [
    {
      "provider": "github",
      "kind": "released",
      "componentSlug": "spark",
      "artifactKey": "runtime",
      "version": "4.0.0",
      "tag": "v4.0.0"
    }
  ]
}
```

After building, inspect `data/providers.json`, `data/artifacts.json`, and
`data/releases.json`. The released page's `pipeline.page.version` and
`pipeline.page.provider` fields provide page-local context.

Provider records must match authored identities and selected contexts. They may
add normalized lifecycle provenance, but they cannot introduce a new public
component, route, or release selection by themselves.

## 2. Model compatibility as an authored assertion

Place the assertion on the component or artifact whose compatibility is being
described:

```yaml
compatibility:
  - subjectRef: component:spark
    targetRef: component:spark-operator
    relation: testedWith
    scope: kubernetes
    confidence: verified
    notes: Spark runtime docs assume the matching operator line.
```

The typed subject and target must resolve within the catalog. The staged
`data/compatibility.json` entry then retains the relationship for renderers:

```json
{
  "subjectId": "component:spark",
  "targetId": "component:spark-operator",
  "relation": "testedWith",
  "scope": "kubernetes",
  "confidence": "verified",
  "notes": "Spark runtime docs assume the matching operator line."
}
```

Do not infer compatibility from similar version numbers. State the relationship
and its scope directly, and update it when the supporting evidence changes.

## 3. Link translated pages

Declare the locale policy in defaults or on one component:

```yaml
localization:
  supportedLocales: [en, de]
  defaultLocale: en
  fallbackLocale: en
  routeMode: prefixAll
```

Place corresponding pages below supported locale directories and give them the
same authored translation key:

```yaml
---
title: Install Spark
translationKey: install
---
```

For example, `en/install.md` and `de/install.md` form one translation set when
both declare `translationKey: install`. The pipeline emits page-local sibling
links and a cross-page entry in `data/translations.json`; the renderer chooses
how to display those links.

The same key may occur only once per locale in a component/artifact context.
With `prefixAll`, a translated page must live below a supported locale prefix,
and sibling routes must have a consistent shape.

## Validate one dimension at a time

1. Build and inspect the authored publication model without optional
   compatibility or translation data.
2. Add provider records and inspect lifecycle aggregates.
3. Add compatibility assertions and inspect `data/compatibility.json`.
4. Add localization policy and one complete translation set, then inspect
   `data/translations.json` and the staged page front matter.
5. Expand only after `site-pipeline check` passes at each step.

## Failure map

| Failure | Inspect first |
| --- | --- |
| selected context has no matching provider record | authored selection and `provider-snapshot.json` identity fields |
| provider and catalog disagree on tag, ref, version, or state | provider diagnostics and authored lifecycle entry |
| compatibility reference is unknown | typed `subjectRef` and `targetRef` values |
| duplicate locale in a translation set | authored `translationKey` values within that locale |
| translation route is inconsistent | locale directories, route mode, and sibling relative paths |

## Read this next

For unreleased development contract details:

- [provider snapshot schema](../../development/reference/provider-snapshot-schema/)
- [provider to staged metadata mapping](../../development/reference/provider-to-staged-metadata-mapping/)
- [security and trust model](../../development/reference/security-and-trust-model/)
- [pipeline model schema reference](../../development/reference/pipeline-model-schema-reference/)
