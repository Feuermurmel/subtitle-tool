from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import toml
from mashumaro.codecs import BasicDecoder


@dataclass
class ToCSVConfig:
    delay_ms: int = 0


@dataclass
class ToSRTConfig:
    pass


@dataclass
class Config:
    to_csv: ToCSVConfig | None = None
    to_srt: ToSRTConfig | None = None

    @classmethod
    def load(cls, path: Path) -> Config:
        if not path.exists():
            return Config()

        return BasicDecoder(Config).decode(toml.loads(path.read_text()))
