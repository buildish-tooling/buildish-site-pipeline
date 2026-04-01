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

# Security Policy

## Supported Versions

Buildish has not published a release yet. Security reports affecting the current
development branches are welcome.

## Reporting a Vulnerability

Do not open a public issue for a suspected vulnerability. Report it privately to
[security@buildish.org](mailto:security@buildish.org), including the affected
component, impact, and reproduction details where possible.

## Threat Model

The [Site Pipeline threat model](docs/reference/threat-model.md) documents the
current trust boundaries and helps maintainers distinguish a component defect
from a renderer, deployment, dependency, or operator responsibility. It is a
review aid, not a guarantee that the project is free of vulnerabilities and not
an authoritative severity, advisory, or CVE determination.

Report uncertain cases privately. Maintainers will assess whether the behavior
crosses a supported trust boundary and coordinate disclosure when appropriate.
The project-wide reporting guidance is also available on the Buildish
[Security page](https://buildish.org/community/security/).
