from __future__ import annotations

from app.schemas.imported import CanonicalImportBundle, ImportedCycle, ImportedFilm
from app.sources.nifff_html.parser import ParsedFilm, slugify


def build_cycle_source_key(cycle_name: str) -> str:
    return f"nifff:cycle:{slugify(cycle_name)}"


def build_film_source_key(parsed: ParsedFilm) -> str:
    return f"nifff:film:{parsed.slug}"


def normalize_parsed_films(*, parsed_films: list[ParsedFilm], year: int) -> CanonicalImportBundle:
    cycles_by_key: dict[str, ImportedCycle] = {}
    imported_films: list[ImportedFilm] = []

    for parsed in parsed_films:
        cycle_source_key: str | None = None
        if parsed.cycle_name:
            cycle_source_key = build_cycle_source_key(parsed.cycle_name)
            cycles_by_key.setdefault(
                cycle_source_key,
                ImportedCycle(
                    source_key=cycle_source_key,
                    name=parsed.cycle_name,
                    slug=slugify(parsed.cycle_name),
                ),
            )

        imported_films.append(
            ImportedFilm(
                source_key=build_film_source_key(parsed),
                title=parsed.title,
                slug=parsed.slug,
                source_url=parsed.source_url,
                cycle_source_key=cycle_source_key,
                directors=parsed.directors,
                year=parsed.year,
                countries=parsed.countries,
                duration_minutes=parsed.duration_minutes,
                tagline=parsed.tagline,
                premiere_label=parsed.premiere_label,
                short_description=parsed.short_description,
                cast=parsed.cast,
                synopsis=parsed.synopsis,
                language=parsed.language,
                age_rating=parsed.age_rating,
                poster_url=parsed.poster_url,
            )
        )

    return CanonicalImportBundle(
        source_name="nifff_html",
        year=year,
        cycles=list(cycles_by_key.values()),
        films=imported_films,
    )
