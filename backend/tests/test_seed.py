import time
from datetime import date
from decimal import Decimal

import pytest

from app.errors import DomainError
from app.reference import COUNTRY_BY_KEY, TITLE_DEPARTMENT
from app.seed import main
from app.seeding import (
    generate_employee_rows,
    insert_generated_employees,
    load_default_names,
    load_names,
)
from app.services.employees import EmployeeService
from app.db import sqlite_url
from tests.conftest import employee_payload


def test_load_names_skips_blanks_and_duplicates(tmp_path):
    path = tmp_path / "first_names.txt"
    path.write_text("\n# comment\nAva\n\nAva\nLiam\n", encoding="utf-8")
    assert load_names(path) == ["Ava", "Liam"]


def test_load_names_rejects_multi_token_or_invalid_lines(tmp_path):
    path = tmp_path / "first_names.txt"
    path.write_text("Mary Jane\n", encoding="utf-8")
    with pytest.raises(DomainError) as caught:
        load_names(path)
    assert caught.value.code == "invalid_name_file"


def test_repository_name_lists_are_single_tokens():
    firsts, lasts = load_default_names()
    assert len(firsts) >= 100
    assert len(lasts) >= 100
    assert len(set(firsts)) == len(firsts)
    assert len(set(lasts)) == len(lasts)


def test_generation_is_deterministic_and_composes_file_names():
    today = date(2026, 11, 25)
    first = generate_employee_rows(20, seed=7, today=today)
    second = generate_employee_rows(20, seed=7, today=today)
    third = generate_employee_rows(20, seed=8, today=today)

    def signature(rows):
        return [
            (
                row["full_name"],
                row["email"],
                str(row["salary"]),
                row["country"],
                row["city"],
                row["job_title"],
                row["status"],
                row["hire_date"].isoformat(),
                row["employee_code"],
            )
            for row in rows
        ]

    assert signature(first) == signature(second)
    assert signature(first) != signature(third)
    first_names, last_names = load_default_names()
    first_set = set(first_names)
    last_set = set(last_names)
    for row in first:
        given, family = row["full_name"].split(" ")
        assert given in first_set
        assert family in last_set
        assert row["department"] == TITLE_DEPARTMENT[row["job_title"]]
        assert row["currency"] == COUNTRY_BY_KEY[row["country"].casefold()].currency
        assert row["salary"] > 0
        assert row["hire_date"] <= today
        assert row["email"].endswith("@northstar.example")


def test_full_seed_shape_and_generation_speed():
    today = date(2026, 11, 25)
    started = time.perf_counter()
    rows = generate_employee_rows(10_000, seed=42, today=today)
    assert time.perf_counter() - started < 2
    assert len(rows) == 10_000
    assert rows[0]["employee_code"] == "EMP-00001"
    assert rows[-1]["employee_code"] == "EMP-10000"
    assert len({row["email"] for row in rows}) == 10_000
    assert len({row["employee_code"] for row in rows}) == 10_000
    assert all(row["salary"] > 0 for row in rows)
    assert all(isinstance(row["salary"], Decimal) for row in rows)


def test_bulk_insert_resets_and_leaves_room_for_later_creates(session, tmp_path):
    today = date(2026, 11, 25)
    rows = generate_employee_rows(3, seed=1, today=today)
    assert insert_generated_employees(session, rows, reset=False) == 3
    with pytest.raises(DomainError) as caught:
        insert_generated_employees(session, rows, reset=False)
    assert caught.value.code == "seed_not_empty"
    insert_generated_employees(session, rows, reset=True)
    created = EmployeeService(session).create(employee_payload(email="new.person@northstar.example", full_name="New Person"))
    assert created.employee_code == "EMP-00004"

    database = tmp_path / "seed.db"
    started = time.perf_counter()
    bulk = generate_employee_rows(10_000, seed=42, today=today)
    from app.db import make_engine
    from app.models import Employee
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import func, select

    engine = make_engine(sqlite_url(database))
    from app.db import Base

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        insert_generated_employees(db, bulk, reset=True)
        db.commit()
        stored = db.scalar(select(func.count()).select_from(Employee))
    engine.dispose()
    assert stored == 10_000
    assert time.perf_counter() - started < 10


def test_cli_refuses_to_overwrite_without_reset(tmp_path, capsys):
    database = tmp_path / "cli.db"
    url = sqlite_url(database)
    from app.seeding import seed_url

    seed_url(url, count=3, seed=1, reset=False, today=date(2026, 11, 25))
    with pytest.raises(SystemExit) as caught:
        main(["--count", "3", "--database-url", url, "--seed", "1"])
    assert caught.value.code == 1
    assert "reset" in capsys.readouterr().err.lower()


def test_invalid_seed_count():
    with pytest.raises(DomainError):
        generate_employee_rows(0, seed=1, today=date(2026, 11, 25))
    with pytest.raises(DomainError):
        generate_employee_rows(100_001, seed=1, today=date(2026, 11, 25))
