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

import json
from pathlib import Path
import tempfile
import unittest

from tools.helpers.snapshot_publish import publish_snapshot


class SnapshotPublishTests(unittest.TestCase):
    def test_publish_snapshot_writes_unique_wheel_and_latest_manifest(self) -> None:
        project_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)
            wheel_path, manifest_path = publish_snapshot(
                out_dir=out_dir,
                project_dir=project_root,
            )

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertTrue(wheel_path.is_file())
            self.assertEqual(manifest_path, out_dir / "latest.json")
            self.assertEqual(manifest["wheel"], wheel_path.name)
            self.assertEqual(manifest["wheelPath"], wheel_path.as_posix())
            self.assertIn("+snapshot.", manifest["version"])
            self.assertEqual(
                manifest["dependencySpec"],
                f"buildish-site-pipeline @ {wheel_path.resolve().as_uri()}",
            )


if __name__ == "__main__":
    unittest.main()
