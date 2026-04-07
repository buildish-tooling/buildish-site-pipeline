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

# Site Pipeline

Apache Buildish Site Pipeline packages a reusable staging pipeline for
multi-repository documentation sites. It discovers component checkouts from a
consumer-owned catalog, validates the content contract, stages normalized site
inputs, and emits metadata that a downstream renderer can consume.

## What it includes

- the `apache_buildish_site_pipeline` Python package,
- the `site-pipeline` CLI entrypoint,
- an optional multi-platform container image that runs `site-pipeline`,
- reader and maintainer pages under `site/pages/`,
- stable reference and versioned docs under `docs/`, and
- a small self-contained generic test suite.

## What the pipeline owns

- catalog and component-metadata interpretation,
- workspace path validation and safety checks,
- normalized staged content, data, and static outputs, and
- build, clean, watch, and preview workflows.

## What the consumer owns

- component inventory and repository layout,
- top-level site content,
- renderer choice, templates, navigation, and branding, and
- publishing and release workflows.

## Quick start

1. Either add the package to the consumer site's Python environment or use the published container image in CI.
2. Create a component catalog, defaulting to `site/components.yaml`.
3. Provide per-component `site/component.yaml`, `site/pages/`, `site/docs/`,
   and optional `site/assets/` inputs.
4. Keep any machine-local checkout remapping in `site/components.local.yaml`
   only; it should remain untracked.
5. Run `site-pipeline build --repo-root <consumer-repo>`.
6. Point the downstream renderer at the staged outputs under `site/.stage/`.

`site-pipeline preview` is also available for a deliberately barebones preview,
but it is far away from a real rendered website.

Human-facing diagnostics use a centralized CLI logger. Use `--quiet`,
`--verbose`, or `--debug` on commands such as `site-pipeline watch` to adjust
stderr log detail without changing explicit report or JSONL event outputs.

## Documentation

- [Component landing page](site/pages/_index.md)
- [Getting started](site/pages/getting-started/_index.md)
- [How-to guides](site/pages/how-to/_index.md)
- [Architecture docs](site/pages/architecture/_index.md)
- [Reference docs](docs/reference/_index.md)
- [Versioned docs landing](docs/_index.md)
- [Maintenance notes](site/pages/maintenance/_index.md)

## Local development

Run the extracted repo checks with:

- `make check`

## Local wheel snapshots

Build a uniquely versioned local wheel snapshot with:

- `make publish-snapshot-local`

By default this writes wheels plus `dist/snapshots/latest.json`. That manifest
includes the exact `file://` dependency spec a local consumer can use while the
project is still only being shared on one machine.

## Preliminary release-legal drafts

Generate a review-oriented legal bundle for the runtime dependency set with:

- `make release-legal-preliminary`

By default this writes generated preliminary `LICENSE` and `NOTICE` drafts under
`dist-release-legal/preliminary/`.

The larger generated review bundle stays under `dist/release-legal-preliminary/`
and includes `inventory.json`, `inventory.md`, and copied per-package legal
files.

The helper derives the runtime package set from `uv.lock` via
`uv export --no-dev --frozen`, then inspects the installed Python distributions
available to the current interpreter.

The output is intentionally **preliminary**. It is meant to speed up ASF
release-legal review, not to replace human review of license compatibility,
bundled notices, or final `LICENSE` / `NOTICE` wording.

The checked-in container-image legal payload lives separately under
`dist-release-legal/`. Maintainer workflow details are documented in
`docs/maintenance/release-legal.md`.


## Container image

The repository also publishes a renderer-agnostic container image whose entrypoint is `site-pipeline`.

That image is intended primarily for CI or other container-first environments. Consumers that also need Hugo, Node, or site-specific publishing helpers should build their own derived images on top of this base image rather than asking the generic pipeline image to own renderer-specific tooling.

Local image build/publish helpers live under `tools/site-pipeline-image/`.
