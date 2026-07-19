"""Integra i fiumi assenti da Natural Earth usando geometrie Nominatim/OSM."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import requests
from shapely.geometry import mapping, shape

from build_european_geography import label_point, line_length_km


FALLBACKS = {
    "AND": ("ad,es", (("Gran Valira", "riu Gran Valira"), ("Valira d'Orient", "Valira d'Orient"), ("Valira del Nord", "Valira del Nord"))),
    "CYP": ("cy", (("Pedieos", "Pedieos"), ("Yialias", "Gialias"), ("Serrachis", "Serrachis"))),
    "DNK": ("dk", (("Gudenå", "Gudenå"), ("Skjern Å", "Skjern Å"), ("Storå", "Storå"))),
    "LIE": ("li,ch,at", (("Reno", "Alpenrhein"), ("Samina", "Samina"), ("Canale interno del Liechtenstein", "Liechtensteiner Binnenkanal"))),
    "LUX": ("lu", (("Alzette", "Alzette"),)),
    "MDA": ("md", (("Răut", "Răut"),)),
    "SMR": ("sm,it", (("Ausa", "torrente Ausa"), ("Marano", "torrente Marano"), ("San Marino", "Rio San Marino"))),
}


def fetch_geometry(query: str, country_code: str, headers: dict[str, str]) -> Any | None:
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": query,
            "format": "geojson",
            "polygon_geojson": 1,
            "countrycodes": country_code,
            "limit": 8,
        },
        headers=headers,
        timeout=40,
    )
    response.raise_for_status()
    candidates = []
    for feature in response.json().get("features", []):
        geometry = feature.get("geometry")
        props = feature.get("properties", {})
        kind = str(props.get("type") or props.get("addresstype") or "").lower()
        category = str(props.get("category") or props.get("class") or "").lower()
        if geometry and geometry.get("type") in {"LineString", "MultiLineString"} and (
            kind in {"river", "stream", "canal", "drain"} or category == "waterway"
        ):
            candidates.append(shape(geometry))
    return max(candidates, key=line_length_km) if candidates else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--countries", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    args = parser.parse_args()
    countries = json.loads(args.countries.read_text(encoding="utf-8"))
    data = json.loads(args.dataset.read_text(encoding="utf-8"))
    country_features = {
        feature["properties"].get("ADM0_A3"): feature
        for feature in countries["features"]
    }
    existing_by_country: dict[str, list[dict[str, Any]]] = {}
    for feature in data["features"]:
        existing_by_country.setdefault(feature["properties"]["country_iso3"], []).append(feature)

    headers = {"User-Agent": "Atlante-Concorsi/3.0 (educational Streamlit map)"}
    added: list[dict[str, Any]] = []
    for code, (osm_country, rivers) in FALLBACKS.items():
        existing = sorted(existing_by_country.get(code, []), key=lambda feature: feature["properties"]["rank"])
        existing_names = {feature["properties"]["name"] for feature in existing}
        country_geometry = shape(country_features[code]["geometry"])
        country_name = country_features[code]["properties"].get("NAME_IT")
        next_rank = len(existing) + 1
        for display_name, query_name in rivers:
            if next_rank > 3:
                break
            if display_name in existing_names:
                continue
            try:
                geometry = fetch_geometry(query_name, osm_country, headers)
            except (requests.RequestException, ValueError) as exc:
                print(f"{code} · {display_name}: {exc}")
                geometry = None
            if geometry is not None:
                clipped = geometry.intersection(country_geometry)
                if not clipped.is_empty and line_length_km(clipped) >= 0.2:
                    latitude, longitude = label_point(clipped)
                    added.append({
                        "type": "Feature",
                        "properties": {
                            "name": display_name,
                            "_label": f"{display_name} · {country_name}",
                            "country": country_name,
                            "country_iso3": code,
                            "rank": next_rank,
                            "length_in_country_km": round(line_length_km(clipped)),
                            "label_lat": latitude,
                            "label_lon": longitude,
                            "source": "OpenStreetMap/Nominatim",
                        },
                        "geometry": mapping(clipped.simplify(0.0008, preserve_topology=True)),
                    })
                    next_rank += 1
            time.sleep(1.1)

    data["features"].extend(added)
    features_by_country: dict[str, list[dict[str, Any]]] = {}
    for feature in data["features"]:
        features_by_country.setdefault(feature["properties"]["country_iso3"], []).append(feature)
    for features in features_by_country.values():
        features.sort(
            key=lambda feature: feature["properties"].get("length_in_country_km", 0),
            reverse=True,
        )
        for rank, feature in enumerate(features, start=1):
            feature["properties"]["rank"] = rank
    counts = {code: 0 for code in data["metadata"]["country_counts"]}
    for feature in data["features"]:
        counts[feature["properties"]["country_iso3"]] += 1
    data["metadata"]["country_counts"] = counts
    data["metadata"]["fallback_source"] = "OpenStreetMap contributors via Nominatim"
    args.dataset.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print(f"Aggiunte {len(added)} geometrie.")
    print("Paesi con meno di tre:", {key: value for key, value in counts.items() if value < 3})


if __name__ == "__main__":
    main()
