from __future__ import annotations

import csv
from collections.abc import Iterable
from collections.abc import Iterator
from dataclasses import dataclass
from dataclasses import replace
from functools import reduce
from itertools import groupby
from pathlib import Path
from pprint import pformat

from subtitle_tool.srt import Block
from subtitle_tool.srt import SRTFile
from subtitle_tool.srt import parse_ts


def join_line(parts: Iterable[str]) -> str:
    result = ""

    for part in parts:
        part = part.strip()
        sep = " "

        without_dash = part.removeprefix("-")

        if without_dash != part:
            part = "- " + without_dash.strip()
            sep = "    "

        if part:
            if result:
                result += sep

            result += part

    return result


@dataclass(kw_only=True)
class InputLine:
    from_ts_ms: int
    to_ts_ms: int
    line_1: str
    line_2: str

    def __add__(self, other: InputLine) -> InputLine:
        # Lines that don't overlap should not be joined, except when the second line is empty.
        assert self.to_ts_ms >= other.from_ts_ms or not (
            other.line_1 or other.line_2
        ), f"Joining non-overlapping lines:\n{pformat(self)}\n{pformat(other)}"

        return InputLine(
            from_ts_ms=min(self.from_ts_ms, other.from_ts_ms),
            to_ts_ms=max(self.to_ts_ms, other.to_ts_ms),
            line_1=join_line([self.line_1, other.line_1]),
            line_2=join_line([self.line_2, other.line_2]),
        )

    @property
    def as_block(self) -> Block:
        return Block(
            from_ts_ms=self.from_ts_ms,
            to_ts_ms=self.to_ts_ms,
            lines=[self.line_1, self.line_2],
        )


def merge_lines(lines: Iterable[tuple[bool, InputLine]]) -> list[InputLine]:
    def iter_lines_with_keys() -> Iterator[tuple[int, InputLine]]:
        key = 0

        for join, line in lines:
            key += not join
            yield key, line

    return [
        reduce(lambda a, b: a + b, (i for _, i in lines_iter))
        for _, lines_iter in groupby(iter_lines_with_keys(), lambda x: x[0])
    ]


def merge_input_lines(lines: list[InputLine]) -> list[InputLine]:
    def join(prev: InputLine, this: InputLine) -> bool:
        # Always join empty lines into the previous line.
        if not this.line_1 and not this.line_2:
            return True

        # Don't join lines that don't overlap.
        if prev.to_ts_ms < this.from_ts_ms:
            return False

        # Don't join consecutive items occupying the same line or when
        # switching back from line 2 to line 1.
        if this.line_1 or prev.line_2:
            return False

        # Otherwise join.
        return True

    return merge_lines(
        (prev is not None and join(prev, this), this)
        for prev, this in zip([None, *lines], lines)
    )


def massage_timestamps(
    lines: list[InputLine], min_gap_ms: int = 200
) -> list[InputLine]:
    res = []

    for this, next in zip(lines, lines[1:] + [None]):
        to_ts_ms = this.to_ts_ms

        if next is not None:
            this = replace(this, to_ts_ms=min(to_ts_ms, next.from_ts_ms - min_gap_ms))

        res.append(this)

    return res


def read_input_lines(input_path: Path) -> list[InputLine]:
    res = []

    with input_path.open("rt") as in_file:
        reader = csv.reader(in_file)
        column_names = next(reader)
        lines = list(reader)

    for values in lines:

        def iter_by_column_name(column_name: str) -> Iterator[str]:
            for c, v in zip(column_names, values):
                if c == column_name:
                    yield v

        from_ts_ms = parse_ts(next(iter_by_column_name("From")))
        to_ts_ms = parse_ts(next(iter_by_column_name("To")))
        line_1 = join_line(iter_by_column_name("Line 1"))
        line_2 = join_line(iter_by_column_name("Line 2"))

        res.append(
            InputLine(
                from_ts_ms=from_ts_ms, to_ts_ms=to_ts_ms, line_1=line_1, line_2=line_2
            )
        )

    return res


def read_combined_csv(path: Path) -> SRTFile:
    input_lines = read_input_lines(path)
    input_lines = merge_input_lines(input_lines)
    input_lines = massage_timestamps(input_lines)

    return SRTFile(blocks=[i.as_block for i in merge_input_lines(input_lines)])
