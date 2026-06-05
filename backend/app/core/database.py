from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def run_sqlite_schema_upgrades() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    film_column_upgrades = {
        "premiere_label": "VARCHAR(255)",
        "short_description": "TEXT",
        "poster_url": "TEXT",
    }

    with engine.begin() as connection:
        existing_tables = {
            row[0]
            for row in connection.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
        }

        if "films" not in existing_tables:
            return

        existing_film_columns = {
            row[1] for row in connection.execute(text("PRAGMA table_info(films)"))
        }

        for column_name, column_type in film_column_upgrades.items():
            if column_name in existing_film_columns:
                continue
            connection.execute(
                text(f"ALTER TABLE films ADD COLUMN {column_name} {column_type}")
            )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
