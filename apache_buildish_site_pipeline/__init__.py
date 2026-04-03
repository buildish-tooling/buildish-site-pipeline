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

"""Public API for the site pipeline package.

Most callers only need the exported build helpers from this module. The package
internals are split into smaller modules so contributors can find the Markdown,
filesystem, watch-mode, and build orchestration logic more easily.
"""

from .cli import main

__all__ = [
    "main",
]
