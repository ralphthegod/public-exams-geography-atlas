from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from shapely.geometry import LineString, MultiLineString, mapping, shape
from shapely.ops import unary_union


EUROPEAN_COUNTRY_CODES = frozenset(
    "ALB AND ARM AUT AZE BLR BEL BIH BGR HRV CYP CZE DNK EST FIN FRA GEO DEU "
    "GRC HUN ISL IRL ITA KOS LVA LIE LTU LUX MLT MDA MCO MNE NLD MKD NOR "
    "POL PRT ROU RUS SMR SRB SVK SVN ESP SWE CHE TUR UKR GBR VAT".split()
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def country_code(properties: dict[str, Any]) -> str:
    return str(properties.get("ADM0_A3") or properties.get("SOV_A3") or "")


def italian_name(properties: dict[str, Any], *fallbacks: str) -> str:
    for key in ("NAME_IT", "name_it", *fallbacks):
        if properties.get(key):
            return str(properties[key])
    return ""


def iter_lines(geometry: Any) -> Iterable[LineString]:
    if isinstance(geometry, LineString):
        yield geometry
    elif isinstance(geometry, MultiLineString):
        yield from geometry.geoms
    elif hasattr(geometry, "geoms"):
        for child in geometry.geoms:
            yield from iter_lines(child)


def line_length_km(geometry: Any) -> float:
    radius_km = 6371.0088
    total = 0.0
    for line in iter_lines(geometry):
        points = list(line.coords)
        for (lon1, lat1), (lon2, lat2) in zip(points, points[1:]):
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = phi2 - phi1
            dlambda = math.radians(lon2 - lon1)
            value = (
                math.sin(dphi / 2) ** 2
                + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
            )
            total += radius_km * 2 * math.atan2(math.sqrt(value), math.sqrt(max(0, 1 - value)))
    return total


def label_point(geometry: Any) -> tuple[float, float]:
    lines = list(iter_lines(geometry))
    longest = max(lines, key=lambda item: item.length)
    point = longest.interpolate(0.5, normalized=True)
    return round(point.y, 5), round(point.x, 5)


def build_capitals(countries: dict[str, Any], places: dict[str, Any]) -> dict[str, Any]:
    country_names = {
        country_code(feature["properties"]): italian_name(
            feature["properties"], "ADMIN", "NAME"
        )
        for feature in countries["features"]
        if country_code(feature["properties"]) in EUROPEAN_COUNTRY_CODES
    }
    capitals: list[dict[str, Any]] = []
    for feature in places["features"]:
        props = feature.get("properties", {})
        code = country_code(props)
        if props.get("ADM0CAP") != 1 or code not in EUROPEAN_COUNTRY_CODES:
            continue
        name = italian_name(props, "NAME", "NAMEASCII")
        lon, lat = feature["geometry"]["coordinates"]
        capitals.append({
            "name": name,
            "country": country_names[code],
            "country_iso3": code,
            "latitude": round(float(lat), 5),
            "longitude": round(float(lon), 5),
            "label_offset": [0, -13],
        })
    capitals.sort(key=lambda item: (item["country"], item["name"]))
    missing = sorted(EUROPEAN_COUNTRY_CODES - {item["country_iso3"] for item in capitals})
    if missing:
        raise ValueError(f"Capitali mancanti: {', '.join(missing)}")
    return {"source": "Natural Earth 1:10m populated places", "capitals": capitals}


def river_key(properties: dict[str, Any]) -> str:
    wikidata = properties.get("wikidataid") or properties.get("WIKIDATAID")
    name = italian_name(properties, "name", "NAME", "name_en", "NAME_EN")
    return str(wikidata or name).casefold()


def build_rivers(
    countries: dict[str, Any],
    river_collections: list[dict[str, Any]],
) -> dict[str, Any]:
    country_features = {
        country_code(feature["properties"]): feature
        for feature in countries["features"]
        if country_code(feature["properties"]) in EUROPEAN_COUNTRY_CODES
    }
    grouped: dict[str, list[Any]] = defaultdict(list)
    properties_by_key: dict[str, dict[str, Any]] = {}
    for collection in river_collections:
        for feature in collection["features"]:
            props = feature.get("properties", {})
            name = italian_name(props, "name", "NAME", "name_en", "NAME_EN")
            if not name or not feature.get("geometry"):
                continue
            key = river_key(props)
            grouped[key].append(shape(feature["geometry"]))
            properties_by_key.setdefault(key, props)

    rivers = {key: unary_union(parts) for key, parts in grouped.items()}
    features: list[dict[str, Any]] = []
    country_counts: dict[str, int] = {}
    for code, country_feature in sorted(country_features.items()):
        country_geometry = shape(country_feature["geometry"])
        candidates: list[tuple[float, str, Any]] = []
        for key, river_geometry in rivers.items():
            if not river_geometry.bounds or not country_geometry.intersects(river_geometry):
                continue
            clipped = river_geometry.intersection(country_geometry)
            length = line_length_km(clipped)
            if length >= 1:
                candidates.append((length, key, clipped))
        selected = sorted(candidates, reverse=True, key=lambda item: item[0])[:3]
        country_counts[code] = len(selected)
        country_props = country_feature["properties"]
        country_name = italian_name(country_props, "ADMIN", "NAME")
        for rank, (length, key, geometry) in enumerate(selected, start=1):
            river_props = properties_by_key[key]
            name = italian_name(river_props, "name", "NAME", "name_en", "NAME_EN")
            lat, lon = label_point(geometry)
            simplified = geometry.simplify(0.002, preserve_topology=True)
            features.append({
                "type": "Feature",
                "properties": {
                    "name": name,
                    "_label": f"{name} · {country_name}",
                    "country": country_name,
                    "country_iso3": code,
                    "rank": rank,
                    "length_in_country_km": round(length),
                    "label_lat": lat,
                    "label_lon": lon,
                },
                "geometry": mapping(simplified),
            })
    return {
        "type": "FeatureCollection",
        "metadata": {
            "source": "Natural Earth 1:10m rivers and Europe supplement",
            "ranking": "Lunghezza cartografica del tratto entro i confini nazionali",
            "country_counts": country_counts,
        },
        "features": features,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--countries", type=Path, required=True)
    parser.add_argument("--places", type=Path, required=True)
    parser.add_argument("--rivers", type=Path, action="append", required=True)
    parser.add_argument("--capitals-output", type=Path, required=True)
    parser.add_argument("--rivers-output", type=Path, required=True)
    args = parser.parse_args()

    countries = load(args.countries)
    write(args.capitals_output, build_capitals(countries, load(args.places)))
    write(
        args.rivers_output,
        build_rivers(countries, [load(path) for path in args.rivers]),
    )


if __name__ == "__main__":
    main()
