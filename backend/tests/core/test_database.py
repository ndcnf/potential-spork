from pathlib import Path

from sqlalchemy import create_engine, text

from app.core.database import run_sqlite_schema_upgrades


def create_legacy_cycles_schema(database_path: Path) -> str:
    database_url = f"sqlite:///{database_path}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE cycles (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    slug VARCHAR(255) NOT NULL,
                    color VARCHAR(32),
                    priority VARCHAR(32) NOT NULL
                )
                """
            )
        )

    engine.dispose()
    return database_url


def create_legacy_venues_and_screenings_schema(database_path: Path) -> str:
    database_url = f"sqlite:///{database_path}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE venues (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    comfort_rating INTEGER
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE screenings (
                    id INTEGER PRIMARY KEY,
                    film_id INTEGER NOT NULL,
                    venue_id INTEGER,
                    starts_at DATETIME,
                    ends_at DATETIME,
                    selection_status VARCHAR(32) NOT NULL
                )
                """
            )
        )

    engine.dispose()
    return database_url


def create_legacy_films_schema(database_path: Path) -> str:
    database_url = f"sqlite:///{database_path}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE films (
                    id INTEGER PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    slug VARCHAR(255) NOT NULL,
                    directors TEXT,
                    year INTEGER,
                    countries TEXT,
                    duration_minutes INTEGER,
                    tagline TEXT,
                    cast TEXT,
                    synopsis TEXT,
                    language TEXT,
                    age_rating VARCHAR(32),
                    source_url TEXT,
                    priority VARCHAR(32) NOT NULL,
                    cycle_id INTEGER
                )
                """
            )
        )

    engine.dispose()
    return database_url


def test_run_sqlite_schema_upgrades_adds_missing_nullable_film_columns(tmp_path: Path) -> None:
    database_url = create_legacy_films_schema(tmp_path / "legacy.db")
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    run_sqlite_schema_upgrades(engine)

    with engine.begin() as connection:
        film_columns = {row[1] for row in connection.execute(text("PRAGMA table_info(films)"))}

    assert {"source_key", "premiere_label", "short_description", "poster_url", "planning_type"}.issubset(film_columns)


def test_run_sqlite_schema_upgrades_adds_missing_nullable_cycle_columns(tmp_path: Path) -> None:
    database_url = create_legacy_cycles_schema(tmp_path / "legacy_cycles.db")
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    run_sqlite_schema_upgrades(engine)

    with engine.begin() as connection:
        cycle_columns = {row[1] for row in connection.execute(text("PRAGMA table_info(cycles)"))}

    assert {"source_key"}.issubset(cycle_columns)


def test_run_sqlite_schema_upgrades_adds_missing_nullable_venue_and_screening_columns(tmp_path: Path) -> None:
    database_url = create_legacy_venues_and_screenings_schema(tmp_path / "legacy_venues_screenings.db")
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    run_sqlite_schema_upgrades(engine)

    with engine.begin() as connection:
        venue_columns = {row[1] for row in connection.execute(text("PRAGMA table_info(venues)"))}
        screening_columns = {row[1] for row in connection.execute(text("PRAGMA table_info(screenings)"))}

    assert {"source_key"}.issubset(venue_columns)
    assert {"source_key", "source_url"}.issubset(screening_columns)


def test_run_sqlite_schema_upgrades_is_idempotent(tmp_path: Path) -> None:
    database_url = create_legacy_films_schema(tmp_path / "legacy.db")
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    run_sqlite_schema_upgrades(engine)
    run_sqlite_schema_upgrades(engine)

    with engine.begin() as connection:
        film_columns = [
            row[1] for row in connection.execute(text("PRAGMA table_info(films)"))
        ]

    assert film_columns.count("source_key") == 1
    assert film_columns.count("premiere_label") == 1
    assert film_columns.count("short_description") == 1
    assert film_columns.count("poster_url") == 1
    assert film_columns.count("planning_type") == 1


def test_run_sqlite_schema_upgrades_normalizes_all_medium_legacy_films_to_low(tmp_path: Path) -> None:
    database_url = create_legacy_films_schema(tmp_path / "legacy_priorities.db")
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO films (id, title, slug, priority)
                VALUES
                    (1, 'Alpha', 'alpha', 'medium'),
                    (2, 'Beta', 'beta', 'medium')
                """
            )
        )

    run_sqlite_schema_upgrades(engine)

    with engine.begin() as connection:
        priorities = {
            row[0]
            for row in connection.execute(text("SELECT priority FROM films"))
        }

    assert priorities == {"low"}


def test_run_sqlite_schema_upgrades_preserves_mixed_user_priorities(tmp_path: Path) -> None:
    database_url = create_legacy_films_schema(tmp_path / "mixed_priorities.db")
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO films (id, title, slug, priority)
                VALUES
                    (1, 'Alpha', 'alpha', 'medium'),
                    (2, 'Beta', 'beta', 'high'),
                    (3, 'Gamma', 'gamma', 'ignore')
                """
            )
        )

    run_sqlite_schema_upgrades(engine)

    with engine.begin() as connection:
        priorities = {
            row[0]
            for row in connection.execute(text("SELECT priority FROM films"))
        }

    assert priorities == {"medium", "high", "ignore"}
