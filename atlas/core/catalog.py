from __future__ import annotations

from collections.abc import Iterable, Iterator

from atlas.core.models import MapEntity


class EntityCatalog:
    def __init__(self) -> None:
        self._entities: dict[str, MapEntity] = {}

    def add(self, entity: MapEntity) -> None:
        if entity.id in self._entities:
            raise ValueError(f"Entità duplicata: {entity.id}")
        self._entities[entity.id] = entity

    def extend(self, entities: Iterable[MapEntity]) -> None:
        for entity in entities:
            self.add(entity)

    def __iter__(self) -> Iterator[MapEntity]:
        return iter(self._entities.values())

    def __len__(self) -> int:
        return len(self._entities)

    def clear(self) -> None:
        self._entities.clear()

    def search_index(self) -> dict[str, tuple[float, float, int]]:
        return {
            entity.search_label: (entity.latitude, entity.longitude, entity.zoom)
            for entity in sorted(self, key=lambda item: item.search_label.casefold())
        }
