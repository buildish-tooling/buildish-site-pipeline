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

"""Helpers for writing visible stage files without needless byte-identical churn."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile

from apache_buildish_site_pipeline.cli.errors import StageIntegrityError


def write_utf8_text_file(path: Path, text: str) -> bool:
    """Write one UTF-8 text file atomically unless the existing bytes already match."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if _existing_text_matches(path=path, text=text):
        return False
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_file.write(text)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_path = Path(temp_file.name)
        os.replace(temp_path, path)
    except OSError as exc:
        raise StageIntegrityError(f"Could not write stage text file {path}: {exc}") from exc
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink(missing_ok=True)
    return True


def _existing_text_matches(*, path: Path, text: str) -> bool:
    if not path.exists():
        return False
    if path.is_symlink() or not path.is_file():
        raise StageIntegrityError(f"Stage text output must be a normal file: {path}")
    try:
        return path.read_text(encoding="utf-8") == text
    except OSError as exc:
        raise StageIntegrityError(f"Could not read existing stage text file {path}: {exc}") from exc