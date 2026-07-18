from __future__ import annotations

import html

import folium

from atlas.config.entities import coordinate_map
from atlas.core.models import LayerDefinition, ModuleContext
from atlas.presentation.folium_helpers import map_tooltip


class RiverSourcesModule:
    id = "river_sources"
    layers = (LayerDefinition("sources", "Sorgenti dei fiumi", False, "Idrografia"),)

    def load(self, context: ModuleContext) -> dict[str, tuple]:
        del context
        return coordinate_map("river_sources")

    def contribute_entities(self, data: dict[str, tuple], context: ModuleContext) -> None:
        del data, context  # Le sorgenti sono raggiungibili attraverso il relativo fiume.

    def render(self, map_object: folium.Map, data: dict[str, tuple], context: ModuleContext) -> None:
        layer = self.layers[0]
        group = folium.FeatureGroup(name=layer.label, show=context.is_visible(layer))
        for river, (lat, lon, source) in data.items():
            popup = f"<b>Sorgente del {html.escape(river)}</b><br>{html.escape(source)}"
            folium.CircleMarker(
                [lat, lon], radius=6.5, color="#fff", weight=2, fill=True,
                fill_color="#d5a94e", fill_opacity=1,
                tooltip=map_tooltip(f"{river} · {source}"), popup=popup,
            ).add_to(group)
        group.add_to(map_object)
