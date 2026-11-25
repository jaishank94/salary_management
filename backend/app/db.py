"""Database engine helpers. SQLite is the default, and any SQLAlchemy URL works."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def default_db_path() -> Path:
    return Path(__file__).resolve().parents[1] / "northstar.db"


def sqlite_url(path: Path) -> str:
    return "sqlite:///" + path.resolve().as_posix()


def make_engine(url: str) -> Engine:
    options: dict = {}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        if url in {"sqlite://", "sqlite:///:memory:"}:
            options["poolclass"] = StaticPool
    return create_engine(url, **options)
