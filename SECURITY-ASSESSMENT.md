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

# Security Assessment Status

_Updated:_ 2026-08-04

This file previously described an early implementation that included a built-in
preview server and local component-override file. Those features are not part of
the current Site Pipeline CLI, so the earlier assessment no longer applies and
has been replaced.

The current supported security boundary is documented in the
[Site Pipeline threat model](docs/reference/threat-model.md). In summary, Site
Pipeline validates and stages local workspace content for a downstream renderer;
it does not render or serve the website, fetch component repositories, or act as
a sandbox for a hostile local execution environment.

This status note is not a security certification. Security conclusions must be
re-evaluated against the current source, dependencies, execution environment,
and deployment design. Suspected vulnerabilities should be reported through
the private process in [SECURITY.md](SECURITY.md).
