from __future__ import annotations

from datetime import UTC, datetime
from datetime import timedelta

from sqlalchemy.orm import Session

from app.models.screening import Screening
from app.services.screenings import derive_screening_state, screenings_overlap, sync_film_screening_status


def test_screenings_overlap_returns_false_for_same_screening(screening_factory) -> None:
    screening = screening_factory()

    assert screenings_overlap(screening, screening) is False


def test_screenings_overlap_returns_false_when_boundaries_missing(screening_factory) -> None:
    left = screening_factory(starts_at=None, ends_at=None)
    right = screening_factory()

    assert screenings_overlap(left, right) is False


def test_screenings_overlap_returns_true_for_overlapping_ranges(screening_factory, aware_datetime_factory) -> None:
    left = screening_factory(
        starts_at=aware_datetime_factory(1),
        ends_at=aware_datetime_factory(1) + timedelta(minutes=120),
    )
    right = screening_factory(
        starts_at=aware_datetime_factory(2),
        ends_at=aware_datetime_factory(2) + timedelta(minutes=120),
    )

    assert screenings_overlap(left, right) is True


def test_derive_screening_state_returns_past_for_elapsed_screening(screening_factory, aware_datetime_factory) -> None:
    screening = screening_factory(
        starts_at=datetime(2000, 1, 1, 18, 0, tzinfo=UTC),
        ends_at=datetime(2000, 1, 1, 20, 0, tzinfo=UTC),
    )

    assert derive_screening_state(screening, [screening]) == "past"


def test_derive_screening_state_returns_selected_for_confirmed_screening(screening_factory) -> None:
    screening = screening_factory(selection_status="confirmed")

    assert derive_screening_state(screening, [screening]) == "selected"


def test_derive_screening_state_returns_disabled_when_sibling_is_selected(screening_factory, film_factory) -> None:
    film = film_factory()
    selected = screening_factory(film=film, selection_status="tentative")
    other = screening_factory(film=film)

    assert derive_screening_state(other, [selected, other]) == "disabled"


def test_derive_screening_state_returns_conflict_when_selected_screening_overlaps(screening_factory, aware_datetime_factory) -> None:
    selected = screening_factory(
        selection_status="confirmed",
        starts_at=aware_datetime_factory(1),
        ends_at=aware_datetime_factory(1) + timedelta(minutes=120),
    )
    other = screening_factory(
        starts_at=aware_datetime_factory(2),
        ends_at=aware_datetime_factory(2) + timedelta(minutes=120),
    )

    assert derive_screening_state(other, [selected, other]) == "conflict"


def test_derive_screening_state_returns_available_otherwise(screening_factory) -> None:
    screening = screening_factory(selection_status="none")

    assert derive_screening_state(screening, [screening]) == "available"


def test_sync_film_screening_status_resets_siblings_when_confirmed(db_session: Session, screening_factory, film_factory) -> None:
    film = film_factory()
    confirmed = screening_factory(film=film, selection_status="confirmed")
    sibling = screening_factory(film=film, selection_status="tentative")

    sync_film_screening_status(db_session, confirmed)
    db_session.flush()

    refreshed_sibling = db_session.get(Screening, sibling.id)
    assert refreshed_sibling is not None
    assert refreshed_sibling.selection_status == "none"


def test_sync_film_screening_status_does_nothing_when_not_confirmed(db_session: Session, screening_factory, film_factory) -> None:
    film = film_factory()
    tentative = screening_factory(film=film, selection_status="tentative")
    sibling = screening_factory(film=film, selection_status="tentative")

    sync_film_screening_status(db_session, tentative)
    db_session.flush()

    refreshed_sibling = db_session.get(Screening, sibling.id)
    assert refreshed_sibling is not None
    assert refreshed_sibling.selection_status == "tentative"
