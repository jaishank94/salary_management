"""Salary insights for an HR manager.

Every average is scoped to one country and one currency. Terminated employees
are omitted unless the caller asks for them, because current pay bands should
describe people the company still employs.
"""

from collections import Counter, defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Employee
from app.reference import COMPENSATION_STATUSES, STATUSES
from app.salary_stats import SalarySummary, summarize_salaries
from app.validation import canonical_country, normalize_job_title


def _status_counts(rows) -> dict[str, int]:
    counts = {status: 0 for status in STATUSES}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    return counts


def _included(include_terminated: bool) -> list[str]:
    if include_terminated:
        return list(STATUSES)
    return list(COMPENSATION_STATUSES)


def _summary_payload(summary: SalarySummary) -> dict:
    return {
        "headcount": summary.headcount,
        "minimum": summary.minimum,
        "maximum": summary.maximum,
        "average": summary.average,
        "median": summary.median,
        "p25": summary.p25,
        "p75": summary.p75,
        "total_payroll": summary.total_payroll,
        "bands": [
            {"minimum": band.minimum, "maximum": band.maximum, "count": band.count}
            for band in summary.bands
        ],
    }


def _group(rows, attribute: str) -> list[dict]:
    buckets: dict[str, list] = defaultdict(list)
    for row in rows:
        buckets[getattr(row, attribute)].append(row.salary)
    groups = []
    for key, salaries in buckets.items():
        summary = summarize_salaries(salaries)
        groups.append(
            {
                "key": key,
                "headcount": summary.headcount,
                "minimum": summary.minimum,
                "maximum": summary.maximum,
                "average": summary.average,
                "total_payroll": summary.total_payroll,
            }
        )
    groups.sort(key=lambda item: (-item["headcount"], item["key"]))
    return groups


class InsightsService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def overview(self, *, include_terminated: bool = False) -> dict:
        rows = self._rows()
        population = self._population(rows, include_terminated)
        buckets: dict[tuple[str, str], list] = defaultdict(list)
        for row in population:
            buckets[(row.country, row.currency)].append(row.salary)
        countries = []
        for (country, currency), salaries in buckets.items():
            summary = summarize_salaries(salaries)
            countries.append(
                {
                    "country": country,
                    "currency": currency,
                    "headcount": summary.headcount,
                    "minimum": summary.minimum,
                    "maximum": summary.maximum,
                    "average": summary.average,
                    "total_payroll": summary.total_payroll,
                }
            )
        countries.sort(key=lambda item: (-item["headcount"], item["country"], item["currency"]))
        return {
            "workforce_count": len(rows),
            "compensation_headcount": len(population),
            "status_breakdown": _status_counts(rows),
            "included_statuses": _included(include_terminated),
            "countries": countries,
        }

    def country(self, country: str, *, include_terminated: bool = False) -> dict:
        canonical = canonical_country(country)
        rows = self._rows(country_name=canonical.name)
        excluded = sum(1 for row in rows if row.currency != canonical.currency)
        scoped = [row for row in rows if row.currency == canonical.currency]
        population = self._population(scoped, include_terminated)
        summary = summarize_salaries([row.salary for row in population])
        return {
            "country": canonical.name,
            "currency": canonical.currency,
            "included_statuses": _included(include_terminated),
            "excluded_currency_count": excluded,
            "status_breakdown": _status_counts(scoped),
            **_summary_payload(summary),
            "by_department": _group(population, "department"),
            "by_job_title": _group(population, "job_title"),
            "by_employment_type": _group(population, "employment_type"),
        }

    def job_title(self, country: str, job_title: str, *, include_terminated: bool = False) -> dict:
        canonical = canonical_country(country)
        normalized = normalize_job_title(job_title)
        rows = self._rows(country_name=canonical.name, job_title=normalized)
        excluded = sum(1 for row in rows if row.currency != canonical.currency)
        scoped = [row for row in rows if row.currency == canonical.currency]
        population = self._population(scoped, include_terminated)
        summary = summarize_salaries([row.salary for row in population])
        display = normalized
        if scoped:
            display = Counter(row.job_title for row in scoped).most_common(1)[0][0]
        return {
            "country": canonical.name,
            "currency": canonical.currency,
            "job_title": display,
            "included_statuses": _included(include_terminated),
            "excluded_currency_count": excluded,
            **_summary_payload(summary),
        }

    def _population(self, rows, include_terminated: bool):
        if include_terminated:
            return list(rows)
        return [row for row in rows if row.status in COMPENSATION_STATUSES]

    def _rows(self, country_name: str | None = None, job_title: str | None = None):
        stmt = select(
            Employee.salary,
            Employee.department,
            Employee.job_title,
            Employee.employment_type,
            Employee.status,
            Employee.country,
            Employee.currency,
        )
        if country_name is not None:
            stmt = stmt.where(Employee.country == country_name)
        if job_title is not None:
            stmt = stmt.where(func.lower(Employee.job_title) == job_title.casefold())
        return self.session.execute(stmt).all()
