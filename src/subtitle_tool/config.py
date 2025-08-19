from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

import toml
from mashumaro.codecs import BasicDecoder


@dataclass
class ConfigToCSV:
    delay_ms: int = 0


@dataclass
class Config:
    to_csv: ConfigToCSV = field(default_factory=ConfigToCSV)

    @classmethod
    def load(cls, path: Path) -> Config:
        if not path.exists():
            return Config()

        return BasicDecoder(Config).decode(toml.loads(path.read_text()))
