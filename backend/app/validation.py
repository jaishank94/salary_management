"""Pure validation for employee fields.

These functions are the source of truth for what the directory will store.
They do not touch the database, so the edge cases can be tested directly.
"""

import math
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from email_validator import EmailNotValidError, validate_email

from app.errors import DomainError
from app.reference import COUNTRY_BY_KEY, Country

TWOPLACES = Decimal("0.01")
MAX_SALARY = Decimal("1000000000")
EARLIEST_HIRE = date(1950, 1, 1)
_NAME_PUNCTUATION = set(".'’-")
_TITLE_EXTRA = set("&/+")
_SALARY_AMOUNT = re.compile(r"\d+(\.\d+)?")
_SALARY_NEGATIVE = re.compile(r"-\d+(\.\d+)?")


def quantize_money(amount: Decimal) -> Decimal:
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def as_decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool) or value is None:
        raise DomainError("invalid_salary", "Salary is required.", {"salary": "Enter a salary greater than zero."})
    if isinstance(value, float):
        if not math.isfinite(value):
            raise DomainError(
                "invalid_salary",
                "Salary must be a finite number.",
                {"salary": "Enter a salary greater than zero."},
            )
        return Decimal(format(value, "f"))
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise DomainError(
            "invalid_salary",
            "Enter a salary using digits and an optional decimal point.",
            {"salary": "Enter a positive amount with up to 2 decimal places."},
        ) from exc


def _reject(code: str, message: str, field: str) -> DomainError:
    return DomainError(code, message, {field: message})


def _collapse(value: str) -> str:
    return " ".join(value.split())


def _check_token_shape(collapsed: str, *, field: str, code: str, label: str, minimum: int, maximum: int, allow_digits: bool, allow_extra: str) -> None:
    if len(collapsed) < minimum:
        raise _reject(code, f"{label} must be at least {minimum} characters.", field)
    if len(collapsed) > maximum:
        raise _reject(code, f"{label} must be {maximum} characters or fewer.", field)
    if not collapsed[0].isalpha():
        raise _reject(code, f"{label} must start with a letter.", field)
    allowed = set(_NAME_PUNCTUATION)
    allowed.update(allow_extra)
    allowed.add(" ")
    for character in collapsed:
        if character.isalpha() or (allow_digits and character.isdigit()) or character in allowed:
            continue
        raise _reject(
            code,
            f"{label} contains a character that is not allowed.",
            field,
        )
    if not collapsed[-1].isalpha() and collapsed[-1] not in {".", *(() if not allow_digits else "0123456789")}:
        if not (allow_digits and collapsed[-1].isdigit()):
            raise _reject(code, f"{label} must end with a letter.", field)
    for left, right in zip(collapsed, collapsed[1:]):
        if left in _NAME_PUNCTUATION and right in _NAME_PUNCTUATION:
            raise _reject(code, f"{label} has misplaced punctuation.", field)
        if left in _TITLE_EXTRA and right in _TITLE_EXTRA:
            raise _reject(code, f"{label} has misplaced punctuation.", field)


def normalize_full_name(value: object) -> str:
    if not isinstance(value, str):
        raise _reject("invalid_name", "Full name is required.", "full_name")
    collapsed = _collapse(value)
    if not collapsed:
        raise _reject("invalid_name", "Full name is required.", "full_name")
    _check_token_shape(
        collapsed,
        field="full_name",
        code="invalid_name",
        label="Full name",
        minimum=2,
        maximum=120,
        allow_digits=False,
        allow_extra="",
    )
    return collapsed


def normalize_city(value: object) -> str:
    if not isinstance(value, str):
        raise _reject("invalid_city", "City is required.", "city")
    collapsed = _collapse(value)
    if not collapsed:
        raise _reject("invalid_city", "City is required.", "city")
    _check_token_shape(
        collapsed,
        field="city",
        code="invalid_city",
        label="City",
        minimum=2,
        maximum=60,
        allow_digits=False,
        allow_extra="",
    )
    return collapsed


def normalize_job_title(value: object) -> str:
    if not isinstance(value, str):
        raise _reject("invalid_job_title", "Job title is required.", "job_title")
    collapsed = _collapse(value)
    if not collapsed:
        raise _reject("invalid_job_title", "Job title is required.", "job_title")
    _check_token_shape(
        collapsed,
        field="job_title",
        code="invalid_job_title",
        label="Job title",
        minimum=2,
        maximum=80,
        allow_digits=True,
        allow_extra="&/+",
    )
    return collapsed


def normalize_department(value: object) -> str:
    if not isinstance(value, str):
        raise _reject("invalid_department", "Department is required.", "department")
    collapsed = _collapse(value)
    if not collapsed:
        raise _reject("invalid_department", "Department is required.", "department")
    _check_token_shape(
        collapsed,
        field="department",
        code="invalid_department",
        label="Department",
        minimum=2,
        maximum=40,
        allow_digits=False,
        allow_extra="&/",
    )
    return collapsed


def canonical_country(value: object) -> Country:
    if not isinstance(value, str) or not value.strip():
        raise _reject("invalid_country", "Choose a country.", "country")
    key = _collapse(value).casefold()
    country = COUNTRY_BY_KEY.get(key)
    if country is None:
        raise _reject("invalid_country", "Choose a supported country.", "country")
    return country


def assert_currency(country: Country, currency: object | None) -> str:
    """Keep a country's salaries in one currency so averages stay meaningful."""
    if currency is None or currency == "":
        return country.currency
    if not isinstance(currency, str) or not currency.strip():
        raise _reject("currency_mismatch", f"Use {country.currency} for {country.name}.", "currency")
    code = currency.strip().upper()
    if code != country.currency:
        raise DomainError(
            "currency_mismatch",
            f"Salaries in {country.name} are recorded in {country.currency} so averages stay comparable.",
            {"currency": f"Use {country.currency} for {country.name}."},
        )
    return code


def normalize_email(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _reject("invalid_email", "Email is required.", "email")
    try:
        result = validate_email(value.strip(), check_deliverability=False)
    except EmailNotValidError as exc:
        raise _reject("invalid_email", "Enter a valid email address.", "email") from exc
    return result.normalized.casefold()


def parse_salary(value: object) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise _reject("invalid_salary", "Enter a salary greater than zero.", "salary")
    if isinstance(value, Decimal):
        raw = format(value, "f")
    elif isinstance(value, int):
        raw = str(value)
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise _reject("invalid_salary", "Salary must be a finite number.", "salary")
        raw = format(value, "f")
    elif isinstance(value, str):
        raw = value.strip().replace(",", "").replace(" ", "").replace("_", "")
    else:
        raise _reject("invalid_salary", "Enter a salary greater than zero.", "salary")

    if _SALARY_NEGATIVE.fullmatch(raw):
        raise _reject("invalid_salary", "Salary must be greater than zero.", "salary")
    if not _SALARY_AMOUNT.fullmatch(raw):
        raise _reject(
            "invalid_salary",
            "Enter a positive amount with up to 2 decimal places.",
            "salary",
        )
    amount = Decimal(raw)
    if quantize_money(amount) != amount:
        raise _reject("invalid_salary", "Use at most 2 decimal places.", "salary")
    if amount <= 0:
        raise _reject("invalid_salary", "Salary must be greater than zero.", "salary")
    if amount > MAX_SALARY:
        raise _reject("invalid_salary", "Salary must be 1,000,000,000 or less.", "salary")
    return quantize_money(amount)


def parse_hire_date(value: object, today: date | None = None) -> date:
    current = today or date.today()
    if isinstance(value, datetime):
        raise _reject("invalid_hire_date", "Use a calendar date (YYYY-MM-DD).", "hire_date")
    if isinstance(value, date):
        parsed = value
    elif isinstance(value, str):
        text = value.strip()
        try:
            parsed = date.fromisoformat(text)
        except ValueError as exc:
            raise _reject("invalid_hire_date", "Use a calendar date (YYYY-MM-DD).", "hire_date") from exc
    else:
        raise _reject("invalid_hire_date", "Hire date is required.", "hire_date")
    if parsed > current:
        raise _reject("invalid_hire_date", "Hire date cannot be in the future.", "hire_date")
    if parsed < EARLIEST_HIRE:
        raise _reject("invalid_hire_date", "Hire date must be on or after 1950-01-01.", "hire_date")
    return parsed


def _alias(value: object, mapping: dict[str, str], *, field: str, code: str, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _reject(code, message, field)
    key = _collapse(value).casefold().replace("-", " ").replace("_", " ")
    found = mapping.get(key)
    if found is None:
        raise _reject(code, message, field)
    return found


def parse_employment_type(value: object) -> str:
    return _alias(
        value,
        {
            "full time": "full_time",
            "part time": "part_time",
            "contract": "contract",
            "contractor": "contract",
        },
        field="employment_type",
        code="invalid_employment_type",
        message="Choose full-time, part-time, or contract.",
    )


def parse_status(value: object) -> str:
    return _alias(
        value,
        {
            "active": "active",
            "on leave": "on_leave",
            "leave": "on_leave",
            "terminated": "terminated",
        },
        field="status",
        code="invalid_status",
        message="Choose active, on leave, or terminated.",
    )


def is_valid_name_token(value: str) -> bool:
    """A single given name or surname, safe to combine into a full name."""
    if not value or " " in value:
        return False
    try:
        normalize_full_name(value)
    except DomainError:
        return False
    return True
