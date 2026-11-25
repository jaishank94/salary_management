"""Employee directory use cases."""

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models import Employee
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

SORT_COLUMNS = {
    "full_name": Employee.full_name,
    "salary": Employee.salary,
    "hire_date": Employee.hire_date,
    "country": Employee.country,
    "city": Employee.city,
    "job_title": Employee.job_title,
    "department": Employee.department,
    "employee_code": Employee.employee_code,
    "status": Employee.status,
    "created_at": Employee.created_at,
}


@dataclass
class EmployeeFilters:
    q: str | None = None
    country: str | None = None
    job_title: str | None = None
    department: str | None = None
    city: str | None = None
    status: str | None = None
    employment_type: str | None = None
    page: int = 1
    page_size: int = 25
    sort: str = "full_name"
    direction: str = "asc"


@dataclass
class EmployeePage:
    items: list[Employee]
    total: int
    page: int
    page_size: int
    pages: int


def _like(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped.casefold()}%"


class EmployeeService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: dict) -> Employee:
        fields = self._normalize(data)
        self._ensure_email_available(fields["email"])
        now = datetime.now(timezone.utc)
        employee = Employee(employee_code=f"TMP-{uuid4().hex[:12]}", created_at=now, updated_at=now, **fields)
        try:
            with self.session.begin_nested():
                self.session.add(employee)
                self.session.flush()
        except IntegrityError as exc:
            raise DomainError(
                "duplicate_email",
                "An employee with this email already exists.",
                {"email": "This email is already in use."},
            ) from exc
        employee.employee_code = f"EMP-{employee.id:05d}"
        self.session.flush()
        return employee

    def get(self, employee_id: int) -> Employee:
        if isinstance(employee_id, bool) or not isinstance(employee_id, int) or employee_id < 1:
            raise DomainError("not_found", "Employee not found.")
        employee = self.session.get(Employee, employee_id)
        if employee is None:
            raise DomainError("not_found", "Employee not found.")
        return employee

    def update(self, employee_id: int, changes: dict) -> Employee:
        employee = self.get(employee_id)
        if not changes:
            return employee
        # Currency follows the country unless the caller sets it explicitly.
        # A country change must not keep the previous currency by accident.
        if "currency" in changes:
            currency_value = changes["currency"]
        else:
            currency_value = None
        raw = {
            "full_name": changes.get("full_name", employee.full_name),
            "email": changes.get("email", employee.email),
            "job_title": changes.get("job_title", employee.job_title),
            "department": changes.get("department", employee.department),
            "country": changes.get("country", employee.country),
            "city": changes.get("city", employee.city),
            "salary": changes.get("salary", employee.salary),
            "employment_type": changes.get("employment_type", employee.employment_type),
            "status": changes.get("status", employee.status),
            "hire_date": changes.get("hire_date", employee.hire_date),
            "currency": currency_value,
        }
        fields = self._normalize(raw)
        if fields["email"] != employee.email:
            self._ensure_email_available(fields["email"], exclude_id=employee.id)
        for key, value in fields.items():
            setattr(employee, key, value)
        employee.updated_at = datetime.now(timezone.utc)
        try:
            with self.session.begin_nested():
                self.session.flush()
        except IntegrityError as exc:
            raise DomainError(
                "duplicate_email",
                "An employee with this email already exists.",
                {"email": "This email is already in use."},
            ) from exc
        return employee

    def delete(self, employee_id: int) -> None:
        employee = self.get(employee_id)
        self.session.delete(employee)
        self.session.flush()

    def list_employees(self, filters: EmployeeFilters) -> EmployeePage:
        if filters.page < 1:
            raise DomainError("invalid_page", "Page must be 1 or greater.", {"page": "Page must be 1 or greater."})
        if filters.page_size < 1 or filters.page_size > 100:
            raise DomainError(
                "invalid_page_size",
                "Page size must be between 1 and 100.",
                {"page_size": "Page size must be between 1 and 100."},
            )
        sort_key = (filters.sort or "full_name").casefold()
        direction = (filters.direction or "asc").casefold()
        column = SORT_COLUMNS.get(sort_key)
        if column is None:
            allowed = ", ".join(sorted(SORT_COLUMNS))
            raise DomainError("invalid_sort", f"Sort must be one of: {allowed}.", {"sort": "Unsupported sort field."})
        if direction not in {"asc", "desc"}:
            raise DomainError("invalid_direction", "Direction must be asc or desc.", {"direction": "Use asc or desc."})

        clauses = self._filter_clauses(filters)
        total = self.session.scalar(select(func.count()).select_from(Employee).where(*clauses)) or 0
        ordering = column.desc() if direction == "desc" else column.asc()
        stmt = (
            select(Employee)
            .where(*clauses)
            .order_by(ordering, Employee.id.asc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )
        items = list(self.session.scalars(stmt))
        pages = math.ceil(total / filters.page_size) if total else 0
        return EmployeePage(items=items, total=int(total), page=filters.page, page_size=filters.page_size, pages=pages)

    def _filter_clauses(self, filters: EmployeeFilters) -> list:
        clauses: list = []
        if filters.q and filters.q.strip():
            needle = _like(filters.q.strip())
            clauses.append(
                or_(
                    func.lower(Employee.full_name).like(needle, escape="\\"),
                    func.lower(Employee.email).like(needle, escape="\\"),
                    func.lower(Employee.employee_code).like(needle, escape="\\"),
                    func.lower(Employee.job_title).like(needle, escape="\\"),
                    func.lower(Employee.department).like(needle, escape="\\"),
                    func.lower(Employee.city).like(needle, escape="\\"),
                    func.lower(Employee.country).like(needle, escape="\\"),
                )
            )
        if filters.country and filters.country.strip():
            clauses.append(Employee.country == canonical_country(filters.country).name)
        if filters.job_title and filters.job_title.strip():
            clauses.append(func.lower(Employee.job_title) == normalize_job_title(filters.job_title).casefold())
        if filters.department and filters.department.strip():
            clauses.append(func.lower(Employee.department) == normalize_department(filters.department).casefold())
        if filters.city and filters.city.strip():
            clauses.append(func.lower(Employee.city) == normalize_city(filters.city).casefold())
        if filters.status and filters.status.strip():
            clauses.append(Employee.status == parse_status(filters.status))
        if filters.employment_type and filters.employment_type.strip():
            clauses.append(Employee.employment_type == parse_employment_type(filters.employment_type))
        return clauses

    def _normalize(self, data: dict) -> dict:
        country = canonical_country(data.get("country"))
        return {
            "full_name": normalize_full_name(data.get("full_name")),
            "email": normalize_email(data.get("email")),
            "job_title": normalize_job_title(data.get("job_title")),
            "department": normalize_department(data.get("department")),
            "country": country.name,
            "city": normalize_city(data.get("city")),
            "currency": assert_currency(country, data.get("currency")),
            "salary": parse_salary(data.get("salary")),
            "employment_type": parse_employment_type(data.get("employment_type", "full_time")),
            "status": parse_status(data.get("status", "active")),
            "hire_date": parse_hire_date(data.get("hire_date")),
        }

    def _ensure_email_available(self, email: str, exclude_id: int | None = None) -> None:
        stmt = select(Employee.id).where(Employee.email == email)
        if exclude_id is not None:
            stmt = stmt.where(Employee.id != exclude_id)
        if self.session.scalar(stmt) is not None:
            raise DomainError(
                "duplicate_email",
                "An employee with this email already exists.",
                {"email": "This email is already in use."},
            )
