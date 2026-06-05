from __future__ import annotations


def test_list_films_returns_ordered_films(client, db_session, film_factory, cycle_factory) -> None:
    cycle = cycle_factory(name="Midnight", slug="midnight")
    film_factory(title="Zulu", slug="zulu", cycle=cycle)
    film_factory(title="Alpha", slug="alpha", cycle=cycle)
    db_session.commit()

    response = client.get("/api/films")

    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["Alpha", "Zulu"]


def test_list_films_filters_by_query(client, db_session, film_factory) -> None:
    film_factory(title="A Cure for Wellness", slug="a-cure", directors="Gore Verbinski")
    film_factory(title="The Substance", slug="the-substance", directors="Coralie Fargeat")
    db_session.commit()

    response = client.get("/api/films", params={"q": "Verbinski"})

    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["A Cure for Wellness"]


def test_list_films_filters_by_cycle_id(client, db_session, film_factory, cycle_factory) -> None:
    target_cycle = cycle_factory(name="Target", slug="target")
    other_cycle = cycle_factory(name="Other", slug="other")
    film_factory(title="In", slug="in", cycle=target_cycle)
    film_factory(title="Out", slug="out", cycle=other_cycle)
    db_session.commit()

    response = client.get("/api/films", params={"cycle_id": target_cycle.id})

    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["In"]


def test_list_films_filters_by_priority(client, db_session, film_factory) -> None:
    film_factory(title="Must See", slug="must-see", priority="must-see")
    film_factory(title="Ignore", slug="ignore", priority="ignore")
    db_session.commit()

    response = client.get("/api/films", params={"priority": "must-see"})

    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["Must See"]


def test_update_film_updates_priority(client, db_session, film_factory) -> None:
    film = film_factory(priority="medium")
    db_session.commit()

    response = client.patch(f"/api/films/{film.id}", json={"priority": "high"})

    assert response.status_code == 200
    assert response.json()["priority"] == "high"


def test_update_film_returns_404_for_unknown_id(client) -> None:
    response = client.patch("/api/films/999999", json={"priority": "high"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Film not found"}


def test_update_film_returns_422_for_invalid_payload(client, db_session, film_factory) -> None:
    film = film_factory()
    db_session.commit()

    response = client.patch(f"/api/films/{film.id}", json={"priority": "invalid"})

    assert response.status_code == 422
