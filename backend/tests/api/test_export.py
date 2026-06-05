from __future__ import annotations


def test_export_confirmed_ics_returns_calendar_response(client, db_session, screening_factory, film_factory, venue_factory) -> None:
    film = film_factory(title="A Cure for Wellness", slug="a-cure", tagline="Mind-bending wellness horror")
    venue = venue_factory(name="Théâtre")
    screening_factory(film=film, venue=venue, selection_status="confirmed")
    db_session.commit()

    response = client.get("/api/exports/confirmed.ics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/calendar")
    assert response.headers["content-disposition"] == 'attachment; filename="potential-spork-confirmed.ics"'
    assert "SUMMARY:A Cure for Wellness" in response.text


def test_export_confirmed_ics_only_contains_confirmed_screenings(client, db_session, screening_factory, film_factory) -> None:
    confirmed_film = film_factory(title="Confirmed Film", slug="confirmed-film")
    skipped_film = film_factory(title="Tentative Film", slug="tentative-film")
    screening_factory(film=confirmed_film, selection_status="confirmed")
    screening_factory(film=skipped_film, selection_status="tentative")
    db_session.commit()

    response = client.get("/api/exports/confirmed.ics")

    assert response.status_code == 200
    assert "SUMMARY:Confirmed Film" in response.text
    assert "SUMMARY:Tentative Film" not in response.text
