from __future__ import annotations

from atlas.core.engine import MapEngine
from atlas.presentation.page import PageRenderer


class AtlasApplication:
    def __init__(self, engine: MapEngine, page: PageRenderer) -> None:
        self.engine = engine
        self.page = page

    def run(self) -> None:
        self.page.render(self.engine)
