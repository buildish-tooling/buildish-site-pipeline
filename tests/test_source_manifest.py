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

"""Contract checks for literal source-distribution manifest entries."""

from __future__ import annotations

from pathlib import Path
import unittest


class SourceManifestTests(unittest.TestCase):
    def test_literal_include_entries_exist(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        manifest_path = project_root / "MANIFEST.in"
        included_paths = tuple(
            line.removeprefix("include ").strip()
            for line in manifest_path.read_text(encoding="utf-8").splitlines()
            if line.startswith("include ")
        )

        missing_paths = tuple(
            relative_path
            for relative_path in included_paths
            if not (project_root / relative_path).is_file()
        )
        self.assertEqual(missing_paths, ())


if __name__ == "__main__":
    unittest.main()
