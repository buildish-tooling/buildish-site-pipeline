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

"""Tests for provider-context validation helpers."""

from __future__ import annotations

from types import SimpleNamespace
import unittest

from buildish_site_pipeline.evaluation.providers import _matching_records


class ProviderValidationTests(unittest.TestCase):
    def test_matching_records_rejects_unhandled_record_kind(self) -> None:
        planning = SimpleNamespace(
            provider_index=SimpleNamespace(
                contexts_by_artifact={
                    ("spark", "runtime"): SimpleNamespace(
                        development_records=(),
                        line_heads_by_release_line={},
                        released_by_version={},
                        named_refs_by_key={},
                        refs_by_ref={},
                        candidates_by_version={},
                    )
                }
            )
        )
        context = SimpleNamespace(
            component_slug="spark",
            artifact_key="runtime",
            kind=object(),
            release_line=None,
            version=None,
            named_ref_key=None,
            ref=None,
        )

        with self.assertRaisesRegex(AssertionError, "Unhandled record kind in provider matching"):
            _matching_records(planning=planning, context=context)