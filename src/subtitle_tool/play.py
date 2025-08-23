import os
import shlex
import sys
import time
from pathlib import Path
from subprocess import call
from tempfile import TemporaryDirectory
from threading import Event
from threading import Thread

from subtitle_tool.config import Config
from subtitle_tool.inputs import read_input
from subtitle_tool.srt import SRTFile
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

        def update_srt_file() -> tuple[SRTFile, Config]:
            srt_file, config = read_input(input_file, 0)
            write_srt_file(temp_srt_path, srt_file, validate=False)

            return srt_file, config

        srt_file, config = update_srt_file()

        if delay_ms is None:
            delay_ms = config.delay_ms

        r, w = os.pipe()
        w_file = os.fdopen(w, "wt")
        thread_stop_event = Event()

        def thread_target() -> None:
            stat = None

            while not thread_stop_event.is_set():
                time.sleep(0.5)
                new_stat = input_file.stat()

                if new_stat != stat:
                    try:
                        print(f"Reloading subtitles from {input_file}.")
                        update_srt_file()
                    except Exception as e:
                        print(f"Error while reloading subtitles: {e}")

                    print("sub-reload", file=w_file, flush=True)
                    stat = new_stat

        thread = Thread(target=thread_target)
        thread.start()

        try:
            cmdline = [
                "mpv",
                f"{video_file}",
                "--osd-level=2",
                "--osd-fractions",
                "--sid=1",
                f"--sub-file={temp_srt_path}",
                f"--sub-delay={delay_ms / 1000:0.3f}",
                f"--input-ipc-client=fd://{r}",
            ]

            if start_at_id is not None:
                start_ms = srt_file.blocks[start_at_id - 1].from_ts_ms
                cmdline.append(f"--start={start_ms / 1000:0.3f}")

            cmdline.extend(mpv_args)

            print(f"Running: {shlex.join(cmdline)}")
            sys.exit(call(cmdline, pass_fds=[r]))
        finally:
            thread_stop_event.set()
            thread.join()
