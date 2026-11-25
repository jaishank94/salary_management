"""Controlled vocabulary for countries, roles, and employment.

Salaries are recorded in the currency of the employee's country. Country
insights therefore never average incompatible currencies. ``fx_per_usd`` and
``pay_index`` are seed-only knobs used to invent plausible local pay; they are
not treated as live foreign-exchange rates.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Country:
    name: str
    currency: str
    fx_per_usd: Decimal
    pay_index: Decimal
    cities: tuple[str, ...]


COUNTRIES: tuple[Country, ...] = (
    Country("United States", "USD", Decimal("1"), Decimal("1"), ("New York", "Austin", "Seattle", "Chicago")),
    Country("United Kingdom", "GBP", Decimal("0.78"), Decimal("0.85"), ("London", "Manchester", "Edinburgh")),
    Country("Germany", "EUR", Decimal("0.92"), Decimal("0.90"), ("Berlin", "Munich", "Hamburg")),
    Country("India", "INR", Decimal("84"), Decimal("0.22"), ("Bengaluru", "Hyderabad", "Mumbai", "Pune")),
    Country("Canada", "CAD", Decimal("1.36"), Decimal("0.90"), ("Toronto", "Vancouver", "Montreal")),
    Country("Australia", "AUD", Decimal("1.52"), Decimal("0.95"), ("Sydney", "Melbourne", "Brisbane")),
    Country("Singapore", "SGD", Decimal("1.34"), Decimal("0.95"), ("Singapore",)),
    Country("Brazil", "BRL", Decimal("5.40"), Decimal("0.32"), ("São Paulo", "Rio de Janeiro")),
    Country("Japan", "JPY", Decimal("149"), Decimal("0.72"), ("Tokyo", "Osaka")),
    Country("Netherlands", "EUR", Decimal("0.92"), Decimal("0.92"), ("Amsterdam", "Rotterdam")),
    Country("Ireland", "EUR", Decimal("0.92"), Decimal("0.95"), ("Dublin", "Cork")),
    Country("United Arab Emirates", "AED", Decimal("3.67"), Decimal("0.80"), ("Dubai", "Abu Dhabi")),
    Country("Mexico", "MXN", Decimal("17.20"), Decimal("0.30"), ("Mexico City", "Guadalajara")),
    Country("France", "EUR", Decimal("0.92"), Decimal("0.85"), ("Paris", "Lyon")),
    Country("South Africa", "ZAR", Decimal("18.20"), Decimal("0.28"), ("Johannesburg", "Cape Town")),
)

COUNTRY_BY_KEY: dict[str, Country] = {
    " ".join(country.name.split()).casefold(): country for country in COUNTRIES
}

JOB_TITLES: tuple[str, ...] = (
    "Software Engineer",
    "Senior Software Engineer",
    "Engineering Manager",
    "Product Manager",
    "Product Designer",
    "Data Analyst",
    "Data Scientist",
    "HR Business Partner",
    "Recruiter",
    "Finance Analyst",
    "Accountant",
    "Sales Representative",
    "Account Executive",
    "Customer Success Manager",
    "Marketing Manager",
    "Operations Manager",
    "People Operations Specialist",
    "Legal Counsel",
    "QA Engineer",
    "DevOps Engineer",
)

TITLE_DEPARTMENT: dict[str, str] = {
    "Software Engineer": "Engineering",
    "Senior Software Engineer": "Engineering",
    "Engineering Manager": "Engineering",
    "QA Engineer": "Engineering",
    "DevOps Engineer": "Engineering",
    "Product Manager": "Product",
    "Product Designer": "Design",
    "Data Analyst": "Data",
    "Data Scientist": "Data",
    "HR Business Partner": "People",
    "Recruiter": "People",
    "People Operations Specialist": "People",
    "Finance Analyst": "Finance",
    "Accountant": "Finance",
    "Sales Representative": "Sales",
    "Account Executive": "Sales",
    "Customer Success Manager": "Customer Success",
    "Marketing Manager": "Marketing",
    "Operations Manager": "Operations",
    "Legal Counsel": "Legal",
}

# Annual USD bands before the country pay index and FX conversion.
TITLE_USD_BANDS: dict[str, tuple[int, int]] = {
    "Software Engineer": (115_000, 165_000),
    "Senior Software Engineer": (155_000, 210_000),
    "Engineering Manager": (175_000, 245_000),
    "Product Manager": (125_000, 185_000),
    "Product Designer": (110_000, 165_000),
    "Data Analyst": (80_000, 120_000),
    "Data Scientist": (130_000, 185_000),
    "HR Business Partner": (90_000, 140_000),
    "Recruiter": (70_000, 110_000),
    "Finance Analyst": (80_000, 120_000),
    "Accountant": (68_000, 100_000),
    "Sales Representative": (60_000, 95_000),
    "Account Executive": (85_000, 140_000),
    "Customer Success Manager": (72_000, 115_000),
    "Marketing Manager": (95_000, 145_000),
    "Operations Manager": (90_000, 140_000),
    "People Operations Specialist": (65_000, 100_000),
    "Legal Counsel": (140_000, 210_000),
    "QA Engineer": (90_000, 135_000),
    "DevOps Engineer": (125_000, 180_000),
}

DEPARTMENTS: tuple[str, ...] = (
    "Engineering",
    "Product",
    "Design",
    "Data",
    "People",
    "Finance",
    "Sales",
    "Customer Success",
    "Marketing",
    "Operations",
    "Legal",
)

EMPLOYMENT_TYPES: tuple[str, ...] = ("full_time", "part_time", "contract")
STATUSES: tuple[str, ...] = ("active", "on_leave", "terminated")

EMPLOYMENT_LABELS: dict[str, str] = {
    "full_time": "Full-time",
    "part_time": "Part-time",
    "contract": "Contract",
}
STATUS_LABELS: dict[str, str] = {
    "active": "Active",
    "on_leave": "On leave",
    "terminated": "Terminated",
}

COMPENSATION_STATUSES: tuple[str, ...] = ("active", "on_leave")
