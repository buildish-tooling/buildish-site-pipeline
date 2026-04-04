---
weight: 37
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

# How to create HTTP server config from staged metadata

This document explains how a deployment adapter can turn the pipeline's staged
route and redirect metadata into concrete HTTP server, CDN, or edge-routing
configuration.

The pipeline intentionally emits server-neutral metadata. It does not emit a
stable Apache `httpd`, Nginx, CDN, or platform-specific config format.

## What this is for

Use this guide when you want to build consumer-owned deployment config such as:

- redirect rules
- per-origin host or vhost routing
- path-ownership inventories for a published docs site

## What this is not

This guide does not define:

- a stable server-specific output format from the pipeline
- a renderer dev-server workflow
- a replacement for the renderer or site-publication layer

The pipeline owns staged content and deployment-neutral metadata. The deployment
adapter owns target-specific config generation.

## Inputs to read

Read these files in this order:

1. `manifest.json`
2. the path referenced by `manifest.dataFiles.routes`
3. the path referenced by `manifest.dataFiles.redirects`

`manifest.json` is authoritative. Do not assume `data/routes.json` or
`data/redirects.json` exist at hard-coded paths without checking the manifest.

The manifest stores stage-relative contract paths such as `data/routes.json`.
Those contract paths are POSIX strings. After resolving them against the local
stage root, normal host-native filesystem access rules apply.

## What the two aggregates mean

`routes.json` gives the resolved public route inventory. It tells you:

- which origin a route belongs to
- the resolved public `path`
- the fully qualified `url`
- whether a route is canonical, an alias, or a redirect

`redirects.json` gives the resolved redirect inventory. It is the main input for
emitting concrete redirect rules because each entry already contains:

- `fromUrl`
- `toUrl`
- `status`
- optional `reason`

Use `routes.json` to understand route ownership and origin grouping. Use
`redirects.json` to generate redirect behavior.

## Recommended adapter algorithm

1. Read `manifest.json` and resolve the declared aggregate paths under the stage
   root.
2. Load `routes.json` and `redirects.json` as JSON.
3. Group route entries by `originKey`, `baseUrl`, hostname, or another
   deployment unit that matches your hosting platform.
4. Use `routes.json` to determine which public paths belong to each published
   origin and which paths are canonical versus aliases.
5. Use `redirects.json` to emit concrete redirect rules for the matching host or
   origin.
6. Preserve the resolved redirect `status` exactly. Do not silently rewrite a
   `302` into a `301`, or a `307` into a `302`.
7. Emit target-specific syntax only at the final adapter step.

## Practical mapping guidance

For a server or CDN adapter, the usual split is:

- canonical and alias routes from `routes.json` describe the published route
  surface that the site owns
- redirect entries from `redirects.json` describe request paths that should
  return a redirect response instead of site content

If your platform needs path-only rules instead of absolute URLs, derive those
path rules from the fully qualified URLs only after grouping by the host or
origin that the adapter owns.

For example:

- if `fromUrl` is `https://docs.example.org/spark/latest/`
- and the adapter is generating config for `docs.example.org`
- then the emitted rule source path can safely be `/spark/latest/`

Do not strip hosts from redirect URLs before you know that the redirect belongs
to the current deployment target.

## Safety rules

Adapters should fail closed when staged metadata is malformed or does not match
the deployment target they are generating config for.

In particular:

- trust `manifest.json` for file presence and layout
- treat `PublicPath` values as URL paths, not local filesystem paths
- preserve redirect destinations exactly as resolved by the pipeline
- do not invent wildcard rewrites unless you can prove they preserve the staged
  semantics exactly
- reject or isolate entries whose host does not belong to the deployment target
- do not interpolate request-derived values into redirect targets

That last rule matters for security. The staged metadata already gives you a
fully resolved destination URL. Rebuilding it from request variables can create
open-redirect or host-header problems that the pipeline contract is trying to
avoid.

## What stays adapter-specific

The adapter still owns several decisions:

- Apache `httpd` versus Nginx versus CDN rule syntax
- whether one config file covers one host, one origin, or many origins
- how exact-match versus prefix-match rules are represented on the target
- how the generated config is packaged, deployed, and reloaded

Those details should stay outside the pipeline contract so the staged metadata
remains portable across hosting targets.

## Read this next

For the underlying contract details, see:

- [../v1/staged-output-contract.md](../v1/staged-output-contract.md)
- [../v1/pipeline-model-schema-reference.md](../v1/pipeline-model-schema-reference.md)
- [../v1/security-and-trust-model.md](../v1/security-and-trust-model.md)