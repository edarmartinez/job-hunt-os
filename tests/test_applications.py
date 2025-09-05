import os
import time
from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base

os.environ.setdefault("API_KEY", "test-secret")
client = TestClient(app)

def auth_headers():
    return {"X-API-Key": os.environ["API_KEY"]}

def test_create_and_list():
    # ensure tables exist
    Base.metadata.create_all(bind=engine)

    payload = {
        "company": "Acme",
        "role": "Backend Developer",
        "location": "NYC, NY",
        "source": "LinkedIn",
        "link": "https://example.com/job/1",
        "salary_min": 100000,
        "salary_max": 130000,
        "employment_type": "full-time",
        "stage": "applied",
        "status": "active",
        "notes": "First app"
    }
    r = client.post("/applications", json=payload, headers=auth_headers())
    assert r.status_code == 200, r.text
    created = r.json()
    assert created["id"] >= 1
    assert created["company"] == "Acme"
    assert created["created_at"] and created["updated_at"]

    # list
    r2 = client.get("/applications")
    data = r2.json()
    assert "items" in data and "total" in data
    assert data["total"] >= 1

def test_filters_and_pagination():
    # add second record
    payload2 = {
        "company": "Beta Inc",
        "role": "Data Engineer",
        "stage": "wishlist",
        "status": "active"
    }
    client.post("/applications", json=payload2, headers=auth_headers())

    # search
    r = client.get("/applications?search=beta")
    assert r.status_code == 200
    data = r.json()
    assert any("Beta" in item["company"] for item in data["items"])

    # pagination
    r = client.get("/applications?page=2&page_size=1")
    assert r.status_code == 200
    data = r.json()
    assert data["page"] == 2
    assert data["page_size"] == 1

def test_get_update_delete():
    # create
    r = client.post("/applications", json={"company": "Gamma", "role": "Dev"}, headers=auth_headers())
    app_id = r.json()["id"]

    # get
    g = client.get(f"/applications/{app_id}")
    assert g.status_code == 200
    assert g.json()["company"] == "Gamma"

    # update and check updated_at changes
    before = g.json()["updated_at"]
    u = client.put(f"/applications/{app_id}", json={"stage": "applied"}, headers=auth_headers())
    assert u.status_code == 200
    after = u.json()["updated_at"]
    assert after != before

    # delete
    d = client.delete(f"/applications/{app_id}", headers=auth_headers())
    assert d.status_code == 204
    not_found = client.get(f"/applications/{app_id}")
    assert not_found.status_code == 404

def test_auth_required():
    r = client.post("/applications", json={"company": "NoAuth", "role": "Dev"})
    assert r.status_code == 401

def test_salary_bounds_and_enums():
    bad = {
        "company": "BadCo",
        "role": "Dev",
        "salary_min": 200,
        "salary_max": 100  # invalid
    }
    r = client.post("/applications", json=bad, headers=auth_headers())
    assert r.status_code == 400
    # bad enum
    bad2 = {
        "company": "BadCo",
        "role": "Dev",
        "employment_type": "gig"
    }
    r2 = client.post("/applications", json=bad2, headers=auth_headers())
    assert r2.status_code == 400

def test_export_csv():
    r = client.get("/export.csv?status=active")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    text = r.text.splitlines()
    assert len(text) >= 2  # header + at least one row
    assert "company" in text[0]
