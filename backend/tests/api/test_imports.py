from __future__ import annotations


def test_import_catalog_accepts_minimal_payload(client, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.imports.import_nifff_catalog",
        lambda db, year, schedule_url=None: {
            "cycles_created": 1,
            "films_created": 2,
            "films_updated": 3,
        },
    )

    response = client.post("/api/imports/nifff/catalog", json={"year": 2025})

    assert response.status_code == 200
    assert response.json() == {
        "cycles_created": 1,
        "films_created": 2,
        "films_updated": 3,
    }


def test_import_catalog_accepts_schedule_url(client, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_import_nifff_catalog(db, year, schedule_url=None):
        captured["year"] = year
        captured["schedule_url"] = schedule_url
        return {
            "cycles_created": 0,
            "films_created": 0,
            "films_updated": 0,
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
        "schedule_url": "https://example.test/schedule?type=film",
    }


def test_import_catalog_returns_422_for_invalid_payload(client) -> None:
    response = client.post(
        "/api/imports/nifff/catalog",
        json={"year": 2025, "schedule_url": "not-a-url"},
    )

    assert response.status_code == 422
