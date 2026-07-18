from __future__ import annotations

from typing import Any, Protocol

import folium

from atlas.core.models import LayerDefinition, ModuleContext


class GeoJsonSource(Protocol):
    def load(self) -> dict[str, Any] | None: ...


class MapModule(Protocol):
    id: str
    layers: tuple[LayerDefinition, ...]

    def load(self, context: ModuleContext) -> Any: ...
    def contribute_entities(self, data: Any, context: ModuleContext) -> None: ...
    def render(self, map_object: folium.Map, data: Any, context: ModuleContext) -> None: ...


class MapControl(Protocol):
    id: str

    def render(self, map_object: folium.Map, context: ModuleContext, layer_control_name: str) -> None: ...
