from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).with_name("static_entities.json")


@lru_cache(maxsize=1)
def static_entities() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def coordinate_map(name: str) -> dict[str, tuple]:
    return {key: tuple(value) for key, value in static_entities()[name].items()}
