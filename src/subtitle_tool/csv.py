from __future__ import annotations

import csv
from pathlib import Path

from subtitle_tool.srt import SRTFile
from subtitle_tool.srt import format_ts


def write_csv_file(path: Path, srt_file: SRTFile) -> None:
    with path.open("wt") as out_file:
        writer = csv.writer(out_file)
        writer.writerow(("From", "To", "From (ms)", "Line 1", "Line 2"))

        for i in srt_file.blocks:
            from_ts_ms = i.from_ts_ms
            to_ts_ms = i.to_ts_ms

            writer.writerow(
                (format_ts(from_ts_ms), format_ts(to_ts_ms), from_ts_ms, *i.lines)
            )
