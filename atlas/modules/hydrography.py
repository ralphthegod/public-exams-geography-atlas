from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Any

import folium

from atlas.config.entities import coordinate_map
from atlas.core.geojson import feature_in_bbox, select_features
from atlas.core.models import LayerDefinition, MapEntity, ModuleContext, entity_id
from atlas.presentation.folium_helpers import map_tooltip


@dataclass
class HydrographyData:
    european_rivers: dict[str, Any] | None
    italian_rivers: dict[str, Any] | None
    european_lakes: dict[str, Any] | None
    italian_lakes: dict[str, Any] | None
    river_labels: dict[str, tuple]
    lake_labels: dict[str, tuple]


def _european_physical_features(
    data: dict[str, Any] | None,
    context: ModuleContext,
) -> dict[str, Any] | None:
    selected = select_features(
        data,
        lambda feature: feature_in_bbox(feature, context.settings.europe_bbox),
    )
    for feature in (selected or {}).get("features", []):
        props = feature.setdefault("properties", {})
        props["_label"] = (
            props.get("name_it") or props.get("NAME_IT") or props.get("name")
            or props.get("NAME") or "Elemento idrografico"
        )
    return selected


class HydrographyModule:
    id = "hydrography"
    layers = (
        LayerDefinition("rivers", "Traccia fiumi", True, "Idrografia"),
        LayerDefinition("lakes", "Traccia laghi", True, "Idrografia"),
        LayerDefinition("river_labels", "Etichette fiumi", False, "Etichette"),
        LayerDefinition("lake_labels", "Etichette laghi", False, "Etichette"),
    )

    def load(self, context: ModuleContext) -> HydrographyData:
        sources = context.sources.get_many(
            "natural_earth.rivers", "osm.italian_rivers",
            "natural_earth.lakes", "osm.italian_lakes",
        )
        return HydrographyData(
            european_rivers=_european_physical_features(
                sources["natural_earth.rivers"], context,
            ),
            italian_rivers=sources["osm.italian_rivers"],
            european_lakes=_european_physical_features(
                sources["natural_earth.lakes"], context,
            ),
            italian_lakes=sources["osm.italian_lakes"],
            river_labels=coordinate_map("river_labels"),
            lake_labels=coordinate_map("lake_labels"),
        )

    def contribute_entities(self, data: HydrographyData, context: ModuleContext) -> None:
        for name, (lat, lon) in data.river_labels.items():
            context.catalog.add(MapEntity(
                id=entity_id("river", name), kind="Fiume", name=name,
                latitude=lat, longitude=lon, zoom=9, layer_id="rivers",
            ))
        for name, (lat, lon) in data.lake_labels.items():
            context.catalog.add(MapEntity(
                id=entity_id("lake", name), kind="Lago", name=name,
                latitude=lat, longitude=lon, zoom=9, layer_id="lakes",
            ))

    def render(self, map_object: folium.Map, data: HydrographyData, context: ModuleContext) -> None:
        rivers_layer, lakes_layer, river_labels_layer, lake_labels_layer = self.layers
        self._render_rivers(map_object, data, context, rivers_layer)
        self._render_lakes(map_object, data, context, lakes_layer)
        self._render_labels(
            map_object, data.river_labels, river_labels_layer,
            context.is_visible(river_labels_layer), "river-label", "Fiume",
        )
        self._render_labels(
            map_object, data.lake_labels, lake_labels_layer,
            context.is_visible(lake_labels_layer), "lake-label", "",
        )

    @staticmethod
    def _render_rivers(
        map_object: folium.Map,
        data: HydrographyData,
        context: ModuleContext,
        layer: LayerDefinition,
    ) -> None:
        group = folium.FeatureGroup(name=layer.label, show=context.is_visible(layer))
        if data.european_rivers:
            folium.GeoJson(
                data.european_rivers, smooth_factor=.7,
                style_function=lambda _feature: {"color": "#2187b5", "weight": 2.0, "opacity": .82},
                tooltip=folium.GeoJsonTooltip(
                    fields=["_label"], aliases=[""], labels=False, sticky=True,
                    direction="bottom", offset=(0, 14), class_name="map-tooltip",
                ),
                popup=folium.GeoJsonPopup(fields=["_label"], aliases=[""], labels=False),
            ).add_to(group)
        if data.italian_rivers:
            folium.GeoJson(
                data.italian_rivers, smooth_factor=.45,
                style_function=lambda _feature: {"color": "#147eac", "weight": 2.25, "opacity": .9},
                tooltip=folium.GeoJsonTooltip(
                    fields=["name"], aliases=["Fiume"], sticky=True,
                    direction="bottom", offset=(0, 14), class_name="map-tooltip",
                ),
                popup=folium.GeoJsonPopup(fields=["name"], aliases=["Fiume"]),
            ).add_to(group)
        group.add_to(map_object)

    @staticmethod
    def _render_lakes(
        map_object: folium.Map,
        data: HydrographyData,
        context: ModuleContext,
        layer: LayerDefinition,
    ) -> None:
        group = folium.FeatureGroup(name=layer.label, show=context.is_visible(layer))
        if data.european_lakes:
            folium.GeoJson(
                data.european_lakes, smooth_factor=.7,
                style_function=lambda _feature: {
                    "color": "#1d78a3", "weight": 1.3,
                    "fillColor": "#58b4d8", "fillOpacity": .55,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["_label"], aliases=[""], labels=False, sticky=True,
                    direction="bottom", offset=(0, 14), class_name="map-tooltip",
                ),
                popup=folium.GeoJsonPopup(fields=["_label"], aliases=[""], labels=False),
            ).add_to(group)
        if data.italian_lakes:
            folium.GeoJson(
                data.italian_lakes, smooth_factor=.35,
                style_function=lambda _feature: {
                    "color": "#126d96", "weight": 1.6,
                    "fillColor": "#48a9d0", "fillOpacity": .62,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["name"], aliases=["Lago"], sticky=True,
                    direction="bottom", offset=(0, 14), class_name="map-tooltip",
                ),
                popup=folium.GeoJsonPopup(fields=["name"], aliases=["Lago"]),
            ).add_to(group)
        group.add_to(map_object)

    @staticmethod
    def _render_labels(
        map_object: folium.Map,
        labels: dict[str, tuple],
        layer: LayerDefinition,
        show: bool,
        css_class: str,
        prefix: str,
    ) -> None:
        group = folium.FeatureGroup(name=layer.label, show=show)
        for label, (lat, lon) in labels.items():
            escaped = html.escape(label)
            popup_label = f"{prefix} {escaped}".strip()
            folium.Marker(
                [lat, lon],
                icon=folium.DivIcon(
                    html=f"<span class='{css_class}'>{escaped}</span>",
                    icon_size=(150, 20), icon_anchor=(75, 10),
                ),
                tooltip=map_tooltip(label), popup=f"<b>{popup_label}</b>",
            ).add_to(group)
        group.add_to(map_object)
