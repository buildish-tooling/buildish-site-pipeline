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

"""Regression tests for first-use and contributor documentation contracts."""

from __future__ import annotations

import re
import tomllib
import unittest
from pathlib import Path

from buildish_site_pipeline.cli import parse_invocation
from buildish_site_pipeline.cli.contract import BuildInvocation, CheckInvocation


_README = Path("README.md")
_CONTRIBUTING = Path("CONTRIBUTING.md")
_COMPONENT_LANDING = Path("site/pages/_index.md")
_RENDERER_INDEX = Path("site/pages/how-to/_index.md")
_CI_WORKFLOW = Path(".github/workflows/ci.yml")


class FirstUseDocumentationTests(unittest.TestCase):
    """Keep central onboarding claims aligned with executable project contracts."""

    def test_readme_uses_current_workspace_and_catalog_contract(self) -> None:
        readme = _README.read_text(encoding="utf-8")

        self.assertIn("site/catalog.yaml", readme)
        self.assertIn("--workspace-root /workspace", readme)
        self.assertIn("--catalog /workspace/buildish-site/site/catalog.yaml", readme)
        self.assertNotIn("site/components.yaml", readme)
        self.assertNotIn("--repo-root", readme)
        self.assertNotIn("site-pipeline preview", readme)

        self.assertIsInstance(parse_invocation(["check"]), CheckInvocation)
        self.assertIsInstance(
            parse_invocation(
                [
                    "build",
                    "--workspace-root",
                    "/workspace",
                    "--catalog",
                    "/workspace/buildish-site/site/catalog.yaml",
                ]
            ),
            BuildInvocation,
        )

    def test_readme_acquisition_claims_match_repository_evidence(self) -> None:
        readme = _README.read_text(encoding="utf-8")
        workflow = _CI_WORKFLOW.read_text(encoding="utf-8")
        image_match = re.search(
            r"IMAGE_REF: (ghcr\.io/\$\{\{ github\.repository_owner \}\}/"
            r"buildish-site-pipeline:latest)",
            workflow,
        )

        if image_match is None:
            self.fail("CI must expose the canonical latest image coordinate")
        image_ref = image_match.group(1).replace(
            "${{ github.repository_owner }}",
            "buildish-tooling",
        )
        self.assertIn(
            "git clone https://github.com/buildish-tooling/buildish-site-pipeline.git",
            readme,
        )
        self.assertIn("uv sync --frozen", readme)
        self.assertRegex(
            readme,
            r"does not currently document a package-index\s+installation\s+coordinate",
        )
        self.assertIn(image_ref, readme)
        self.assertIn("moving development image", readme)

    def test_contributor_prerequisites_match_project_and_ci(self) -> None:
        contributing = _CONTRIBUTING.read_text(encoding="utf-8")
        project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual(project["project"]["requires-python"], ">=3.13")
        for prerequisite in (
            "Python 3.13 or newer",
            "uv sync --frozen",
            "Java 21 or newer",
            "make help",
            "make check",
            "make schemas",
        ):
            self.assertIn(prerequisite, contributing)

    def test_renderer_index_distinguishes_verification_levels(self) -> None:
        renderer_index = _RENDERER_INDEX.read_text(encoding="utf-8")

        self.assertIn(
            "integrate-with-hugo/) — documented direct mounts", renderer_index
        )
        self.assertIn(
            "integrate-with-roq/) — documented consumer-side adapter", renderer_index
        )
        self.assertEqual(renderer_index.count("planned-guide status page, not"), 2)
        self.assertEqual(renderer_index.count("a turnkey recipe"), 2)

    def test_landing_labels_development_docs_as_unreleased(self) -> None:
        landing = _COMPONENT_LANDING.read_text(encoding="utf-8")

        self.assertIn(
            'kind="development" label="Read unreleased development docs"', landing
        )
        self.assertIn(
            "[Unreleased development reference](development/reference/)", landing
        )
        self.assertNotIn('kind="development" label="Read docs"', landing)


if __name__ == "__main__":
    unittest.main()
