from pathlib import Path

from subtitle_tool.csv import write_csv_file
from subtitle_tool.inputs import read_input
from subtitle_tool.merge import join_line
from subtitle_tool.srt import SRTFile
from subtitle_tool.srt import format_ts
from subtitle_tool.srt import strip_formatting
from subtitle_tool.srt import write_srt_file
from subtitle_tool.utils import UserError


def write_flat_txt_file(output_path: Path, srt_file: SRTFile) -> None:
    with output_path.open("wt") as out_file:
        prev_from_ts_ms = 0

        for block in srt_file.blocks:
            joined_line = strip_formatting(join_line(block.lines))

            for s in range(prev_from_ts_ms // 1000, block.from_ts_ms // 1000):
                print(format_ts(s * 1000, include_ms=False), file=out_file)

            print(f"{joined_line}", file=out_file)

            prev_from_ts_ms = block.from_ts_ms


def convert_command(input_file: Path, output: Path, delay_ms: int | None) -> None:
    srt_file, config = read_input(input_file, delay_ms)

    if output.suffix == ".csv":
        write_csv_file(output, srt_file)
    elif output.suffix == ".srt":
        write_srt_file(output, srt_file)
    elif output.suffix == ".txt":
        write_flat_txt_file(output, srt_file)
    else:
        raise UserError(f"Unknown output file type: {output}")

    print(f"Wrote {len(srt_file.blocks)} blocks to {output}.")
