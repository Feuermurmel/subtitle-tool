from __future__ import annotations

import csv
from pathlib import Path

from subtitle_tool.config import Config
from subtitle_tool.srt import format_ts
from subtitle_tool.srt import read_srt_file
from subtitle_tool.utils import iter_files


def convert_file(input_path: Path, output_path: Path, config: Config) -> None:
    file = read_srt_file(input_path)

    with output_path.open("wt") as out_file:
        writer = csv.writer(out_file)
        writer.writerow(("Start", "End", "Start (ms)", "Line 1", "Line 2"))

        for i in file.blocks:
            writer.writerow(
                (
                    format_ts(i.from_ts_ms + config.to_csv.delay_ms),
                    format_ts(i.to_ts_ms + config.to_csv.delay_ms),
                    i.from_ts_ms,
                    *i.lines,
                )
            )

    print(f"Wrote {len(file.blocks)} blocks to {output_path}.")


def to_csv_command(root_dir: Path) -> None:
    for i in iter_files(root_dir):
        if i.suffix == ".srt":
            output_path = i.with_suffix(".csv")
            config_path = i.with_suffix(".toml")

            if config_path.exists():
                convert_file(i, output_path, Config.load(config_path))
