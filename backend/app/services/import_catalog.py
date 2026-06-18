from __future__ import annotations

from app.schemas.imported import CanonicalImportBundle, ImportReport
from app.sources.base import FestivalSource
from app.sources.nifff_html.normalizer import normalize_parsed_films
from app.sources.nifff_html.source import NifffHtmlCatalogPayload


class EmptyCatalogError(RuntimeError):
    """Raised when a live source is reachable but yields no importable catalog items."""


def validate_source_payload(*, source: FestivalSource, payload: object, year: int) -> None:
    if (
        source.source_name == "nifff_html"
        and source.source_mode == "prod"
        and isinstance(payload, NifffHtmlCatalogPayload)
        and not payload.parsed_films
    ):
        raise EmptyCatalogError(
            f"Source NIFFF chargée pour {year}, mais aucun film n’a été détecté. Vérifie l’URL live ou le parser."
        )


def normalize_source_payload(*, source_name: str, payload: object, year: int) -> CanonicalImportBundle:
    if source_name == "nifff_html":
        if not isinstance(payload, NifffHtmlCatalogPayload):
            raise TypeError("nifff_html source returned an unsupported catalog payload")
        return normalize_parsed_films(parsed_films=payload.parsed_films, year=year)

    raise ValueError(f"Unsupported source: {source_name}")


def import_catalog(*, source: FestivalSource, year: int) -> tuple[CanonicalImportBundle, ImportReport]:
    payload = source.fetch_catalog(year)
    validate_source_payload(source=source, payload=payload, year=year)
    bundle = normalize_source_payload(source_name=source.source_name, payload=payload, year=year)
    report = ImportReport(
        source_name=bundle.source_name,
        year=bundle.year,
        warnings=list(bundle.warnings),
    )
    return bundle, report
