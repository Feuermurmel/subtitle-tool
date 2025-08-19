from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from dataclasses import field
from itertools import groupby
from pathlib import Path

import toml
from mashumaro.codecs import BasicDecoder

from subtitle_tool.utils import iter_files


@dataclass(kw_only=True)
class Block:
    from_ts_ms: int
    to_ts_ms: int
    lines: list[str]


@dataclass
class ConfigToCSV:
    delay_ms: int = 0


@dataclass
class Config:
    to_csv: ConfigToCSV = field(default_factory=ConfigToCSV)

    @classmethod
    def load(cls, path: Path) -> Config:
        if not path.exists():
            return Config()

        return BasicDecoder(Config).decode(toml.loads(path.read_text()))


def parse_ts(ts_str: str) -> int:
    match = re.fullmatch("(\d\d):(\d\d):(\d\d),(\d\d\d)", ts_str)
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


def convert_file(input_path: Path, output_path: Path, config: Config) -> None:
    blocks = []

    for k, group_iter in groupby(input_path.read_text().splitlines(), key=bool):
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
                Block(
                    from_ts_ms=from_ts_ms + config.to_csv.delay_ms,
                    to_ts_ms=to_ts_ms + config.to_csv.delay_ms,
                    lines=lines,
                )
            )

    with output_path.open("wt") as file:
        writer = csv.writer(file)
        writer.writerow(("Start", "End", "Start (ms)", "Line 1", "Line 2"))

        for i in blocks:
            writer.writerow(
                (format_ts(i.from_ts_ms), format_ts(i.to_ts_ms), i.from_ts_ms, *i.lines)
            )

    print(f"Wrote {len(blocks)} blocks to {output_path}.")


def to_csv_command(root_dir: Path) -> None:
    for i in iter_files(root_dir):
        if i.suffix == ".srt":
            output_path = i.with_suffix(".csv")
            config_path = i.with_suffix(".toml")

            if config_path.exists():
                convert_file(i, output_path, Config.load(config_path))
