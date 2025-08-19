import logging
import sys
from argparse import ArgumentParser
from argparse import Namespace
from pathlib import Path
from typing import Any

from subtitle_tool.to_csv import to_csv_command
from subtitle_tool.to_srt import to_srt_command


class UserError(Exception):
    pass


def parse_args() -> Namespace:
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    to_csv_parser = subparsers.add_parser("to-csv")
    to_csv_parser.add_argument("root_dir", nargs="?", type=Path, default=Path())

    to_srt_parser = subparsers.add_parser("to-srt")
    to_srt_parser.add_argument("root_dir", nargs="?", type=Path, default=Path())

    return parser.parse_args()


def main(command: str, **kwargs: Any) -> None:
    commands = {"to-csv": to_csv_command, "to-srt": to_srt_command}

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
