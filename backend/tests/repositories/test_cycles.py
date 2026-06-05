from __future__ import annotations

from app.repositories.cycles import CycleRepository
from app.schemas.imported import ImportedCycle


def test_cycle_repository_creates_cycle_when_missing(db_session) -> None:
    repository = CycleRepository(db_session)

    result = repository.upsert(
        ImportedCycle(source_key="nifff:cycle:international-competition", name="International Competition", slug="international-competition")
    )

    assert result.created is True
    assert result.cycle.id is not None
    assert result.cycle.source_key == "nifff:cycle:international-competition"
    assert result.cycle.slug == "international-competition"


def test_cycle_repository_updates_existing_cycle(db_session, cycle_factory) -> None:
    existing = cycle_factory(name="Old Name", slug="international-competition", color=None, source_key=None)
    repository = CycleRepository(db_session)

    result = repository.upsert(
        ImportedCycle(
            source_key="nifff:cycle:international-competition",
            name="International Competition",
            slug="international-competition",
            color="#ff00aa",
        )
    )

    assert result.created is False
    assert result.cycle.id == existing.id
    assert result.cycle.source_key == "nifff:cycle:international-competition"
    assert result.cycle.name == "International Competition"
    assert result.cycle.color == "#ff00aa"
