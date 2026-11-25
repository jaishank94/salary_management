from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.db import Base, make_engine
from app.main import create_app


@pytest.fixture
def session():
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = factory()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.fixture
def client():
    application = create_app("sqlite://")
    with TestClient(application) as test_client:
        yield test_client


def employee_payload(**overrides) -> dict:
    data = {
        "full_name": "Priya Sharma",
        "email": "priya.sharma@northstar.example",
        "job_title": "Software Engineer",
        "department": "Engineering",
        "country": "India",
        "city": "Bengaluru",
        "salary": "1840000.50",
        "employment_type": "full_time",
        "status": "active",
        "hire_date": "2022-04-18",
    }
    data.update(overrides)
    return data


FIXED_TODAY = date(2026, 11, 25)
