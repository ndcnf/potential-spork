from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.film import Film
from app.services.import_pipeline import run_import_pipeline
from app.sources.nifff_html.parser import ParsedFilm
from app.sources.nifff_html.source import NifffHtmlCatalogPayload


class FakeNifffHtmlSource:
    source_name = "nifff_html"
    source_mode = "demo"

    def fetch_catalog(self, year: int) -> NifffHtmlCatalogPayload:
        return NifffHtmlCatalogPayload(
            parsed_films=[
                ParsedFilm(
                    title="A Cure for Wellness",
                    slug="a-cure-for-wellness",
                    source_url=f"https://nifff.ch/prog/{year}/film/a-cure-for-wellness",
                )
            ]
        )


def test_run_import_pipeline_applies_bundle_then_postprocessors(db_session: Session) -> None:
    observed_titles: list[str] = []

    def postprocess(db: Session) -> None:
        film = db.scalar(select(Film).where(Film.slug == "a-cure-for-wellness"))
        if film is not None:
            observed_titles.append(film.title)

    summary = run_import_pipeline(
        db=db_session,
        source=FakeNifffHtmlSource(),
        year=2025,
        postprocessors=(postprocess,),
    )

    assert summary.films_created == 1
    assert observed_titles == ["A Cure for Wellness"]
