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

    assert {"source_key", "premiere_label", "short_description", "poster_url"}.issubset(film_columns)


def test_run_sqlite_schema_upgrades_adds_missing_nullable_cycle_columns(tmp_path: Path) -> None:
    database_url = create_legacy_cycles_schema(tmp_path / "legacy_cycles.db")
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    run_sqlite_schema_upgrades(engine)

    with engine.begin() as connection:
        cycle_columns = {row[1] for row in connection.execute(text("PRAGMA table_info(cycles)"))}

    assert {"source_key"}.issubset(cycle_columns)


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
