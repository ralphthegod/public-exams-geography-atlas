from __future__ import annotations

import html

import folium

from atlas.config.entities import coordinate_map
from atlas.core.models import LayerDefinition, MapEntity, ModuleContext, entity_id
from atlas.presentation.folium_helpers import map_tooltip


class CapitalsModule:
    id = "capitals"
    layers = (LayerDefinition("capitals", "Capoluoghi di regione", True, "Città"),)

    def load(self, context: ModuleContext) -> dict[str, tuple]:
        del context
        return coordinate_map("capitals")

    def contribute_entities(self, data: dict[str, tuple], context: ModuleContext) -> None:
        for name, (lat, lon, region) in data.items():
            context.catalog.add(MapEntity(
                id=entity_id("capital", name), kind="Capoluogo", name=name,
                latitude=lat, longitude=lon, zoom=11, layer_id="capitals",
                metadata={"regione": region},
            ))

    def render(self, map_object: folium.Map, data: dict[str, tuple], context: ModuleContext) -> None:
        layer = self.layers[0]
        group = folium.FeatureGroup(name=layer.label, show=context.is_visible(layer))
        for city, (lat, lon, region) in data.items():
            popup = f"<b>{html.escape(city)}</b><br><span>{html.escape(region)}</span>"
            folium.CircleMarker(
                [lat, lon], radius=5.5, color="#fff", weight=2, fill=True,
                fill_color="#b5483e", fill_opacity=1,
                tooltip=map_tooltip(city), popup=popup,
            ).add_to(group)
        group.add_to(map_object)
