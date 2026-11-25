PY=backend/.venv/bin/python
PYTEST=backend/.venv/bin/pytest

.PHONY: test test-backend test-frontend seed dev-api dev-web

test: test-backend test-frontend

test-backend:
	cd backend && .venv/bin/pytest

test-frontend:
	cd frontend && npm test

seed:
	cd backend && .venv/bin/python -m app.seed --count 10000 --reset

dev-api:
	cd backend && .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

dev-web:
	cd frontend && npm run dev
