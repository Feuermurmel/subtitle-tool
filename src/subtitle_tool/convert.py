from pathlib import Path

from subtitle_tool.csv import write_csv_file
from subtitle_tool.inputs import read_input
from subtitle_tool.srt import write_srt_file
from subtitle_tool.utils import UserError


def convert_command(input_file: Path, output: Path, delay_ms: int | None) -> None:
    srt_file, config = read_input(input_file, delay_ms)

    if output.suffix == ".csv":
        write_csv_file(output, srt_file)
    if output.suffix == ".srt":
        write_srt_file(output, srt_file)
    else:
        raise UserError(f"Unknown output file type: {output}")

    print(f"Wrote {len(srt_file.blocks)} blocks to {output}.")
