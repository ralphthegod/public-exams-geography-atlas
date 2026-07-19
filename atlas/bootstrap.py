from __future__ import annotations

from atlas.application import AtlasApplication
from atlas.config.entities import coordinate_map, static_entities
from atlas.config.settings import SETTINGS
from atlas.config.sources import SOURCE_OPTIMIZATION
from atlas.core.catalog import EntityCatalog
from atlas.core.engine import MapEngine
from atlas.core.models import ModuleContext
from atlas.infrastructure.sources import (
    FallbackSource,
    LocalGeoJsonSource,
    OptimizedGeoJsonSource,
    OsmRiverFallbackSource,
    RemoteGeoJsonSource,
    SourceRegistry,
)
from atlas.modules import (
    CapitalsModule,
    CountriesModule,
    EuropeanCapitalsModule,
    EuropeanNationalRiversModule,
    HydrographyModule,
    ItalianAdministrationModule,
    MountainsModule,
    RiverSourcesModule,
)
from atlas.modules.search import SearchControl
from atlas.presentation.page import PageRenderer


def _optimized_remote(key: str):
    tolerance, properties = SOURCE_OPTIMIZATION[key]
    return OptimizedGeoJsonSource(
        RemoteGeoJsonSource(SETTINGS.data_urls[key], SETTINGS.http_headers),
        tolerance,
        properties,
    )


def create_source_registry() -> SourceRegistry:
    river_names = set(coordinate_map("river_labels"))
    raw_rivers = FallbackSource(
        LocalGeoJsonSource(SETTINGS.root / "data" / "italy_rivers.geojson"),
        OsmRiverFallbackSource(river_names, SETTINGS.overpass_endpoints, SETTINGS.http_headers),
    )
    river_tolerance, river_properties = SOURCE_OPTIMIZATION["local_rivers"]
    lake_tolerance, lake_properties = SOURCE_OPTIMIZATION["local_lakes"]
    return SourceRegistry({
        "natural_earth.countries": _optimized_remote("countries"),
        "openpolis.regions": _optimized_remote("regions"),
        "openpolis.provinces": _optimized_remote("provinces"),
        "natural_earth.rivers": _optimized_remote("rivers"),
        "natural_earth.lakes": _optimized_remote("lakes"),
        "osm.italian_rivers": OptimizedGeoJsonSource(raw_rivers, river_tolerance, river_properties),
        "osm.italian_lakes": OptimizedGeoJsonSource(
            LocalGeoJsonSource(SETTINGS.root / "data" / "italy_lakes.geojson"),
            lake_tolerance,
            lake_properties,
        ),
    })


def create_application() -> AtlasApplication:
    context = ModuleContext(
        sources=create_source_registry(),
        catalog=EntityCatalog(),
        settings=SETTINGS,
        layer_defaults=dict(static_entities()["layer_defaults"]),
    )
    modules = [
        CountriesModule(),
        ItalianAdministrationModule(),
        CapitalsModule(),
        EuropeanCapitalsModule(),
        HydrographyModule(),
        EuropeanNationalRiversModule(),
        RiverSourcesModule(),
        MountainsModule(),
    ]
    engine = MapEngine(
        modules=modules,
        controls=[SearchControl()],
        context=context,
        map_styles_path=SETTINGS.root / "atlas" / "presentation" / "map.css",
    )
    return AtlasApplication(engine=engine, page=PageRenderer(SETTINGS.root))
