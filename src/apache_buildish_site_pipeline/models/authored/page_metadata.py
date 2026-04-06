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

"""Page-authored metadata models."""

from __future__ import annotations

from ..documentation import ComponentOwnedAuthoredModel as SitePipelineBaseModel
from ..scalars import NonEmptyString


class PageTranslationMetadata(SitePipelineBaseModel):
    """Authored page metadata used to link locale siblings."""

    translation_key: NonEmptyString
