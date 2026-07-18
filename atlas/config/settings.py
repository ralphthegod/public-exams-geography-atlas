from pathlib import Path

from atlas.core.models import AppSettings

ROOT = Path(__file__).resolve().parents[2]

SETTINGS = AppSettings(
    root=ROOT,
    europe_bbox=(-12.0, 34.0, 32.0, 72.0),
    http_headers={"User-Agent": "Atlante-Concorsi/3.0 (educational Streamlit map)"},
    overpass_endpoints=(
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass-api.de/api/interpreter",
    ),
    data_urls={
        "countries": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson",
        "regions": "https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_regions.geojson",
        "provinces": "https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_provinces.geojson",
        "rivers": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_rivers_lake_centerlines.geojson",
        "lakes": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_lakes.geojson",
    },
)
