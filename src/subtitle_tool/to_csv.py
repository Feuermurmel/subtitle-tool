from __future__ import annotations

import csv
from pathlib import Path

from subtitle_tool.config import Config
from subtitle_tool.config import ToCSVConfig
from subtitle_tool.srt import format_ts
from subtitle_tool.srt import read_srt_file
from subtitle_tool.utils import iter_files


def convert_file(input_path: Path, output_path: Path, config: ToCSVConfig) -> None:
    file = read_srt_file(input_path)

    with output_path.open("wt") as out_file:
        writer = csv.writer(out_file)
        writer.writerow(("From", "To", "From (ms)", "Line 1", "Line 2"))

        for i in file.blocks:
            writer.writerow(
                (
                    format_ts(i.from_ts_ms + config.delay_ms),
                    format_ts(i.to_ts_ms + config.delay_ms),
                    i.from_ts_ms,
                    *i.lines,
                )
            )

    print(f"Wrote {len(file.blocks)} blocks to {output_path}.")


def to_csv_command(root_dir: Path) -> None:
    for i in iter_files(root_dir):
        if i.suffix == ".srt":
            output_path = i.with_suffix(".csv")
            config = Config.load(i.with_suffix(".toml"))

            if config.to_csv is not None:
                convert_file(i, output_path, config.to_csv)
