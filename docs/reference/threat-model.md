---
title: "Threat model"
description: "Threat model for the Site Pipeline CLI, staged outputs, and supported trust boundaries."
weight: 17
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

## §1 Header

Project: Buildish Site Pipeline.

Version binding: this threat model is versioned alongside the project. A report
against project version N is triaged against the threat model shipped with
version N, not against the model at a later development commit. *(documented)*

Version and commit: draft for `buildish-site-pipeline` `0.1.0` at commit
`467558fffb31`. *(documented)*

Date: 2026-06-05. *(documented)*

Authors: Buildish maintainers; initial structured draft prepared by
Codex from repository documentation and source review. *(inferred)*

Reporting cross-reference: findings that fall under §8 should be reported per
this repository's `SECURITY.md` disclosure channel; findings that fall under §3
or §9 may be closed by citing this document. *(documented)*

Status: draft, pending maintainer review as of 2026-06-05. *(inferred)*

Provenance legend: *(documented)* means supported by repository documentation or
code; *(maintainer)* means confirmed by a maintainer; *(inferred)* means a draft
claim derived from current structure and requiring confirmation.

Draft confidence: approximately 48 documented / 0 maintainer / 29 inferred
claims. Counts are intentionally rough and should be updated when maintainers
ratify or correct the open questions in §14.

Buildish Site Pipeline is a Python CLI and package for staging
multi-repository documentation-site inputs into a normalized tree and metadata
set for downstream renderers. It reads a consumer-owned catalog, optional
provider snapshots, component metadata, site pages, docs, and static assets;
validates the structural contract; stages normalized outputs; and emits reports
and aggregate JSON files that renderers and deployment adapters consume.
*(documented)*

## §2 Scope and intended use

Primary intended use cases:

- Validate a trusted workspace's site catalog, component metadata, publication
  model, paths, routes, redirects, and provider-derived inputs before staging.
  *(documented)*
- Build a staged output tree under `site/.stage/` for a downstream renderer or
  deployment adapter. *(documented)*
- Keep staged outputs fresh during local editing with `site-pipeline watch`.
  *(documented)*
- Expose effective component source roots for local wrappers or container mount
  orchestration through `site-pipeline component-source-roots`. *(documented)*
- Provide JSON Schema and reference documentation for authored, provider, and
  emitted pipeline contracts. *(documented)*

Deployment contexts:

- Local developer workstation CLI. *(documented)*
- CI CLI, either from a Python environment or the optional container image.
  *(documented)*
- In-process Python imports are implementation detail unless a specific model or
  helper is documented as a public contract. The stable invocation API is the
  `site-pipeline` executable. *(documented)*
- This project is not a network service, daemon, browser sandbox, or renderer.
  *(documented)*

Caller and actor expectations:

- The operator invoking the CLI is trusted for the workspace and output
  location. *(documented)*
- Repository-authored catalog and component files may be reviewed project input,
  but are not assumed to be safe HTML or safe filesystem paths until validated.
  *(documented)*
- Provider snapshots are external data inputs and are validated as data, not
  trusted code. *(documented)*
- Downstream renderers and deployment adapters are separate trusted components
  responsible for HTML escaping, browser-origin policy, CSP, cookies, storage,
  and publication. *(documented)*

Component-family table:

| Family | Representative entry point | External surface touched | In model? | Notes |
| --- | --- | --- | --- | --- |
| CLI control plane | `site-pipeline plan`, `check`, `build`, `watch`, `component-source-roots` | Filesystem, process stdout/stderr, signals for watch | Yes | Stable invocation API. *(documented)* |
| Document loading and models | `load_site_catalog_document`, `load_provider_snapshot_document`, Pydantic models | YAML/JSON bytes, validation schemas | Yes | Safe loader, duplicate-key rejection, strict models. *(documented)* |
| Planning and evaluation | `evaluate_planning`, `run_evaluation` | In-memory model data, workspace paths | Yes | Computes diagnostics, routes, publication decisions, limits. *(documented)* |
| Staging and publication | `publish_stage`, `finalize_stage_publication` | Filesystem reads and writes under source roots and stage roots | Yes | Includes containment and symlink checks. *(documented)* |
| Watch mode | `site-pipeline watch` | Filesystem watcher, stdout/stderr/events, signals | Yes | Local development and wrapper integration surface. *(documented)* |
| Staged output contracts | `site/.stage/`, `manifest.json`, `data/*.json`, staged pages/assets | Filesystem output consumed by renderers | Yes | Stable output API. *(documented)* |
| Optional container image | `tools/site-pipeline-image/*`, published image entrypoint | Container build/runtime environment | Partly | In scope for packaging expectations; base-image and registry security are out of scope. *(inferred)* |
| Release-legal helpers | `make release-legal-preliminary`, `buildish_site_pipeline.legal.release_legal` | Local Python environment, package metadata, subprocess execution | Partly | In scope for repository maintenance safety; not part of normal site staging threat boundary. *(inferred)* |
| Tests, docs, generated schemas | `tests/`, `docs/`, `site/pages/schemas/` | Repository files | No for runtime guarantees | Useful evidence, but not runtime security boundary. *(inferred)* |

## §3 Out of scope

Explicit non-goals:

- Making malicious authored HTML, JavaScript, CSS, or renderer templates safe to
  publish. Imported active content is trusted browser-executable code.
  *(documented)*
- Providing authentication, authorization, secrets management, or tenant
  isolation for published sites. *(documented)*
- Securing the downstream renderer, web server, CDN, browser origin, CSP, cookie
  scope, storage scope, or deployment adapter. *(documented)*
- Defending against an attacker who controls the local process, Python
  environment, installed dependencies, shell, container runtime, CI runner, or
  host filesystem permissions. *(inferred)*
- Treating `site/components.local.yaml` or equivalent local overrides as
  untrusted content. They are local operator-controlled inputs. *(documented)*
- Fetching, authenticating, or verifying source repositories, SCM state, or
  provider APIs. The pipeline consumes local inputs and provider snapshots.
  *(documented)*
- Guaranteeing that generated preliminary release-legal drafts replace human
  release review. *(documented)*
- Treating test fixtures, generated outputs, `dist/`, `.venv/`, caches, and
  local build artifacts as covered runtime components. *(inferred)*
- Security of third-party dependencies beyond normal dependency-management and
  release processes. *(inferred)*
- Security of non-default or locally modified builds that bypass validation,
  monkeypatch internals, or call private Python functions directly. *(inferred)*

## §4 Trust boundaries and data flow

The primary trust boundary is the CLI boundary plus the declared workspace and
stage-root filesystem boundaries. CLI-local arguments are trusted operator
choices; authored and provider documents are parsed as untrusted data and must
pass schema, path, route, URL, publication, and size validation before their
values influence staged outputs. *(documented)*

Data flow:

1. The operator invokes `site-pipeline` with command arguments and optional
   report/event sinks. *(documented)*
2. The CLI resolves workspace, catalog, stage, work, report, and watch-event
   paths relative to the current process and rejects unsafe output combinations.
   *(documented)*
3. Catalog, provider snapshot, and component metadata files are read as UTF-8,
   parsed with safe YAML or JSON loaders, rejected on duplicate keys, and loaded
   into strict Pydantic models. *(documented)*
4. Planning resolves component source roots, publication paths, routes,
   redirects, provider references, limits, and diagnostics. *(documented)*
5. `check` stops after validation and report emission; `build` and `watch`
   publish a staged tree only when the stage gate allows it. *(documented)*
6. Staging copies authored pages/assets and emits normalized front matter,
   manifests, reports, and aggregate JSON files under the stage root.
   *(documented)*
7. A downstream renderer consumes the staged tree and is responsible for HTML
   rendering and browser-facing security policy. *(documented)*

Reachability preconditions:

| Component family | In-model finding must be reachable from |
| --- | --- |
| CLI control plane | A supported `site-pipeline` command using documented flags and normal process streams. *(documented)* |
| Document loading and models | Authored catalog/component files, provider snapshot files, or emitted contract files parsed by public loaders. *(documented)* |
| Planning and evaluation | Valid or invalid loaded model data plus workspace paths accepted by CLI layout resolution. *(documented)* |
| Staging and publication | A `build` or `watch` path whose evaluation stage gate reaches publication. *(documented)* |
| Watch mode | A supported watch invocation, watched filesystem changes, or configured report/event sinks. *(documented)* |
| Staged output contracts | Data emitted by the pipeline and consumed according to documented staged-output contracts. *(documented)* |
| Optional container image | The published generic image running the documented `site-pipeline` entrypoint. *(inferred)* |
| Release-legal helpers | Maintainer-invoked release-legal commands, not ordinary site staging commands. *(inferred)* |

## §5 Assumptions about the environment

Runtime assumptions:

- Python 3.13 or newer is available. *(documented)*
- The process can read declared local inputs and write configured reports,
  work roots, and stage roots. *(inferred)*
- Filesystem semantics are close enough to `pathlib.Path.resolve()` and
  `is_relative_to()` expectations for containment checks to be meaningful.
  *(inferred)*
- The operator controls CLI arguments, local overrides, and output destinations.
  *(inferred)*
- The workspace may contain symlinks, but output targets and staged trees must
  satisfy the project's symlink-safety checks. *(documented)*
- Watch mode assumes local filesystem event delivery by `watchfiles` and handles
  `SIGINT`/`SIGTERM` for shutdown. *(documented)*
- The project does not assume concurrent writes by multiple independent pipeline
  processes to the same stage/work root are safe. *(inferred)*

No-surprise side effects inventory for the normal staging CLI:

- Reads local files under configured workspace/source roots and selected catalog
  or provider-snapshot paths. *(documented)*
- Writes reports to stdout or configured report paths, and watch events to stdout
  or configured event paths. *(documented)*
- Writes and replaces staged output under the configured stage root for `build`
  and `watch`. *(documented)*
- Writes transient work data under the configured work root during staging.
  *(documented)*
- Does not fetch source repositories, provider APIs, or remote content during
  `plan`, `check`, `build`, or `watch`. *(documented)*
- Does not execute renderer commands, shell snippets, or repository-authored
  scripts as part of the stable staging commands. *(inferred)*
- Does not open listening network sockets in the stable CLI surface described by
  this model. *(inferred)*
- Does not install signal handlers except for watch-mode shutdown behavior.
  *(documented)*
- Does not treat metadata strings as trusted HTML. *(documented)*

## §5a Build-time and configuration variants

| Variant or knob | Default | Security effect | Maintainer stance |
| --- | --- | --- | --- |
| Python version | `>=3.13` | The model assumes current Python 3.13 `pathlib`, typing, and dependency behavior. | Required by package metadata. *(documented)* |
| CLI command | No command default | `check` is non-mutating; `build` and `watch` mutate stage/work outputs; `component-source-roots` prints local paths. | Stable command API. *(documented)* |
| `--workspace-root` / `--catalog` | Current directory and `site/catalog.yaml` | Selects the trusted workspace and catalog input boundary. | Operator-controlled. *(documented)* |
| `--report-output` | stdout | May write a report file; output is revalidated against forbidden stage/work roots. | Supported. *(documented)* |
| `--unstable-events-output` | stdout when events are enabled | Watch-only event sink; must differ from report output. | Supported but event format is explicitly unstable. *(documented)* |
| Local provider-size and route/count defaults | Documented safe operational defaults | Exceeding defaults should fail clearly unless a local operator policy raises them. | Override surface must remain local operator-controlled. *(documented)* |
| Optional container image | Not required for Python package use | Adds container runtime and base-image assumptions. | Intended for CI/container-first use. *(documented)* |
| Release-legal helper commands | Not run by staging commands | Use subprocesses and inspect local package metadata; not part of normal staging boundary. | Maintainer tooling only. *(inferred)* |

No build-time flag is currently documented as intentionally weakening a §8
security property for normal `site-pipeline` staging. *(inferred)*

## §6 Assumptions about inputs

General input assumptions:

- Catalog, component metadata, provider snapshots, page front matter, route
  metadata, redirect metadata, and provider records are data inputs and may be
  malformed or adversarial within the bounds of local workspace access.
  *(documented)*
- CLI filesystem arguments are trusted operator input, but still validated where
  they select report, event, stage, work, or source locations. *(documented)*
- Page bodies and static assets can contain active browser content; staging them
  does not make them safe. *(documented)*
- Provider snapshots may be large, so documented byte and record defaults matter
  for availability. *(documented)*

Per-parameter trust table:

| Entry point | Parameter or input | Attacker-controllable? | Caller must enforce |
| --- | --- | --- | --- |
| `site-pipeline plan/check/build/watch` | Command name and flags | No, trusted operator | Do not expose CLI invocation directly to untrusted users. *(inferred)* |
| `--workspace-root` | Local filesystem root | No, trusted operator | Select a workspace whose content is appropriate for staging. *(inferred)* |
| `--catalog` | Local catalog path | No, trusted operator path; file contents may be untrusted data | Keep catalog under intended workspace policy. *(documented)* |
| `--report-output` | Report path or stdout | No, trusted operator | Do not point reports at sensitive or shared locations unintentionally. *(inferred)* |
| `--unstable-events-output` | Watch event path or stdout | No, trusted operator | Keep machine-readable events separate from report output. *(documented)* |
| `site/catalog.yaml` | Catalog document fields | Yes, if repository content is attacker-influenced | Review source roots, publication paths, redirects, and local overrides before CI use. *(documented)* |
| `site/components.local.yaml` | Local override document | No, trusted local operator | Keep local-only and untracked. *(documented)* |
| `provider-snapshot.{yaml,yml,json}` | Provider records and metadata | Yes | Treat as external data; enforce documented size and schema limits. *(documented)* |
| Component `site/component.yaml` | Component identity/content roots | Yes, if component repo is attacker-influenced | Accept only component repos intended to participate in the site. *(documented)* |
| Page front matter | Titles, descriptions, translation keys, metadata | Yes | Renderer must escape by default; raw HTML requires explicit policy. *(documented)* |
| Page body and static assets | Markdown, AsciiDoc, HTML, JS, CSS, images, archives | Yes | Treat active content as trusted code or isolate it at deployment. *(documented)* |
| Staged outputs | JSON reports, manifests, aggregates, staged pages/assets | Pipeline-produced; may reflect input data | Downstream consumers must validate schema version and escape data in presentation. *(documented)* |

Size, shape, and rate assumptions:

- Mounted metadata payloads are limited to 16 KiB per `metadata` object after JSON
  serialization. *(documented)*
- Diagnostic detail payloads are limited to 8 KiB per `details` object after JSON
  serialization, with a reduction rule instead of malformed JSON. *(documented)*
- Provider snapshot, route, redirect, content-index, watched-directory, and
  staged-version-context defaults are documented operational limits. *(documented)*
- Watch mode is intended for local editing cadence, not hostile high-rate event
  floods. *(inferred)*

## §7 Adversary model

In-scope adversaries:

- A contributor or compromised component repository that can modify authored
  catalog-referenced content, component metadata, page front matter, page bodies,
  static assets, redirects, or provider-like data that the operator chooses to
  stage. *(inferred)*
- A provider-data source that can supply malformed or oversized provider
  snapshot records. *(inferred)*
- A bug-finding tool or reporter that supplies malformed YAML/JSON, paths,
  redirects, URLs, metadata strings, or page content and claims violation of a
  stated §8 property. *(inferred)*

Attacker goals in scope:

- Cause writes outside the configured stage/work/report boundaries. *(documented)*
- Smuggle local filesystem paths or private workspace details into public staged
  outputs. *(documented)*
- Cause unsafe route, URL, redirect, or staged metadata output that violates the
  documented contract. *(documented)*
- Cause denial of service through oversized structured inputs beyond documented
  limits. *(documented)*
- Cause the stable CLI to execute attacker-controlled local commands or unsafe
  deserialization payloads. *(inferred)*

Out-of-scope adversaries:

- An attacker with control over the operator account, shell, Python interpreter,
  dependency installation, CI runner, container runtime, or host filesystem.
  *(inferred)*
- A downstream renderer or deployment adapter that intentionally renders
  unescaped metadata, publishes active content on an unsafe origin, or ignores
  staged `trustClass` and route metadata. *(documented)*
- A network attacker against a published website, CDN, renderer development
  server, SCM host, package index, or provider API. *(inferred)*
- A malicious maintainer modifying source code or release artifacts. *(inferred)*

## §8 Security properties the project provides

| Property | Conditions | Violation symptom | Severity tier | Provenance |
| --- | --- | --- | --- | --- |
| Safe YAML/JSON data loading | Public loaders parse YAML with a safe loader, reject duplicate keys, require mapping roots and schema versions, and validate with strict models. | Unsafe object construction, duplicate-key ambiguity, accepted unexpected fields, or accepted wrong schema version. | Security-critical if reachable from authored/provider input. | *(documented)* |
| Path containment for source and output decisions | Path-bearing inputs and output targets are normalized and must stay under declared roots or allowed operator-selected destinations. | Stage/report/work writes outside intended roots; source-root traversal. | Security-critical. | *(documented)* |
| Symlink safety for staged publication | Visible stage targets and staged trees must not resolve through symlinked parents or contain symlinked entries where publication validation forbids them. | Symlink escape into or out of staged output. | Security-critical. | *(documented)* |
| Non-mutating validation command | `site-pipeline check` stops before stage-root mutation, file copying, aggregate writes, or watch-loop startup. | `check` mutates stage/work/output trees except explicit report output. | Security-critical for CI validation usage; otherwise high-severity correctness. | *(documented)* |
| No repository-authored command execution in stable staging commands | Normal `plan`, `check`, `build`, and `watch` do not execute renderer commands or repo-authored shell snippets. | Attacker-controlled catalog/content causes local command execution. | Security-critical. | *(inferred)* |
| Public-output local-path minimization | Public diagnostics and aggregate outputs prefer stable IDs, public paths, and public URLs; private roots are redacted in report details. | Absolute workstation paths or private stage/work roots leak into public reports or staged metadata contrary to contract. | Security-sensitive information disclosure. | *(documented)* |
| Metadata is data, not trusted HTML | Pipeline preserves human-facing strings as structured text and expects renderers to escape by default. | Pipeline itself marks arbitrary metadata as safe HTML or bypasses the staged trust contract. | Security-critical if it creates browser XSS in a compliant renderer. | *(documented)* |
| URL and redirect validation | URL-bearing fields reject unsupported schemes and internal redirects must resolve to known routes where required by the contract. | `javascript:`, `data:`, malformed public URL, or dangling internal redirect reaches staged contract as valid. | Security-critical for browser-facing consumers. | *(documented)* |
| Active mounted content is classified | Imported active HTML/JS/CSS trees are represented as active content requiring deployment policy rather than inert content. | Active browser code is mislabeled as passive under the pipeline-owned contract. | Security-critical for downstream deployment policy. | *(documented)* |
| Resource ceilings for structured metadata | Hard and default limits are enforced or diagnosed for mounted metadata, diagnostic details, provider snapshots, routes, redirects, content index, watch roots, and version contexts. | Unbounded allocation, malformed JSON after truncation, or missing limit diagnostics. | Security-critical for hard ceilings; availability/correctness for operational defaults. | *(documented)* |
| Stable exit-code and report contract | CLI returns documented low application exit codes and emits selected text/JSON reports without mixing human logs into machine outputs. | Automation cannot distinguish validation failure from invocation/internal failure; machine output is polluted by lifecycle logs. | Correctness/security-adjacent for automation. | *(documented)* |

## §9 Security properties the project does not provide

The project does not provide:

- HTML sanitization for authored page bodies, imported active content, renderer
  templates, or arbitrary metadata rendered by downstream systems. *(documented)*
- Browser same-origin isolation, CSP enforcement, cookie policy, local storage
  isolation, or web-server headers. *(documented)*
- Authentication, authorization, cryptographic integrity, signatures, or
  provenance verification for source repositories, provider snapshots, staged
  outputs, or published content. *(documented)*
- A sandbox boundary between untrusted repository content and the local operator
  account running the CLI. *(inferred)*
- Safe multi-tenant service behavior when exposing the CLI to untrusted network
  users. *(inferred)*
- Protection after an attacker controls the local process, Python environment,
  dependency set, container runtime, CI runner, or filesystem permissions.
  *(inferred)*
- Constant-time behavior, secret handling, or cryptographic APIs. *(inferred)*
- Complete denial-of-service resistance against unbounded local filesystem size,
  hostile watch-event storms, extremely large static assets, or intentionally
  expensive downstream rendering. *(inferred)*
- Security guarantees for generated preliminary legal drafts, release review
  conclusions, or third-party package metadata quality. *(documented)*

False-friend properties:

- JSON Schema validation is structural validation, not proof that published
  content is safe HTML or safe to execute in a browser. *(documented)*
- `trustClass: passive` or `trustClass: active` is a deployment signal, not an
  isolation mechanism by itself. *(documented)*
- `check` validates pipeline contracts; it does not prove that a downstream
  renderer, theme, web server, or CDN deployment is secure. *(documented)*
- Provider snapshot validation does not authenticate provider identity or prove
  that provider data came from an official source. *(inferred)*
- The optional container image gives a reproducible entrypoint; it is not a
  sandbox for malicious workspaces unless the operator supplies appropriate
  container isolation and mounts. *(inferred)*

Well-known attack classes left to callers or downstream layers:

- XSS through authored HTML, Markdown extensions, imported active trees, or
  renderer templates must be handled by renderer escaping and deployment policy.
  *(documented)*
- Open redirect and unsafe URL publication must be controlled by catalog policy,
  URL validation, and deployment review. *(documented)*
- Supply-chain compromise of dependencies, base images, provider snapshots, or
  component repositories is outside the pipeline's local staging boundary.
  *(inferred)*
- Local secret exfiltration by malicious renderer commands or wrapper scripts is
  outside this project unless the stable pipeline CLI executes those commands.
  *(inferred)*

## §10 Downstream responsibilities

Operators and integrators must:

- Report suspected §8 violations through the private security channel in
  `SECURITY.md`. *(documented)*
- Run the CLI only on workspaces and component repositories they intend to trust
  for local file reads and browser-facing content publication. *(inferred)*
- Keep machine-local overrides such as `site/components.local.yaml` local-only
  and untracked. *(documented)*
- Use `site-pipeline check` before `build` or publication in automation.
  *(inferred)*
- Keep report and watch-event output paths out of staged/work roots and away
  from unintended public artifacts. *(documented)*
- Configure downstream renderers to HTML-escape metadata and treat raw HTML as an
  explicit opt-in outside the core pipeline contract. *(documented)*
- Apply origin isolation, CSP, cookie, storage, and server policies for active
  mounted content. *(documented)*
- Treat provider snapshots as external data and enforce documented size/count
  limits or local operator-only overrides. *(documented)*
- Do not expose the CLI directly as a multi-tenant network service or remote
  build API without an additional isolation layer. *(inferred)*
- Review optional container image, base image, dependency, and registry posture
  according to the deployment environment's supply-chain policy. *(inferred)*

## §11 Known misuse patterns

- Rendering metadata strings as raw HTML because they were accepted by the
  pipeline schema. This is unsafe; renderers should escape by default.
  *(documented)*
- Publishing imported active site trees on the same origin as sensitive pages
  without deliberate isolation policy. *(documented)*
- Treating provider snapshots as authenticated source-of-truth data rather than
  external data loaded from a local file. *(inferred)*
- Committing `site/components.local.yaml` or relying on local override state in
  shared CI. *(documented)*
- Sharing staged reports or aggregate outputs without considering whether they
  contain repo-relative source paths or redacted local-path placeholders.
  *(inferred)*
- Calling private Python modules directly and expecting the same compatibility
  and threat-model guarantees as the stable CLI. *(documented)*
- Running multiple pipeline processes against the same stage/work root and
  treating the result as synchronized. *(inferred)*

## §11a Known non-findings

- A report that a trusted operator can pass a sensitive `--workspace-root`,
  `--catalog`, `--report-output`, or `--unstable-events-output` path is not by
  itself a vulnerability; those are trusted operator-selected CLI parameters per
  §6. *(inferred)*
- A report that active HTML/JS/CSS can execute after publication is not by itself
  a pipeline vulnerability when the content is staged as active content and the
  downstream deployment shares an origin by policy; see §9. *(documented)*
- A report that `site/components.local.yaml` can redirect local source roots is
  not by itself a vulnerability; it is a trusted local override per §3 and §6.
  *(documented)*
- A report against generated files, caches, `dist/`, `.venv/`, or test fixtures
  is out of model unless it is reachable through the supported CLI or staged
  output contract; see §3 and §4. *(inferred)*
- A report that preliminary release-legal output requires human review is not a
  security bug; that limitation is documented and by design. *(documented)*

## §12 Conditions that would change this model

Revise this threat model when the project:

- Adds a new stable CLI command, public Python API, staged output contract, or
  schema family. *(inferred)*
- Starts fetching remote repositories, provider APIs, package indexes, or other
  network resources during stable staging commands. *(inferred)*
- Adds a preview server, renderer integration, template execution, subprocess
  runner, plugin system, or user-supplied command hook to the stable CLI.
  *(inferred)*
- Changes defaults or override policy for §5a resource limits, report/event
  sinks, stage/work roots, or local overrides. *(inferred)*
- Changes path normalization, symlink handling, publication finalization, or
  public-output redaction behavior. *(inferred)*
- Promotes container-image, release-legal, generated-doc, or helper-script
  behavior into the core runtime security boundary. *(inferred)*
- Receives a vulnerability report that cannot be routed to one of the §13
  dispositions. Such a report is a model gap, not an ad-hoc exception.
  *(inferred)*

## §13 Triage dispositions

| Disposition | Meaning | Licensed by |
| --- | --- | --- |
| `VALID` | Violates a §8 property through an in-scope adversary and an in-scope input or entry point. | §6, §7, §8 |
| `VALID-HARDENING` | No §8 property is violated, but the API or output contract makes a §11 misuse easy enough that the project elects to harden it. | §11 |
| `OUT-OF-MODEL: trusted-input` | Requires attacker control of a parameter or environment element marked trusted. | §6 |
| `OUT-OF-MODEL: adversary-not-in-scope` | Requires an attacker capability excluded from the model. | §7 |
| `OUT-OF-MODEL: unsupported-component` | Lands only in tests, generated outputs, caches, local artifacts, or helper areas excluded from the runtime model. | §3 |
| `OUT-OF-MODEL: non-default-build` | Only manifests under a locally modified, discouraged, or unsupported configuration outside §5a. | §5a |
| `BY-DESIGN: property-disclaimed` | Concerns a property explicitly not provided. | §9 |
| `KNOWN-NON-FINDING` | Matches a recurring false positive documented in this model. | §11a |
| `MODEL-GAP` | Cannot be cleanly routed to any disposition above. The model must be revised. | §12 |

## §14 Open questions for the maintainers

Wave 1, security boundary:

- Should the author/status line in §1 name a maintainer owner for the threat
  model? Proposed answer: yes; make this document maintainer-owned after review.
- Is the optional container image partly in scope as described in §2 and §5a, or
  should it be moved entirely to §3? Proposed answer: keep only its
  `site-pipeline` entrypoint behavior in scope.
- Are release-legal helper commands correctly treated as maintainer tooling
  outside the normal site-staging threat boundary? Proposed answer: yes.
- Should stable Python imports remain out of scope except for documented model
  loaders/contracts? Proposed answer: yes; the CLI and emitted schemas are the
  supported public API.

Wave 2, environmental assumptions:

- Should the model explicitly disclaim safe concurrent writers to the same
  stage/work root? Proposed answer: yes, unless a locking design is added.
- Is it accurate that stable staging commands do not open listening sockets or
  fetch network resources? Proposed answer: yes for current `plan`, `check`,
  `build`, `watch`, and `component-source-roots`.
- Is it accurate that stable staging commands do not execute repository-authored
  commands or renderer hooks? Proposed answer: yes.
- Are filesystem assumptions based on `Path.resolve()` sufficient for supported
  platforms, or should the model name tested filesystems/OSes? Proposed answer:
  keep generic until a platform-specific guarantee is needed.

Wave 3, inputs and adversaries:

- Should repository-authored catalog and component files be modeled as
  attacker-controllable data in CI when pull requests can change them? Proposed
  answer: yes, within the local-workspace boundary.
- Should provider snapshots be modeled as unauthenticated external data even
  when generated by trusted provider tooling? Proposed answer: yes, because this
  project only consumes the snapshot file.
- Should watch-event floods be treated as out of scope or as a bounded
  availability property? Proposed answer: out of scope except for ordinary local
  editing cadence.
- Should extremely large static assets have explicit default limits like
  structured metadata does? Proposed answer: not currently; add a §8 property
  only when such limits are implemented and documented.

Wave 4, non-findings and publication:

- Should active content execution after publication be a known non-finding when
  `trustClass: active` and downstream deployment policy are correct? Proposed
  answer: yes.
- Should reports about trusted operator-selected output paths be closed as
  `OUT-OF-MODEL: trusted-input` unless they bypass revalidation or containment?
  Proposed answer: yes.
- Should local-path disclosure in public staged artifacts remain a §8 property
  for stage-run reports only, or for all aggregate outputs? Proposed answer:
  all public staged outputs should minimize machine-local details.
- Should this document add a machine-readable companion file now? Proposed
  answer: no; defer until triage automation needs it.

## §15 Optional machine-readable companion

No `threat-model.yaml` companion is currently maintained. The prose document is
canonical. If triage automation is added later, derive a sidecar from §2, §3,
§6, §8, §9, §11a, and §13 rather than treating the sidecar as independent
policy. *(inferred)*
