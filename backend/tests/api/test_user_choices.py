from __future__ import annotations

from app.models.film import Film
from app.models.screening import Screening


def test_reset_user_choices_endpoint_resets_product_choices(
    client,
    db_session,
    film_factory,
    screening_factory,
) -> None:
    film = film_factory(priority="medium")
    screening = screening_factory(film=film, selection_status="confirmed")
    db_session.commit()

    response = client.post("/api/user-choices/reset")

    assert response.status_code == 200
    assert response.json() == {"films_reset": 1, "screenings_reset": 1}
    assert db_session.get(Film, film.id).priority == "low"
    assert db_session.get(Screening, screening.id).selection_status == "none"
