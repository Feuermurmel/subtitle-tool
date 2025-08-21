import csv
from pathlib import Path

from subtitle_tool.inputs import read_input
from subtitle_tool.srt import Block
from subtitle_tool.srt import format_ts


def combine_command(
    input_file_1: Path, input_file_2: Path, output: Path, sort_delay: int
) -> None:
    assert output.suffix == ".csv"

    srt_file_1, config_1 = read_input(input_file_1)
    srt_file_2, config_2 = read_input(input_file_2)

    file_1_max_lines = max(len(i.lines) for i in srt_file_1.blocks)
    file_2_max_lines = max(len(i.lines) for i in srt_file_2.blocks)

    with output.open("wt") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(
            (
                "From",
                "To",
                "Sorting Timestamp (ms)",
                *["Line 1"] * file_1_max_lines,
                *["Line 2"] * file_2_max_lines,
            )
        )

        def write_block(
            block: Block, sorting_ts: int, lines_1: list[str], lines_2: list[str]
        ) -> None:
            writer.writerow(
                (
                    format_ts(block.from_ts_ms),
                    format_ts(block.to_ts_ms),
                    sorting_ts,
                    *lines_1,
                    *[""] * (file_1_max_lines - len(lines_1)),
                    *lines_2,
                    *[""] * (file_2_max_lines - len(lines_2)),
                )
            )

        for block in srt_file_1.blocks:
            write_block(block, block.from_ts_ms, block.lines, [])

        for block in srt_file_2.blocks:
            write_block(block, block.from_ts_ms + sort_delay, [], block.lines)
