"""Fast, deterministic employee generation.

Engineers re-run this regularly, so generation stays in memory and the insert
is a batched executemany inside one transaction. Names are always a first name
from first_names.txt plus a last name from last_names.txt.
"""

import os
import time
import unicodedata
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from random import Random

from sqlalchemy import delete, func, insert, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base, make_engine
from app.errors import DomainError
from app.models import Employee
from app.reference import COUNTRIES, JOB_TITLES, TITLE_DEPARTMENT, TITLE_USD_BANDS
from app.validation import MAX_SALARY, is_valid_name_token, quantize_money

CHUNK = 400


def name_file_paths() -> tuple[Path, Path]:
    override = os.environ.get("NORTHSTAR_DATA_DIR")
    if override:
        root = Path(override)
        return root / "first_names.txt", root / "last_names.txt"
    here = Path(__file__).resolve()
    for parent in here.parents:
        first = parent / "data" / "first_names.txt"
        last = parent / "data" / "last_names.txt"
        if first.exists() and last.exists():
            return first, last
    raise DomainError(
        "missing_names",
        "Could not find data/first_names.txt and data/last_names.txt.",
    )


def load_names(path: Path) -> list[str]:
    seen: set[str] = set()
    names: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        name = " ".join(line.strip().split())
        if not name or name.startswith("#"):
            continue
        if not is_valid_name_token(name):
            raise DomainError(
                "invalid_name_file",
                f"{path.name}:{line_number} must be a single name token made of letters.",
            )
        if name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names


def load_default_names() -> tuple[list[str], list[str]]:
    first_path, last_path = name_file_paths()
    return load_names(first_path), load_names(last_path)


def _slug(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(character for character in decomposed if character.isascii() and character.isalnum())
    return ascii_text.lower() or "x"


def generate_employee_rows(
    count: int,
    *,
    seed: int = 42,
    today: date | None = None,
    first_names: list[str] | None = None,
    last_names: list[str] | None = None,
    created_at: datetime | None = None,
) -> list[dict]:
    if count < 1 or count > 100_000:
        raise DomainError("invalid_seed_count", "Employee count must be between 1 and 100000.")
    current_day = today or date.today()
    if first_names is None or last_names is None:
        first_names, last_names = load_default_names()
    if not first_names or not last_names:
        raise DomainError("missing_names", "Name files must each contain at least one name.")
    rng = Random(seed)
    stamp = created_at or datetime.now(timezone.utc)
    origin = date(2012, 1, 1)
    span_days = max((current_day - origin).days, 0)
    rows: list[dict] = []
    for index in range(1, count + 1):
        first = first_names[rng.randrange(len(first_names))]
        last = last_names[rng.randrange(len(last_names))]
        country = COUNTRIES[rng.randrange(len(COUNTRIES))]
        title = JOB_TITLES[rng.randrange(len(JOB_TITLES))]
        city = country.cities[rng.randrange(len(country.cities))]
        employment_roll = rng.randrange(100)
        if employment_roll < 82:
            employment = "full_time"
        elif employment_roll < 92:
            employment = "part_time"
        else:
            employment = "contract"
        status_roll = rng.randrange(100)
        if status_roll < 88:
            status = "active"
        elif status_roll < 93:
            status = "on_leave"
        else:
            status = "terminated"
        low, high = TITLE_USD_BANDS[title]
        usd = Decimal(rng.randint(low, high))
        if employment == "contract":
            usd *= Decimal("1.15")
        elif employment == "part_time":
            usd *= Decimal("0.6")
        salary = quantize_money(usd * country.fx_per_usd * country.pay_index)
        if salary <= 0:
            salary = Decimal("0.01")
        if salary > MAX_SALARY:
            salary = MAX_SALARY
        hire_day = origin if span_days == 0 else origin + timedelta(days=rng.randrange(span_days + 1))
        if hire_day > current_day:
            hire_day = current_day
        rows.append(
            {
                "id": index,
                "employee_code": f"EMP-{index:05d}",
                "full_name": f"{first} {last}",
                "email": f"{_slug(first)}.{_slug(last)}.{index:05d}@northstar.example",
                "job_title": title,
                "department": TITLE_DEPARTMENT[title],
                "country": country.name,
                "city": city,
                "currency": country.currency,
                "salary": salary,
                "employment_type": employment,
                "status": status,
                "hire_date": hire_day,
                "created_at": stamp,
                "updated_at": stamp,
            }
        )
    return rows


def insert_generated_employees(session: Session, rows: list[dict], *, reset: bool) -> int:
    existing = session.scalar(select(func.count()).select_from(Employee)) or 0
    if reset:
        session.execute(delete(Employee))
        session.flush()
    elif existing:
        raise DomainError(
            "seed_not_empty",
            "Employees already exist. Re-run with --reset to replace them.",
        )
    statement = insert(Employee)
    for start in range(0, len(rows), CHUNK):
        session.execute(statement, rows[start : start + CHUNK])
    session.flush()
    return len(rows)


def _tune_sqlite(engine, url: str) -> None:
    if not url.startswith("sqlite") or url in {"sqlite://", "sqlite:///:memory:"}:
        return
    with engine.connect() as connection:
        connection.execute(text("PRAGMA journal_mode=WAL"))
        connection.execute(text("PRAGMA synchronous=OFF"))
        connection.commit()


def seed_url(url: str, *, count: int, seed: int, reset: bool, today: date | None = None) -> int:
    engine = make_engine(url)
    try:
        Base.metadata.create_all(engine)
        _tune_sqlite(engine, url)
        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        started = time.perf_counter()
        rows = generate_employee_rows(count, seed=seed, today=today)
        generated_at = time.perf_counter()
        with factory() as session:
            inserted = insert_generated_employees(session, rows, reset=reset)
            session.commit()
        elapsed = time.perf_counter() - started
        generate_elapsed = generated_at - started
        print(
            f"Generated {count} rows in {generate_elapsed:.2f}s; "
            f"committed {inserted} in {elapsed:.2f}s "
            f"({inserted / elapsed:.0f} rows/s)."
        )
        return inserted
    finally:
        engine.dispose()


def seed_session_if_empty(session: Session, *, count: int = 10_000, seed: int = 42) -> int:
    existing = session.scalar(select(func.count()).select_from(Employee)) or 0
    if existing:
        return 0
    rows = generate_employee_rows(count, seed=seed)
    inserted = insert_generated_employees(session, rows, reset=False)
    session.flush()
    print(f"Seeded {inserted} employees into an empty directory.")
    return inserted
