from __future__ import annotations

import requests


def test_import_catalog_accepts_minimal_payload(client, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.imports.import_nifff_catalog",
        lambda db, year, source_mode="demo", schedule_url=None: {
            "cycles_created": 1,
            "films_created": 2,
            "films_updated": 3,
            "venues_created": 0,
            "venues_updated": 0,
            "screenings_created": 0,
            "screenings_updated": 0,
            "warnings_count": 0,
            "errors_count": 0,
        },
    )

    response = client.post("/api/imports/nifff/catalog", json={"year": 2025})

    assert response.status_code == 200
    assert response.json() == {
        "cycles_created": 1,
        "films_created": 2,
        "films_updated": 3,
        "venues_created": 0,
        "venues_updated": 0,
        "screenings_created": 0,
        "screenings_updated": 0,
        "warnings_count": 0,
        "errors_count": 0,
        "warnings": [],
        "errors": [],
    }


def test_import_catalog_accepts_schedule_url(client, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_import_nifff_catalog(db, year, source_mode="demo", schedule_url=None):
        captured["year"] = year
        captured["source_mode"] = source_mode
        captured["schedule_url"] = schedule_url
        return {
            "cycles_created": 0,
            "films_created": 0,
            "films_updated": 0,
            "venues_created": 0,
            "venues_updated": 0,
            "screenings_created": 0,
            "screenings_updated": 0,
            "warnings_count": 0,
            "errors_count": 0,
        }

    monkeypatch.setattr("app.api.routes.imports.import_nifff_catalog", fake_import_nifff_catalog)

    response = client.post(
        "/api/imports/nifff/catalog",
        json={
            "year": 2025,
            "schedule_url": "https://example.test/schedule?type=film",
        },
    )

    assert response.status_code == 200
    assert captured == {
        "year": 2025,
        "source_mode": "demo",
        "schedule_url": "https://example.test/schedule?type=film",
    }


def test_import_catalog_routes_to_live_source_mode(client, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_import_nifff_catalog(db, year, source_mode="demo", schedule_url=None):
        captured["year"] = year
        captured["source_mode"] = source_mode
        captured["schedule_url"] = schedule_url
        return {
            "cycles_created": 0,
            "films_created": 0,
            "films_updated": 0,
            "venues_created": 0,
            "venues_updated": 0,
            "screenings_created": 0,
            "screenings_updated": 0,
            "warnings_count": 0,
            "errors_count": 0,
        }

    monkeypatch.setattr("app.api.routes.imports.import_nifff_catalog", fake_import_nifff_catalog)

    response = client.post(
        "/api/imports/nifff/catalog",
        json={
            "year": 2025,
            "source_mode": "prod",
            "schedule_url": "https://example.test/programme?type=film",
        },
    )

    assert response.status_code == 200
    assert captured == {
        "year": 2025,
        "source_mode": "prod",
        "schedule_url": "https://example.test/programme?type=film",
    }


def test_import_catalog_returns_422_for_invalid_payload(client) -> None:
    response = client.post(
        "/api/imports/nifff/catalog",
        json={"year": 2025, "schedule_url": "not-a-url"},
    )

    assert response.status_code == 422


def test_import_catalog_returns_502_when_source_fetch_fails(client, monkeypatch) -> None:
    def fake_import_nifff_catalog(db, year, source_mode="demo", schedule_url=None):
        raise requests.HTTPError("404 Client Error")

    monkeypatch.setattr("app.api.routes.imports.import_nifff_catalog", fake_import_nifff_catalog)

    response = client.post(
        "/api/imports/nifff/catalog",
        json={"year": 2025, "source_mode": "prod"},
    )

    assert response.status_code == 502
    assert "Source NIFFF indisponible" in response.json()["detail"]
