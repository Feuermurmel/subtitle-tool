import logging
import sys
from argparse import ArgumentParser
from argparse import Namespace
from collections.abc import Callable
from pathlib import Path
from typing import Any

from subtitle_tool.convert import convert_command
from subtitle_tool.srt import parse_ts
from subtitle_tool.utils import UserError


def parse_args() -> Namespace:
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    csv_parser = subparsers.add_parser("convert")
    csv_parser.add_argument("-d", "--delay", type=parse_ts, dest="delay_ms")
    csv_parser.add_argument("input_file", type=Path)
    csv_parser.add_argument("-o", "--output", type=Path, required=True)

    return parser.parse_args()


def main(command: str, **kwargs: Any) -> None:
    commands: dict[str, Callable[..., None]] = {"convert": convert_command}

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
