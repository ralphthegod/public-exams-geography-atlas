from pathlib import Path

from atlas.config.entities import static_entities
from atlas.config.settings import SETTINGS
from atlas.core.catalog import EntityCatalog
from atlas.core.engine import MapEngine
from atlas.core.models import ModuleContext
from atlas.modules import CapitalsModule, HydrographyModule, MountainsModule
from atlas.modules.search import SearchControl


class FakeSources:
    def __init__(self):
        self.data = {
            "natural_earth.rivers": None,
            "natural_earth.lakes": None,
            "osm.italian_rivers": {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {"name": "Tevere"},
                    "geometry": {"type": "LineString", "coordinates": [[12.1, 43.7], [12.4, 42.1]]},
                }],
            },
            "osm.italian_lakes": {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {"name": "Lago di Garda"},
                    "geometry": {"type": "Polygon", "coordinates": [[[10.5, 45.5], [10.7, 45.5], [10.7, 45.7], [10.5, 45.5]]]},
                }],
            },
        }

    def get(self, source_id):
        return self.data[source_id]

    def get_many(self, *source_ids):
        return {source_id: self.get(source_id) for source_id in source_ids}


def build_test_map():
    context = ModuleContext(
        sources=FakeSources(),
        catalog=EntityCatalog(),
        settings=SETTINGS,
        layer_defaults=static_entities()["layer_defaults"],
    )
    engine = MapEngine(
        modules=[CapitalsModule(), HydrographyModule(), MountainsModule()],
        controls=[SearchControl()],
        context=context,
        map_styles_path=SETTINGS.root / "atlas" / "presentation" / "map.css",
    )
    return engine.build(), context


def test_map_renders_modules_and_search_without_streamlit_rerun():
    map_object, context = build_test_map()
    rendered = map_object.get_root().render()
    assert "Traccia fiumi" in rendered
    assert "Traccia laghi" in rendered
    assert "Lago di Garda" in rendered
    assert "atlas-search-input" in rendered
    assert "Fiume · Tevere" in rendered
    assert ".slice(0, 6)" in rendered
    assert "localStorage" not in rendered
    assert len(context.catalog) > 0


def test_layer_control_is_touch_responsive():
    map_object, _ = build_test_map()
    rendered = map_object.get_root().render()
    assert '"collapsed": true' in rendered
    assert "pointer: coarse" in rendered
    assert "atlasLayerControl.collapse()" in rendered


def test_public_entrypoint_is_thin():
    source = (SETTINGS.root / "app.py").read_text(encoding="utf-8")
    assert len(source.splitlines()) <= 10
    assert "create_application" in source
    assert "folium" not in source


def test_home_screen_assets_exist():
    for filename in ("icon-180.png", "icon-192.png", "icon-512.png", "manifest.webmanifest"):
        assert (SETTINGS.root / "static" / filename).is_file()
