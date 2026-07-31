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

"""Measure Markdown link extraction scaling on a repeatable synthetic corpus.

This is a local diagnostic rather than a CI performance assertion. Machine
load, Python builds, and dependency versions affect absolute timings; compare
median scaling ratios from equivalent runs instead of treating milliseconds as
a stable project contract.
"""

from __future__ import annotations

import argparse
import statistics
import time
from pathlib import Path

from buildish_site_pipeline.evaluation.link_references import extract_link_references


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sizes",
        default="250,500,1000,2000",
        help="Comma-separated link counts (default: %(default)s).",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=5,
        help="Measured repetitions per size (default: %(default)s).",
    )
    parser.add_argument(
        "--workload",
        choices=("inline", "reference", "titled-reference", "complex-reference"),
        default="inline",
        help=(
            "Use plain inline links, plain or titled full-reference links, or "
            "multiple references per line that retain the full Markdown parser "
            "fallback (default: %(default)s)."
        ),
    )
    return parser


def _workload(*, link_count: int, workload: str) -> str:
    if workload == "inline":
        return "".join(
            f"[link {index}](target-{index % 8}/)\n" for index in range(link_count)
        )
    if workload == "complex-reference":
        references = "".join(
            f"[link {index}][target-{index % 8}] "
            f"[second {index}][target-{index % 8}]\n"
            for index in range(link_count // 2)
        )
        if link_count % 2:
            references += f"[link {link_count - 1}][target-0]\n"
    else:
        references = "".join(
            f"[link {index}][target-{index % 8}]\n" for index in range(link_count)
        )
    definition_title = ' "Target title"' if workload == "titled-reference" else ""
    definitions = "\n".join(
        f"[target-{index}]: target-{index}/{definition_title}" for index in range(8)
    )
    return f"{references}\n{definitions}\n"


def _median_seconds(*, text: str, repeats: int, expected_count: int) -> float:
    source_path = Path("benchmark.md")
    extracted = extract_link_references(source_path=source_path, text=text)
    if len(extracted) != expected_count:
        raise RuntimeError(
            f"Expected {expected_count} extracted links, got {len(extracted)}"
        )

    timings: list[float] = []
    for _ in range(repeats):
        started = time.perf_counter()
        extract_link_references(source_path=source_path, text=text)
        timings.append(time.perf_counter() - started)
    return statistics.median(timings)


def main(argv: list[str] | None = None) -> int:
    """Run the local benchmark and print median time and adjacent ratios."""

    args = _build_parser().parse_args(argv)
    sizes = tuple(int(value) for value in args.sizes.split(","))
    if not sizes or any(size <= 0 for size in sizes):
        raise ValueError("--sizes must contain positive integers")
    if args.repeats <= 0:
        raise ValueError("--repeats must be positive")

    previous_seconds: float | None = None
    for size in sizes:
        text = _workload(link_count=size, workload=args.workload)
        median_seconds = _median_seconds(
            text=text,
            repeats=args.repeats,
            expected_count=size,
        )
        ratio = (
            "-"
            if previous_seconds is None
            else f"{median_seconds / previous_seconds:.2f}x"
        )
        print(  # noqa: T201
            f"{args.workload:>9}  {size:>6} links  {len(text):>7} chars  "
            f"median={median_seconds:.6f}s  adjacent-ratio={ratio}"
        )
        previous_seconds = median_seconds
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
