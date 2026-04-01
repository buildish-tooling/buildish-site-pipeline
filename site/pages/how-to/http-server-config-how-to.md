---
title: "How to create HTTP server config from staged metadata"
description: "Generate exact Apache httpd redirects from staged metadata, or choose an explicit fallback for static-only hosts such as GitHub Pages."
weight: 37
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

Site Pipeline resolves redirects, but deliberately stops before choosing a web
server, CDN, or edge-platform syntax. A deployment adapter reads the completed
stage and turns its server-neutral redirect inventory into configuration for
one deployment target.

This guide gives you a tested Apache httpd adapter and explains what changes
when the deployment target is GitHub Pages.

## Before you start

You need:

- a successful `site-pipeline build` and its completed stage directory;
- Python 3.13 or newer to run the copyable reference adapter; and
- for the Apache path, control of an Apache httpd 2.4 server or virtual-host
  configuration with `mod_rewrite` enabled.

The example emits a config fragment. Your deployment still owns where that
fragment is installed, how `httpd` configuration is tested, and when the server
is reloaded.

## Understand the adapter boundary

The adapter starts at `manifest.json`. It follows
`manifest.dataFiles.redirects` instead of assuming that the aggregate always
lives at `data/redirects.json`.

For example, the manifest may contain:

```json
{
  "schemaVersion": 1,
  "stageLayoutVersion": 1,
  "aggregateFormat": "json",
  "dataFiles": {
    "redirects": "data/redirects.json"
  }
}
```

The referenced aggregate contains already-resolved absolute URLs:

```json
{
  "items": [
    {
      "fromUrl": "https://docs.example.org/spark/development/docs/",
      "toUrl": "https://docs.example.org/spark/releases/4.0.0/",
      "status": 308,
      "reason": "The released documentation has a stable URL.",
      "sourceKind": "catalog"
    }
  ]
}
```

`routes.json` remains useful for route ownership, origin grouping, and
canonical-route inspection. Concrete redirect behavior comes from
`redirects.json`; the adapter does not infer redirects from aliases in the route
inventory.

## Generate an Apache httpd fragment

The repository contains a
[copyable standard-library adapter](https://github.com/buildish-tooling/buildish-site-pipeline/blob/main/examples/apache_httpd/generate_redirects.py).
From a Site Pipeline source checkout, run it once per deployed source origin.
The origin includes the scheme and optional non-default port, so HTTP and HTTPS
redirect inventories cannot be collapsed accidentally:

```bash
uv run --frozen python examples/apache_httpd/generate_redirects.py \
  /workspace/site/.stage \
  https://docs.example.org \
  /workspace/build/httpd/docs-example-redirects.conf
```

The output for the aggregate above is:

```apache
# Generated from Site Pipeline staged redirect metadata.
# Target source origin: https://docs.example.org
# Include in server or VirtualHost context; do not use in .htaccess.
RewriteEngine On

RewriteCond "%{HTTPS}" "^on$" [NC]
RewriteCond "%{HTTP_HOST}" "^docs\.example\.org(?::443)?$" [NC]
RewriteRule "^/spark/development/docs/$" "https://docs.example.org/spark/releases/4.0.0/" [R=308,L,NE,QSD]
```

Include the generated file from server or `VirtualHost` context, for example:

```apache
<VirtualHost *:443>
    ServerName docs.example.org
    Include /workspace/build/httpd/docs-example-redirects.conf

    # TLS and document-root configuration stay consumer-owned.
</VirtualHost>
```

Then use your installation's configuration test before deployment, commonly:

```bash
apachectl configtest
```

The generated rules are deliberately exact:

- scheme, hostname, effective port, and source path are all preserved;
- the `%{HTTPS}` guard separates HTTP from HTTPS, while the `HTTP_HOST` guard
  accepts either an omitted default port or that origin's exact default port;
- a non-default source port is matched exactly;
- each staged `301`, `302`, `307`, or `308` status is retained;
- `QSD` prevents an incoming query string from being appended when the staged
  destination has no query; and
- `NE` keeps an already-resolved destination URL from being escaped again.

Apache documents that a `RewriteRule` in server or `VirtualHost` context sees
the URL path with its leading slash. That differs from per-directory and
`.htaccess` matching, which is why the generated fragment must not be moved to
`.htaccess`. See the
[Apache `RewriteRule` matching documentation](https://httpd.apache.org/docs/current/mod/mod_rewrite.html#rewriterule)
and the [`mod_rewrite` flag reference](https://httpd.apache.org/docs/current/rewrite/flags.html).

The HTTPS guard describes the connection Apache sees. If TLS terminates at a
proxy and Apache receives plain HTTP, this reference fragment intentionally
does not guess from forwarded headers. Adapt the scheme condition to your
trusted proxy setup and test it end to end before deployment.

The simpler Apache [`Redirect`
directive](https://httpd.apache.org/docs/current/mod/mod_alias.html#redirect)
uses path-prefix mapping in its common form. Emitting that form for a staged
exact path could redirect additional requests, so the reference adapter uses
anchored rewrite rules instead.

## Know what the reference adapter rejects

The adapter validates the entire redirect aggregate before it writes output. It
fails without replacing an existing output file when it encounters:

- a missing, malformed, symlinked, or escaping manifest/aggregate path;
- an unsupported manifest schema, stage layout, or aggregate format;
- a redirect status other than `301`, `302`, `307`, or `308`;
- duplicate source paths for the same scheme, hostname, and effective port;
- a source URL with a query, fragment, non-normalized path, non-ASCII path, or
  percent-encoded path;
- a malformed requested source origin or one with no redirects; or
- URL text that could be interpreted as Apache configuration, a rewrite
  backreference, or a rewrite-map/server-variable expansion.

The ASCII and percent-encoding restrictions are conservative. Apache matches a
decoded URL path in server context; guessing how an encoded source path should
map could broaden or break a rule. If a real deployment needs such paths,
extend the adapter together with target-server integration tests.

Destinations may point to a different host. They remain fixed absolute URLs
from staged metadata; the adapter never reconstructs them from request headers
or request variables.

## Use the same contract with another server or CDN

Keep the discovery and validation steps the same:

1. Read `manifest.json`.
2. Resolve `manifest.dataFiles.redirects` beneath the stage root.
3. Validate the redirect aggregate.
4. Select entries for one deployment source origin, including scheme and port.
5. Preserve each source path, destination URL, and status.
6. Render only syntax whose exact-match behavior is understood and tested for
   the target.

Do not discard schemes or ports before selecting the deployment target,
silently rewrite status codes, invent wildcard rules, or rebuild destinations
from `Host` or other request-derived values.

## Deploying on GitHub Pages

GitHub Pages deploys a static site artifact. A custom Actions workflow can run a
renderer or adapter while building that artifact, but it does not add an Apache
configuration layer to the Pages service. GitHub documents the artifact-based
custom workflow in [Using custom workflows with GitHub
Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

Choose between two materially different outcomes:

### Generate static fallback pages

A build adapter can create an HTML file at every staged source path. The file
can contain a canonical link, a visible destination link, and optional browser
navigation through a refresh element or script.

This is a fallback page, not an HTTP redirect. The initial response is a normal
static-page response, so it cannot preserve the staged `301`, `302`, `307`, or
`308` status or their method-handling semantics. Browsers, crawlers, caches, and
API clients may therefore behave differently. A Pages adapter should report
that loss explicitly, and a deployment that requires status fidelity should
reject this mode.

### Put redirect rules at an external edge

If the status codes are part of the publication contract, place a CDN, reverse
proxy, or other programmable edge in front of the static site. That adapter can
consume the same `redirects.json`, return the declared status, and send all
non-redirect requests to Pages.

GitHub Pages' automatic custom-domain redirects cover paired domain forms such
as an apex domain and its `www` variant. They are not a replacement for the
per-path redirect inventory described here. See [Managing a custom domain for
your GitHub Pages
site](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site#configuring-an-apex-domain-and-the-www-subdomain-variant).

## Check the result

For an Apache deployment, verify at least:

- `apachectl configtest` succeeds;
- every generated rule appears under the intended source origin;
- a representative redirect returns its staged status and exact `Location`;
- a longer path sharing the same prefix does not redirect; and
- an unrelated scheme, hostname, or port does not receive the rule.

For GitHub Pages, document whether the deployment chose degraded static
fallback pages or an external status-preserving edge. Do not describe the first
option as equivalent to the second.

## Read this next

- [Inspect staged output and routes](../inspect-staged-output-and-routes/)
- [Unreleased development staged-output
  contract](../../development/reference/staged-output-contract/)
- [Unreleased development security and trust
  model](../../development/reference/security-and-trust-model/)
