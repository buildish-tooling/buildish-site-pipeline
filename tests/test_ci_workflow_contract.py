# Copyright 2026 The Buildish Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Stable assertions for security-sensitive CI workflow contracts."""

from __future__ import annotations

import unittest
from pathlib import Path


class CiWorkflowContractTests(unittest.TestCase):
    def test_latest_container_publish_is_gated_to_main_after_check(self) -> None:
        workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
        publish_job = workflow.split("  container-publish:\n", maxsplit=1)[1].split(
            "\n  codeql:\n", maxsplit=1
        )[0]

        self.assertIn("      - check\n", publish_job)
        self.assertIn("packages: write", publish_job)
        self.assertIn("github.ref == 'refs/heads/main'", publish_job)
        self.assertIn("github.event_name == 'push'", publish_job)
        self.assertIn("github.event_name == 'workflow_dispatch'", publish_job)
        self.assertIn("buildish-site-pipeline:latest", publish_job)


if __name__ == "__main__":
    unittest.main()
