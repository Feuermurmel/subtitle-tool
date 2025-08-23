import sys
from pathlib import Path

from subtitle_tool.inputs import read_input
from subtitle_tool.srt import format_ts
from subtitle_tool.srt import strip_formatting

characters_per_second = 20


def lint_command(input_file: Path, delay_ms: int | None, empty_lines: bool) -> None:
    srt_file, config = read_input(input_file, delay_ms)
    has_warnings = False

    for block in srt_file.blocks:
        warnings = []
        stripped_lines = [strip_formatting(i) for i in block.lines]

        if empty_lines and not all(stripped_lines):
            warnings.append("Empty line.")

        for index, stripped_line in enumerate(stripped_lines, 1):
            duration = (block.to_ts_ms - block.from_ts_ms) / 1000
            cps = len(stripped_line) / duration

            if cps > characters_per_second:
                warnings.append(f"Fast line (line {index}): {cps:0.1f} characters/s")

        line_lengths = [l for i in stripped_lines if (l := len(i))]

        if line_lengths:
            min_line_length = min(line_lengths)
            max_line_length = max(line_lengths)
            ratio = max_line_length / min_line_length

            if ratio > 1.5 and max_line_length - min_line_length > 9:
                warnings.append(f"Unequal line lengths: 1:{ratio:0.2f}")

        if warnings:
            print(
                f"\x1b[34m{format_ts(block.from_ts_ms)} "
                f"--> {format_ts(block.to_ts_ms)}\x1b[m"
            )
            for i in block.lines:
                print(i)

            print()
            for i in warnings:
                print(f"\x1b[35m- {i}\x1b[m")
            print()

            has_warnings = True

    sys.exit(1 if has_warnings else 0)
