from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.import_postprocessing import sync_existing_package_member_planning_types


def test_sync_existing_package_member_planning_types_marks_members_without_screenings(
    db_session: Session,
    cycle_factory,
    film_factory,
    screening_factory,
) -> None:
    cycle = cycle_factory(
        source_key="nifff:cycle:shorts-programs",
        name="Shorts Programs",
        slug="shorts-programs",
    )
    package = film_factory(
        cycle=cycle,
        source_url="https://nifff.ch/prog/2025/film-package/asian-shorts",
        planning_type="standalone",
    )
    member = film_factory(
        cycle=cycle,
        source_url="https://nifff.ch/prog/2025/film/atom-void",
        planning_type="standalone",
    )
    standalone_with_screening = film_factory(
        cycle=cycle,
        source_url="https://nifff.ch/prog/2025/film/screened-short",
        planning_type="standalone",
    )
    screening_factory(film=standalone_with_screening)

    sync_existing_package_member_planning_types(db_session)

    assert package.planning_type == "package"
    assert member.planning_type == "package_member"
    assert standalone_with_screening.planning_type == "standalone"
