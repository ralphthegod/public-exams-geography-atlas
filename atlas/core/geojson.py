from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from shapely.errors import GEOSException
from shapely.geometry import mapping, shape


def load_label(feature: dict[str, Any]) -> str:
    props = feature.get("properties", {})
    return str(
        props.get("_label") or props.get("prov_name") or props.get("reg_name")
        or props.get("name") or props.get("ADMIN") or "Area"
    )


def prepare_admin_labels(data: dict[str, Any] | None) -> dict[str, Any] | None:
    if data:
        for feature in data.get("features", []):
            props = feature.setdefault("properties", {})
            props["_label"] = str(
                props.get("prov_name") or props.get("reg_name") or props.get("_label")
                or props.get("name") or props.get("ADMIN") or "Area"
            )
    return data


def coordinate_pairs(value: Any) -> Iterator[tuple[float, float]]:
    if isinstance(value, (list, tuple)) and len(value) >= 2 and all(
        isinstance(number, (int, float)) for number in value[:2]
    ):
        yield float(value[0]), float(value[1])
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from coordinate_pairs(child)


def geometry_center(feature: dict[str, Any]) -> tuple[float, float] | None:
    props = feature.get("properties", {})
    label_lat = props.get("LABEL_Y") or props.get("label_y")
    label_lon = props.get("LABEL_X") or props.get("label_x")
    if isinstance(label_lat, (int, float)) and isinstance(label_lon, (int, float)):
        return float(label_lat), float(label_lon)
    pairs = list(coordinate_pairs(feature.get("geometry", {}).get("coordinates", [])))
    if not pairs:
        return None
    longitudes, latitudes = zip(*pairs)
    return (
        (min(latitudes) + max(latitudes)) / 2,
        (min(longitudes) + max(longitudes)) / 2,
    )


def feature_in_bbox(
    feature: dict[str, Any],
    bbox: tuple[float, float, float, float],
) -> bool:
    center = geometry_center(feature)
    return bool(center and bbox[1] <= center[0] <= bbox[3] and bbox[0] <= center[1] <= bbox[2])


def select_features(data: dict[str, Any] | None, predicate) -> dict[str, Any] | None:
    if not data:
        return None
    return {
        "type": "FeatureCollection",
        "features": [feature for feature in data.get("features", []) if predicate(feature)],
    }


def _round_coordinates(value: Any, decimals: int = 5) -> Any:
    if isinstance(value, (list, tuple)):
        return [_round_coordinates(item, decimals) for item in value]
    if isinstance(value, float):
        return round(value, decimals)
    return value


def optimize_geojson(
    data: dict[str, Any] | None,
    tolerance: float,
    allowed_properties: set[str] | frozenset[str],
) -> dict[str, Any] | None:
    if not data:
        return None
    optimized: list[dict[str, Any]] = []
    for feature in data.get("features", []):
        geometry = feature.get("geometry")
        if not geometry:
            continue
        try:
            simplified = shape(geometry).simplify(tolerance, preserve_topology=True)
        except (GEOSException, TypeError, ValueError):
            simplified = None
        if simplified is None or simplified.is_empty:
            continue
        properties = {
            key: value for key, value in feature.get("properties", {}).items()
            if key in allowed_properties and value not in (None, "")
        }
        compact_geometry = mapping(simplified)
        compact_geometry["coordinates"] = _round_coordinates(compact_geometry.get("coordinates", []))
        optimized.append({"type": "Feature", "properties": properties, "geometry": compact_geometry})
    return {"type": "FeatureCollection", "features": optimized}
