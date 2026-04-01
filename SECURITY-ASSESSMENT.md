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

# Security Assessment

_Date:_ 2026-04-01

## Scope

This document captures a strict security-oriented review of the `buildish-site-pipeline` codebase.
The review focused on:

- YAML/config/model loading
- filesystem path resolution and staging
- preview HTML generation and preview HTTP serving
- watch-mode path collection
- subprocess usage
- snapshot publishing
- container helper scripts

## Executive Summary

The reviewed code paths present a **reasonably hardened trusted-workspace build pipeline**.
Within the assessment scope, no known direct path was found to cache poisoning, arbitrary preview-script execution, arbitrary local command execution, or repository-file exfiltration through the built-in preview flow.

The codebase has several meaningful controls in place:

- YAML is loaded with `yaml.safe_load`
- Pydantic models forbid unexpected fields
- component slugs are validated with a strict allowlist
- derived stage and preview output paths are containment-checked before writes
- symlinks are skipped during staged copying
- preview slug paths are URL-encoded before inclusion in HTML
- repository links in preview pages are restricted to absolute `http` / `https` URLs
- the preview server is scoped to the generated preview directory
- `site/components.local.yaml` is treated as local-only and emits a runtime warning when active
- no `shell=True`, `eval`, `exec`, `pickle`, or similar unsafe deserialization was found

These conclusions are intentionally narrow: they reflect the reviewed code paths and should not be read as a guarantee that the project is free of all security defects.

## Direct Answers to the Original Questions

### Are there issues that could lead to security incidents?

**No known direct issue was found in the reviewed areas after the implemented fixes.**
As with any build pipeline, incidents would still be possible if trusted local files, the execution environment, or external dependencies are compromised.

### Is it possible to poison the cache contents?

**No known path was found in the reviewed areas.**
Stage and preview outputs are protected by slug validation plus derived-path containment checks.

### Is arbitrary code execution possible?

**Browser context:** No known direct path was found in the reviewed preview flows.

**Local OS/process context:** No direct path was found from reviewed catalog/content/config input to shell or subprocess execution.
The codebase does not appear vulnerable to obvious shell injection or unsafe deserialization in the reviewed areas.

### Is secret/credential-stealing possible?

**No known direct path was found in the reviewed areas.**
The built-in preview flow is constrained to `site/.preview`, and preview links do not expose a known direct script-execution path in the reviewed code.

## Current Security Properties

### Filesystem and staging safety

- component slug values are restricted to lowercase letters, digits, and single hyphens
- derived component output paths are resolved through containment checks before stage/preview writes
- stage and preview writes are confined beneath their intended parent directories
- symlinks are skipped during copy operations, which reduces link-based staging surprises

### Preview safety

- preview index links URL-encode slug-based path segments
- repository links are rendered as active links only for absolute `http` / `https` URLs with a host
- unsupported or unsafe repository link schemes render as plain text
- the built-in preview server serves only the generated preview directory

### Configuration and input handling

- YAML is parsed with `yaml.safe_load`
- typed models reject unexpected fields
- no direct path was found from reviewed input sources to shell execution
- `site/components.local.yaml` remains an explicitly trusted local operator input, not a general untrusted-content input

## Security Regression Coverage

Focused regression tests now cover the implemented protections, including:

- invalid component slug rejection
- derived-path containment for stage/preview outputs
- preview-link safety for slug-derived URLs
- preview server scoping to the preview directory
- repository link scheme safety
- runtime warnings for active local overrides

## Residual Observations

- Some generated metadata still includes absolute local filesystem paths. This is not a direct exploit path in the reviewed code, but it can leak workstation path information if generated artifacts are shared.
- `NODE_MODULES_DIR` still influences vendored asset sourcing. This remains environment-trust-sensitive rather than a direct repository-content exploit.
- `site/components.local.yaml` is intentionally trusted as a local operator-controlled input and should not be treated as untrusted content.

## Recommended Ongoing Hardening

1. Avoid writing absolute workstation paths into generated manifests unless explicitly needed.
2. Continue keeping `site/components.local.yaml` local-only and untracked.
3. Preserve the added security regression tests when refactoring build or preview code.
4. Re-run a focused security review if new preview rendering features, richer HTML templating, or new subprocess/network behavior are introduced.

## Final Assessment

The codebase is **not broadly unsafe** in the reviewed areas and currently presents a sensible set of controls around metadata loading, output-path construction, preview rendering, and preview serving.

The remaining notable concerns are lower severity and mostly operational:

- local override files are still trusted operator input
- absolute path metadata may disclose workstation layout if artifacts are shared
- environment-driven asset resolution remains sensitive to local environment trust

Overall, the current state is consistent with a **reasonably hardened trusted-workspace build pipeline**, with no known direct path in the reviewed areas to cache poisoning, arbitrary preview-script execution, arbitrary local command execution, or secret theft.
