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

"""Protect the renderer boundary described by the Roq integration guide."""

from __future__ import annotations

import unittest
from pathlib import Path


class RoqIntegrationDocsTests(unittest.TestCase):
    """Keep the copyable Roq contract aligned with Site Pipeline output."""

    def test_renderer_index_links_to_roq_with_a_pretty_route(self) -> None:
        index_text = Path("site/pages/how-to/_index.md").read_text(encoding="utf-8")

        self.assertIn("[integrate with Roq](integrate-with-roq/)", index_text)
        self.assertNotIn("integrate-with-roq.md", index_text)

    def test_guide_maps_each_stage_root_to_the_correct_roq_root(self) -> None:
        guide_text = Path("site/pages/how-to/integrate-with-roq.md").read_text(
            encoding="utf-8"
        )

        for expected_mapping in (
            "site/.stage/content/ site/roq/content/",
            "site/.stage/data/ site/roq/data/",
            "site/.stage/static/ site/roq/public/",
        ):
            self.assertIn(expected_mapping, guide_text)

        self.assertIn("site.slugify-files=false", guide_text)
        self.assertIn("Do not synchronize `manifest.json` into `data/`", guide_text)
        self.assertNotIn("site/.stage/static/ site/roq/static/", guide_text)

    def test_guide_uses_current_roq_and_watch_commands(self) -> None:
        guide_text = Path("site/pages/how-to/integrate-with-roq.md").read_text(
            encoding="utf-8"
        )

        for command in (
            "roq start",
            "roq generate",
            "--unstable-events jsonl",
            "--unstable-events-output",
        ):
            self.assertIn(command, guide_text)

        self.assertIn("does not download or execute Roq", guide_text)

    def test_smoke_fixture_pins_the_roq_runtime_contract(self) -> None:
        fixture_root = Path("tests/fixtures/roq-smoke")
        pom_text = (fixture_root / "pom.xml").read_text(encoding="utf-8")

        self.assertIn("<maven.compiler.release>21</maven.compiler.release>", pom_text)
        self.assertIn("<quarkus.version>3.35.1</quarkus.version>", pom_text)
        self.assertIn("<roq.version>2.1.6</roq.version>", pom_text)
        for relative_path in (
            "content/index.md",
            "content/components/site-pipeline/index.md",
            "data/components.json",
            "public/assets/site-pipeline-smoke.txt",
            "templates/layouts/smoke.html",
        ):
            self.assertTrue((fixture_root / relative_path).is_file(), relative_path)


if __name__ == "__main__":
    unittest.main()
