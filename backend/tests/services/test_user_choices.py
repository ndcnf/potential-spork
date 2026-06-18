from __future__ import annotations

from app.models.film import Film
from app.models.screening import Screening
from app.services.user_choices import reset_user_choices


def test_reset_user_choices_resets_film_priorities_and_screening_selections(
    db_session,
    film_factory,
    screening_factory,
) -> None:
    high = film_factory(priority="high")
    maybe = film_factory(priority="medium")
    ignored = film_factory(priority="ignore")
    confirmed = screening_factory(film=high, selection_status="confirmed")
    tentative = screening_factory(film=maybe, selection_status="tentative")
    db_session.commit()

    summary = reset_user_choices(db_session)

    assert summary == {"films_reset": 3, "screenings_reset": 2}
    assert {film.priority for film in db_session.query(Film).all()} == {"low"}
    assert {screening.selection_status for screening in db_session.query(Screening).all()} == {"none"}
    assert confirmed.selection_status == "none"
    assert tentative.selection_status == "none"
