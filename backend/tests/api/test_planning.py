from __future__ import annotations


def test_get_planning_groups_screenings_by_day(client, db_session, screening_factory, aware_datetime_factory) -> None:
    screening_factory(starts_at=aware_datetime_factory(1))
    screening_factory(starts_at=aware_datetime_factory(2))
    screening_factory(starts_at=aware_datetime_factory(30))
    db_session.commit()

    response = client.get("/api/planning")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert payload[0]["date"] == "2030-07-05"
    assert len(payload[0]["screenings"]) == 2
    assert payload[1]["date"] == "2030-07-06"
    assert len(payload[1]["screenings"]) == 1


def test_get_planning_skips_screenings_without_start(client, db_session, screening_factory) -> None:
    screening_factory(starts_at=None, ends_at=None)
    db_session.commit()

    response = client.get("/api/planning")

    assert response.status_code == 200
    assert response.json() == []


def test_get_planning_returns_days_in_sorted_order(client, db_session, screening_factory, aware_datetime_factory) -> None:
    screening_factory(starts_at=aware_datetime_factory(30))
    screening_factory(starts_at=aware_datetime_factory(1))
    db_session.commit()

    response = client.get("/api/planning")

    assert response.status_code == 200
    assert [item["date"] for item in response.json()] == ["2030-07-05", "2030-07-06"]
