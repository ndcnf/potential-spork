from collections.abc import Generator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def _is_sqlite_url(database_url: str) -> bool:
    return database_url.startswith("sqlite")


def _engine_connect_args(database_url: str) -> dict[str, bool]:
    if _is_sqlite_url(database_url):
        return {"check_same_thread": False}
    return {}


engine = create_engine(
    settings.database_url,
    connect_args=_engine_connect_args(settings.database_url),
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


SQLITE_COMPATIBILITY_COLUMNS: dict[str, dict[str, str]] = {
    "cycles": {
        "source_key": "VARCHAR(255)"
    },
    "films": {
        "source_key": "VARCHAR(255)",
        "premiere_label": "VARCHAR(255)",
        "short_description": "TEXT",
        "poster_url": "TEXT",
    },
    "venues": {
        "source_key": "VARCHAR(255)"
    },
    "screenings": {
        "source_key": "VARCHAR(255)",
        "source_url": "VARCHAR(500)",
    }
}


def _ensure_missing_nullable_columns(
    target_engine: Engine, table_name: str, expected_columns: dict[str, str]
) -> None:
    with target_engine.begin() as connection:
        existing_tables = {
            row[0]
            for row in connection.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
        }

        if table_name not in existing_tables:
            return

        existing_columns = {
            row[1]
            for row in connection.execute(text(f"PRAGMA table_info({table_name})"))
        }

        for column_name, column_type in expected_columns.items():
            if column_name in existing_columns:
                continue
            connection.execute(
                text(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                )
            )


def _normalize_all_medium_legacy_film_priorities(target_engine: Engine) -> None:
    with target_engine.begin() as connection:
        existing_tables = {
            row[0]
            for row in connection.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
        }

        if "films" not in existing_tables:
            return

        total_films = connection.execute(text("SELECT COUNT(*) FROM films")).scalar_one()
        if total_films == 0:
            return

        non_medium_films = connection.execute(
            text("SELECT COUNT(*) FROM films WHERE priority != 'medium'")
        ).scalar_one()
        if non_medium_films > 0:
            return

        connection.execute(text("UPDATE films SET priority = 'low' WHERE priority = 'medium'"))


def run_sqlite_schema_upgrades(target_engine: Engine | None = None) -> None:
    engine_to_use = target_engine or engine

    if not _is_sqlite_url(str(engine_to_use.url)):
        return

    for table_name, expected_columns in SQLITE_COMPATIBILITY_COLUMNS.items():
        _ensure_missing_nullable_columns(engine_to_use, table_name, expected_columns)

    _normalize_all_medium_legacy_film_priorities(engine_to_use)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
