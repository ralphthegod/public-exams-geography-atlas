from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import folium

from atlas.core.geojson import geometry_center, load_label, prepare_admin_labels
from atlas.core.models import LayerDefinition, MapEntity, ModuleContext, entity_id
from atlas.presentation.folium_helpers import add_admin_labels, add_boundary_layer, add_centroid_points


@dataclass
class AdministrationData:
    regions: dict[str, Any] | None
    provinces: dict[str, Any] | None


class ItalianAdministrationModule:
    id = "italian_administration"
    layers = (
        LayerDefinition("regions", "Regioni italiane", True, "Confini"),
        LayerDefinition("provinces", "Province e città metropolitane", False, "Confini"),
        LayerDefinition("province_points", "Punti province e città metropolitane", False, "Punti"),
        LayerDefinition("province_labels", "Etichette province e città metropolitane", False, "Etichette"),
    )

    def load(self, context: ModuleContext) -> AdministrationData:
        sources = context.sources.get_many("openpolis.regions", "openpolis.provinces")
        return AdministrationData(
            regions=prepare_admin_labels(sources["openpolis.regions"]),
            provinces=prepare_admin_labels(sources["openpolis.provinces"]),
        )

    def contribute_entities(self, data: AdministrationData, context: ModuleContext) -> None:
        for source, kind, prefix, zoom, layer in (
            (data.regions, "Regione", "region", 7, "regions"),
            (data.provinces, "Provincia / città metropolitana", "province", 9, "provinces"),
        ):
            for feature in (source or {}).get("features", []):
                center = geometry_center(feature)
                if center:
                    name = load_label(feature)
                    context.catalog.add(MapEntity(
                        id=entity_id(prefix, name), kind=kind, name=name,
                        latitude=center[0], longitude=center[1], zoom=zoom, layer_id=layer,
                    ))

    def render(self, map_object: folium.Map, data: AdministrationData, context: ModuleContext) -> None:
        regions, provinces, points, labels = self.layers
        add_boundary_layer(map_object, data.regions, regions.label, "#1d6f5f", 1.8, context.is_visible(regions))
        add_boundary_layer(map_object, data.provinces, provinces.label, "#86745b", .8, context.is_visible(provinces))
        add_centroid_points(map_object, data.provinces, points.label, context.is_visible(points), "#8b6047", 3.6)
        add_admin_labels(map_object, data.provinces, labels.label, context.is_visible(labels), "province-label")
