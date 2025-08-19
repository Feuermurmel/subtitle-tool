from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path
from pprint import pformat


@dataclass(kw_only=True)
class Block:
    from_ts_ms: int
    to_ts_ms: int
    lines: list[str]


@dataclass(kw_only=True)
class SRTFile:
    blocks: list[Block]


def parse_ts(ts_str: str) -> int:
    match = re.fullmatch(r"(\d\d):(\d\d):(\d\d),(\d\d\d)", ts_str)
    assert match
    h = int(match.group(1))
    m = int(match.group(2))
    s = int(match.group(3))
    ms = int(match.group(4))

    return ms + 1000 * (s + 60 * (m + 60 * h))


def format_ts(ts_ms: int) -> str:
    rest, ms = divmod(ts_ms, 1000)
    rest, s = divmod(rest, 60)
    h, m = divmod(rest, 60)

    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def read_srt_file(path: Path) -> SRTFile:
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

            blocks.append(Block(from_ts_ms=from_ts_ms, to_ts_ms=to_ts_ms, lines=lines))

    return SRTFile(blocks=blocks)


def write_srt_file(path: Path, file: SRTFile) -> None:
    for a, b in zip(file.blocks, file.blocks[1:]):
        assert a.from_ts_ms < b.to_ts_ms, f"Non-positive interval:\b{pformat(a)}"
        assert (
            a.to_ts_ms < b.from_ts_ms
        ), f"Timestamps overlap:\n{pformat(a)}\n{pformat(b)}"

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
