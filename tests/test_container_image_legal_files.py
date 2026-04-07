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

from pathlib import Path
import unittest


class ContainerImageLegalFilesTests(unittest.TestCase):
    def test_containerfile_copies_final_release_legal_files_and_disclaimer(self) -> None:
        containerfile_text = Path("tools/site-pipeline-image/Containerfile").read_text(
            encoding="utf-8"
        )

        self.assertIn("COPY DISCLAIMER ./DISCLAIMER", containerfile_text)
        self.assertIn(
            "COPY dist-release-legal/LICENSE dist-release-legal/NOTICE ./dist-release-legal/",
            containerfile_text,
        )

    def test_final_release_legal_files_exist(self) -> None:
        self.assertTrue(Path("DISCLAIMER").is_file())
        self.assertTrue(Path("dist-release-legal/LICENSE").is_file())
        self.assertTrue(Path("dist-release-legal/NOTICE").is_file())


if __name__ == "__main__":
    unittest.main()