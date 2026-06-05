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

# Security Policy

Apache Buildish follows the Apache Software Foundation security process.

Please report suspected security issues to [security@apache.org](mailto:security@apache.org).

## Threat Model

The Buildish project maintains a threat model in
[docs/reference/threat-model.md](docs/reference/threat-model.md). It documents
security boundaries, in-scope vs. out-of-scope issues, trust assumptions,
security invariants, and triage guidance — useful both for human
reviewers handling reports and for automated security tooling that
consults the model before scanning.

## Security issues

Before reporting or fixing security issues, read
[docs/reference/threat-model.md](docs/reference/threat-model.md) to determine
whether a finding is a Buildish vulnerability, a deployment responsibility,
a dependency issue, or a false positive. Use [`SECURITY.md`](SECURITY.md)
reporting process and disclosure handling.

ASF severity, advisory status, and CVE candidacy are non-authoritative triage
estimates. Do not infer them from `docs/reference/threat-model.md` alone.

Do not treat a test as proof of a vulnerability unless it demonstrates that the
stated actor can cross a real trust boundary without already-authorized access,
privileged fixtures, mocked trust decisions, or protected information.

Do not include private vulnerability details, exploit payloads, reporter names,
private mailing-list content, secrets, or non-public infrastructure details in
code, comments, tests, documentation, commit messages, or PR descriptions.
