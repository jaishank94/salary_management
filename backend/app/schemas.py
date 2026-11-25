"""HTTP request and response models."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer

from app.validation import quantize_money


def _money(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return f"{quantize_money(value):.2f}"


class EmployeeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str
    email: str
    job_title: str
    department: str
    country: str
    city: str
    salary: str | int | float | Decimal
    employment_type: str = "full_time"
    status: str = "active"
    hire_date: date
    currency: str | None = None


class EmployeeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = None
    email: str | None = None
    job_title: str | None = None
    department: str | None = None
    country: str | None = None
    city: str | None = None
    salary: str | int | float | Decimal | None = None
    employment_type: str | None = None
    status: str | None = None
    hire_date: date | None = None
    currency: str | None = None


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_code: str
    full_name: str
    email: str
    job_title: str
    department: str
    country: str
    city: str
    currency: str
    salary: Decimal
    employment_type: str
    status: str
    hire_date: date
    created_at: datetime
    updated_at: datetime

    @field_serializer("salary")
    def serialize_salary(self, value: Decimal) -> str:
        return _money(value) or "0.00"


class EmployeeListResponse(BaseModel):
    items: list[EmployeeRead]
    total: int
    page: int
    page_size: int
    pages: int


class GroupBreakdown(BaseModel):
    key: str
    headcount: int
    minimum: Decimal | None
    maximum: Decimal | None
    average: Decimal | None
    total_payroll: Decimal

    @field_serializer("minimum", "maximum", "average", "total_payroll")
    def serialize_money(self, value: Decimal | None) -> str | None:
        return _money(value)


class SalaryBandRead(BaseModel):
    minimum: Decimal
    maximum: Decimal
    count: int

    @field_serializer("minimum", "maximum")
    def serialize_money(self, value: Decimal) -> str:
        return _money(value) or "0.00"


class CountryRollup(BaseModel):
    country: str
    currency: str
    headcount: int
    minimum: Decimal | None
    maximum: Decimal | None
    average: Decimal | None
    total_payroll: Decimal

    @field_serializer("minimum", "maximum", "average", "total_payroll")
    def serialize_money(self, value: Decimal | None) -> str | None:
        return _money(value)


class OverviewResponse(BaseModel):
    workforce_count: int
    compensation_headcount: int
    status_breakdown: dict[str, int]
    included_statuses: list[str]
    countries: list[CountryRollup]


class CountryInsightsResponse(BaseModel):
    country: str
    currency: str
    included_statuses: list[str]
    excluded_currency_count: int
    status_breakdown: dict[str, int]
    headcount: int
    minimum: Decimal | None
    maximum: Decimal | None
    average: Decimal | None
    median: Decimal | None
    p25: Decimal | None
    p75: Decimal | None
    total_payroll: Decimal
    bands: list[SalaryBandRead]
    by_department: list[GroupBreakdown]
    by_job_title: list[GroupBreakdown]
    by_employment_type: list[GroupBreakdown]

    @field_serializer("minimum", "maximum", "average", "median", "p25", "p75", "total_payroll")
    def serialize_money(self, value: Decimal | None) -> str | None:
        return _money(value)


class TitleInsightsResponse(BaseModel):
    country: str
    currency: str
    job_title: str
    included_statuses: list[str]
    excluded_currency_count: int
    headcount: int
    minimum: Decimal | None
    maximum: Decimal | None
    average: Decimal | None
    median: Decimal | None
    p25: Decimal | None
    p75: Decimal | None
    total_payroll: Decimal
    bands: list[SalaryBandRead]

    @field_serializer("minimum", "maximum", "average", "median", "p25", "p75", "total_payroll")
    def serialize_money(self, value: Decimal | None) -> str | None:
        return _money(value)
