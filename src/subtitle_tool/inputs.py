from pathlib import Path

from subtitle_tool.config import Config
from subtitle_tool.merge import read_combined_csv
from subtitle_tool.srt import SRTFile
from subtitle_tool.srt import read_srt_file
from subtitle_tool.utils import UserError


def read_input(path: Path, delay_ms: int | None) -> tuple[SRTFile, Config]:
    config = Config.load(path.with_suffix(".toml"))

    if delay_ms is None:
        delay_ms = config.delay_ms

    if path.suffix == ".srt":
        file = read_srt_file(path)
    elif path.suffix == ".csv":
        file = read_combined_csv(path)
    else:
        raise UserError(f"Unknown input file type: {path}")

    return file.add_delay(delay_ms), config
