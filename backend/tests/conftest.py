from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from itertools import count
from pathlib import Path

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models.cycle import Cycle
from app.models.film import Film
from app.models.screening import Screening
from app.models.venue import Venue


@pytest.fixture
def test_engine(tmp_path: Path) -> Iterator[Engine]:
    database_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def session_factory(test_engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


@pytest.fixture
def db_session(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    with session_factory() as session:
        yield session
        session.rollback()


@pytest.fixture
def fixture_text_loader() -> Callable[[str], str]:
    fixtures_dir = Path(__file__).parent / "fixtures"

    def load(relative_path: str) -> str:
        return (fixtures_dir / relative_path).read_text(encoding="utf-8")

    return load


@pytest.fixture
def aware_datetime_factory() -> Callable[[int], datetime]:
    base = datetime(2030, 7, 5, 10, 0, tzinfo=UTC)

    def build(hours_offset: int = 0) -> datetime:
        return base + timedelta(hours=hours_offset)

    return build


@pytest.fixture
def cycle_factory(db_session: Session) -> Callable[..., Cycle]:
    sequence = count(1)

    def create(**overrides: object) -> Cycle:
        index = next(sequence)
        cycle = Cycle(
            source_key=overrides.pop("source_key", None),
            name=overrides.pop("name", f"Cycle {index}"),
            slug=overrides.pop("slug", f"cycle-{index}"),
            color=overrides.pop("color", None),
            priority=overrides.pop("priority", "medium"),
        )
        for field, value in overrides.items():
            setattr(cycle, field, value)
        db_session.add(cycle)
        db_session.flush()
        return cycle

    return create


@pytest.fixture
def film_factory(db_session: Session, cycle_factory: Callable[..., Cycle]) -> Callable[..., Film]:
    sequence = count(1)

    def create(**overrides: object) -> Film:
        index = next(sequence)
        cycle = overrides.pop("cycle", None)
        if cycle is None and overrides.pop("with_cycle", False):
            cycle = cycle_factory()

        film = Film(
            source_key=overrides.pop("source_key", None),
            title=overrides.pop("title", f"Film {index}"),
            slug=overrides.pop("slug", f"film-{index}"),
            directors=overrides.pop("directors", "Director Example"),
            year=overrides.pop("year", 2030),
            countries=overrides.pop("countries", "CH"),
            duration_minutes=overrides.pop("duration_minutes", 100),
            tagline=overrides.pop("tagline", "Tagline"),
            premiere_label=overrides.pop("premiere_label", None),
            short_description=overrides.pop("short_description", None),
            cast=overrides.pop("cast", None),
            synopsis=overrides.pop("synopsis", None),
            language=overrides.pop("language", None),
            age_rating=overrides.pop("age_rating", None),
            poster_url=overrides.pop("poster_url", None),
            source_url=overrides.pop("source_url", None),
            priority=overrides.pop("priority", "medium"),
            cycle_id=cycle.id if cycle is not None else overrides.pop("cycle_id", None),
        )
        for field, value in overrides.items():
            setattr(film, field, value)
        db_session.add(film)
        db_session.flush()
        return film

    return create


@pytest.fixture
def venue_factory(db_session: Session) -> Callable[..., Venue]:
    sequence = count(1)

    def create(**overrides: object) -> Venue:
        index = next(sequence)
        venue = Venue(
            source_key=overrides.pop("source_key", None),
            name=overrides.pop("name", f"Venue {index}"),
            comfort_rating=overrides.pop("comfort_rating", None),
        )
        for field, value in overrides.items():
            setattr(venue, field, value)
        db_session.add(venue)
        db_session.flush()
        return venue

    return create


@pytest.fixture
def screening_factory(
    db_session: Session,
    film_factory: Callable[..., Film],
    venue_factory: Callable[..., Venue],
    aware_datetime_factory: Callable[[int], datetime],
) -> Callable[..., Screening]:
    sequence = count(1)

    def create(**overrides: object) -> Screening:
        index = next(sequence)
        film = overrides.pop("film", None) or film_factory()
        venue = overrides.pop("venue", None)
        create_venue = overrides.pop("with_venue", False)
        if venue is None and create_venue:
            venue = venue_factory()

        starts_at = overrides.pop("starts_at", aware_datetime_factory(index))
        ends_at = overrides.pop("ends_at", starts_at + timedelta(minutes=100) if starts_at is not None else None)
        screening = Screening(
            source_key=overrides.pop("source_key", None),
            film_id=film.id,
            venue_id=venue.id if venue is not None else overrides.pop("venue_id", None),
            starts_at=starts_at,
            ends_at=ends_at,
            source_url=overrides.pop("source_url", None),
            selection_status=overrides.pop("selection_status", "none"),
        )
        screening.film = film
        screening.venue = venue
        for field, value in overrides.items():
            setattr(screening, field, value)
        db_session.add(screening)
        db_session.flush()
        return screening

    return create
