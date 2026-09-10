import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.seed import ensure_landlord, LANDLORD_EMAIL, LANDLORD_PASSWORD


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
    # Avoid lifespan side-effects on real DB during tests
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
    db.close()


def _login(client, email, password):
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    data = r.json()
    return data["access_token"], data["user"]


def test_cannot_register_as_landlord(client):
    r = client.post(
        "/auth/register",
        json={
            "email": "bad@example.com",
            "password": "password123",
            "full_name": "Bad Actor",
            "role": "landlord",
        },
    )
    assert r.status_code in (400, 422)


def test_pending_user_cannot_access_dashboard(client):
    r = client.post(
        "/auth/register",
        json={
            "email": "tenant1@example.com",
            "password": "password123",
            "full_name": "Pending Tenant",
            "role": "tenant",
        },
    )
    assert r.status_code == 201
    assert r.json()["status"] == "pending"
    token, user = _login(client, "tenant1@example.com", "password123")
    assert user["status"] == "pending"
    dash = client.get(
        "/dashboard/tenant", headers={"Authorization": f"Bearer {token}"}
    )
    assert dash.status_code == 403


def test_landlord_can_approve_then_access(client):
    client.post(
        "/auth/register",
        json={
            "email": "agent1@example.com",
            "password": "password123",
            "full_name": "Agent One",
            "role": "agent",
        },
    )
    ll_token, _ = _login(client, LANDLORD_EMAIL, LANDLORD_PASSWORD)
    pending = client.get(
        "/admin/pending-users", headers={"Authorization": f"Bearer {ll_token}"}
    )
    assert pending.status_code == 200
    users = pending.json()
    assert any(u["email"] == "agent1@example.com" for u in users)
    uid = next(u["id"] for u in users if u["email"] == "agent1@example.com")
    apr = client.post(
        f"/admin/users/{uid}/approve", headers={"Authorization": f"Bearer {ll_token}"}
    )
    assert apr.status_code == 200
    assert apr.json()["status"] == "approved"
    token, user = _login(client, "agent1@example.com", "password123")
    assert user["status"] == "approved"
    dash = client.get(
        "/dashboard/agent", headers={"Authorization": f"Bearer {token}"}
    )
    assert dash.status_code == 200


def test_approved_agent_can_approve_tenant(client):
    client.post(
        "/auth/register",
        json={
            "email": "agent2@example.com",
            "password": "password123",
            "full_name": "Agent Two",
            "role": "agent",
        },
    )
    ll_token, _ = _login(client, LANDLORD_EMAIL, LANDLORD_PASSWORD)
    pending = client.get(
        "/admin/pending-users", headers={"Authorization": f"Bearer {ll_token}"}
    ).json()
    agent_id = next(u["id"] for u in pending if u["email"] == "agent2@example.com")
    client.post(
        f"/admin/users/{agent_id}/approve",
        headers={"Authorization": f"Bearer {ll_token}"},
    )
    agent_token, _ = _login(client, "agent2@example.com", "password123")

    client.post(
        "/auth/register",
        json={
            "email": "tenant2@example.com",
            "password": "password123",
            "full_name": "Tenant Two",
            "role": "tenant",
        },
    )
    pending2 = client.get(
        "/admin/pending-users", headers={"Authorization": f"Bearer {agent_token}"}
    ).json()
    tid = next(u["id"] for u in pending2 if u["email"] == "tenant2@example.com")
    apr = client.post(
        f"/admin/users/{tid}/approve",
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert apr.status_code == 200
    assert apr.json()["status"] == "approved"
