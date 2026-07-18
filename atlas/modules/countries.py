from __future__ import annotations

from typing import Any

import folium

from atlas.config.entities import static_entities
from atlas.core.geojson import geometry_center, load_label, select_features
from atlas.core.models import LayerDefinition, MapEntity, ModuleContext, entity_id
from atlas.presentation.folium_helpers import add_admin_labels, add_boundary_layer, add_centroid_points


class CountriesModule:
    id = "countries"
    layers = (
        LayerDefinition("countries", "Confini nazionali europei", True, "Confini"),
        LayerDefinition("country_points", "Punti nazioni europee", False, "Punti"),
        LayerDefinition("country_labels", "Etichette nazioni europee", False, "Etichette"),
    )

    def load(self, context: ModuleContext) -> dict[str, Any] | None:
        data = context.sources.get("natural_earth.countries")
        names = static_entities()["country_names_it"]

        def is_european(feature: dict[str, Any]) -> bool:
            props = feature.get("properties", {})
            admin = props.get("ADMIN") or props.get("NAME") or props.get("name")
            continent = props.get("CONTINENT") or props.get("continent")
            return continent == "Europe" or admin in {
                "Turkey", "Cyprus", "Georgia", "Armenia", "Azerbaijan",
            }

        selected = select_features(data, is_european)
        for feature in (selected or {}).get("features", []):
            props = feature.setdefault("properties", {})
            admin = props.get("ADMIN") or props.get("NAME") or props.get("name")
            props["_label"] = names.get(str(admin), str(admin))
        return selected

    def contribute_entities(self, data: dict[str, Any] | None, context: ModuleContext) -> None:
        for feature in (data or {}).get("features", []):
            center = geometry_center(feature)
            if center:
                name = load_label(feature)
                context.catalog.add(MapEntity(
                    id=entity_id("country", name), kind="Paese europeo", name=name,
                    latitude=center[0], longitude=center[1], zoom=6, layer_id="countries",
                ))

    def render(self, map_object: folium.Map, data: dict[str, Any] | None, context: ModuleContext) -> None:
        countries, points, labels = self.layers
        add_boundary_layer(map_object, data, countries.label, "#4e625b", 1.15, context.is_visible(countries))
        add_centroid_points(map_object, data, points.label, context.is_visible(points), "#4e625b", 3.2)
        add_admin_labels(map_object, data, labels.label, context.is_visible(labels), "country-label")
