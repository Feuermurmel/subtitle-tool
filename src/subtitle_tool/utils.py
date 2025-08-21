from collections.abc import Iterator
from pathlib import Path


class UserError(Exception):
    pass


def iter_files(root: Path) -> Iterator[Path]:
    for dirpath, dirnames, filenames in root.walk():
        for names in dirnames, filenames:
            names[:] = [i for i in names if not i.startswith(".")]

        for i in filenames:
            yield dirpath / i
