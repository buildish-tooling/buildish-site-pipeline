# Copyright 2026 The Apache Software Foundation
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

"""Regression tests that keep copied getting-started packets aligned with fixtures."""

from __future__ import annotations

import io
import json
import unittest
from pathlib import Path

from apache_buildish_site_pipeline.cli import _run
from tests.support.workspace import _cwd, _workspace


class GettingStartedDocsTests(unittest.TestCase):
    """Protect the high-value getting-started examples readers are likely to copy."""

    def test_medium_page_packet_matches_two_artifact_fixture(self) -> None:
        page_text = Path("site/pages/getting-started/medium.md").read_text(encoding="utf-8")

        for expected_text in (
            "      runtime/",
            "        guide/",
            "      reference/",
            "      mountPath: /spark/",
            "        docsRoot: docs/runtime",
            "          tagPattern: ^api-v.*$",
            "site-pipeline build",
            "content/spark/development/guide/index.md",
            "content/spark/development/reference/index.md",
            "content/spark/releases/4.0.0/guide/index.md",
            "content/spark/releases/4.0.0/reference/index.md",
            "data/content-index.json",
            "data/routes.json",
        ):
            self.assertIn(expected_text, page_text)

        with _workspace(with_content_file=True, topology="two_artifacts") as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=stdout, stderr=stderr)

            stage_root = workspace_root / "site/.stage"
            content_paths = {
                entry["path"]: entry["sourcePath"]
                for entry in json.loads((stage_root / "data/content-index.json").read_text(encoding="utf-8"))["items"]
            }
            released_target_ids = {
                entry["targetId"]
                for entry in json.loads((stage_root / "data/routes.json").read_text(encoding="utf-8"))["items"]
                if entry["path"] == "/spark/releases/4.0.0/"
            }
            development_target_ids = {
                entry["targetId"]
                for entry in json.loads((stage_root / "data/routes.json").read_text(encoding="utf-8"))["items"]
                if entry["path"] == "/spark/development/"
            }

            self.assertEqual(exit_code, 0)
            self.assertEqual(stderr.getvalue(), "")
            self.assertTrue((stage_root / "content/spark/development/guide/index.md").is_file())
            self.assertTrue((stage_root / "content/spark/development/reference/index.md").is_file())
            self.assertTrue((stage_root / "content/spark/releases/4.0.0/guide/index.md").is_file())
            self.assertTrue((stage_root / "content/spark/releases/4.0.0/reference/index.md").is_file())
            self.assertEqual(
                development_target_ids,
                {"development:spark", "development:spark:api", "development:spark:runtime"},
            )
            self.assertEqual(
                released_target_ids,
                {"released:spark:api:4.0.0", "released:spark:runtime:4.0.0"},
            )
            self.assertEqual(
                content_paths["/spark/development/guide"],
                "components/runtime/docs/runtime/guide/index.md",
            )
            self.assertEqual(
                content_paths["/spark/development/reference"],
                "components/api/docs/reference/index.md",
            )
            self.assertEqual(
                content_paths["/spark/releases/4.0.0/guide"],
                "components/runtime/docs/runtime/releases/4.0.0/guide/index.md",
            )
            self.assertEqual(
                content_paths["/spark/releases/4.0.0/reference"],
                "components/api/docs/releases/4.0.0/reference/index.md",
            )

    def test_large_page_packet_matches_grouped_large_fixture(self) -> None:
        page_text = Path("site/pages/getting-started/large.md").read_text(encoding="utf-8")

        for expected_text in (
            "  spark:\n    localDir: components/spark",
            "  operator:\n    localDir: components/operator",
            "    pathPrefix: /platform/",
            "        targetRef: component:spark-operator",
            "        relation: testedWith",
            "          tagPattern: ^operator-v.*$",
            "site-pipeline check",
            "site-pipeline build",
            "data/components.json",
            "data/compatibility.json",
            "data/releases.json",
            "data/routes.json",
        ):
            self.assertIn(expected_text, page_text)

        with _workspace(with_content_file=True, topology="grouped_large") as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=stdout, stderr=stderr)

            stage_root = workspace_root / "site/.stage"
            components = {
                entry["slug"]: entry
                for entry in json.loads((stage_root / "data/components.json").read_text(encoding="utf-8"))["items"]
            }
            compatibility = json.loads((stage_root / "data/compatibility.json").read_text(encoding="utf-8"))["items"]
            releases = {
                (entry["componentSlug"], entry["version"]): entry
                for entry in json.loads((stage_root / "data/releases.json").read_text(encoding="utf-8"))["items"]
            }
            routes = {
                entry["path"]: entry["targetId"]
                for entry in json.loads((stage_root / "data/routes.json").read_text(encoding="utf-8"))["items"]
            }

            self.assertEqual(exit_code, 0)
            self.assertEqual(stderr.getvalue(), "")
            self.assertEqual(components["spark"]["group"], "streaming")
            self.assertEqual(components["spark-operator"]["group"], "streaming")
            self.assertTrue(
                any(
                    entry["subjectId"] == "component:spark"
                    and entry["targetId"] == "component:spark-operator"
                    and entry["relation"] == "testedWith"
                    for entry in compatibility
                )
            )
            self.assertEqual(
                components["spark"]["artifacts"][0]["releaseLines"],
                [{"key": "4.0", "latest": "4.0.0"}],
            )
            self.assertEqual(
                components["spark-operator"]["artifacts"][0]["releaseLines"],
                [{"key": "1.2", "latest": "1.2.0"}],
            )
            self.assertEqual(releases[("spark", "4.0.0")]["tag"], "v4.0.0")
            self.assertEqual(releases[("spark-operator", "1.2.0")]["tag"], "operator-v1.2.0")
            self.assertEqual(routes["/platform/spark/releases/4.0.0/"], "released:spark:runtime:4.0.0")
            self.assertEqual(
                routes["/platform/spark-operator/releases/1.2.0/"],
                "released:spark-operator:operator:1.2.0",
            )


if __name__ == "__main__":
    unittest.main()