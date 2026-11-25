from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from app.errors import DomainError
from app.validation import (
    assert_currency,
    canonical_country,
    normalize_city,
    normalize_department,
    normalize_email,
    normalize_full_name,
    normalize_job_title,
    parse_employment_type,
    parse_hire_date,
    parse_salary,
    parse_status,
)


def test_full_name_strips_and_collapses_whitespace():
    assert normalize_full_name("  Priya   Sharma  ") == "Priya Sharma"


def test_full_name_accepts_unicode_and_apostrophes():
    assert normalize_full_name("李娜") == "李娜"
    assert normalize_full_name("José Álvarez") == "José Álvarez"
    assert normalize_full_name("Mary-Jane O'Brien") == "Mary-Jane O'Brien"


@pytest.mark.parametrize(
    "value",
    ["", "   ", "A", "John3", "Mary--Jane", "123", None, 12, "A" * 121],
)
def test_full_name_rejects_bad_values(value):
    with pytest.raises(DomainError) as caught:
        normalize_full_name(value)
    assert caught.value.code == "invalid_name"
    assert "full_name" in caught.value.fields


def test_full_name_accepts_max_length():
    assert len(normalize_full_name("A" * 120)) == 120


def test_city_accepts_punctuation_used_in_real_cities():
    assert normalize_city("  São   Paulo ") == "São Paulo"
    assert normalize_city("St. Louis") == "St. Louis"


def test_job_title_accepts_digits_and_slash():
    assert normalize_job_title("  engineer   II ") == "engineer II"
    assert normalize_job_title("QA/SDET") == "QA/SDET"


def test_department_accepts_ampersand():
    assert normalize_department("R&D") == "R&D"


def test_country_match_is_case_insensitive_and_rejects_unknown():
    assert canonical_country("  united   states ").name == "United States"
    assert canonical_country("INDIA").currency == "INR"
    with pytest.raises(DomainError) as caught:
        canonical_country("Narnia")
    assert caught.value.code == "invalid_country"


def test_currency_defaults_to_the_country_and_rejects_a_mismatch():
    india = canonical_country("india")
    assert assert_currency(india, None) == "INR"
    assert assert_currency(india, " inr ") == "INR"
    with pytest.raises(DomainError) as caught:
        assert_currency(india, "USD")
    assert caught.value.code == "currency_mismatch"


def test_email_is_normalized_and_casefolded():
    assert normalize_email("  Priya.Sharma@Northstar.Example ") == "priya.sharma@northstar.example"
    with pytest.raises(DomainError) as caught:
        normalize_email("not-an-email")
    assert caught.value.fields["email"]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1840000.50", Decimal("1840000.50")),
        ("120,000.50", Decimal("120000.50")),
        ("120 000.50", Decimal("120000.50")),
        (10, Decimal("10.00")),
        (Decimal("10.2"), Decimal("10.20")),
        (Decimal("10.500"), Decimal("10.50")),
    ],
)
def test_salary_parses_exact_money(raw, expected):
    assert parse_salary(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [None, True, False, "", "0", "0.00", "-5", "10.999", "1e2", "$120", float("nan"), float("inf"), "ten"],
)
def test_salary_rejects_bad_values(raw):
    with pytest.raises(DomainError) as caught:
        parse_salary(raw)
    assert caught.value.code == "invalid_salary"


def test_salary_rejects_amounts_above_the_cap():
    with pytest.raises(DomainError) as caught:
        parse_salary("1000000000.01")
    assert "1,000,000,000" in caught.value.message


def test_hire_date_bounds():
    assert parse_hire_date("1950-01-01") == date(1950, 1, 1)
    assert parse_hire_date(date(2020, 1, 2)) == date(2020, 1, 2)
    with pytest.raises(DomainError):
        parse_hire_date(date.today() + timedelta(days=1))
    with pytest.raises(DomainError):
        parse_hire_date("1949-12-31")
    with pytest.raises(DomainError):
        parse_hire_date(datetime.now())
    with pytest.raises(DomainError):
        parse_hire_date("yesterday")


def test_employment_and_status_aliases():
    assert parse_employment_type("Part-time") == "part_time"
    assert parse_employment_type("contractor") == "contract"
    assert parse_status("on leave") == "on_leave"
    assert parse_status("on-leave") == "on_leave"
    with pytest.raises(DomainError):
        parse_employment_type("intern")
    with pytest.raises(DomainError):
        parse_status("inactive")
