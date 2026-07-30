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
import unittest


class ContainerImageLegalFilesTests(unittest.TestCase):
    def test_containerfile_copies_build_inputs_before_install(self) -> None:
        containerfile_text = Path("tools/site-pipeline-image/Containerfile").read_text(
            encoding="utf-8"
        )

        copy_root_inputs = containerfile_text.index(
            "COPY README.md pyproject.toml uv.lock main.py dist-release-legal/LICENSE dist-release-legal/NOTICE ./"
        )
        copy_src = containerfile_text.index("COPY src ./src")
        copy_tools = containerfile_text.index("COPY tools/helpers ./tools/helpers")
        apt_install_step = containerfile_text.index("apt-get install -y --no-install-recommends ca-certificates;")
        install_step = containerfile_text.index("uv sync --frozen --no-dev --no-editable;")

        self.assertLess(copy_root_inputs, install_step)
        self.assertLess(copy_src, install_step)
        self.assertLess(copy_tools, install_step)
        self.assertLess(apt_install_step, install_step)

    def test_containerfile_derives_build_time_release_legal_layout_from_root_files(self) -> None:
        containerfile_text = Path("tools/site-pipeline-image/Containerfile").read_text(
            encoding="utf-8"
        )

        self.assertIn("mkdir -p dist-release-legal;", containerfile_text)
        self.assertIn("cp LICENSE NOTICE dist-release-legal/;", containerfile_text)

    def test_containerfile_removes_build_only_inputs_after_install(self) -> None:
        containerfile_text = Path("tools/site-pipeline-image/Containerfile").read_text(
            encoding="utf-8"
        )

        self.assertIn("rm -rf tools dist-release-legal pyproject.toml uv.lock", containerfile_text)
        self.assertNotIn("rm -f /usr/local/bin/uv /usr/local/bin/uvx", containerfile_text)

    def test_containerfile_copies_final_release_legal_files(self) -> None:
        containerfile_text = Path("tools/site-pipeline-image/Containerfile").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "COPY README.md pyproject.toml uv.lock main.py dist-release-legal/LICENSE dist-release-legal/NOTICE ./",
            containerfile_text,
        )
        self.assertIn("COPY --from=uvbin /uv /uvx /usr/local/bin/", containerfile_text)

    def test_containerfile_runs_as_dedicated_non_root_runtime_user(self) -> None:
        containerfile_text = Path("tools/site-pipeline-image/Containerfile").read_text(
            encoding="utf-8"
        )

        self.assertIn("groupadd --system --gid 10001 site-pipeline", containerfile_text)
        self.assertIn(
            "useradd --system --uid 10001 --gid site-pipeline --create-home --home-dir /home/site-pipeline site-pipeline",
            containerfile_text,
        )
        self.assertIn(
            "chown -R site-pipeline:site-pipeline /home/site-pipeline /workspace",
            containerfile_text,
        )
        self.assertIn("HOME=/home/site-pipeline", containerfile_text)
        self.assertIn("PYTHONDONTWRITEBYTECODE=1", containerfile_text)
        self.assertIn("WORKDIR /workspace", containerfile_text)
        self.assertIn("USER site-pipeline", containerfile_text)

    def test_final_release_legal_files_exist(self) -> None:
        self.assertTrue(Path("dist-release-legal/LICENSE").is_file())
        self.assertTrue(Path("dist-release-legal/NOTICE").is_file())


if __name__ == "__main__":
    unittest.main()
