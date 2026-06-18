from __future__ import annotations


DEFAULT_FILM_PRIORITY = "low"
USER_FILM_PRIORITIES = ("medium", "high", "must-see", "ignore")
PLANNING_FILM_PRIORITIES = ("medium", "high", "must-see")


def priority_after_import(current_priority: str | None) -> str:
    if current_priority in USER_FILM_PRIORITIES:
        return current_priority
    return DEFAULT_FILM_PRIORITY
