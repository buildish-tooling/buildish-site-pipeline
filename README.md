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

# Site Pipeline

Buildish Site Pipeline packages a reusable staging pipeline for
multi-repository documentation sites. It discovers component checkouts from a
consumer-owned catalog, validates the content contract, stages normalized site
inputs, and emits metadata that a downstream renderer can consume. The CLI also
exposes `site-pipeline component-source-roots` for local wrappers that need the
effective component source-root locators.

The project has not published a release yet. The source checkout and moving
development container described below are for evaluation and development, not
versioned release coordinates.

## What it includes

- the `buildish_site_pipeline` Python package,
- the `site-pipeline` CLI entrypoint,
- a multi-platform container definition and CI publication workflow for
  `site-pipeline`,
- reader and maintainer pages under `site/pages/`,
- development and reference docs under `docs/`, and
- a small self-contained generic test suite.

## What the pipeline owns

- catalog and component-metadata interpretation,
- workspace path validation and safety checks,
- normalized staged content, data, and static outputs, and
- check, plan, build, and watch workflows.

## What the consumer owns

- component inventory and repository layout,
- top-level site content,
- renderer choice, templates, navigation, and branding, and
- publishing and release workflows.

## Quick start from a source checkout

Site Pipeline does not currently document a package-index installation
coordinate. The reproducible first-use path is a source checkout with
[uv](https://docs.astral.sh/uv/) and Python 3.13 or newer:

```bash
git clone https://github.com/buildish-tooling/buildish-site-pipeline.git
cd buildish-site-pipeline
uv sync --frozen
SITE_PIPELINE="$PWD/.venv/bin/site-pipeline"
"$SITE_PIPELINE" --help
```

Keep that shell open and move to the consumer workspace you want to stage. The
smallest useful workspace has a consumer-owned `site/catalog.yaml` and at least
one component source tree:

```text
consumer-workspace/
  site/
    catalog.yaml
  components/
    runtime/
      docs/
```

The [tiny-site guide](site/pages/how-to/create-a-tiny-site.md) contains a
copyable catalog and authored page. After creating those inputs, run from the
consumer workspace root:

```bash
cd /path/to/consumer-workspace
"$SITE_PIPELINE" check
"$SITE_PIPELINE" build
```

Both commands default to the current directory as `--workspace-root` and to
`site/catalog.yaml` below that root. `check` validates without writing the stage;
`build` writes the renderer hand-off under `site/.stage/`. For a split checkout
layout, select both inputs explicitly:

```bash
"$SITE_PIPELINE" build \
  --workspace-root /workspace \
  --catalog /workspace/buildish-site/site/catalog.yaml
```

Point the downstream renderer at the completed staged outputs rather than at
the component repositories. Site Pipeline deliberately does not include a
preview server; the renderer owns preview and publication.

If Site Pipeline is already installed in a consumer environment, use
`site-pipeline` in place of `"$SITE_PIPELINE"`. Maintainers can also create a
uniquely versioned local wheel with `make publish-snapshot-local`; see
[Local wheel snapshots](#local-wheel-snapshots).

Human-facing diagnostics use a centralized CLI logger. Use `--quiet`,
`--verbose`, or `--debug` on commands such as `site-pipeline watch` to adjust
stderr log detail without changing explicit report or JSONL event outputs.

## Documentation

- [Component website](https://buildish.org/components/site-pipeline/)
- [Component landing page](site/pages/_index.md)
- [Getting started](site/pages/getting-started/_index.md)
- [How-to guides](site/pages/how-to/_index.md)
- [Architecture docs](site/pages/architecture/_index.md)
- [Reference docs](docs/reference/_index.md)
- [Versioned docs landing](docs/_index.md)
- [Maintenance notes](site/pages/maintenance/_index.md)

Project-wide guidance is available from the Buildish
[community](https://buildish.org/community/), including the
[Code of Conduct](https://github.com/buildish-tooling/buildish/blob/main/CODE_OF_CONDUCT.md),
[security reporting process](https://buildish.org/community/security/), and
[license information](https://buildish.org/community/license/).

## Local development

See [CONTRIBUTING.md](CONTRIBUTING.md) for prerequisites and focused workflows.
Run the complete repository gate with:

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

The output is intentionally **preliminary**. It is meant to speed up
release-legal review, not to replace human review of license compatibility,
bundled notices, or final `LICENSE` / `NOTICE` wording.

The checked-in container-image legal payload lives separately under
`dist-release-legal/`. Maintainer workflow details are documented in
`docs/maintenance/release-legal.md`.


## Container image

The canonical repository's CI is configured to publish the renderer-agnostic
`ghcr.io/buildish-tooling/buildish-site-pipeline:latest` image after checks pass
on `main`. Its entrypoint is `site-pipeline`.

`latest` is a moving development image, not a versioned release coordinate.
Verify registry access and pin an immutable digest before relying on it in a
production workflow. The source-checkout path above remains the canonical
first-use route while release distribution is being adopted.

That image is intended primarily for CI or other container-first environments.
Consumers that also need Hugo, Node, or site-specific publishing helpers should
build their own derived images on top of this base image rather than asking the
generic pipeline image to own renderer-specific tooling.

Local image build/publish helpers live under `tools/site-pipeline-image/`.
