from decimal import Decimal

from app.services.employees import EmployeeService
from app.services.insights import InsightsService
from tests.conftest import employee_payload


def _add(session, **overrides):
    return EmployeeService(session).create(employee_payload(**overrides))


def test_country_stats_ignore_other_countries_and_terminated_people(session):
    _add(session, salary="100.00", department="Engineering", job_title="Software Engineer")
    _add(session, salary="200.00", email="b@northstar.example", full_name="Ananya Iyer", department="Engineering")
    _add(session, salary="300.00", email="c@northstar.example", full_name="Rohan Gupta", department="Design", job_title="Product Designer")
    _add(
        session,
        salary="10000.00",
        email="d@northstar.example",
        full_name="Former Employee",
        status="terminated",
    )
    _add(
        session,
        salary="50.00",
        email="e@northstar.example",
        full_name="Greta Fischer",
        country="Germany",
        city="Berlin",
    )

    stats = InsightsService(session).country("india")
    assert stats["country"] == "India"
    assert stats["currency"] == "INR"
    assert stats["headcount"] == 3
    assert stats["minimum"] == Decimal("100.00")
    assert stats["maximum"] == Decimal("300.00")
    assert stats["average"] == Decimal("200.00")
    assert stats["median"] == Decimal("200.00")
    assert stats["total_payroll"] == Decimal("600.00")
    assert stats["included_statuses"] == ["active", "on_leave"]
    assert stats["status_breakdown"]["terminated"] == 1
    assert stats["status_breakdown"]["active"] == 3
    assert stats["excluded_currency_count"] == 0
    engineering = next(item for item in stats["by_department"] if item["key"] == "Engineering")
    assert engineering["headcount"] == 2
    assert engineering["average"] == Decimal("150.00")
    assert sum(band["count"] for band in stats["bands"]) == 3

    with_terminated = InsightsService(session).country("India", include_terminated=True)
    assert with_terminated["headcount"] == 4
    assert with_terminated["maximum"] == Decimal("10000.00")

    title = InsightsService(session).job_title("India", "  software   engineer ")
    assert title["job_title"] == "Software Engineer"
    assert title["headcount"] == 2
    assert title["average"] == Decimal("150.00")
    assert title["minimum"] == Decimal("100.00")
    assert title["maximum"] == Decimal("200.00")

    missing = InsightsService(session).job_title("Japan", "Accountant")
    assert missing["headcount"] == 0
    assert missing["average"] is None
    assert missing["total_payroll"] == Decimal("0.00")


def test_overview_groups_by_country_and_currency(session):
    _add(session, salary="100.00")
    _add(session, salary="300.00", email="b@northstar.example", full_name="Ananya Iyer")
    _add(
        session,
        salary="50.00",
        email="c@northstar.example",
        full_name="Greta Fischer",
        country="Germany",
        city="Berlin",
        status="terminated",
    )
    overview = InsightsService(session).overview()
    assert overview["workforce_count"] == 3
    assert overview["compensation_headcount"] == 2
    assert overview["status_breakdown"]["terminated"] == 1
    assert [item["country"] for item in overview["countries"]] == ["India"]
    assert overview["countries"][0]["currency"] == "INR"
    assert overview["countries"][0]["average"] == Decimal("200.00")

    empty = InsightsService(session).overview()
    assert empty["workforce_count"] == 3


def test_mixed_currencies_are_not_averaged_together(session):
    employee = _add(session, salary="100.00")
    employee.currency = "USD"
    session.flush()
    _add(session, salary="300.00", email="b@northstar.example", full_name="Ananya Iyer")

    stats = InsightsService(session).country("India")
    assert stats["excluded_currency_count"] == 1
    assert stats["headcount"] == 1
    assert stats["average"] == Decimal("300.00")

    overview = InsightsService(session).overview()
    pairs = {(item["country"], item["currency"]) for item in overview["countries"]}
    assert ("India", "INR") in pairs
    assert ("India", "USD") in pairs


def test_even_median_and_percentiles_for_a_country(session):
    amounts = ["100.00", "200.00", "300.00", "400.00"]
    for index, amount in enumerate(amounts):
        _add(
            session,
            salary=amount,
            email=f"p{index}@northstar.example",
            full_name="Person " + "ABCD"[index],
        )
    stats = InsightsService(session).country("India")
    assert stats["median"] == Decimal("250.00")
    assert stats["p25"] == Decimal("100.00")
    assert stats["p75"] == Decimal("300.00")
    assert stats["average"] == Decimal("250.00")
