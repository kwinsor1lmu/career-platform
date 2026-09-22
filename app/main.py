from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes.resume import router as resume_router

from app.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="Personal Resume Platform")
    app.state.settings = settings or Settings()
    app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parent / "static"), name="static")
    app.include_router(resume_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
