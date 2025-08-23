from __future__ import annotations

import re
from dataclasses import dataclass
from dataclasses import replace
from itertools import groupby
from pathlib import Path
from pprint import pformat
from typing import override


def strip_formatting(line: str) -> str:
    return re.sub(r"<.+?>|\{\\.+?}", "", line).strip()


@dataclass(kw_only=True)
class Block:
    from_ts_ms: int
    to_ts_ms: int
    lines: list[str]

    @override
    def __repr__(self) -> str:
        return (
            f"Block("
            f"{format_ts(self.from_ts_ms)} --> {format_ts(self.to_ts_ms)}, {self.lines}"
            f")"
        )


@dataclass(kw_only=True)
class SRTFile:
    blocks: list[Block]

    def add_delay(self, delay_ms: int) -> SRTFile:
        if not delay_ms:
            return self

        blocks = [
            replace(
                i, from_ts_ms=i.from_ts_ms + delay_ms, to_ts_ms=i.to_ts_ms + delay_ms
            )
            for i in self.blocks
        ]

        return replace(self, blocks=blocks)


def parse_ts(ts_str: str) -> int:
    if match := re.fullmatch(r"-?\d+", ts_str):
        return int(match.group())

    if match := re.fullmatch(r"(-?)(\d\d):(\d\d):(\d\d)[.,](\d\d\d)", ts_str):
        sign = -1 if match.group(1) else 1
        h = int(match.group(2))
        m = int(match.group(3))
        s = int(match.group(4))
        ms = int(match.group(5))

        return sign * (ms + 1000 * (s + 60 * (m + 60 * h)))

    raise ValueError(f"Invalid timestamp: {ts_str}")


def format_ts(ts_ms: int, *, include_ms: bool = True) -> str:
    if ts_ms < 0:
        sign = "-"
        ts_ms = -ts_ms
    else:
        sign = ""

    rest, ms = divmod(ts_ms, 1000)
    rest, s = divmod(rest, 60)
    h, m = divmod(rest, 60)
    result = f"{sign}{h:02}:{m:02}:{s:02}"

    if include_ms:
        result += f",{ms:03}"

    return result


def read_srt_file(path: Path) -> SRTFile:
    try:
        blocks = []

        for k, group_iter in groupby(path.read_text().splitlines(), key=bool):
            if k:
                _seq, timestamps_str, *lines = group_iter
                from_ts_str, sep, to_ts_str = timestamps_str.partition(" --> ")
                assert sep, timestamps_str

                # Debug: Check roundtrip.
                assert format_ts(parse_ts(from_ts_str)) == from_ts_str
                assert format_ts(parse_ts(to_ts_str)) == to_ts_str

                from_ts_ms = parse_ts(from_ts_str)
                to_ts_ms = parse_ts(to_ts_str)

                blocks.append(
                    Block(from_ts_ms=from_ts_ms, to_ts_ms=to_ts_ms, lines=lines)
                )

        return SRTFile(blocks=blocks)
    except Exception as e:
        e.add_note(f"While loading file {path}.")

        raise


def write_srt_file(path: Path, file: SRTFile, *, validate: bool = True) -> None:
    if validate:
        for i in file.blocks:
            assert i.from_ts_ms >= 0, f"Negative timestamp:\n{pformat(i)}"
            assert i.from_ts_ms < i.to_ts_ms, f"Non-positive interval:\n{pformat(i)}"

        # for a, b in zip(file.blocks, file.blocks[1:]):
        #     assert (
        #         a.to_ts_ms < b.from_ts_ms
        #     ), f"Timestamps overlap:\n{pformat(a)}\n{pformat(b)}"

    with path.open("wt") as output_file:
        for seq, block in enumerate(file.blocks, 1):
            print(seq, file=output_file)
            print(
                f"{format_ts(block.from_ts_ms)} --> {format_ts(block.to_ts_ms)}",
                file=output_file,
            )

            for line in block.lines:
                line = line.strip()

                if not line:
                    # lolololol
                    line = "<i>\xa0</i>"

                print(line, file=output_file)

            print(file=output_file)
