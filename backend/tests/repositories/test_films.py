from __future__ import annotations

from app.repositories.films import FilmRepository
from app.schemas.imported import ImportedFilm


def test_film_repository_creates_film_from_imported_model(db_session, cycle_factory) -> None:
    repository = FilmRepository(db_session)
    cycle = cycle_factory(name="International Competition", slug="international-competition")

    result = repository.upsert(
        ImportedFilm(
            source_key="nifff:film:a-cure-for-wellness",
            title="A Cure for Wellness",
            slug="a-cure-for-wellness",
            source_url="https://nifff.ch/prog/2025/film/a-cure-for-wellness",
            cycle_source_key="nifff:cycle:international-competition",
            directors="Gore Verbinski",
            year=2016,
            countries="DE/LU/US",
            duration_minutes=146,
            tagline="Psychological horror",
        ),
        cycle=cycle,
    )

    assert result.created is True
    assert result.film.id is not None
    assert result.film.source_key == "nifff:film:a-cure-for-wellness"
    assert result.film.cycle_id == cycle.id
    assert result.film.priority == "medium"


def test_film_repository_updates_existing_film_without_duplication(db_session, film_factory) -> None:
    existing = film_factory(title="Old Title", slug="a-cure-for-wellness", priority="high", source_key=None)
    repository = FilmRepository(db_session)

    result = repository.upsert(
        ImportedFilm(
            source_key="nifff:film:a-cure-for-wellness",
            title="A Cure for Wellness",
            slug="a-cure-for-wellness",
            source_url="https://nifff.ch/prog/2025/film/a-cure-for-wellness",
            cycle_source_key=None,
            directors="Gore Verbinski",
            short_description="Updated description.",
        )
    )

    assert result.created is False
    assert result.film.id == existing.id
    assert result.film.source_key == "nifff:film:a-cure-for-wellness"
    assert result.film.title == "A Cure for Wellness"
    assert result.film.short_description == "Updated description."
    assert result.film.priority == "high"
