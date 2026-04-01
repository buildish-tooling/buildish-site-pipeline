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

"""Tests for snapshot publishing helpers."""

from __future__ import annotations

import datetime as dt
import unittest

from apache_buildish_site_pipeline.snapshot_publish import format_snapshot_version
from apache_buildish_site_pipeline.snapshot_publish import replace_project_version


class SnapshotPublishTest(unittest.TestCase):
    def test_format_snapshot_version_includes_git_revision(self) -> None:
        version = format_snapshot_version(
            "0.1.0",
            built_at=dt.datetime(2026, 4, 1, 12, 34, 56, tzinfo=dt.UTC),
            git_revision="ABC123def4567890",
        )

        self.assertEqual("0.1.0.dev20260401123456+gabc123def456", version)

    def test_replace_project_version_rewrites_first_assignment(self) -> None:
        updated = replace_project_version(
            "[project]\nversion = \"0.1.0\"\nname = \"demo\"\n",
            "0.1.0.dev20260401123456+gabc123def456",
        )

        self.assertIn(
            'version = "0.1.0.dev20260401123456+gabc123def456"',
            updated,
        )