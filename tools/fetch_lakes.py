"""Genera il dataset locale dei principali laghi italiani usando Nominatim/OSM."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.config.entities import static_entities  # noqa: E402
from atlas.config.settings import SETTINGS  # noqa: E402
from atlas.infrastructure.sources import LocalGeoJsonSource  # noqa: E402

ITALIAN_LAKES = set(static_entities()["italian_lakes"])
LOCAL_LAKES_PATH = SETTINGS.root / "data" / "italy_lakes.geojson"

ALIASES = {
    "Lago Maggiore": ("Lago Maggiore", "Verbano"),
    "Lago di Como": ("Lago di Como", "Lario"),
    "Lago d'Iseo": ("Lago d'Iseo", "Sebino"),
    "Lago di Lugano": ("Lago di Lugano", "Ceresio"),
    "Lago d'Orta": ("Lago d'Orta", "Cusio"),
}


def fetch_named_lake(label: str, query_name: str) -> list[dict]:
    transboundary = label == "Lago di Lugano"
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": query_name if transboundary else f"{query_name}, Italia",
            "format": "geojson",
            "polygon_geojson": 1,
            "countrycodes": "it,ch" if transboundary else "it",
            "limit": 6,
        },
        headers=SETTINGS.http_headers,
        timeout=40,
    )
    response.raise_for_status()
    matches = []
    for feature in response.json().get("features", []):
        geometry_type = feature.get("geometry", {}).get("type", "")
        properties = feature.get("properties", {})
        kind = str(properties.get("type") or properties.get("addresstype") or "").lower()
        category = str(properties.get("category") or properties.get("class") or "").lower()
        if geometry_type in {"Polygon", "MultiPolygon"} and (
            kind in {"water", "lake", "reservoir"} or category in {"natural", "water"}
        ):
            feature["properties"] = {"name": label}
            matches.append(feature)
    return matches[:1]


def main() -> None:
    requested = sys.argv[1:] or sorted(ITALIAN_LAKES)
    unknown = set(requested) - ITALIAN_LAKES
    if unknown:
        raise SystemExit("Laghi sconosciuti: " + ", ".join(sorted(unknown)))
    destination = LOCAL_LAKES_PATH
    existing = LocalGeoJsonSource(destination).load() if sys.argv[1:] else None
    features = [
        feature for feature in (existing or {}).get("features", [])
        if feature.get("properties", {}).get("name") not in requested
    ]
    missing = []
    for label in requested:
        matches = []
        for query_name in ALIASES.get(label, (label,)):
            try:
                matches = fetch_named_lake(label, query_name)
            except (requests.RequestException, ValueError) as exc:
                print(f"{label}: {exc}", file=sys.stderr)
            time.sleep(1.05)
            if matches:
                break
        if matches:
            features.extend(matches)
        else:
            missing.append(label)
    if not features:
        raise SystemExit("Nominatim non ha restituito geometrie lacustri.")
    data = {"type": "FeatureCollection", "features": features}
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    covered = {feature.get("properties", {}).get("name") for feature in features}
    print(f"Dataset: {len(features)} geometrie per {len(covered - {None})}/{len(ITALIAN_LAKES)} laghi.")
    if missing:
        print("Senza geometria: " + ", ".join(missing), file=sys.stderr)


if __name__ == "__main__":
    main()
