from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Screening(Base):
    __tablename__ = "screenings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source_key: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    film_id: Mapped[int] = mapped_column(ForeignKey("films.id"))
    venue_id: Mapped[int | None] = mapped_column(ForeignKey("venues.id"), nullable=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    selection_status: Mapped[str] = mapped_column(String(32), default="none")

    film = relationship("Film", back_populates="screenings")
    venue = relationship("Venue", back_populates="screenings")
