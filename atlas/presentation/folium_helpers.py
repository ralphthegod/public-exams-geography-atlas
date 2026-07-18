from __future__ import annotations

import html
from typing import Any

import folium

from atlas.core.geojson import geometry_center, load_label, prepare_admin_labels


def map_tooltip(text: str) -> folium.Tooltip:
    return folium.Tooltip(
        text,
        sticky=True,
        direction="bottom",
        offset=(0, 14),
        class_name="map-tooltip",
    )


def add_boundary_layer(
    map_object: folium.Map,
    data: dict[str, Any] | None,
    name: str,
    color: str,
    weight: float,
    show: bool,
) -> None:
    group = folium.FeatureGroup(name=name, show=show)
    if data:
        prepare_admin_labels(data)
        folium.GeoJson(
            data,
            smooth_factor=1.1,
            style_function=lambda _feature, c=color, w=weight: {
                "fillColor": c, "fillOpacity": 0.025, "color": c, "weight": w,
            },
            highlight_function=lambda _feature, c=color: {
                "fillColor": c, "fillOpacity": 0.14, "weight": 2.4,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["_label"], aliases=[""], labels=False, sticky=True,
                direction="bottom", offset=(0, 14), class_name="map-tooltip",
                style="font-family:DM Sans;padding:6px 10px",
            ),
            popup=folium.GeoJsonPopup(
                fields=["_label"], aliases=[""], labels=False,
                style="font-family:DM Sans;font-weight:600",
            ),
        ).add_to(group)
    group.add_to(map_object)


def add_centroid_points(
    map_object: folium.Map,
    data: dict[str, Any] | None,
    name: str,
    show: bool,
    color: str,
    radius: float,
) -> None:
    group = folium.FeatureGroup(name=name, show=show)
    if data:
        for feature in data.get("features", []):
            center = geometry_center(feature)
            if center:
                label = load_label(feature)
                folium.CircleMarker(
                    center, radius=radius, color="#ffffff", weight=1.6,
                    fill=True, fill_color=color, fill_opacity=.95,
                    tooltip=map_tooltip(label), popup=html.escape(label),
                ).add_to(group)
    group.add_to(map_object)


def add_admin_labels(
    map_object: folium.Map,
    data: dict[str, Any] | None,
    name: str,
    show: bool,
    css_class: str,
) -> None:
    group = folium.FeatureGroup(name=name, show=show)
    if data:
        for feature in data.get("features", []):
            center = geometry_center(feature)
            if center:
                label = html.escape(load_label(feature))
                folium.Marker(
                    center,
                    icon=folium.DivIcon(
                        html=f"<span class='{css_class}'>{label}</span>",
                        icon_size=(150, 20), icon_anchor=(75, 10),
                    ),
                    tooltip=map_tooltip(load_label(feature)),
                    popup=f"<b>{label}</b>",
                ).add_to(group)
    group.add_to(map_object)
