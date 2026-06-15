from __future__ import annotations

from datetime import timedelta


def test_list_screenings_returns_derived_states(client, db_session, film_factory, screening_factory, aware_datetime_factory) -> None:
    selected_film = film_factory(title="Selected", slug="selected")
    conflict_film = film_factory(title="Conflict", slug="conflict")
    selected = screening_factory(
        film=selected_film,
        selection_status="confirmed",
        starts_at=aware_datetime_factory(1),
        ends_at=aware_datetime_factory(1) + timedelta(minutes=120),
    )
    screening_factory(
        film=conflict_film,
        starts_at=aware_datetime_factory(2),
        ends_at=aware_datetime_factory(2) + timedelta(minutes=120),
    )
    db_session.commit()

    response = client.get("/api/screenings")

    assert response.status_code == 200
    states_by_id = {item["id"]: item["derived_state"] for item in response.json()}
    assert states_by_id[selected.id] == "selected"
    assert "conflict" in states_by_id.values()


def test_update_screening_updates_selection_status(client, db_session, screening_factory) -> None:
    screening = screening_factory(selection_status="none")
    db_session.commit()

    response = client.patch(f"/api/screenings/{screening.id}", json={"selection_status": "confirmed"})

    assert response.status_code == 200
    assert response.json()["selection_status"] == "confirmed"


def test_update_screening_can_ignore_screening_without_rejecting_film(client, db_session, film_factory, screening_factory) -> None:
    film = film_factory(priority="high")
    screening = screening_factory(film=film, selection_status="none")
    db_session.commit()

    response = client.patch(f"/api/screenings/{screening.id}", json={"selection_status": "rejected"})

    assert response.status_code == 200
    assert response.json()["selection_status"] == "rejected"
    assert db_session.get(type(film), film.id).priority == "high"


def test_update_screening_resets_sibling_states_when_confirmed(client, db_session, film_factory, screening_factory) -> None:
    film = film_factory()
    selected = screening_factory(film=film, selection_status="none")
    sibling = screening_factory(film=film, selection_status="tentative")
    db_session.commit()

    response = client.patch(f"/api/screenings/{selected.id}", json={"selection_status": "confirmed"})

    assert response.status_code == 200

    refreshed = client.get("/api/screenings")
    payload_by_id = {item["id"]: item for item in refreshed.json()}
    assert payload_by_id[selected.id]["selection_status"] == "confirmed"
    assert payload_by_id[sibling.id]["selection_status"] == "none"


def test_update_screening_returns_404_for_unknown_id(client) -> None:
    response = client.patch("/api/screenings/999999", json={"selection_status": "confirmed"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Screening not found"}


def test_update_screening_returns_422_for_invalid_payload(client, db_session, screening_factory) -> None:
    screening = screening_factory()
    db_session.commit()

    response = client.patch(f"/api/screenings/{screening.id}", json={"selection_status": "invalid"})

    assert response.status_code == 422
