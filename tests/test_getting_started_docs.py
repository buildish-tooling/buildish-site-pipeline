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


if __name__ == "__main__":
    unittest.main()