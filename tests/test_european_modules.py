import json

from atlas.config.entities import static_entities
from atlas.config.settings import SETTINGS
from atlas.core.catalog import EntityCatalog
from atlas.core.engine import MapEngine
from atlas.core.models import ModuleContext
from atlas.modules import EuropeanCapitalsModule, EuropeanNationalRiversModule
from atlas.modules.search import SearchControl


def context():
    return ModuleContext(object(), EntityCatalog(), SETTINGS, static_entities()["layer_defaults"])


def test_european_capitals_are_complete_unique_and_searchable():
    module_context = context()
    module = EuropeanCapitalsModule()
    data = module.load(module_context)
    assert len(data) == 50
    assert len({capital["country_iso3"] for capital in data}) == 50
    module.contribute_entities(data, module_context)
    labels = set(module_context.catalog.search_index())
    assert any("Roma" in label and "Italia" in label for label in labels)
    assert any("Parigi" in label and "Francia" in label for label in labels)


def test_national_river_dataset_has_ranked_country_sections():
    data = json.loads(
        (SETTINGS.root / "atlas" / "modules" / "european_national_rivers" / "rivers.geojson")
        .read_text(encoding="utf-8")
    )
    by_country = {}
    for feature in data["features"]:
        props = feature["properties"]
        by_country.setdefault(props["country_iso3"], []).append(props)
        assert -90 <= props["label_lat"] <= 90
        assert -180 <= props["label_lon"] <= 180

    country_codes = set(data["metadata"]["country_counts"])
    assert len(country_codes) == 50
    assert country_codes - set(by_country) == {"MCO", "MLT", "VAT"}
    assert all(1 <= len(features) <= 3 for features in by_country.values())
    assert {props["name"] for props in by_country["ITA"]} == {"Po", "Adige", "Tevere"}
    assert all(
        sorted(props["rank"] for props in features) == list(range(1, len(features) + 1))
        for features in by_country.values()
    )


def test_new_european_modules_render_independently():
    module_context = context()
    engine = MapEngine(
        modules=[EuropeanCapitalsModule(), EuropeanNationalRiversModule()],
        controls=[SearchControl()],
        context=module_context,
        map_styles_path=SETTINGS.root / "atlas" / "presentation" / "map.css",
    )
    rendered = engine.build().get_root().render()
    assert "Capitali europee" in rendered
    assert "Etichette capitali europee" in rendered
    assert "Tre fiumi principali per nazione" in rendered
    assert "Etichette fiumi per nazione" in rendered
    assert "Roma" in rendered and "Italia" in rendered
    assert "Po" in rendered and "Fiume nazionale" in rendered
