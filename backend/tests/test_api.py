from tests.conftest import employee_payload


def test_health_reference_and_root(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/").json()["service"] == "Northstar"
    reference = client.get("/api/reference").json()
    currencies = {item["name"]: item["currency"] for item in reference["countries"]}
    assert currencies["India"] == "INR"
    assert "Software Engineer" in reference["job_titles"]
    assert reference["statuses"][0]["value"] == "active"


def test_employee_crud_contract(client):
    created = client.post("/api/employees", json=employee_payload())
    assert created.status_code == 201
    body = created.json()
    assert body["employee_code"] == "EMP-00001"
    assert body["salary"] == "1840000.50"
    assert body["currency"] == "INR"
    employee_id = body["id"]

    fetched = client.get(f"/api/employees/{employee_id}")
    assert fetched.status_code == 200
    assert fetched.json()["full_name"] == "Priya Sharma"

    updated = client.patch(f"/api/employees/{employee_id}", json={"salary": "1900000", "status": "on leave"})
    assert updated.status_code == 200
    assert updated.json()["salary"] == "1900000.00"
    assert updated.json()["status"] == "on_leave"

    listed = client.get("/api/employees", params={"q": "priya", "country": "india"})
    assert listed.status_code == 200
    payload = listed.json()
    assert payload["total"] == 1
    assert payload["pages"] == 1
    assert payload["items"][0]["employee_code"] == "EMP-00001"

    removed = client.delete(f"/api/employees/{employee_id}")
    assert removed.status_code == 204
    assert removed.content == b""
    missing = client.get(f"/api/employees/{employee_id}")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"


def test_validation_errors_use_a_stable_shape(client):
    payload = employee_payload(salary="10.999")
    response = client.post("/api/employees", json=payload)
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "invalid_salary"
    assert "salary" in error["fields"]

    incomplete = employee_payload()
    del incomplete["full_name"]
    missing = client.post("/api/employees", json=incomplete)
    assert missing.status_code == 422
    assert missing.json()["error"]["code"] == "validation_error"

    extra = employee_payload(nickname="P")
    assert client.post("/api/employees", json=extra).status_code == 422

    conflict = client.post("/api/employees", json=employee_payload())
    assert conflict.status_code == 201
    again = client.post("/api/employees", json=employee_payload(full_name="Priya Shah"))
    assert again.status_code == 409
    assert again.json()["error"]["fields"]["email"]


def test_insights_endpoints(client):
    client.post("/api/employees", json=employee_payload(salary="100.00"))
    client.post(
        "/api/employees",
        json=employee_payload(salary="300.00", email="b@northstar.example", full_name="Ananya Iyer"),
    )
    client.post(
        "/api/employees",
        json=employee_payload(
            salary="9999.00",
            email="c@northstar.example",
            full_name="Former Employee",
            status="terminated",
        ),
    )

    overview = client.get("/api/insights/overview")
    assert overview.status_code == 200
    assert overview.json()["compensation_headcount"] == 2
    assert overview.json()["countries"][0]["average"] == "200.00"

    country = client.get("/api/insights/country", params={"country": "india"})
    assert country.status_code == 200
    body = country.json()
    assert body["minimum"] == "100.00"
    assert body["maximum"] == "300.00"
    assert body["average"] == "200.00"
    assert body["currency"] == "INR"
    assert body["headcount"] == 2

    title = client.get(
        "/api/insights/job-title",
        params={"country": "India", "job_title": "software engineer"},
    )
    assert title.status_code == 200
    assert title.json()["average"] == "200.00"
    assert title.json()["job_title"] == "Software Engineer"

    unknown = client.get("/api/insights/country", params={"country": "Narnia"})
    assert unknown.status_code == 422
    assert unknown.json()["error"]["code"] == "invalid_country"

    empty = client.get("/api/insights/country", params={"country": "Japan"})
    assert empty.status_code == 200
    assert empty.json()["headcount"] == 0
    assert empty.json()["average"] is None
