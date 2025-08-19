from __future__ import annotations

import csv
from collections.abc import Iterable
from collections.abc import Iterator
from dataclasses import dataclass
from functools import reduce
from itertools import groupby
from pathlib import Path

from subtitle_tool.config import Config
from subtitle_tool.config import ToSRTConfig
from subtitle_tool.srt import Block
from subtitle_tool.srt import SRTFile
from subtitle_tool.srt import parse_ts
from subtitle_tool.srt import write_srt_file
from subtitle_tool.utils import iter_files


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
        return InputLine(
            from_ts_ms=min(self.from_ts_ms, other.from_ts_ms),
            to_ts_ms=min(self.to_ts_ms, other.to_ts_ms),
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


def merge_input_lines(lines: list[InputLine]) -> list[InputLine]:
    def iter_lines_with_keys() -> Iterator[tuple[int, InputLine]]:
        seq = 0

        for prev, this in zip([None, *lines], lines):
            if prev is None or prev.line_2 or this.line_1:
                seq += 1

            yield seq, this

    return [
        reduce(lambda a, b: a + b, (i for _, i in lines_iter))
        for _, lines_iter in groupby(iter_lines_with_keys(), lambda x: x[0])
    ]


def massage_timestamps(blocks: list[Block], min_gap_ms: int = 200) -> None:
    for this, next in zip(blocks, blocks[1:]):
        this.to_ts_ms = min(this.to_ts_ms, next.from_ts_ms - min_gap_ms)


def convert_file(input_path: Path, output_path: Path, config: ToSRTConfig) -> None:
    with input_path.open("rt") as in_file:
        reader = csv.reader(in_file)
        column_names = next(reader)
        lines = list(reader)

    input_lines = []

    for values in lines:

        def iter_by_column_name(column_name: str) -> Iterator[str]:
            for c, v in zip(column_names, values):
                if c == column_name:
                    yield v

        from_ts_ms = parse_ts(next(iter_by_column_name("From")))
        to_ts_ms = parse_ts(next(iter_by_column_name("To")))
        line_1 = join_line(iter_by_column_name("Line 1"))
        line_2 = join_line(iter_by_column_name("Line 2"))

        input_lines.append(
            InputLine(
                from_ts_ms=from_ts_ms, to_ts_ms=to_ts_ms, line_1=line_1, line_2=line_2
            )
        )

    blocks = [i.as_block for i in merge_input_lines(input_lines)]
    massage_timestamps(blocks)

    write_srt_file(output_path, SRTFile(blocks=blocks))


def to_srt_command(root_dir: Path) -> None:
    for i in iter_files(root_dir):
        if i.suffix == ".csv":
            output_path = i.with_suffix(".srt")
            config = Config.load(i.with_suffix(".toml"))

            if config.to_srt:
                convert_file(i, output_path, config.to_srt)
