---
title: "How to integrate Site Pipeline with Hugo"
description: "Use this guide when you want a Hugo site to render Site Pipeline staged content, staged JSON metadata, and component-aware links without hard-coding public routes."
weight: 38
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

## Keep the hand-off boundary clear

The clean split is:

- Site Pipeline validates inputs, resolves publication paths, and writes the
  staged tree under `site/.stage/`
- Hugo renders pages, applies the theme, builds navigation, and serves or
  publishes the site

That means Hugo should consume:

- staged Markdown under `site/.stage/content/`
- staged JSON under `site/.stage/data/`
- staged assets under `site/.stage/static/`

Hugo should **not** reconstruct provider state, infer routes from repository
layout, or treat internal Python objects as renderer input. The staged tree is
the supported downstream contract.

## Minimal repository shape

Start with a normal Hugo site and add the stage root alongside it:

```text
site/
  hugo.yaml
  content/
  data/
  layouts/
  static/
  assets/
  .stage/
    content/
    data/
    static/
    manifest.json
```

The local Hugo directories are still useful:

- `content/` for consumer-owned landing pages, section roots, or cascades
- `data/` for helper files such as slug-to-repository maps
- `layouts/` and `assets/` for renderer-specific templates and styling
- `static/` for site-owned assets that are not staged by the pipeline

## The main change from a vanilla `hugo.yaml`

Do **not** point `contentDir` directly at `.stage/content`. That throws away the
local `content/`, `data/`, and `static/` roots that most Hugo sites still need.

Instead, switch to explicit mounts and merge the local roots with the staged
roots:

```yaml
baseURL: https://docs.example.org/
title: Example Docs

module:
  mounts:
    # Keep consumer-authored section roots and cascades.
    - source: content
      target: content
    # Add staged component and docs pages.
    - source: .stage/content
      target: content

    # Expose pipeline-generated aggregate JSON files.
    - source: .stage/data
      target: data
    # Keep consumer-owned helper data such as component_repos.json.
    - source: data
      target: data

    # Publish staged component assets.
    - source: .stage/static
      target: static
    # Keep site-owned static files.
    - source: static
      target: static

    # Renderer-owned templates and Hugo Pipes inputs.
    - source: layouts
      target: layouts
    - source: assets
      target: assets
```

Two important details:

1. `source` is the real directory on disk. `target` is the Hugo virtual root
   where that directory should appear.
2. Entries where `source == target` are intentional. Once you opt into explicit
   mounts, Hugo no longer assumes its implicit default roots. Any local root you
   still want Hugo to see must be mounted again explicitly.

If your site imports a theme as a Hugo module, keep the existing `module.imports`
configuration and add these mounts alongside it.

## Keep the Hugo version boundary explicit

Site Pipeline writes renderer-neutral files and does not execute Hugo, so it
does not impose a Hugo version requirement. The sibling Buildish site currently
declares Hugo Extended 0.160.1 as its minimum and uses the integration pattern
shown here. Treat that as a known consumer baseline, not as a Site Pipeline
minimum; your theme and Hugo configuration may require a different version.

## Recommended local development loop

Use Site Pipeline to keep the stage fresh, and let Hugo keep owning the preview
server and live reload loop.

Validation and one-off stage refresh:

```bash
site-pipeline check --workspace-root . --catalog site/catalog.yaml
site-pipeline build --workspace-root . --catalog site/catalog.yaml
```

Hugo preview:

```bash
hugo server --source site --config site/hugo.yaml
```

Live editing usually means two terminals:

```bash
# terminal 1
site-pipeline watch --workspace-root . --catalog site/catalog.yaml

# terminal 2
hugo server --source site --config site/hugo.yaml
```

There is intentionally no `site-pipeline serve` command. The pipeline owns the
staged output; the renderer owns the dev server.

## Optional: wrap watch + Hugo in a `serve-local` target

Once the two-terminal loop is working, many teams add one consumer-side target
that coordinates both processes. The Buildish site does exactly that in its
own `site/Makefile`.

The pattern is straightforward:

1. start `site-pipeline watch` in the background
2. write watch events to a temporary JSONL file
3. wait until the watcher reports a ready stage
4. launch `hugo server`
5. kill the watcher and delete the temporary events file when Hugo exits

A compact sketch looks like this:

```make
serve-local:
	@watch_pid=''; events_file=''; \
	cleanup() { status=$$?; if [ -n "$$watch_pid" ] && kill -0 "$$watch_pid" 2>/dev/null; then kill "$$watch_pid" 2>/dev/null || true; wait "$$watch_pid" 2>/dev/null || true; fi; if [ -n "$$events_file" ]; then rm -f "$$events_file"; fi; exit $$status; }; \
	trap cleanup EXIT INT TERM; \
	events_file="$$(mktemp .watch-events.XXXXXX.jsonl)"; \
	site-pipeline watch --workspace-root . --catalog site/catalog.yaml --unstable-events jsonl --unstable-events-output "$$events_file" & \
	watch_pid=$$!; \
	wait-for-watch-ready --events-file "$$events_file" --pid "$$watch_pid" --timeout 60; \
	hugo server --source site --config site/hugo.yaml --renderToMemory
```

Two details matter in practice:

- wait for watcher readiness before starting Hugo, otherwise the first page load
  may race the initial stage
- make cleanup explicit, otherwise the watch process may keep running after the
  preview server exits

`wait-for-watch-ready` is only a placeholder command name in this sketch. In the
Buildish site the consumer repo [owns that helper](https://github.com/buildish-tooling/buildish/tree/main/site/scripts/wait_for_watch_ready.py)
as `site/scripts/wait_for_watch_ready.py`, and the helper waits for the first
usable `ready` event in the JSONL stream written by `--unstable-events-output`.
If you do not already have such a helper, add a small wrapper that blocks until
the first ready event before launching Hugo.

This section is intentionally about consumer ergonomics, not about the pipeline
contract itself. The contract is still the same: Site Pipeline stages content,
and Hugo serves the rendered site.

## Use `manifest.json` for discovery, not for templates

`site/.stage/manifest.json` is the discovery entry point for wrapper scripts,
build tooling, or deployment adapters. It tells you where the stage roots and
aggregate files live for this stage.

Do **not** treat it as normal template data. In Hugo templates, render from the
staged pages and the aggregate JSON files instead.

## Read staged front matter directly from pages

Every staged page carries normalized `pipeline` front matter. One real example
looks like this:

```yaml
pipeline:
  component:
    slug: site-pipeline
    displayName: Site Pipeline
    publication:
      paths:
        component: /components/site-pipeline/
        docs: /components/site-pipeline/development/
  page:
    kind: component-page
    path: /components/site-pipeline/_index
    canonicalUrl: https://docs.example.org/components/site-pipeline/_index
```

That means a Hugo layout can learn the component identity, route shape, and page
kind without reverse-engineering file paths.

One practical template pattern is:

```go-html-template
{{ $pipeline := index .Params "pipeline" }}
{{ with $pipeline }}
  {{ $component := index . "component" }}
  {{ $page := index . "page" }}
  <p class="eyebrow">{{ or (index $component "displayName") (humanize (index $component "slug")) }}</p>
  {{ with index $page "version" }}
    <p class="text-muted">Version: {{ index . "label" }}</p>
  {{ end }}
{{ end }}
```

This is the simplest way to make page chrome react to the staged publication
model.

## Normalize component context once in a helper partial

The Buildish site uses a dedicated partial to normalize page metadata before any
breadcrumb, list, or shortcode tries to render it.

That helper does three useful things:

- reads `pipeline.component` and `pipeline.page` from front matter
- normalizes paths from either `component.paths` or
  `component.publication.paths`
- joins consumer-owned helper data, such as a slug-to-repository map in
  `data/component_repos.json`

That pattern is worth copying. It keeps compatibility logic in one place and
makes the rest of the templates much simpler.

## Make title and description fallbacks explicit

Landing pages, section cards, and breadcrumbs should prefer authored page
metadata first, then fall back to pipeline-derived metadata.

The Buildish site uses this pattern in its resolved title and description
partials:

- prefer `.Title` and `.Description` when authors set them
- then try `pipeline.page.derivedTitle` and `pipeline.page.derivedDescription`
- then fall back to `pipeline.component.displayName`
- finally fall back to a slug or path-derived label

Using one shared fallback helper for page `<title>`, breadcrumb labels, and
section cards prevents blank navigation labels when staged pages rely on derived
metadata.

## Read aggregate JSON through `hugo.Data`

The staged `data/*.json` files answer cross-page questions that page front
matter cannot answer by itself.

Useful aggregates include:

- `components.json` for component inventories and publication paths
- `content-index.json` for cross-page discovery
- `routes.json` for the published route inventory
- `redirects.json` for redirect behavior

In modern Hugo, prefer `hugo.Data` over `.Site.Data`.

One practical component-grid example is:

```go-html-template
{{ $components := index (index hugo.Data "components") "items" }}
{{ range $component := $components }}
  {{ $paths := index (index $component "publication") "paths" }}
  <div class="entry">
    <h3><a href="{{ index $paths "component" }}">{{ index $component "displayName" }}</a></h3>
  </div>
{{ end }}
```

For file names that contain a hyphen, use `index` explicitly:

```go-html-template
{{ $contentIndex := index (index hugo.Data "content-index") "items" }}
{{ $currentSlug := index (index (index .Params "pipeline") "component") "slug" }}
<ul>
  {{ range $entry := $contentIndex }}
    {{ if eq (index $entry "componentSlug") $currentSlug }}
      <li><a href="{{ index $entry "path" }}">{{ index $entry "title" }}</a></li>
    {{ end }}
  {{ end }}
</ul>
```

This is a good way to build component landing pages, section indexes, or custom
search/bootstrap data without scanning the whole content tree yourself.

## Keep consumer-owned data separate from pipeline-owned data

The Buildish site keeps a local `site/data/component_repos.json` file with a
simple component-slug to repository-URL mapping. The template helper merges that
consumer-owned file with the staged pipeline metadata.

That is a useful general rule:

- let the pipeline own normalized publication and lifecycle metadata
- let the consumer site own renderer-specific or branding-specific helper data
- avoid filename collisions between local `data/` files and staged aggregate
  files

## Turn repeated component links into shortcodes

If authors frequently need links such as “Overview”, “Read docs”, or “Source
repository”, do not hard-code those URLs into Markdown. Read them from pipeline
metadata.

The Buildish site wraps this in shortcodes backed by the shared component
context helper. A small example looks like this:

```go-html-template
{{- $component := or .Page.Params.sitePipelineComponent (index (index .Page.Params "pipeline") "component") -}}
{{- $paths := index (index $component "publication") "paths" -}}
{{- $kind := or (.Get "kind") "docs" -}}
{{- $label := or (.Get "label") "Read docs" -}}
{{- $href := index $paths $kind -}}
{{- with $href -}}
  <a href="{{ . }}">{{ $label }}</a>
{{- end -}}
```

This keeps authored Markdown clean and makes route changes flow through the
renderer automatically when publication paths change.

## Render release summaries from staged metadata

If your component metadata includes version lines or latest-stable information,
prefer a small helper or shortcode that reads the staged artifact metadata
instead of hard-coding release banners into content.

The Buildish site uses this pattern to render release summaries from
`pipeline.component.artifacts[*].releaseLines` and `latestStable`, while still
rendering nothing when a component does not publish release-line metadata yet.

That “optional when absent” behavior is important when one renderer template is
shared by both versioned and non-versioned components.

## Deployment hand-off

For CI or publication jobs, the simplest contract is still:

```bash
site-pipeline build --workspace-root . --catalog site/catalog.yaml
hugo --source site --config site/hugo.yaml
```

Deployment adapters may additionally read `manifest.json`, `routes.json`, or
`redirects.json`, but the Hugo render itself should continue to use staged pages,
staged data, and staged assets as its direct inputs.

## What to copy first

If you are integrating Hugo for the first time, the highest-value pieces to copy
from the Buildish site are:

1. explicit `module.mounts` for local + staged roots
2. one shared component-context partial
3. one shared title/description fallback helper
4. one or two shortcodes for component-aware links
5. one component-grid or section-index template that reads `components.json` or
   `content-index.json`

That gives you a working renderer integration without pushing Hugo-specific
logic back into the pipeline or hard-coding public URLs in page content.

## Read this next

- [Inspect staged output and routes](../inspect-staged-output-and-routes/)
- [Staged output and consumers](../../concepts/staged-output-and-consumers/)
- [Create a tiny site](../create-a-tiny-site/)
- [Staged output contract](../../development/reference/staged-output-contract/)
- [Pipeline model schema reference](../../development/reference/pipeline-model-schema-reference/)
