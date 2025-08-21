from __future__ import annotations

import re
from pathlib import Path

from subtitle_tool.config import Config
from subtitle_tool.config import ToCSVConfig
from subtitle_tool.srt import read_srt_file
from subtitle_tool.to_srt import join_line


def convert_file(
    input_path: Path, output_path: Path, config: ToCSVConfig | None
) -> None:
    file = read_srt_file(input_path)

    with output_path.open("wt") as out_file:
        prev_from_ts_ms = 0
        d = config.delay_ms if config else 0

        for block in file.blocks:
            # diff_s = (block.from_ts_ms - prev_from_ts_ms + 500) // 1000
            joined_line = re.sub("<.+?>", "", join_line(block.lines))
            # hash = hashlib.sha256(
            #     re.sub("[^a-z]", "", joined_line.lower()).encode()
            # ).hexdigest()[:8]

            # print(f"{diff_s}", file=out_file)
            # print(hash, file=out_file)

            for s in range(
                (prev_from_ts_ms + d) // 1000, (block.from_ts_ms + d) // 1000
            ):
                print(s if config else "-", file=out_file)

            print(f"{joined_line}", file=out_file)

            prev_from_ts_ms = block.from_ts_ms


def flatten_srt_command(files: list[Path]) -> None:
    for file in files:
        assert file.suffix == ".srt"

        config = Config.load(file.with_suffix(".toml"))

        output_path = file.with_name(f"{file.stem}_flat.txt")
        convert_file(file, output_path, config.to_csv)
