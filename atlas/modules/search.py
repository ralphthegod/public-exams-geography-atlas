from __future__ import annotations

import json
from pathlib import Path

import folium
from branca.element import MacroElement
from jinja2 import Template

from atlas.core.models import ModuleContext

TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "presentation" / "templates" / "search_control.js"


class SearchControl:
    id = "search"

    def render(self, map_object: folium.Map, context: ModuleContext, layer_control_name: str) -> None:
        control = MacroElement()
        control._name = "DatasetSearch"
        control.index_json = json.dumps(
            context.catalog.search_index(), ensure_ascii=False,
        ).replace("<", "\\u003c")
        control.layer_control_name = layer_control_name
        control._template = Template(TEMPLATE_PATH.read_text(encoding="utf-8"))
        control.add_to(map_object)
