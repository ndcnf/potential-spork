from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cycle import Cycle
from app.schemas.imported import ImportedCycle


@dataclass(slots=True)
class UpsertCycleResult:
    cycle: Cycle
    created: bool


class CycleRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def upsert(self, imported_cycle: ImportedCycle) -> UpsertCycleResult:
        cycle = self._db.scalar(select(Cycle).where(Cycle.source_key == imported_cycle.source_key))
        if cycle is None:
            cycle = self._db.scalar(select(Cycle).where(Cycle.slug == imported_cycle.slug))
        created = cycle is None

        if cycle is None:
            cycle = Cycle(
                source_key=imported_cycle.source_key,
                name=imported_cycle.name,
                slug=imported_cycle.slug,
                color=imported_cycle.color,
            )
        else:
            cycle.source_key = imported_cycle.source_key
            cycle.name = imported_cycle.name
            cycle.color = imported_cycle.color

        self._db.add(cycle)
        self._db.flush()
        return UpsertCycleResult(cycle=cycle, created=created)
