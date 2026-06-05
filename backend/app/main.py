from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import cycles, export, films, gaps, imports, planning, screenings
from app.core.config import settings
from app.core.database import Base, engine, run_sqlite_schema_upgrades


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    run_sqlite_schema_upgrades()


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(cycles.router, prefix=settings.api_prefix)
app.include_router(films.router, prefix=settings.api_prefix)
app.include_router(imports.router, prefix=settings.api_prefix)
app.include_router(screenings.router, prefix=settings.api_prefix)
app.include_router(planning.router, prefix=settings.api_prefix)
app.include_router(gaps.router, prefix=settings.api_prefix)
app.include_router(export.router, prefix=settings.api_prefix)
