---
weight: 45
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

# Design principles and future evolution

This document collects the generic design principles that should remain true even
as Site Pipeline evolves.

## Renderer-neutral staged contract

The pipeline should own staging and validation, not the final renderer.
Consumers may use Hugo today and something else later, but they should still
consume the same predictable staged tree.

## Supported content profile

Component repositories should contribute only portable content inputs:

- authored pages and docs,
- static assets inside approved roots,
- small renderer-neutral metadata, and
- no custom renderer logic, plugins, or arbitrary build steps.

The guaranteed portable subset should stay conservative: headings, prose, lists,
links, code blocks, simple tables, images, and documented metadata.

## Version and lifecycle model

The generic model should keep these distinctions clear:

- `development` is the rendered view of the current default-branch content,
- exact tags such as `v1.2.3` are the canonical released versions,
- moving aliases such as `v1` remain informational only, and
- lifecycle state belongs to release lines rather than to ad hoc URL aliases.

## Generated metadata and aggregation

The pipeline should continue to generate normalized metadata alongside staged
content so consumers do not have to rediscover lifecycle, alias, or provenance
relationships at render time.

That keeps renderer integrations simple and makes the staging boundary testable.

## Security posture

Site Pipeline should remain conservative by default:

- no path traversal outside approved workspace roots,
- no symlink escapes while copying docs or assets,
- no arbitrary component-owned renderer extensions,
- no remote fetching during normal builds, and
- no component-authored shadowing of reserved pipeline-managed paths.

## Planned evolution

The current implementation is intentionally smaller than the long-term design.
Likely future work includes:

- stricter validation of supported content conventions,
- incremental handling of released-doc snapshots,
- richer lifecycle publication metadata, and
- clearer CI manifests for resolved build inputs.

Those changes should refine the contract rather than blur the boundary between
pipeline-owned staging and consumer-owned rendering/publishing.

## Read next

- [Site Pipeline overview](../site-pipeline/)
- [Site component contract](../site-component-contract/)
- [Consumer workspace and CI model](../workspace-and-ci-model/)
