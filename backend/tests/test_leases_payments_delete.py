from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.seed import LANDLORD_EMAIL, LANDLORD_PASSWORD, ensure_landlord


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


import pytest


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    ensure_landlord(db)

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
    db.close()


def _login(client, email, password):
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    data = r.json()
    return data["access_token"], data["user"]


def _approve(client, token, email):
    headers = {"Authorization": f"Bearer {token}"}
    pending = client.get("/admin/pending-users", headers=headers).json()
    uid = next(u["id"] for u in pending if u["email"] == email)
    r = client.post(f"/admin/users/{uid}/approve", headers=headers)
    assert r.status_code == 200
    return uid


def test_tenants_options_lists_approved_tenants(client):
    ll_token, _ = _login(client, LANDLORD_EMAIL, LANDLORD_PASSWORD)
    client.post(
        "/auth/register",
        json={
            "email": "tenant-a@example.com",
            "password": "password123",
            "full_name": "Tenant A",
            "role": "tenant",
        },
    )
    client.post(
        "/auth/register",
        json={
            "email": "tenant-b@example.com",
            "password": "password123",
            "full_name": "Tenant B",
            "role": "tenant",
        },
    )
    # pending should not appear
    empty = client.get(
        "/leases/options/tenants", headers={"Authorization": f"Bearer {ll_token}"}
    )
    assert empty.status_code == 200
    assert empty.json() == []

    _approve(client, ll_token, "tenant-a@example.com")
    listed = client.get(
        "/leases/options/tenants", headers={"Authorization": f"Bearer {ll_token}"}
    )
    assert listed.status_code == 200
    emails = [t["email"] for t in listed.json()]
    assert emails == ["tenant-a@example.com"]
    assert listed.json()[0]["full_name"] == "Tenant A"

    # legacy path still works
    legacy = client.get(
        "/leases/meta/tenants", headers={"Authorization": f"Bearer {ll_token}"}
    )
    assert legacy.status_code == 200
    assert len(legacy.json()) == 1


def test_active_leases_for_payment_include_labels(client):
    ll_token, _ = _login(client, LANDLORD_EMAIL, LANDLORD_PASSWORD)
    h = {"Authorization": f"Bearer {ll_token}"}
    client.post(
        "/auth/register",
        json={
            "email": "pay-tenant@example.com",
            "password": "password123",
            "full_name": "Pay Tenant",
            "role": "tenant",
        },
    )
    tid = _approve(client, ll_token, "pay-tenant@example.com")
    prop = client.post(
        "/properties",
        headers=h,
        json={
            "name": "Flat 2",
            "address": "12 Road",
            "property_type": "Two bedroom",
            "default_rent": 80000,
        },
    ).json()
    empty = client.get("/leases/options/active", headers=h)
    assert empty.status_code == 200
    assert empty.json() == []

    lease = client.post(
        "/leases",
        headers=h,
        json={
            "property_id": prop["id"],
            "tenant_id": tid,
            "rent_amount": 80000,
            "due_day": 5,
            "start_date": str(date.today()),
            "status": "active",
        },
    ).json()
    assert lease["tenant_name"] == "Pay Tenant"
    assert lease["property_name"] == "Flat 2"
    assert lease["property_type"] == "Two bedroom"

    active = client.get("/leases/options/active", headers=h).json()
    assert len(active) == 1
    assert active[0]["id"] == lease["id"]
    assert active[0]["tenant_name"] == "Pay Tenant"
    assert active[0]["property_name"] == "Flat 2"


def test_tenant_dashboard_only_own_leases(client):
    ll_token, _ = _login(client, LANDLORD_EMAIL, LANDLORD_PASSWORD)
    h = {"Authorization": f"Bearer {ll_token}"}
    for email, name in [
        ("own@example.com", "Own Tenant"),
        ("other@example.com", "Other Tenant"),
    ]:
        client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "password123",
                "full_name": name,
                "role": "tenant",
            },
        )
    own_id = _approve(client, ll_token, "own@example.com")
    other_id = _approve(client, ll_token, "other@example.com")
    prop = client.post(
        "/properties",
        headers=h,
        json={
            "name": "House",
            "address": "A",
            "property_type": "Self",
            "default_rent": 10,
        },
    ).json()
    client.post(
        "/leases",
        headers=h,
        json={
            "property_id": prop["id"],
            "tenant_id": other_id,
            "rent_amount": 10,
            "due_day": 1,
            "start_date": str(date.today()),
            "status": "active",
        },
    )
    own_token, _ = _login(client, "own@example.com", "password123")
    dash = client.get(
        "/dashboard/tenant", headers={"Authorization": f"Bearer {own_token}"}
    )
    assert dash.status_code == 200
    assert dash.json()["leases"] == []

    client.post(
        "/leases",
        headers=h,
        json={
            "property_id": prop["id"],
            "tenant_id": own_id,
            "rent_amount": 20,
            "due_day": 1,
            "start_date": str(date.today()),
            "status": "active",
        },
    )
    dash2 = client.get(
        "/dashboard/tenant", headers={"Authorization": f"Bearer {own_token}"}
    ).json()
    assert len(dash2["leases"]) == 1
    assert dash2["leases"][0]["tenant_id"] == own_id


def test_delete_tenant_ends_leases_agent_ok(client):
    ll_token, _ = _login(client, LANDLORD_EMAIL, LANDLORD_PASSWORD)
    h = {"Authorization": f"Bearer {ll_token}"}
    client.post(
        "/auth/register",
        json={
            "email": "agent-del@example.com",
            "password": "password123",
            "full_name": "Agent Del",
            "role": "agent",
        },
    )
    client.post(
        "/auth/register",
        json={
            "email": "agent-other@example.com",
            "password": "password123",
            "full_name": "Agent Other",
            "role": "agent",
        },
    )
    client.post(
        "/auth/register",
        json={
            "email": "tenant-del@example.com",
            "password": "password123",
            "full_name": "Tenant Del",
            "role": "tenant",
        },
    )
    _approve(client, ll_token, "agent-del@example.com")
    other_agent_id = _approve(client, ll_token, "agent-other@example.com")
    tid = _approve(client, ll_token, "tenant-del@example.com")
    prop = client.post(
        "/properties",
        headers=h,
        json={
            "name": "X",
            "address": "Y",
            "property_type": "Store",
            "default_rent": 1,
        },
    ).json()
    client.post(
        "/leases",
        headers=h,
        json={
            "property_id": prop["id"],
            "tenant_id": tid,
            "rent_amount": 1,
            "due_day": 1,
            "start_date": str(date.today()),
            "status": "active",
        },
    )
    agent_token, _ = _login(client, "agent-del@example.com", "password123")
    ah = {"Authorization": f"Bearer {agent_token}"}
    # agent cannot delete another agent
    bad = client.delete(f"/admin/users/{other_agent_id}", headers=ah)
    assert bad.status_code == 403

    deleted = client.delete(f"/admin/users/{tid}", headers=ah)
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"

    leases = client.get("/leases", headers=h).json()
    assert leases[0]["status"] == "ended"
    assert client.get("/leases/options/tenants", headers=h).json() == []
    assert client.get("/leases/options/active", headers=h).json() == []


def test_landlord_deletes_agent_not_self(client):
    ll_token, ll_user = _login(client, LANDLORD_EMAIL, LANDLORD_PASSWORD)
    h = {"Authorization": f"Bearer {ll_token}"}
    client.post(
        "/auth/register",
        json={
            "email": "agent-x@example.com",
            "password": "password123",
            "full_name": "Agent X",
            "role": "agent",
        },
    )
    aid = _approve(client, ll_token, "agent-x@example.com")
    self_del = client.delete(f"/admin/users/{ll_user['id']}", headers=h)
    assert self_del.status_code == 400
    landlord_del = client.delete(f"/admin/users/{ll_user['id']}", headers=h)
    assert landlord_del.status_code == 400
    ok = client.delete(f"/admin/users/{aid}", headers=h)
    assert ok.status_code == 200
    assert ok.json()["status"] == "deleted"
