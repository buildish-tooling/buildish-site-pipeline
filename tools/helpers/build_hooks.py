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

"""Small setuptools wheel hook for final legal-file layout tweaks.

The project now relies on standard ``project.license-files`` metadata so
setuptools handles nearly all of the legal-file work for sdists and wheels.
That standard behavior intentionally preserves source-relative paths inside the
wheel's ``.dist-info/licenses/`` directory. For files declared as
``dist-release-legal/LICENSE`` and ``dist-release-legal/NOTICE``, that produces
paths under ``licenses/dist-release-legal/``.

For this project we want a narrower result:

* ``DISCLAIMER`` should remain exactly where setuptools places it,
  ``.dist-info/licenses/DISCLAIMER``.
* ``dist-release-legal/LICENSE`` should land at
  ``.dist-info/licenses/LICENSE``.
* ``dist-release-legal/NOTICE`` should land at
  ``.dist-info/licenses/NOTICE``.

The customization here deliberately stays small. Instead of reimplementing the
entire wheel build, we hook into ``bdist_wheel.egg2dist()``, let setuptools
copy the declared license files normally, prune repo-only helper modules that
must never ship in the wheel, then flatten the two curated paths and rewrite
the wheel ``METADATA`` ``License-File`` fields to match the final archive
layout.
"""

from __future__ import annotations

from pathlib import Path
import shutil

from setuptools.command.bdist_wheel import bdist_wheel

_FLATTENED_LICENSE_PATHS = {
    "dist-release-legal/LICENSE": "LICENSE",
    "dist-release-legal/NOTICE": "NOTICE",
}
_UNSHIPPED_PACKAGE_FILES = (
    "release_legal.py",
    "snapshot_publish.py",
)
_UNSHIPPED_PACKAGE_PATHS = (
    "models/documentation.py",
    "reference_export.py",
    "schema_export.py",
)
_UNSHIPPED_PACKAGE_DIRS = (
    "models/reference_docs",
)


class FlattenedLicenseFilesBdistWheel(bdist_wheel):
    """Flatten selected wheel license files after setuptools copies them.

    ``project.license-files`` remains the source of truth for what gets bundled.
    This class only adjusts the wheel-facing paths for the two curated ASF
    release files that should appear directly under ``.dist-info/licenses/``.
    """

    def egg2dist(self, egginfo_path: str, distinfo_path: str) -> None:
        """Convert egg metadata, then normalize the wheel license layout.

        ``bdist_wheel.run()`` calls ``egg2dist()`` after installation into the
        wheel staging tree but before ``RECORD`` and the final archive are
        written. That makes it the narrowest safe point for path rewrites:
        setuptools has already copied the legal files into ``licenses/``, and we
        can still update both the files and the ``METADATA`` entries before the
        wheel is sealed.
        """

        super().egg2dist(egginfo_path, distinfo_path)
        self._flatten_dist_info_license_files(Path(distinfo_path))

    def _flatten_dist_info_license_files(self, distinfo_dir: Path) -> None:
        """Move selected license files to ``licenses/`` root and fix metadata."""

        self._remove_repo_only_wheel_modules(distinfo_dir.parent)
        licenses_dir = distinfo_dir / "licenses"
        moved_paths: dict[str, str] = {}

        for original_relative_path, flattened_name in _FLATTENED_LICENSE_PATHS.items():
            source_path = licenses_dir / original_relative_path
            if not source_path.is_file():
                continue

            target_path = licenses_dir / flattened_name
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(source_path, target_path)
            moved_paths[original_relative_path] = flattened_name

        # Remove the now-empty intermediate directories so the wheel contains
        # only the final license files and no dead ``dist-release-legal/`` tree.
        dist_release_legal_dir = licenses_dir / "dist-release-legal"
        if dist_release_legal_dir.exists() and not any(dist_release_legal_dir.iterdir()):
            dist_release_legal_dir.rmdir()

        if moved_paths:
            self._rewrite_license_file_metadata(
                metadata_path=distinfo_dir / "METADATA",
                moved_paths=moved_paths,
            )

    @staticmethod
    def _remove_repo_only_wheel_modules(wheel_root: Path) -> None:
        """Delete repo-maintenance helpers from the wheel staging tree.

        ``setuptools`` reuses the local ``build/`` directory between invocations.
        When Python files move out of ``src/apache_buildish_site_pipeline/``,
        stale copies can remain under ``build/lib/apache_buildish_site_pipeline``
        and would otherwise be picked up by a later wheel build. Removing the
        known repo-only helpers here keeps the wheel contents aligned with the
        current source layout without requiring callers to manually clean
        ``build/`` first.
        """

        package_dir = wheel_root / "apache_buildish_site_pipeline"
        for module_name in _UNSHIPPED_PACKAGE_FILES:
            module_path = package_dir / module_name
            if module_path.exists():
                module_path.unlink()
        for relative_path in _UNSHIPPED_PACKAGE_PATHS:
            package_path = package_dir / relative_path
            if package_path.exists():
                package_path.unlink()
        for relative_dir in _UNSHIPPED_PACKAGE_DIRS:
            package_path = package_dir / relative_dir
            if package_path.exists():
                shutil.rmtree(package_path)

    @staticmethod
    def _rewrite_license_file_metadata(
        *,
        metadata_path: Path,
        moved_paths: dict[str, str],
    ) -> None:
        """Rewrite ``License-File`` lines so wheel metadata matches wheel paths."""

        original_lines = metadata_path.read_text(encoding="utf-8").splitlines()
        rewritten_lines: list[str] = []

        for line in original_lines:
            if not line.startswith("License-File: "):
                rewritten_lines.append(line)
                continue

            _, _, declared_path = line.partition(": ")
            normalized_path = moved_paths.get(declared_path, declared_path)
            rewritten_lines.append(f"License-File: {normalized_path}")

        metadata_path.write_text("\n".join(rewritten_lines) + "\n", encoding="utf-8")
