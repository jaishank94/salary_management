# Northstar

Salary directory and compensation insights for an HR manager, built for a workforce of about 10,000 people.

An employee has a name, job title, country, and salary, plus email, department, city, employment type, status, and hire date. Insights show the minimum, maximum, and average salary in a country, and the average for a job title in that country. Averages are never mixed across currencies.

## Run it

Python 3.13 and Node 20 or newer.

```bash
python3.13 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/python -m app.seed --count 10000 --reset
backend/.venv/bin/uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173. The API docs are at http://127.0.0.1:8000/docs.

Docker runs both and seeds an empty database on startup:

```bash
docker compose up --build
```

The app is then at http://127.0.0.1:8080.

## Tests

```bash
make test-backend
make test-frontend
```

Backend tests cover validation, directory rules, salary insights, the HTTP API, and the 10,000-row seed. Frontend tests cover money formatting and the employee form.

## Design notes

- [Design](docs/DESIGN.md)
- [Tradeoffs](docs/TRADEOFFS.md)
- [AI usage](docs/AI_USAGE.md)

This copy has no authentication. Do not load real employee data into it.
