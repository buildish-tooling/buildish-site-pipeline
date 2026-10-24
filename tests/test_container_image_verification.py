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

from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import Mock

from tools.helpers.verify_container_image import (
    fetch_uv_license,
    smoke_test,
    verify_licenses,
)


class ContainerImageVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        image_dir = Path("tools/site-pipeline-image")
        shutil.copytree(image_dir / "legal", self.root / image_dir / "legal")
        shutil.copyfile(
            image_dir / "Containerfile", self.root / image_dir / "Containerfile"
        )
        shutil.copyfile("LICENSE", self.root / "LICENSE")
        self.python_license = self.root / image_dir / "legal/base-images/python/LICENSE"
        self.upstream_uv = {
            "LICENSE-APACHE": (self.root / "LICENSE").read_text(encoding="utf-8"),
            "LICENSE-MIT": (
                self.root / image_dir / "legal/base-images/uv/LICENSE-MIT"
            ).read_text(encoding="utf-8"),
        }
        self.fetch_uv = Mock(
            side_effect=lambda version, filename: self.upstream_uv[filename]
        )

    def test_unchanged_texts_pass_and_use_the_pinned_uv_version(self) -> None:
        containerfile = self.root / "tools/site-pipeline-image/Containerfile"
        containerfile.write_text(
            containerfile.read_text(encoding="utf-8").replace("uv:0.12.1", "uv:0.13.5"),
            encoding="utf-8",
        )
        verify_licenses(self.root, self.python_license, self.fetch_uv)
        self.assertEqual(
            self.fetch_uv.call_args_list,
            [
                unittest.mock.call("0.13.5", "LICENSE-APACHE"),
                unittest.mock.call("0.13.5", "LICENSE-MIT"),
            ],
        )

    def test_uv_license_changes_fail_with_a_diff(self) -> None:
        self.upstream_uv["LICENSE-MIT"] += "New upstream notice\n"
        with self.assertRaisesRegex(RuntimeError, r"\+New upstream notice"):
            verify_licenses(self.root, self.python_license, self.fetch_uv)

    def test_python_license_changes_fail_with_a_diff(self) -> None:
        installed = self.root / "installed-LICENSE.txt"
        installed.write_text("Changed Python license\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, r"\+Changed Python license"):
            verify_licenses(self.root, installed, self.fetch_uv)

    def test_unavailable_upstream_fails_the_check(self) -> None:
        self.fetch_uv.side_effect = OSError("Upstream unavailable")
        with self.assertRaisesRegex(OSError, "Upstream unavailable"):
            verify_licenses(self.root, self.python_license, self.fetch_uv)

    def test_source_fetch_rejects_unexpected_versions_and_paths(self) -> None:
        for version, filename in (
            ("../main", "LICENSE-MIT"),
            ("0.13.5", "../README.md"),
        ):
            with self.subTest(version=version, filename=filename):
                with self.assertRaises(ValueError):
                    fetch_uv_license(version, filename)

    def test_installed_cli_stages_a_real_page(self) -> None:
        smoke_test()


if __name__ == "__main__":
    unittest.main()
