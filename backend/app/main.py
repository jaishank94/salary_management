"""Northstar API application."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401  (register tables)
from app.api import build_router
from app.db import Base, default_db_path, make_engine, sqlite_url
from app.errors import DomainError
from app.seeding import seed_session_if_empty

_ERROR_STATUS = {
    "not_found": 404,
    "duplicate_email": 409,
}


def create_app(database_url: str | None = None) -> FastAPI:
    url = database_url or os.environ.get("DATABASE_URL") or sqlite_url(default_db_path())
    engine = make_engine(url)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Base.metadata.create_all(engine)
        if os.environ.get("SEED_IF_EMPTY") == "1":
            with session_factory() as session:
                seed_session_if_empty(session)
                session.commit()
        yield
        engine.dispose()

    app = FastAPI(
        title="Northstar Salary Management",
        version="1.0.0",
        summary="Compensation directory and salary insights for an HR manager.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def get_db():
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.include_router(build_router(get_db))

    @app.exception_handler(DomainError)
    async def handle_domain_error(_request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=_ERROR_STATUS.get(exc.code, 422),
            content={"error": {"code": exc.code, "message": exc.message, "fields": exc.fields}},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
        fields: dict[str, str] = {}
        for error in exc.errors():
            location = [str(item) for item in error["loc"] if item not in ("body", "query", "path")]
            key = location[-1] if location else "request"
            fields[key] = error["msg"]
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Check the highlighted fields.",
                    "fields": fields,
                }
            },
        )

    @app.get("/")
    def root() -> dict:
        return {"service": "Northstar", "health": "/api/health", "docs": "/docs"}

    return app


app = create_app()
