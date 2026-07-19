from __future__ import annotations

import html
from pathlib import Path
from typing import Any

import folium

from atlas.core.contracts import GeoJsonSource
from atlas.core.models import LayerDefinition, MapEntity, ModuleContext, entity_id
from atlas.infrastructure.sources import LocalGeoJsonSource
from atlas.presentation.folium_helpers import map_tooltip


DATA_PATH = Path(__file__).with_name("rivers.geojson")

ITALIAN_NAMES = {
    "Danube": "Danubio",
    "Donau": "Danubio",
    "Dniester": "Dnestr",
    "Dnipro": "Dnepr",
    "Drau": "Drava",
    "Elbe": "Elba",
    "Evros": "Marica",
    "Firat": "Eufrate",
    "Fiume Devoli": "Devoll",
    "Fiume Peneo": "Peneo",
    "Kiz?lirmak": "Kızılırmak",
    "Loire": "Loira",
    "Maas": "Mosa",
    "Mosel": "Mosella",
    "Mur": "Mura",
    "Rhein": "Reno",
    "Schelde": "Schelda",
    "Seine": "Senna",
    "Southern Bug": "Bug Meridionale",
    "Tajo": "Tago",
    "Tejo": "Tago",
    "Thames": "Tamigi",
    "Vistula": "Vistola",
    "Vltava": "Moldava",
}


class EuropeanNationalRiversModule:
    id = "european_national_rivers"
    layers = (
        LayerDefinition(
            "european_national_rivers",
            "Tre fiumi principali per nazione",
            False,
            "Idrografia",
        ),
        LayerDefinition(
            "european_national_river_labels",
            "Etichette fiumi per nazione",
            False,
            "Etichette",
        ),
    )

    def __init__(self, source: GeoJsonSource | None = None) -> None:
        self.source = source or LocalGeoJsonSource(DATA_PATH)

    def load(self, context: ModuleContext) -> dict[str, Any] | None:
        del context
        data = self.source.load()
        for feature in (data or {}).get("features", []):
            props = feature.get("properties", {})
            original = str(props.get("name", ""))
            name = ITALIAN_NAMES.get(original, original)
            props["name"] = name
            props["_label"] = f"{name} · {props.get('country', '')}"
        return data

    def contribute_entities(
        self, data: dict[str, Any] | None, context: ModuleContext
    ) -> None:
        for feature in (data or {}).get("features", []):
            props = feature.get("properties", {})
            name = str(props.get("name", "Fiume"))
            country = str(props.get("country", ""))
            code = str(props.get("country_iso3", ""))
            context.catalog.add(MapEntity(
                id=entity_id("national-river", f"{code}-{name}"),
                kind="Fiume nazionale",
                name=f"{name} — {country}",
                latitude=float(props["label_lat"]),
                longitude=float(props["label_lon"]),
                zoom=7,
                layer_id="european_national_rivers",
                metadata={
                    "paese": country,
                    "posizione": str(props.get("rank", "")),
                    "lunghezza_nel_paese_km": str(props.get("length_in_country_km", "")),
                },
            ))

    def render(
        self,
        map_object: folium.Map,
        data: dict[str, Any] | None,
        context: ModuleContext,
    ) -> None:
        rivers_layer, labels_layer = self.layers
        rivers = folium.FeatureGroup(
            name=rivers_layer.label, show=context.is_visible(rivers_layer)
        )
        if data:
            folium.GeoJson(
                data,
                smooth_factor=0.5,
                style_function=lambda feature: {
                    "color": "#6656a3",
                    "weight": 3.2 - 0.45 * int(feature["properties"].get("rank", 1)),
                    "opacity": 0.88,
                },
                highlight_function=lambda _feature: {
                    "color": "#44347d",
                    "weight": 4.2,
                    "opacity": 1,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["name", "country", "rank"],
                    aliases=["Fiume", "Paese", "Posizione"],
                    sticky=True,
                    direction="bottom",
                    offset=(0, 14),
                    class_name="map-tooltip",
                ),
                popup=folium.GeoJsonPopup(
                    fields=["name", "country", "rank", "length_in_country_km"],
                    aliases=["Fiume", "Paese", "Posizione", "Tratto nel paese (km)"],
                ),
            ).add_to(rivers)
        rivers.add_to(map_object)

        labels = folium.FeatureGroup(
            name=labels_layer.label, show=context.is_visible(labels_layer)
        )
        for feature in (data or {}).get("features", []):
            props = feature.get("properties", {})
            name = str(props.get("name", "Fiume"))
            country = str(props.get("country", ""))
            escaped = html.escape(name)
            folium.Marker(
                [float(props["label_lat"]), float(props["label_lon"])],
                icon=folium.DivIcon(
                    html=f"<span class='national-river-label'>{escaped}</span>",
                    icon_size=(160, 20),
                    icon_anchor=(80, 10),
                ),
                tooltip=map_tooltip(f"{name} · {country}"),
                popup=(
                    f"<b>{escaped}</b><br>{html.escape(country)} · "
                    f"{int(props.get('rank', 0))}° per lunghezza"
                ),
            ).add_to(labels)
        labels.add_to(map_object)
