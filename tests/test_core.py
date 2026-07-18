import pytest

from atlas.core.catalog import EntityCatalog
from atlas.core.geojson import geometry_center, load_label, optimize_geojson, prepare_admin_labels
from atlas.core.models import MapEntity, entity_id


def test_catalog_rejects_duplicate_entity_ids():
    catalog = EntityCatalog()
    entity = MapEntity("river:po", "Fiume", "Po", 45.0, 10.5, 9)
    catalog.add(entity)
    with pytest.raises(ValueError, match="Entità duplicata"):
        catalog.add(entity)


def test_catalog_builds_sorted_search_index():
    catalog = EntityCatalog()
    catalog.add(MapEntity("river:tevere", "Fiume", "Tevere", 42.15, 12.35, 9))
    catalog.add(MapEntity("capital:roma", "Capoluogo", "Roma", 41.9, 12.49, 11))
    assert list(catalog.search_index()) == ["Capoluogo · Roma", "Fiume · Tevere"]


def test_entity_id_is_stable_and_ascii():
    assert entity_id("province", "Forlì-Cesena") == "province:forli-cesena"


def test_province_label_takes_precedence_over_region():
    feature = {"properties": {"reg_name": "Lazio", "prov_name": "Roma"}}
    prepare_admin_labels({"type": "FeatureCollection", "features": [feature]})
    assert load_label(feature) == "Roma"


def test_geometry_center_uses_bounds_when_label_coordinates_are_missing():
    feature = {"geometry": {"type": "LineString", "coordinates": [[10, 40], [14, 44]]}}
    assert geometry_center(feature) == (42.0, 12.0)


def test_geojson_optimization_reduces_vertices_and_properties():
    data = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"name": "Test", "unused": "large"},
            "geometry": {
                "type": "LineString",
                "coordinates": [[x / 1000, (x % 2) / 100000] for x in range(100)],
            },
        }],
    }
    optimized = optimize_geojson(data, 0.0001, {"name"})
    assert optimized is not None
    feature = optimized["features"][0]
    assert len(feature["geometry"]["coordinates"]) < 100
    assert feature["properties"] == {"name": "Test"}
