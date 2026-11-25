"""HTTP routes for the directory and compensation insights."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models import Employee
from app.reference import (
    COUNTRIES,
    DEPARTMENTS,
    EMPLOYMENT_LABELS,
    EMPLOYMENT_TYPES,
    JOB_TITLES,
    STATUS_LABELS,
    STATUSES,
)
from app.schemas import (
    CountryInsightsResponse,
    EmployeeCreate,
    EmployeeListResponse,
    EmployeeRead,
    EmployeeUpdate,
    OverviewResponse,
    TitleInsightsResponse,
)
from app.services.employees import EmployeeFilters, EmployeeService
from app.services.insights import InsightsService


def _blank(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def build_router(get_db):
    router = APIRouter(prefix="/api")

    @router.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok"}

    @router.get("/reference", tags=["meta"])
    def reference() -> dict:
        return {
            "countries": [
                {"name": country.name, "currency": country.currency, "cities": list(country.cities)}
                for country in COUNTRIES
            ],
            "job_titles": list(JOB_TITLES),
            "departments": list(DEPARTMENTS),
            "employment_types": [{"value": value, "label": EMPLOYMENT_LABELS[value]} for value in EMPLOYMENT_TYPES],
            "statuses": [{"value": value, "label": STATUS_LABELS[value]} for value in STATUSES],
        }

    @router.get("/employees", response_model=EmployeeListResponse, tags=["employees"])
    def list_employees(
        q: str | None = None,
        country: str | None = None,
        job_title: str | None = None,
        department: str | None = None,
        city: str | None = None,
        status: str | None = None,
        employment_type: str | None = None,
        page: int = 1,
        page_size: int = 25,
        sort: str = "full_name",
        direction: str = "asc",
        db: Session = Depends(get_db),
    ) -> EmployeeListResponse:
        page_result = EmployeeService(db).list_employees(
            EmployeeFilters(
                q=_blank(q),
                country=_blank(country),
                job_title=_blank(job_title),
                department=_blank(department),
                city=_blank(city),
                status=_blank(status),
                employment_type=_blank(employment_type),
                page=page,
                page_size=page_size,
                sort=sort,
                direction=direction,
            )
        )
        return EmployeeListResponse(
            items=page_result.items,
            total=page_result.total,
            page=page_result.page,
            page_size=page_result.page_size,
            pages=page_result.pages,
        )

    @router.post("/employees", response_model=EmployeeRead, status_code=201, tags=["employees"])
    def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)) -> Employee:
        return EmployeeService(db).create(payload.model_dump())

    @router.get("/employees/{employee_id}", response_model=EmployeeRead, tags=["employees"])
    def get_employee(employee_id: int, db: Session = Depends(get_db)) -> Employee:
        return EmployeeService(db).get(employee_id)

    @router.patch("/employees/{employee_id}", response_model=EmployeeRead, tags=["employees"])
    def update_employee(employee_id: int, payload: EmployeeUpdate, db: Session = Depends(get_db)) -> Employee:
        return EmployeeService(db).update(employee_id, payload.model_dump(exclude_unset=True))

    @router.delete("/employees/{employee_id}", status_code=204, tags=["employees"])
    def delete_employee(employee_id: int, db: Session = Depends(get_db)):
        EmployeeService(db).delete(employee_id)

    @router.get("/insights/overview", response_model=OverviewResponse, tags=["insights"])
    def overview(include_terminated: bool = False, db: Session = Depends(get_db)) -> dict:
        return InsightsService(db).overview(include_terminated=include_terminated)

    @router.get("/insights/country", response_model=CountryInsightsResponse, tags=["insights"])
    def country_insights(country: str, include_terminated: bool = False, db: Session = Depends(get_db)) -> dict:
        return InsightsService(db).country(country, include_terminated=include_terminated)

    @router.get("/insights/job-title", response_model=TitleInsightsResponse, tags=["insights"])
    def title_insights(
        country: str,
        job_title: str,
        include_terminated: bool = False,
        db: Session = Depends(get_db),
    ) -> dict:
        return InsightsService(db).job_title(country, job_title, include_terminated=include_terminated)

    return router
