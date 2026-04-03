---
weight: 29
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

# Provider integration end-to-end example

This example shows one way a component catalog, artifact model, and provider
snapshot could combine into staged metadata.

## Scenario

- component: `spark`
- artifacts:
  - `runtime`
  - `kubernetes-operator`
- provider: ATR
- publication host: `https://spark.example.org`

## Example authored metadata

```yaml
sources:
  spark-repo:
    localDir: ../spark
  operator-repo:
    localDir: ../spark-k8s-operator
origins:
  spark:
    baseUrl: https://spark.example.org
components:
  - slug: spark
    displayName: Apache Spark
    publication:
      origin: spark
      mountPath: /
    artifacts:
      - key: runtime
        source: spark-repo
        versioning:
          developmentRef: main
          maintenanceRefPattern: releases/{line}
          tagPattern: ^v[0-9]+\.[0-9]+\.[0-9]+$
      - key: kubernetes-operator
        source: operator-repo
        versioning:
          developmentRef: main
          tagPattern: ^operator-v[0-9]+\.[0-9]+\.[0-9]+$
```

## Example provider snapshot input

```yaml
schemaVersion: 1
providers:
  - key: atr
    type: atr
    fetchedAt: 2026-04-02T12:00:00Z
records:
  - provider: atr
    kind: released
    componentSlug: spark
    artifactKey: runtime
    externalId: atr:release:spark-runtime:4.0.0
    version: 4.0.0
    tag: v4.0.0
    releaseLine: 4.x
    supportStatus: active
  - provider: atr
    kind: candidate
    componentSlug: spark
    artifactKey: runtime
    externalId: atr:candidate:spark-runtime:4.1.0:2
    version: 4.1.0
    displayVersion: 4.1.0-rc2
    maturity: rc
    candidateSequence: 2
    releaseLine: 4.x
    voteStatus: open
  - provider: atr
    kind: line-head
    componentSlug: spark
    artifactKey: runtime
    ref: releases/4.x
    releaseLine: 4.x
  - provider: atr
    kind: development
    componentSlug: spark
    artifactKey: runtime
    ref: main
```

## Example staged page front matter

For a page staged from the candidate docs:

```yaml
sitePipelineComponentPage:
  kind: docs-page
  artifactKey: runtime
  version:
    kind: candidate
    label: 4.1.0-rc2
    maturity: rc
    releaseLine: 4.x
    candidateSequence: 2
    voteStatus: open
  provider:
    key: atr
    externalId: atr:candidate:spark-runtime:4.1.0:2
```

## Example staged aggregate metadata

### `data/providers.json`

```json
[
  {
    "key": "atr",
    "type": "atr",
    "fetchedAt": "2026-04-02T12:00:00Z"
  }
]
```

### `data/artifacts.json`

```json
[
  {
    "componentSlug": "spark",
    "key": "runtime",
    "providerKeys": ["atr"],
    "latestRelease": { "version": "4.0.0" },
    "latestCandidate": { "displayVersion": "4.1.0-rc2" },
    "releaseLines": [
      { "key": "4.x", "latest": "4.0.0", "supportStatus": "active", "headRef": "releases/4.x" }
    ]
  }
]
```

### `data/releases.json`

```json
[
  {
    "provider": "atr",
    "componentSlug": "spark",
    "artifactKey": "runtime",
    "version": "4.0.0",
    "tag": "v4.0.0",
    "releaseLine": "4.x",
    "supportStatus": "active"
  }
]
```

### `data/candidates.json`

```json
[
  {
    "provider": "atr",
    "componentSlug": "spark",
    "artifactKey": "runtime",
    "version": "4.1.0",
    "displayVersion": "4.1.0-rc2",
    "candidateSequence": 2,
    "releaseLine": "4.x",
    "voteStatus": "open"
  }
]
```

### `data/refs.json`

```json
[
  {
    "provider": "atr",
    "componentSlug": "spark",
    "artifactKey": "runtime",
    "kind": "line-head",
    "ref": "releases/4.x",
    "releaseLine": "4.x"
  },
  {
    "provider": "atr",
    "componentSlug": "spark",
    "artifactKey": "runtime",
    "kind": "development",
    "ref": "main"
  }
]
```

## Why the example uses JSON for aggregate files

The v2 examples often use YAML for readability, but JSON is the safer
baseline for aggregate staged metadata because renderer support for arbitrary YAML
files is inconsistent. YAML remains a good default for front matter.

## Renderer outcomes

From the staged outputs above, a renderer can build:

- a candidate banner for `4.1.0-rc2`
- a release selector showing `4.0.0` and `4.x`
- a vote-status badge for the open candidate
- links to development docs and release-line docs
- download or release summary pages from the aggregate metadata