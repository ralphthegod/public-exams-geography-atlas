import json

from atlas.config.entities import coordinate_map, static_entities
from atlas.config.settings import SETTINGS
from atlas.core.catalog import EntityCatalog
from atlas.core.models import ModuleContext
from atlas.modules import (
    CapitalsModule,
    CountriesModule,
    HydrographyModule,
    ItalianAdministrationModule,
    MountainsModule,
    RiverSourcesModule,
)


MODULES = [
    CountriesModule(), ItalianAdministrationModule(), CapitalsModule(),
    HydrographyModule(), RiverSourcesModule(), MountainsModule(),
]


def test_layer_ids_are_unique_across_modules():
    layer_ids = [layer.id for module in MODULES for layer in module.layers]
    assert len(layer_ids) == len(set(layer_ids))


def test_every_layer_has_public_label_and_category():
    assert all(layer.label and layer.category for module in MODULES for layer in module.layers)


def test_every_river_has_label_and_source():
    assert set(coordinate_map("river_labels")) == set(coordinate_map("river_sources"))


def test_static_points_are_valid_coordinates():
    points = []
    for config_name in ("capitals", "mountains", "river_sources"):
        points.extend((value[0], value[1]) for value in coordinate_map(config_name).values())
    points.extend(coordinate_map("river_labels").values())
    points.extend(coordinate_map("lake_labels").values())
    assert all(-90 <= lat <= 90 and -180 <= lon <= 180 for lat, lon in points)


def test_local_river_dataset_covers_labelled_minor_rivers():
    data = json.loads((SETTINGS.root / "data" / "italy_rivers.geojson").read_text(encoding="utf-8"))
    covered = {feature.get("properties", {}).get("name") for feature in data["features"]}
    assert set(coordinate_map("river_labels")) - {"Po"} <= covered


def test_local_lake_dataset_covers_main_italian_lakes():
    data = json.loads((SETTINGS.root / "data" / "italy_lakes.geojson").read_text(encoding="utf-8"))
    covered = {feature.get("properties", {}).get("name") for feature in data["features"]}
    assert set(static_entities()["italian_lakes"]) <= covered


def test_hydrography_contributes_searchable_entities():
    class Sources:
        def get(self, source_id):
            return None

        def get_many(self, *source_ids):
            return {source_id: self.get(source_id) for source_id in source_ids}

    context = ModuleContext(Sources(), EntityCatalog(), SETTINGS, static_entities()["layer_defaults"])
    module = HydrographyModule()
    data = module.load(context)
    module.contribute_entities(data, context)
    index = context.catalog.search_index()
    assert "Fiume · Po" in index
    assert "Lago · Lago di Garda" in index
