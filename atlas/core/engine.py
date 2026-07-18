from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import folium
from branca.element import Element
from folium.plugins import Fullscreen, MiniMap, MousePosition

from atlas.core.contracts import MapControl, MapModule
from atlas.core.models import ModuleContext


class MapEngine:
    def __init__(
        self,
        modules: list[MapModule],
        controls: list[MapControl],
        context: ModuleContext,
        map_styles_path: Path,
    ) -> None:
        self.modules = modules
        self.controls = controls
        self.context = context
        self.map_styles_path = map_styles_path

    def build(self) -> folium.Map:
        self.context.catalog.clear()
        map_object = folium.Map(
            location=[42.6, 12.4], zoom_start=5, min_zoom=4, max_zoom=12,
            tiles=None, control_scale=True, prefer_canvas=True,
        )
        folium.TileLayer("OpenStreetMap", name="OpenStreetMap", show=True).add_to(map_object)
        folium.TileLayer("CartoDB positron", name="Carta chiara", show=False).add_to(map_object)

        with ThreadPoolExecutor(max_workers=min(8, len(self.modules))) as executor:
            loaded = list(executor.map(lambda module: module.load(self.context), self.modules))

        for module, data in zip(self.modules, loaded):
            module.contribute_entities(data, self.context)
        for module, data in zip(self.modules, loaded):
            module.render(map_object, data, self.context)

        Fullscreen(position="topleft", title="Schermo intero", title_cancel="Esci").add_to(map_object)
        MiniMap(toggle_display=True, position="bottomright", tile_layer="OpenStreetMap").add_to(map_object)
        MousePosition(position="bottomleft", separator=" · ", prefix="Coordinate").add_to(map_object)
        layer_control = folium.LayerControl(position="topright", collapsed=True, sort_layers=False)
        layer_control.add_to(map_object)
        for control in self.controls:
            control.render(map_object, self.context, layer_control.get_name())

        css = self.map_styles_path.read_text(encoding="utf-8")
        map_object.get_root().header.add_child(Element(f"<style>{css}</style>"))
        return map_object
