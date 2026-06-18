from __future__ import annotations

from app.core.priorities import (
    DEFAULT_FILM_PRIORITY,
    PLANNING_FILM_PRIORITIES,
    priority_after_import,
)


def test_priority_after_import_defaults_empty_or_initial_values_to_low() -> None:
    assert DEFAULT_FILM_PRIORITY == "low"
    assert priority_after_import(None) == "low"
    assert priority_after_import("low") == "low"


def test_priority_after_import_preserves_user_decisions() -> None:
    assert priority_after_import("medium") == "medium"
    assert priority_after_import("high") == "high"
    assert priority_after_import("must-see") == "must-see"
    assert priority_after_import("ignore") == "ignore"


def test_planning_priorities_include_maybe_and_high_values() -> None:
    assert PLANNING_FILM_PRIORITIES == ("medium", "high", "must-see")
