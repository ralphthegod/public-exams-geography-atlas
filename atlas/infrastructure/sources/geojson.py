from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import requests
import streamlit as st

from atlas.core.contracts import GeoJsonSource
from atlas.core.geojson import optimize_geojson


@st.cache_data(ttl=86_400, show_spinner=False)
def _fetch_geojson(url: str, headers: tuple[tuple[str, str], ...]) -> dict[str, Any] | None:
    try:
        response = requests.get(url, headers=dict(headers), timeout=25)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, json.JSONDecodeError):
        return None


@st.cache_data(show_spinner=False)
def _load_local_geojson(path: str, modified_at: float) -> dict[str, Any] | None:
    del modified_at  # Parte della cache key: invalida il dato quando cambia il file.
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


@st.cache_data(show_spinner=False)
def _optimize_cached(
    data: dict[str, Any] | None,
    tolerance: float,
    allowed_properties: tuple[str, ...],
) -> dict[str, Any] | None:
    return optimize_geojson(data, tolerance, frozenset(allowed_properties))


class RemoteGeoJsonSource:
    def __init__(self, url: str, headers: dict[str, str]) -> None:
        self.url = url
        self.headers = tuple(sorted(headers.items()))

    def load(self) -> dict[str, Any] | None:
        return _fetch_geojson(self.url, self.headers)


class LocalGeoJsonSource:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, Any] | None:
        modified_at = self.path.stat().st_mtime if self.path.exists() else 0.0
        return _load_local_geojson(str(self.path), modified_at)


class OptimizedGeoJsonSource:
    def __init__(self, source: GeoJsonSource, tolerance: float, allowed_properties: set[str]) -> None:
        self.source = source
        self.tolerance = tolerance
        self.allowed_properties = tuple(sorted(allowed_properties))

    def load(self) -> dict[str, Any] | None:
        return _optimize_cached(self.source.load(), self.tolerance, self.allowed_properties)


class FallbackSource:
    def __init__(self, primary: GeoJsonSource, fallback: GeoJsonSource) -> None:
        self.primary = primary
        self.fallback = fallback

    def load(self) -> dict[str, Any] | None:
        return self.primary.load() or self.fallback.load()


class SourceRegistry:
    def __init__(self, sources: dict[str, GeoJsonSource]) -> None:
        self._sources = dict(sources)

    def get(self, source_id: str) -> dict[str, Any] | None:
        try:
            source = self._sources[source_id]
        except KeyError as exc:
            raise KeyError(f"Sorgente non registrata: {source_id}") from exc
        return source.load()

    def get_many(self, *source_ids: str) -> dict[str, dict[str, Any] | None]:
        with ThreadPoolExecutor(max_workers=min(8, len(source_ids))) as executor:
            values = executor.map(self.get, source_ids)
            return dict(zip(source_ids, values))

    @property
    def ids(self) -> frozenset[str]:
        return frozenset(self._sources)
