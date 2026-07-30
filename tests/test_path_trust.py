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

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from buildish_site_pipeline.path_trust import path_resolves_through_symlink


class PathTrustTests(unittest.TestCase):
    def test_path_resolves_through_symlink_detects_existing_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            real_parent = workspace_root / "real"
            real_parent.mkdir()
            link_parent = workspace_root / "linked"
            link_parent.symlink_to(real_parent, target_is_directory=True)

            self.assertTrue(
                path_resolves_through_symlink(link_parent / "child" / "report.json")
            )

    def test_path_resolves_through_symlink_accepts_plain_existing_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            plain_parent = workspace_root / "plain"
            plain_parent.mkdir()

            self.assertFalse(path_resolves_through_symlink(plain_parent / "report.json"))