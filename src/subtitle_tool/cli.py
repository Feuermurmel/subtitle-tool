import logging
import sys
from argparse import ArgumentParser
from argparse import Namespace
from collections.abc import Callable
from pathlib import Path
from typing import Any

from subtitle_tool.combine import combine_command
from subtitle_tool.convert import convert_command
from subtitle_tool.play import play_command
from subtitle_tool.srt import parse_ts
from subtitle_tool.utils import UserError


def parse_args() -> Namespace:
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    play_parser = subparsers.add_parser("play")
    play_parser.add_argument("-d", "--delay", type=parse_ts, dest="delay_ms")
    play_parser.add_argument("--start-at-id", type=int)
    play_parser.add_argument("video_file", type=Path)
    play_parser.add_argument("input_file", type=Path)
    play_parser.add_argument("mpv_args", nargs="*")

    csv_parser = subparsers.add_parser("convert")
    csv_parser.add_argument("-d", "--delay", type=parse_ts, dest="delay_ms")
    csv_parser.add_argument("input_file", type=Path)
    csv_parser.add_argument("-o", "--output", type=Path, required=True)

    combine_parser = subparsers.add_parser("combine")
    combine_parser.add_argument("input_file_1", type=Path)
    combine_parser.add_argument("input_file_2", type=Path)
    combine_parser.add_argument("--sort-delay", type=parse_ts, default=1000)
    combine_parser.add_argument("-o", "--output", type=Path, required=True)

    return parser.parse_args()


def main(command: str, **kwargs: Any) -> None:
    commands: dict[str, Callable[..., None]] = {
        "play": play_command,
        "convert": convert_command,
        "combine": combine_command,
    }

    commands[command](**kwargs)


def entry_point() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    try:
        main(**vars(parse_args()))
    except UserError as e:
        logging.error(f"error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.error("Operation interrupted.")
        sys.exit(130)
