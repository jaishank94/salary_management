# Northstar design

Northstar is a salary directory for an HR manager responsible for about 10,000 employees. The job to be done is narrow: keep the people record accurate, and answer two compensation questions without mixing currencies.

1. What are the minimum, maximum, and average salaries in a country?
2. What is the average salary for a job title in that country?

## Shape

```text
React (Vite)  -- /api -->  FastAPI  -->  SQLAlchemy  -->  SQLite
                                ^
                                |
                         seed script (bulk insert)
                         data/first_names.txt + data/last_names.txt
```

The UI is a same-origin client. In development Vite proxies `/api`. In Docker, nginx does the same. The browser never talks to a second origin.

## Domain

An employee has a full name, email, job title, department, country, city, annual salary, currency, employment type, status, and hire date. The server assigns `EMP-00001` style codes.

Currency is not a free choice. Each supported country has one currency, and salary insights are always computed inside a single country and currency. A record whose currency does not match its country is counted and excluded from the average rather than blended in.

Compensation figures include active employees and people on leave. Terminated employees stay in the directory and in the status counts, and they are left out of pay statistics unless the HR manager asks for them.

Money is `Decimal` with two places and half-up rounding. The median of an even count is the average of the two middle salaries. The 25th and 75th percentiles use the nearest-rank method.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/employees` | Search, filter, sort, paginate |
| POST | `/api/employees` | Create |
| GET | `/api/employees/{id}` | Read |
| PATCH | `/api/employees/{id}` | Partial update |
| DELETE | `/api/employees/{id}` | Hard delete |
| GET | `/api/insights/overview` | Workforce and per-country rollups |
| GET | `/api/insights/country?country=` | Min, max, average, median, bands, breakdowns |
| GET | `/api/insights/job-title?country=&job_title=` | Average for one title in one country |
| GET | `/api/reference` | Countries, titles, departments, labels |

Errors share one body: `{ "error": { "code", "message", "fields" } }`. Unknown employees are 404. Duplicate emails are 409. Validation is 422.

## Tests

Behavior is specified in pytest before it is trusted:

- `test_validation.py` and `test_salary_stats.py` cover pure rules (names, money, dates, rounding, percentiles).
- `test_employees.py` covers persistence, search escaping, pagination, and currency changes.
- `test_insights.py` covers country isolation, terminated employees, and mixed currencies.
- `test_api.py` covers the HTTP contract.
- `test_seed.py` covers name files, determinism, and a 10,000 row bulk insert.

The Vitest suite covers the same money formatting and form rules the HR manager sees.

## Interface

Two screens: Insights and People. Insights leads with minimum, maximum, average, and median for the selected country, then a title control for the average of one job. People is a searchable directory with create, edit, and delete. The layout collapses to a single column, and tables become cards, below 860px.
