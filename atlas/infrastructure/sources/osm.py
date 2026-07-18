from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import requests
import streamlit as st


@st.cache_data(ttl=3_600, show_spinner=False)
def _fetch_osm_rivers(
    names: tuple[str, ...],
    endpoints: tuple[str, ...],
    headers: tuple[tuple[str, str], ...],
) -> dict[str, Any] | None:
    chunks = [names[index:index + 10] for index in range(0, len(names), 10)]

    def fetch_chunk(chunk: tuple[str, ...]) -> list[dict[str, Any]]:
        patterns = []
        for name in chunk:
            escaped = re.escape(name).replace(r"\-", "[-–— ]").replace("'", "[’']")
            patterns.append(escaped)
        regex = "|".join(patterns)
        query = (
            f'[out:json][timeout:18];way["waterway"~"river|stream"]'
            f'["name"~"^({regex})$",i](36.0,6.0,47.2,18.8);out tags geom;'
        )
        for endpoint in endpoints:
            try:
                response = requests.post(endpoint, data={"data": query}, headers=dict(headers), timeout=20)
                response.raise_for_status()
                features = []
                for element in response.json().get("elements", []):
                    coordinates = [[point["lon"], point["lat"]] for point in element.get("geometry", [])]
                    if len(coordinates) > 1:
                        features.append({
                            "type": "Feature",
                            "properties": {"name": element.get("tags", {}).get("name", "Fiume")},
                            "geometry": {"type": "LineString", "coordinates": coordinates},
                        })
                if features:
                    return features
            except (requests.RequestException, ValueError):
                continue
        return []

    features: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        for batch in executor.map(fetch_chunk, chunks):
            features.extend(batch)
    return {"type": "FeatureCollection", "features": features} if features else None


class OsmRiverFallbackSource:
    def __init__(
        self,
        names: set[str],
        endpoints: tuple[str, ...],
        headers: dict[str, str],
    ) -> None:
        aliases = names | {"Liri", "Garigliano", "Aterno", "Pescara", "Imera Meridionale", "Salso"}
        self.names = tuple(sorted(aliases))
        self.endpoints = endpoints
        self.headers = tuple(sorted(headers.items()))

    def load(self) -> dict[str, Any] | None:
        return _fetch_osm_rivers(self.names, self.endpoints, self.headers)
