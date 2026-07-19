# Public Exams Geography Atlas

An interactive Streamlit atlas designed to help candidates review geography questions for Italian public competitive examinations (*concorsi pubblici*).

The application combines an OpenStreetMap basemap with European countries, Italian regions and provinces, regional capitals, rivers, lakes, river sources, mountains, labels, and a dataset-only search experience. Every visible feature is organized as a switchable Folium layer.

## Why this project exists

Geography questions in Italian public examinations often require candidates to connect administrative and physical geography: regions and capitals, provinces and metropolitan cities, rivers and their sources, lakes, mountains, and the position of European countries.

This project turns that material into an explorable map that can be used for active recall instead of relying only on static pages. It was initially created for INPS exam preparation, but its modular architecture is intended to support other Italian public examinations and additional geography topics.

### Editorial reference

The following book was used as the primary vertical reference for defining the study context and the type of examination the atlas supports:

> **Concorso INPS 2026 1024 funzionari PECS (Progettazione, Erogazione e Controllo dei Servizi) - Manuale Teoria e Quiz per la preparazione della prova scritta (Italian Edition)**

- Full title: **Concorso INPS 2026 1024 funzionari PECS (Progettazione, Erogazione e Controllo dei Servizi) - Manuale Teoria e Quiz per la preparazione della prova scritta (Italian Edition)**
- ISBN-13: **9788891683656**
- ISBN-10: **8891683655**
- Authors: [**AA. VV.**](https://isbndb.com/author/AA.%20VV.)

The book is a study-scope reference only. Its copyrighted text and quizzes are not reproduced in this repository. Geographic geometries and map data come from the open-data sources listed below.

## Features

- OpenStreetMap and CartoDB basemaps.
- European national boundaries and searchable countries.
- Italian regions, provinces, and metropolitan cities.
- Italian regional capitals.
- European national capitals, with independently switchable points and labels.
- Major European and Italian rivers.
- Up to three principal rivers for each European country in an independent module.
- Local OpenStreetMap geometries for the manually selected Italian rivers.
- Major European and Italian lakes.
- Local OpenStreetMap polygons for nine major Italian lakes.
- River and lake labels that can be enabled independently.
- River sources, including the source of the Tiber on Monte Fumaiolo.
- Important Italian and European mountains.
- Dataset-only search: results are limited to entities included in the atlas.
- Search navigation without a Streamlit rerun, so selected map layers are preserved.
- Touch-friendly controls and responsive layouts for iPad portrait, landscape, and Split View.
- Home Screen icon and web-app metadata for Safari on iPadOS.
- Cached, simplified GeoJSON payloads for faster client-side rendering.

## Quick start

The recommended runtime is **Python 3.12**.

### 1. Clone the repository

```bash
git clone <repository-url>
cd mappa_concorso_inps
```

### 2. Create a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

For local development, including tests:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

For a production-only installation:

```bash
python -m pip install -r requirements.txt
```

### 4. Start the application

```bash
streamlit run app.py
```

Streamlit will print the local address, normally:

```text
http://localhost:8501
```

That is all that is required. No database, API key, or Streamlit secret is needed.

### Common startup issues

If the `streamlit` command is not available on your shell path, use:

```bash
python -m streamlit run app.py
```

If PowerShell prevents virtual-environment activation, the environment can be used directly without changing the execution policy:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

If your operating system exposes Python as `python3`, replace `python` with `python3` in the commands above.

The initial startup requires internet access for Natural Earth, Openpolis, and map tiles. Remote GeoJSON responses are cached by Streamlit, while the detailed Italian river and lake geometries are bundled in the repository.

After changing cached data or source configuration, clear the Streamlit cache with:

```bash
streamlit cache clear
```

## Running the tests

```bash
python -m pytest
```

The test suite checks the core catalog, GeoJSON transformations, module contracts, layer uniqueness, local dataset coverage, search generation, touch behavior, and the thin public entrypoint.

To perform a quick syntax check as well:

```bash
python -m compileall -q app.py atlas tools
python -m pytest -q
```

## Architecture

`app.py` is intentionally tiny. It delegates application assembly to an explicit composition root and does not contain geographic or presentation logic.

```text
app.py
atlas/
├── bootstrap.py                     # Composition root and dependency wiring
├── application.py                   # Top-level application object
├── config/
│   ├── settings.py                  # URLs, paths, headers, and map bounds
│   ├── sources.py                   # GeoJSON optimization rules
│   ├── entities.py                  # Typed access to static configuration
│   └── static_entities.json         # Capitals, labels, sources, mountains, defaults
├── core/
│   ├── contracts.py                 # MapModule, MapControl, and GeoJsonSource protocols
│   ├── engine.py                    # Generic Folium map engine
│   ├── catalog.py                   # Unified searchable entity catalog
│   ├── models.py                    # LayerDefinition, MapEntity, and ModuleContext
│   └── geojson.py                   # Geometry centers, labels, filters, simplification
├── infrastructure/
│   └── sources/
│       ├── geojson.py               # HTTP, local files, cache, optimization, registry
│       └── osm.py                   # Overpass fallback for Italian rivers
├── modules/
│   ├── countries.py
│   ├── italian_admin.py
│   ├── capitals.py
│   ├── european_capitals/          # National-capital module and local entities
│   ├── european_national_rivers/   # Per-country river module and local GeoJSON
│   ├── hydrography.py
│   ├── river_sources.py
│   ├── mountains.py
│   └── search.py
└── presentation/
    ├── page.py                       # Streamlit page and web-app metadata
    ├── folium_helpers.py             # Shared Folium rendering helpers
    ├── page.css                      # Streamlit responsive layout
    ├── map.css                       # Leaflet and touch-control styles
    └── templates/search_control.js   # Client-side search control
```

### Runtime flow

The application follows this sequence:

1. `app.py` calls `create_application()`.
2. `bootstrap.py` creates the source registry, entity catalog, modules, controls, and map engine.
3. The engine loads independent modules concurrently.
4. Each module contributes normalized `MapEntity` objects to the catalog.
5. Each module renders its Folium layers.
6. The engine adds shared Leaflet controls and the layer selector.
7. The search control serializes the completed entity catalog into the map.
8. Streamlit renders the resulting Folium document.

There is no automatic module discovery or reflection-based dependency injection. Dependencies are registered explicitly in `atlas/bootstrap.py`, which keeps the public architecture easy to inspect and debug.

## Module contract

A geographic module represents one coherent capability, not necessarily one checkbox. For example, `HydrographyModule` owns four related layers:

- `Traccia fiumi`
- `Traccia laghi`
- `Etichette fiumi`
- `Etichette laghi`

`EuropeanCapitalsModule` and `EuropeanNationalRiversModule` remain independent and own their respective point/label and trace/label pairs.

Every module implements the following lifecycle:

```python
class MapModule(Protocol):
    id: str
    layers: tuple[LayerDefinition, ...]

    def load(self, context: ModuleContext) -> Any: ...
    def contribute_entities(self, data: Any, context: ModuleContext) -> None: ...
    def render(self, map_object: folium.Map, data: Any, context: ModuleContext) -> None: ...
```

Responsibilities are intentionally separated:

- `load()` obtains module data through the source registry.
- `contribute_entities()` describes what the search system can find.
- `render()` translates module data into Folium layers and markers.
- `LayerDefinition` controls the public label and initial visibility of each checkbox.

## Adding a new module

The following example adds a searchable volcano layer.

### 1. Create the module

Create `atlas/modules/volcanoes.py`:

```python
from __future__ import annotations

import folium

from atlas.core.models import (
    LayerDefinition,
    MapEntity,
    ModuleContext,
    entity_id,
)
from atlas.presentation.folium_helpers import map_tooltip


class VolcanoesModule:
    id = "volcanoes"

    layers = (
        LayerDefinition(
            id="volcanoes",
            label="Vulcani",
            default_visible=False,
            category="Rilievi",
        ),
    )

    def load(self, context: ModuleContext) -> dict[str, tuple[float, float, str]]:
        # Static data is fine for a small module. A registered source should be
        # used for larger or remotely maintained datasets.
        return {
            "Etna": (37.7510, 14.9934, "Sicilia"),
            "Vesuvio": (40.8214, 14.4265, "Campania"),
        }

    def contribute_entities(self, data, context: ModuleContext) -> None:
        for name, (latitude, longitude, region) in data.items():
            context.catalog.add(
                MapEntity(
                    id=entity_id("volcano", name),
                    kind="Vulcano",
                    name=name,
                    latitude=latitude,
                    longitude=longitude,
                    zoom=10,
                    layer_id="volcanoes",
                    metadata={"regione": region},
                )
            )

    def render(self, map_object: folium.Map, data, context: ModuleContext) -> None:
        layer = self.layers[0]
        group = folium.FeatureGroup(
            name=layer.label,
            show=context.is_visible(layer),
        )

        for name, (latitude, longitude, region) in data.items():
            folium.CircleMarker(
                [latitude, longitude],
                radius=6,
                color="#ffffff",
                weight=2,
                fill=True,
                fill_color="#b5483e",
                fill_opacity=1,
                tooltip=map_tooltip(name),
                popup=f"<b>{name}</b><br>{region}",
            ).add_to(group)

        group.add_to(map_object)
```

### 2. Export the module

Update `atlas/modules/__init__.py`:

```python
from atlas.modules.volcanoes import VolcanoesModule
```

Adding it to `__all__` is recommended for consistency.

### 3. Register the module

Update the `modules` list in `atlas/bootstrap.py`:

```python
modules = [
    CountriesModule(),
    ItalianAdministrationModule(),
    CapitalsModule(),
    HydrographyModule(),
    RiverSourcesModule(),
    MountainsModule(),
    VolcanoesModule(),
]
```

The engine will automatically load and render the module. Because the module contributes `MapEntity` objects, `Etna` and `Vesuvio` will also appear in search without changing the search implementation.

### 4. Add tests

At minimum, verify that:

- every new layer ID is unique;
- coordinates are valid;
- entity IDs are unique;
- the module still renders when an optional remote source is unavailable;
- properties required by tooltips and popups are preserved after optimization.

## Adding a new data source

Modules should not call `requests` or open files directly. Register an adapter in the source registry and retrieve it through `ModuleContext`.

### Local GeoJSON

```python
from atlas.infrastructure.sources import LocalGeoJsonSource

sources["local.volcanoes"] = LocalGeoJsonSource(
    SETTINGS.root / "data" / "volcanoes.geojson"
)
```

### Remote GeoJSON

```python
from atlas.infrastructure.sources import RemoteGeoJsonSource

sources["remote.volcanoes"] = RemoteGeoJsonSource(
    "https://example.org/volcanoes.geojson",
    SETTINGS.http_headers,
)
```

### Optimized GeoJSON

For map rendering, wrap large datasets in `OptimizedGeoJsonSource`:

```python
from atlas.infrastructure.sources import OptimizedGeoJsonSource

sources["remote.volcanoes"] = OptimizedGeoJsonSource(
    source=RemoteGeoJsonSource(url, SETTINGS.http_headers),
    tolerance=0.001,
    allowed_properties={"name", "elevation"},
)
```

Choose the simplification tolerance carefully and add a test for any property required by labels, popups, search, or styling.

Inside the module:

```python
def load(self, context):
    return context.sources.get("remote.volcanoes")
```

Several independent sources can be loaded concurrently:

```python
def load(self, context):
    return context.sources.get_many(
        "remote.volcanoes",
        "local.volcano_labels",
    )
```

## Search model

Search does not inspect Folium objects or raw GeoJSON. It consumes the unified `EntityCatalog` after every geographic module has registered its entities.

A searchable entity contains:

```python
MapEntity(
    id="river:tevere",
    kind="Fiume",
    name="Tevere",
    latitude=42.15,
    longitude=12.35,
    zoom=9,
    layer_id="rivers",
)
```

Important rules:

- `id` must be globally unique; use `entity_id(kind, name)` where possible.
- `kind` becomes the category shown below each search suggestion.
- `name` is the visible result name.
- coordinates and zoom determine the target map view.
- `aliases` is available in the domain model for future alternative-name indexing.
- `layer_id` links the entity to its owning map layer.

The browser receives only the completed search index. Selecting a result calls Leaflet directly and does not rerun the Streamlit script.

## Geographic data sources

- [OpenStreetMap](https://www.openstreetmap.org/copyright): basemap and detailed local geometries.
- [Natural Earth](https://www.naturalearthdata.com/): European countries, major rivers, and lakes.
- [Openpolis / geojson-italy](https://github.com/openpolis/geojson-italy): Italian administrative boundaries.
- [Overpass API](https://overpass-api.de/): fallback river retrieval when the bundled local dataset is missing.
- [Nominatim](https://nominatim.org/): maintenance scripts used to regenerate local river and lake datasets.

Bundled local datasets:

```text
data/italy_rivers.geojson
data/italy_lakes.geojson
atlas/modules/european_capitals/entities.json
atlas/modules/european_national_rivers/rivers.geojson
```

Regenerate them with:

```bash
python tools/fetch_rivers.py
python tools/fetch_lakes.py
```

These commands access public OpenStreetMap services. Run them only when updating the bundled datasets and respect the relevant service usage policies.

## iPad and touch behavior

The map supports iPad portrait, landscape, and Split View layouts. On touch-oriented displays:

- the layer control starts collapsed;
- interactive targets are enlarged;
- the minimap and mouse-coordinate control are hidden;
- search suggestions use large rows and display no more than six results;
- geographic elements expose tap-friendly popups;
- safe-area insets are respected.

In Safari, use **Share → Add to Home Screen** to launch the atlas with its dedicated icon and web-app metadata.

Regenerate the PNG icons after changing `static/icon.svg`:

```bash
python tools/generate_icons.py
```

## Deploying to Streamlit Community Cloud

1. Push the complete repository to GitHub.
2. Open [share.streamlit.io](https://share.streamlit.io).
3. Sign in and connect the GitHub repository.
4. Create a new application.
5. Select the repository and the `main` branch.
6. Set the entrypoint to `app.py`.
7. Select Python 3.12 in the advanced settings.
8. Deploy.

The application does not currently require secrets. Future pushes to the selected branch will trigger a new deployment automatically.

## Contribution checklist

Before opening a pull request:

```bash
python -m compileall -q app.py atlas tools
python -m pytest -q
```

Please also verify that:

- the map loads with remote services temporarily unavailable;
- new layer names are concise and understandable in Italian;
- layer IDs and entity IDs are unique;
- search includes only entities intentionally exposed by modules;
- large GeoJSON files are simplified before being serialized to Folium;
- required OpenStreetMap, Natural Earth, or third-party attribution is preserved;
- the interface remains usable at tablet and narrow viewport sizes.
