"""Genera il dataset locale dei fiumi etichettati usando Nominatim/OSM."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.config.entities import coordinate_map  # noqa: E402
from atlas.config.settings import SETTINGS  # noqa: E402
from atlas.infrastructure.sources import LocalGeoJsonSource  # noqa: E402

RIVER_LABELS = coordinate_map("river_labels")

ALIASES = {
    "Liri-Garigliano": ("Liri", "Garigliano"),
    "Aterno-Pescara": ("Aterno", "Pescara"),
    "Imera meridionale-Salso": ("Imera meridionale", "Salso"),
    "Cervaro": ("Cervaro", "Torrente Cervaro"),
}


def fetch_named_river(label: str, query_name: str) -> list[dict]:
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": f"{query_name}, Italia",
            "format": "geojson",
            "polygon_geojson": 1,
            "countrycodes": "it",
            "limit": 8,
        },
        headers=SETTINGS.http_headers,
        timeout=35,
    )
    response.raise_for_status()
    features = []
    for feature in response.json().get("features", []):
        geometry_type = feature.get("geometry", {}).get("type", "")
        properties = feature.get("properties", {})
        kind = str(properties.get("type") or properties.get("addresstype") or "").lower()
        category = str(properties.get("category") or properties.get("class") or "").lower()
        if geometry_type in {"LineString", "MultiLineString"} and (kind in {"river", "stream"} or category == "waterway"):
            properties["osm_name"] = properties.get("display_name", "").split(",", 1)[0] or query_name
            properties["name"] = label
            feature["properties"] = properties
            features.append(feature)
    return features


def main() -> None:
    requested = sys.argv[1:] or list(RIVER_LABELS)
    unknown = set(requested) - set(RIVER_LABELS)
    if unknown:
        raise SystemExit("Fiumi sconosciuti: " + ", ".join(sorted(unknown)))
    destination = ROOT / "data" / "italy_rivers.geojson"
    existing = LocalGeoJsonSource(destination).load() if sys.argv[1:] else None
    features = [feature for feature in (existing or {}).get("features", [])
                if feature.get("properties", {}).get("name") not in requested]
    missing = []
    for label in requested:
        matches = []
        for query_name in ALIASES.get(label, (label,)):
            try:
                matches.extend(fetch_named_river(label, query_name))
            except (requests.RequestException, ValueError) as exc:
                print(f"{label}: {exc}", file=sys.stderr)
            time.sleep(1.05)  # Rispetta la policy pubblica di Nominatim.
        if matches:
            features.extend(matches)
        else:
            missing.append(label)
    data = {"type": "FeatureCollection", "features": features}
    if not features:
        raise SystemExit("Nominatim non ha restituito geometrie fluviali.")
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    covered = {feature.get("properties", {}).get("name") for feature in features}
    print(f"Dataset: {len(features)} geometrie per {len(covered - {None})}/{len(RIVER_LABELS)} fiumi.")
    if missing:
        print("Senza geometria: " + ", ".join(missing), file=sys.stderr)


if __name__ == "__main__":
    main()
