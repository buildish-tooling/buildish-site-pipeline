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

"""Self-contained CLI contract tests using repo-local fixtures."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliIntegrationTest(unittest.TestCase):
    def test_second_consumer_fixture_builds_through_cli(self) -> None:
        fixture_root = Path(__file__).parent / "fixtures" / "second-consumer-workspace"
        package_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            shutil.copytree(fixture_root, workspace)
            repo_root = workspace / "consumer-site"

            completed = subprocess.run(  # noqa: S603 - intentional CLI contract test
                [
                    sys.executable,
                    str(package_root / "main.py"),
                    "build",
                    "--repo-root",
                    str(repo_root),
                ],
                cwd=package_root,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, completed.returncode, msg=completed.stderr)
            self.assertIn("Built 1 component(s)", completed.stdout)

            stage_root = repo_root / "out" / "stage"
            preview_root = repo_root / "out" / "preview"
            component_root = stage_root / "content" / "components" / "rocket-cache"
            self.assertTrue((stage_root / "content" / "_index.md").is_file())
            self.assertTrue((stage_root / "manifest.yaml").is_file())
            self.assertTrue((stage_root / "data" / "components.yaml").is_file())
            self.assertTrue((preview_root / "index.html").is_file())
            self.assertTrue((component_root / "_index.md").is_file())
            self.assertTrue((component_root / "development" / "docs" / "getting-started.md").is_file())
            self.assertTrue(
                (
                    stage_root
                    / "static"
                    / "components"
                    / "rocket-cache"
                    / "development"
                    / "assets"
                    / "logos"
                    / "mark.txt"
                ).is_file()
            )
            landing_page = (component_root / "_index.md").read_text(encoding="utf-8")
            self.assertIn("Alt checkout content", landing_page)
            self.assertIn("Rocket Cache Alt", landing_page)