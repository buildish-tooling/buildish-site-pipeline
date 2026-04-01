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

"""Traversal-contract coverage shared by staging source-tree consumers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from buildish_site_pipeline.cli.errors import StageIntegrityError
from buildish_site_pipeline.staging.source_tree import iter_source_tree_files


class SourceTreeTests(unittest.TestCase):
    def test_directory_aliases_and_loops_are_not_traversed(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            source_root = Path(tempdir) / "source"
            real_directory = source_root / "real"
            real_directory.mkdir(parents=True)
            (real_directory / "guide.md").write_text("guide\n", encoding="utf-8")
            (source_root / "alias").symlink_to(
                real_directory,
                target_is_directory=True,
            )
            (real_directory / "loop").symlink_to(
                source_root,
                target_is_directory=True,
            )

            relative_paths = tuple(
                relative_path.as_posix()
                for _, relative_path in iter_source_tree_files(
                    source_root=source_root
                )
            )

        self.assertEqual(relative_paths, ("real/guide.md",))

    def test_contained_file_symlink_is_yielded_without_losing_alias_path(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            source_root = Path(tempdir) / "source"
            source_root.mkdir()
            target = source_root / "guide.md"
            target.write_text("guide\n", encoding="utf-8")
            (source_root / "alias.md").symlink_to(target)

            relative_paths = tuple(
                relative_path.as_posix()
                for _, relative_path in iter_source_tree_files(
                    source_root=source_root
                )
            )

        self.assertEqual(relative_paths, ("alias.md", "guide.md"))

    def test_file_symlink_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            temp_root = Path(tempdir)
            source_root = temp_root / "source"
            source_root.mkdir()
            outside = temp_root / "outside.md"
            outside.write_text("outside\n", encoding="utf-8")
            (source_root / "escape.md").symlink_to(outside)

            with self.assertRaises(StageIntegrityError):
                tuple(iter_source_tree_files(source_root=source_root))


if __name__ == "__main__":
    unittest.main()
