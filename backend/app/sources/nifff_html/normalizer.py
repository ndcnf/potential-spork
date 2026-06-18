from __future__ import annotations

from datetime import timedelta

from app.schemas.imported import CanonicalImportBundle, ImportedCycle, ImportedFilm, ImportedScreening, ImportedVenue
from app.sources.nifff_html.parser import ParsedFilm, ParsedScreening, slugify


def category_tokens(cycle_name: str | None) -> set[str]:
    if not cycle_name:
        return set()
    return {slugify(token) for token in cycle_name.split(",") if slugify(token)}


def is_package(parsed: ParsedFilm) -> bool:
    return parsed.source_url is not None and "/film-package/" in parsed.source_url


def infer_planning_type(parsed: ParsedFilm, package_category_tokens: set[str]) -> str:
    if is_package(parsed):
        return "package"
    if not parsed.screenings and category_tokens(parsed.cycle_name).intersection(package_category_tokens):
        return "package_member"
    return "standalone"


def build_cycle_source_key(cycle_name: str) -> str:
    return f"nifff:cycle:{slugify(cycle_name)}"


def build_film_source_key(parsed: ParsedFilm) -> str:
    return f"nifff:film:{parsed.slug}"


def build_venue_source_key(venue_name: str) -> str:
    return f"nifff:venue:{slugify(venue_name)}"


def build_screening_source_key(parsed_film: ParsedFilm, parsed_screening: ParsedScreening) -> str:
    starts_at_token = parsed_screening.starts_at.isoformat() if parsed_screening.starts_at else "unknown"
    venue_token = slugify(parsed_screening.venue_name or "unknown")
    return f"nifff:screening:{parsed_film.slug}:{venue_token}:{starts_at_token}"


def infer_screening_end(parsed_film: ParsedFilm, parsed_screening: ParsedScreening):
    if parsed_screening.ends_at is not None:
        return parsed_screening.ends_at
    if parsed_screening.starts_at is None or parsed_film.duration_minutes is None:
        return None
    return parsed_screening.starts_at + timedelta(minutes=parsed_film.duration_minutes)


def normalize_parsed_films(*, parsed_films: list[ParsedFilm], year: int) -> CanonicalImportBundle:
    cycles_by_key: dict[str, ImportedCycle] = {}
    venues_by_key: dict[str, ImportedVenue] = {}
    imported_films: list[ImportedFilm] = []
    imported_screenings: list[ImportedScreening] = []
    warnings: list[str] = []
    package_category_tokens = set().union(
        *(category_tokens(parsed.cycle_name) for parsed in parsed_films if is_package(parsed))
    )

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
                planning_type=infer_planning_type(parsed, package_category_tokens),
            )
        )

        for parsed_screening in parsed.screenings:
            venue_source_key: str | None = None
            if parsed_screening.venue_name:
                venue_source_key = build_venue_source_key(parsed_screening.venue_name)
                venues_by_key.setdefault(
                    venue_source_key,
                    ImportedVenue(source_key=venue_source_key, name=parsed_screening.venue_name),
                )

            ends_at = infer_screening_end(parsed, parsed_screening)
            starts_at_token = parsed_screening.starts_at.isoformat() if parsed_screening.starts_at else "unknown"
            if parsed_screening.ends_at is None and ends_at is not None:
                warnings.append(f"Inferred screening end from film duration: film={parsed.slug} starts_at={starts_at_token}")
            elif (
                parsed_screening.ends_at is None
                and parsed_screening.starts_at is not None
                and parsed.duration_minutes is None
            ):
                warnings.append(
                    f"Missing screening end and film duration: film={parsed.slug} starts_at={starts_at_token}"
                )

            imported_screenings.append(
                ImportedScreening(
                    source_key=build_screening_source_key(parsed, parsed_screening),
                    film_source_key=build_film_source_key(parsed),
                    venue_source_key=venue_source_key,
                    starts_at=parsed_screening.starts_at,
                    ends_at=ends_at,
                    source_url=parsed_screening.source_url,
                    ticket_url=parsed_screening.ticket_url,
                )
            )

    return CanonicalImportBundle(
        source_name="nifff_html",
        year=year,
        cycles=list(cycles_by_key.values()),
        films=imported_films,
        venues=list(venues_by_key.values()),
        screenings=imported_screenings,
        warnings=warnings,
    )
