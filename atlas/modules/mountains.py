from __future__ import annotations

import html

import folium

from atlas.config.entities import coordinate_map
from atlas.core.models import LayerDefinition, MapEntity, ModuleContext, entity_id
from atlas.presentation.folium_helpers import map_tooltip


class MountainsModule:
    id = "mountains"
    layers = (LayerDefinition("mountains", "Montagne e vette", True, "Rilievi"),)

    def load(self, context: ModuleContext) -> dict[str, tuple]:
        del context
        return coordinate_map("mountains")

    def contribute_entities(self, data: dict[str, tuple], context: ModuleContext) -> None:
        for name, (lat, lon, altitude) in data.items():
            context.catalog.add(MapEntity(
                id=entity_id("mountain", name), kind="Montagna", name=name,
                latitude=lat, longitude=lon, zoom=10, layer_id="mountains",
                metadata={"altitudine": altitude},
            ))

    def render(self, map_object: folium.Map, data: dict[str, tuple], context: ModuleContext) -> None:
        layer = self.layers[0]
        group = folium.FeatureGroup(name=layer.label, show=context.is_visible(layer))
        for name, (lat, lon, altitude) in data.items():
            icon = folium.DivIcon(
                html="<div class='mountain-pin'>▲</div>",
                icon_size=(22, 22), icon_anchor=(11, 11),
            )
            folium.Marker(
                [lat, lon], icon=icon,
                tooltip=map_tooltip(f"{name} · {altitude}"),
                popup=f"<b>{html.escape(name)}</b><br>{html.escape(altitude)}",
            ).add_to(group)
        group.add_to(map_object)
