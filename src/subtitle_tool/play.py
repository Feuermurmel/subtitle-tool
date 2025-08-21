import shlex
import sys
from pathlib import Path
from subprocess import call
from tempfile import TemporaryDirectory

from subtitle_tool.inputs import read_input
from subtitle_tool.srt import write_srt_file


def play_command(
    video_file: Path,
    input_file: Path,
    delay_ms: int | None,
    start_at_id: int | None,
    mpv_args: list[str],
) -> None:
    with TemporaryDirectory() as temp_dir:
        temp_srt_path = Path(temp_dir) / "temp.srt"
        srt_file, config = read_input(input_file, 0)
        write_srt_file(temp_srt_path, srt_file, validate=False)

        if delay_ms is None:
            delay_ms = config.delay_ms

        cmdline = [
            "mpv",
            f"{video_file}",
            "--osd-fractions",
            "--sid=1",
            f"--sub-file={temp_srt_path}",
            f"--sub-delay={delay_ms / 1000:0.3f}",
        ]

        if start_at_id is not None:
            start_ms = srt_file.blocks[start_at_id - 1].from_ts_ms
            cmdline.append(f"--start={start_ms / 1000:0.3f}")

        cmdline.extend(mpv_args)

        print(f"Running: {shlex.join(cmdline)}")
        sys.exit(call(cmdline))
