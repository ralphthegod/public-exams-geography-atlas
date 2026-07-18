from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import unicodedata
from typing import Any


@dataclass(frozen=True)
class LayerDefinition:
    id: str
    label: str
    default_visible: bool
    category: str


@dataclass(frozen=True)
class MapEntity:
    id: str
    kind: str
    name: str
    latitude: float
    longitude: float
    zoom: int
    aliases: tuple[str, ...] = ()
    layer_id: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def search_label(self) -> str:
        return f"{self.kind} · {self.name}"


@dataclass(frozen=True)
class AppSettings:
    root: Path
    data_urls: dict[str, str]
    europe_bbox: tuple[float, float, float, float]
    http_headers: dict[str, str]
    overpass_endpoints: tuple[str, ...]


@dataclass
class ModuleContext:
    sources: Any
    catalog: Any
    settings: AppSettings
    layer_defaults: dict[str, bool]

    def is_visible(self, layer: LayerDefinition) -> bool:
        return self.layer_defaults.get(layer.id, layer.default_visible)


def entity_id(kind: str, name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.casefold()).strip("-")
    return f"{kind}:{slug}"
