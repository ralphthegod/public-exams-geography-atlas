from __future__ import annotations

import html
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import folium

from atlas.core.models import LayerDefinition, MapEntity, ModuleContext, entity_id
from atlas.presentation.folium_helpers import map_tooltip


DATA_PATH = Path(__file__).with_name("entities.json")


@lru_cache(maxsize=1)
def _load_capitals() -> tuple[dict[str, Any], ...]:
    try:
        payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    return tuple(payload.get("capitals", ()))


class EuropeanCapitalsModule:
    id = "european_capitals"
    layers = (
        LayerDefinition("european_capital_points", "Capitali europee", True, "Città"),
        LayerDefinition(
            "european_capital_labels", "Etichette capitali europee", False, "Etichette"
        ),
    )

    def load(self, context: ModuleContext) -> tuple[dict[str, Any], ...]:
        del context
        return _load_capitals()

    def contribute_entities(
        self, data: tuple[dict[str, Any], ...], context: ModuleContext
    ) -> None:
        for capital in data:
            name = str(capital["name"])
            country = str(capital["country"])
            context.catalog.add(MapEntity(
                id=entity_id("european-capital", f"{capital['country_iso3']}-{name}"),
                kind="Capitale nazionale",
                name=f"{name} — {country}",
                latitude=float(capital["latitude"]),
                longitude=float(capital["longitude"]),
                zoom=8,
                layer_id="european_capital_points",
                metadata={"paese": country, "iso3": str(capital["country_iso3"])},
            ))

    def render(
        self,
        map_object: folium.Map,
        data: tuple[dict[str, Any], ...],
        context: ModuleContext,
    ) -> None:
        points_layer, labels_layer = self.layers
        points = folium.FeatureGroup(
            name=points_layer.label, show=context.is_visible(points_layer)
        )
        labels = folium.FeatureGroup(
            name=labels_layer.label, show=context.is_visible(labels_layer)
        )
        for capital in data:
            name = str(capital["name"])
            country = str(capital["country"])
            latitude = float(capital["latitude"])
            longitude = float(capital["longitude"])
            escaped_name = html.escape(name)
            escaped_country = html.escape(country)
            popup = f"<b>{escaped_name}</b><br><span>Capitale di {escaped_country}</span>"
            folium.CircleMarker(
                [latitude, longitude],
                radius=6,
                color="#ffffff",
                weight=2,
                fill=True,
                fill_color="#263f73",
                fill_opacity=1,
                tooltip=map_tooltip(f"{name} · {country}"),
                popup=popup,
            ).add_to(points)

            offset_x, offset_y = capital.get("label_offset", (0, -13))
            folium.Marker(
                [latitude, longitude],
                icon=folium.DivIcon(
                    html=f"<span class='european-capital-label'>{escaped_name}</span>",
                    icon_size=(170, 22),
                    icon_anchor=(85 - int(offset_x), 11 - int(offset_y)),
                ),
                tooltip=map_tooltip(f"{name} · {country}"),
                popup=popup,
            ).add_to(labels)
        points.add_to(map_object)
        labels.add_to(map_object)
