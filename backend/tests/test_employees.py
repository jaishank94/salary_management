from decimal import Decimal

import pytest

from app.errors import DomainError
from app.services.employees import EmployeeFilters, EmployeeService
from tests.conftest import employee_payload


def test_create_normalizes_and_assigns_a_code(session):
    employee = EmployeeService(session).create(
        employee_payload(full_name="  Priya   Sharma ", email="Priya.Sharma@Northstar.Example", country="india")
    )
    assert employee.id == 1
    assert employee.employee_code == "EMP-00001"
    assert employee.full_name == "Priya Sharma"
    assert employee.email == "priya.sharma@northstar.example"
    assert employee.country == "India"
    assert employee.currency == "INR"
    assert employee.salary == Decimal("1840000.50")
    assert employee.created_at is not None
    assert employee.updated_at is not None


def test_duplicate_email_is_case_insensitive(session):
    service = EmployeeService(session)
    service.create(employee_payload())
    with pytest.raises(DomainError) as caught:
        service.create(employee_payload(email="PRIYA.SHARMA@northstar.example", full_name="Priya Shah"))
    assert caught.value.code == "duplicate_email"
    assert caught.value.fields["email"]


def test_partial_update_keeps_other_fields_and_country_change_switches_currency(session):
    service = EmployeeService(session)
    employee = service.create(employee_payload())
    renamed = service.update(employee.id, {"full_name": "Priya S. Sharma"})
    assert renamed.full_name == "Priya S. Sharma"
    assert renamed.salary == Decimal("1840000.50")
    assert renamed.email == "priya.sharma@northstar.example"

    moved = service.update(employee.id, {"country": "Germany", "city": "Berlin"})
    assert moved.country == "Germany"
    assert moved.currency == "EUR"
    assert moved.salary == Decimal("1840000.50")


def test_explicit_currency_mismatch_does_not_change_the_row(session):
    service = EmployeeService(session)
    employee = service.create(employee_payload())
    with pytest.raises(DomainError) as caught:
        service.update(employee.id, {"currency": "USD"})
    assert caught.value.code == "currency_mismatch"
    assert service.get(employee.id).currency == "INR"


def test_update_rejects_another_employees_email(session):
    service = EmployeeService(session)
    first = service.create(employee_payload())
    second = service.create(employee_payload(email="arjun@northstar.example", full_name="Arjun Mehta"))
    with pytest.raises(DomainError) as caught:
        service.update(second.id, {"email": first.email})
    assert caught.value.code == "duplicate_email"
    assert service.get(second.id).email == "arjun@northstar.example"


def test_same_email_on_update_is_allowed(session):
    service = EmployeeService(session)
    employee = service.create(employee_payload())
    updated = service.update(employee.id, {"email": "PRIYA.SHARMA@northstar.example", "salary": "1900000"})
    assert updated.email == "priya.sharma@northstar.example"
    assert updated.salary == Decimal("1900000.00")


def test_empty_update_is_a_no_op(session):
    service = EmployeeService(session)
    employee = service.create(employee_payload())
    assert service.update(employee.id, {}) is employee


def test_get_and_delete_missing_employees(session):
    service = EmployeeService(session)
    with pytest.raises(DomainError) as caught:
        service.get(99)
    assert caught.value.code == "not_found"
    employee = service.create(employee_payload())
    service.delete(employee.id)
    with pytest.raises(DomainError):
        service.get(employee.id)
    with pytest.raises(DomainError):
        service.delete(employee.id)


def test_future_salary_and_blank_name_are_rejected(session):
    service = EmployeeService(session)
    with pytest.raises(DomainError):
        service.create(employee_payload(salary="0"))
    with pytest.raises(DomainError):
        service.create(employee_payload(full_name="   "))
    with pytest.raises(DomainError):
        service.create(employee_payload(hire_date="2999-01-01"))


def test_search_escapes_like_wildcards_and_filters(session):
    service = EmployeeService(session)
    service.create(employee_payload(full_name="Amy Percent", email="amy.percent@northstar.example"))
    service.create(employee_payload(full_name="Bob Stone", email="bob_stone@northstar.example", city="Mumbai"))
    service.create(
        employee_payload(
            full_name="Clara Weiss",
            email="clara@northstar.example",
            country="Germany",
            city="Berlin",
            status="terminated",
            job_title="Accountant",
            department="Finance",
        )
    )

    wildcard = service.list_employees(EmployeeFilters(q="%"))
    assert wildcard.total == 0
    underscore = service.list_employees(EmployeeFilters(q="_"))
    assert [item.full_name for item in underscore.items] == ["Bob Stone"]
    by_name = service.list_employees(EmployeeFilters(q="amy"))
    assert by_name.total == 1
    by_country = service.list_employees(EmployeeFilters(country="germany"))
    assert [item.full_name for item in by_country.items] == ["Clara Weiss"]
    by_status = service.list_employees(EmployeeFilters(status="on leave"))
    assert by_status.total == 0
    terminated = service.list_employees(EmployeeFilters(status="terminated"))
    assert terminated.total == 1


def test_pagination_and_salary_sort(session):
    service = EmployeeService(session)
    for index in range(30):
        service.create(
            employee_payload(
                full_name="Sample " + chr(65 + index // 26) + chr(65 + index % 26),
                email=f"person{index:02d}@northstar.example",
                salary=str(1000 + index),
            )
        )
    page = service.list_employees(EmployeeFilters(page=2, page_size=10, sort="salary", direction="desc"))
    assert page.total == 30
    assert page.pages == 3
    assert len(page.items) == 10
    assert page.items[0].salary > page.items[-1].salary
    beyond = service.list_employees(EmployeeFilters(page=4, page_size=10))
    assert beyond.items == []
    assert beyond.total == 30

    with pytest.raises(DomainError):
        service.list_employees(EmployeeFilters(page=0))
    with pytest.raises(DomainError):
        service.list_employees(EmployeeFilters(page_size=101))
    with pytest.raises(DomainError):
        service.list_employees(EmployeeFilters(sort="nickname"))


def test_full_name_with_a_number_token_is_rejected_but_titles_may_contain_digits(session):
    service = EmployeeService(session)
    with pytest.raises(DomainError):
        service.create(employee_payload(full_name="Priya 3"))
    employee = service.create(employee_payload(job_title="Engineer II"))
    assert employee.job_title == "Engineer II"
    listed = service.list_employees(EmployeeFilters(job_title="engineer ii"))
    assert listed.total == 1
