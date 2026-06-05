from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Film(Base):
    __tablename__ = "films"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source_key: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    directors: Mapped[str | None] = mapped_column(Text, nullable=True)
    year: Mapped[int | None] = mapped_column(nullable=True)
    countries: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(nullable=True)
    tagline: Mapped[str | None] = mapped_column(Text, nullable=True)
    premiere_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cast: Mapped[str | None] = mapped_column(Text, nullable=True)
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(Text, nullable=True)
    age_rating: Mapped[str | None] = mapped_column(String(32), nullable=True)
    poster_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(32), default="low")
    cycle_id: Mapped[int | None] = mapped_column(ForeignKey("cycles.id"), nullable=True)

    cycle = relationship("Cycle", back_populates="films")
    screenings = relationship("Screening", back_populates="film")
