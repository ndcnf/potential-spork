from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import cycles, export, films, gaps, imports, planning, screenings, user_choices
from app.core.config import settings
from app.core.database import Base, engine, run_sqlite_schema_upgrades


def _register_routes(app: FastAPI) -> None:
    app.include_router(cycles.router, prefix=settings.api_prefix)
    app.include_router(films.router, prefix=settings.api_prefix)
    app.include_router(imports.router, prefix=settings.api_prefix)
    app.include_router(screenings.router, prefix=settings.api_prefix)
    app.include_router(user_choices.router, prefix=settings.api_prefix)
    app.include_router(planning.router, prefix=settings.api_prefix)
    app.include_router(gaps.router, prefix=settings.api_prefix)
    app.include_router(export.router, prefix=settings.api_prefix)


def create_app(*, run_startup_hooks: bool = True) -> FastAPI:
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if run_startup_hooks:
        @app.on_event("startup")
        def on_startup() -> None:
            Base.metadata.create_all(bind=engine)
            run_sqlite_schema_upgrades()

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    _register_routes(app)
    return app


app = create_app()
