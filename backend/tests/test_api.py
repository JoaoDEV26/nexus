"""Cenários de uso e de abuso. Banco exclusivo de teste é obrigatório."""

import os

os.environ.setdefault("JWT_SECRET", "test-only-secret-with-at-least-thirty-two-characters")
os.environ.setdefault("APP_ORIGIN", "http://localhost:5173")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db import Base, get_db
from app.main import app
from app.models import Task, User

PASSWORD = "Only-for-tests-12345"


@pytest.fixture()
def client():
    url = os.environ.get("TEST_DATABASE_URL", "sqlite://")
    # Impede que o procedimento de limpeza aponte por engano para o banco normal.
    if not url.startswith("sqlite") and "/nexus_test" not in url:
        raise RuntimeError("Use um banco exclusivo chamado nexus_test")
    engine = create_engine(
        url,
        **(
            {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}
            if url.startswith("sqlite")
            else {}
        ),
    )
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def fk(conn, _):
            conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    session = sessionmaker(engine, expire_on_commit=False)

    def override():
        with session() as db:
            try:
                yield db
            except Exception:
                db.rollback()
                raise

    app.dependency_overrides[get_db] = override
    with TestClient(app, headers={"Origin": "http://localhost:5173"}) as c:
        c.db = session
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def account(c, email="owner@example.com"):
    r = c.post(
        "/api/v1/auth/register", json={"name": email.split("@")[0], "email": email, "password": PASSWORD}
    )
    assert r.status_code == 201, r.text
    r = c.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def workspace(c, email="owner@example.com"):
    h = account(c, email)
    r = c.post("/api/v1/organizations", json={"name": "Aurora"}, headers=h)
    assert r.status_code == 201, r.text
    base = "/api/v1/organizations/" + r.json()["id"]
    r = c.post(base + "/projects", json={"name": "Portal"}, headers=h)
    assert r.status_code == 201, r.text
    return h, base, r.json()["id"]


def task(c, h, base, project, **extra):
    r = c.post(base + "/tasks", json={"title": "Entregar página", "project_id": project, **extra}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


def test_health_and_password_hash(client):
    h = account(client)
    assert client.get("/health/ready").status_code == 200
    assert client.get("/api/v1/users/me", headers=h).status_code == 200
    with client.db() as db:
        user = db.scalar(select(User))
        assert user.password_hash.startswith("$argon2")
        assert PASSWORD not in user.password_hash


def test_wrong_password_duplicate_and_validation(client):
    account(client)
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": "owner@example.com", "password": "incorrect-password"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/register", json={"name": "Same", "email": "owner@example.com", "password": PASSWORD}
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/v1/auth/register", json={"name": "", "email": "wrong", "password": "short"}
        ).status_code
        == 422
    )


def test_origin_and_anonymous_access(client):
    assert client.post("/api/v1/auth/refresh", headers={"Origin": "https://evil.example"}).status_code == 403
    assert client.get("/api/v1/organizations").status_code == 401


def test_refresh_rotation_replay_and_logout(client):
    h = account(client)
    old = client.cookies.get("nexus_refresh")
    r = client.post("/api/v1/auth/refresh")
    assert r.status_code == 200
    fresh = {"Authorization": "Bearer " + r.json()["access_token"]}
    assert client.get("/api/v1/users/me", headers=h).status_code == 401
    assert client.get("/api/v1/users/me", headers=fresh).status_code == 200
    client.cookies.clear()
    client.cookies.set("nexus_refresh", old, path="/api/v1/auth")
    assert client.post("/api/v1/auth/refresh").status_code == 401
    assert client.get("/api/v1/users/me", headers=fresh).status_code == 401
    h = client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": PASSWORD}).json()
    assert client.post("/api/v1/auth/logout").status_code == 204
    assert (
        client.get("/api/v1/users/me", headers={"Authorization": "Bearer " + h["access_token"]}).status_code
        == 401
    )


def test_full_workflow_and_project_rule(client):
    h, b, p = workspace(client)
    t = task(client, h, b, p, due_date="2020-01-01")
    assert client.get(b + "/dashboard", headers=h).json()["overdue_tasks"] == 1
    assert client.patch(b + "/projects/" + p, json={"status": "COMPLETED"}, headers=h).status_code == 409
    assert (
        client.post(
            b + "/tasks/" + t["id"] + "/comments", json={"body": "Primeira entrega"}, headers=h
        ).status_code
        == 201
    )
    r = client.patch(b + "/tasks/" + t["id"] + "/status", json={"status": "DONE"}, headers=h)
    assert r.status_code == 200 and r.json()["completed_at"]
    assert client.get(b + "/dashboard", headers=h).json()["completed_tasks"] == 1
    assert client.patch(b + "/projects/" + p, json={"status": "COMPLETED"}, headers=h).status_code == 200
    assert (
        client.patch(b + "/tasks/" + t["id"] + "/status", json={"status": "TODO"}, headers=h).status_code
        == 409
    )
    assert client.patch(b + "/projects/" + p, json={"status": "ACTIVE"}, headers=h).status_code == 200
    r = client.patch(b + "/tasks/" + t["id"] + "/status", json={"status": "TODO"}, headers=h)
    assert r.json()["completed_at"] is None
    assert client.get(b + "/dashboard", headers=h).json()["completed_tasks"] == 0
    assert client.get(b + "/activity", headers=h).json()["total"] >= 6


def test_tenant_isolation_all_surfaces(client):
    ha, ba, pa = workspace(client)
    ta = task(client, ha, ba, pa)
    hb, bb, pb = workspace(client, "other@example.com")
    for path in [
        "/tasks",
        "/projects",
        "/members",
        "/dashboard",
        "/activity",
        "/tasks/" + ta["id"],
        "/tasks/" + ta["id"] + "/comments",
    ]:
        assert client.get(ba + path, headers=hb).status_code == 404, path
    assert client.patch(ba + "/tasks/" + ta["id"], json={"title": "Intrusão"}, headers=hb).status_code == 404
    assert (
        client.post(
            ba + "/tasks/" + ta["id"] + "/comments", json={"body": "Intrusão"}, headers=hb
        ).status_code
        == 404
    )
    assert (
        client.post(bb + "/tasks", json={"title": "Mistura", "project_id": pa}, headers=hb).status_code == 404
    )
    assert client.get(bb + "/tasks", headers=hb).json()["total"] == 0
    assert client.get(bb + "/dashboard", headers=hb).json()["pending_tasks"] == 0


def test_member_permissions_and_field_injection(client):
    h, b, p = workspace(client)
    hm = account(client, "member@example.com")
    m = client.post(b + "/members", json={"email": "member@example.com"}, headers=h).json()["id"]
    mine = task(client, h, b, p, assignee_id=m)
    other = task(client, h, b, p)
    assert (
        client.patch(
            b + "/tasks/" + mine["id"] + "/status", json={"status": "IN_PROGRESS"}, headers=hm
        ).status_code
        == 200
    )
    assert (
        client.patch(b + "/tasks/" + other["id"] + "/status", json={"status": "DONE"}, headers=hm).status_code
        == 403
    )
    assert (
        client.patch(
            b + "/tasks/" + mine["id"] + "/status", json={"status": "DONE", "priority": "HIGH"}, headers=hm
        ).status_code
        == 422
    )
    assert (
        client.patch(b + "/tasks/" + mine["id"], json={"title": "Alteração"}, headers=hm).status_code == 403
    )
    assert client.post(b + "/projects", json={"name": "Inválido"}, headers=hm).status_code == 403
    assert (
        client.post(
            b + "/tasks/" + other["id"] + "/comments", json={"body": "Posso comentar"}, headers=hm
        ).status_code
        == 201
    )


def test_protected_owner_and_admin(client):
    h, b, p = workspace(client)
    ha = account(client, "admin@example.com")
    aid = client.post(b + "/members", json={"email": "admin@example.com", "role": "ADMIN"}, headers=h).json()[
        "id"
    ]
    owner = next(x for x in client.get(b + "/members", headers=h).json() if x["role"] == "OWNER")["id"]
    assert client.delete(b + "/members/" + owner, headers=h).status_code == 403
    assert client.patch(b + "/members/" + owner, json={"role": "MEMBER"}, headers=ha).status_code == 403
    assert client.patch(b + "/members/" + aid, json={"role": "MEMBER"}, headers=ha).status_code == 403
    account(client, "third@example.com")
    assert (
        client.post(
            b + "/members", json={"email": "third@example.com", "role": "ADMIN"}, headers=ha
        ).status_code
        == 403
    )


def test_removed_member_loses_access_and_assignments(client):
    h, b, p = workspace(client)
    hm = account(client, "member@example.com")
    m = client.post(b + "/members", json={"email": "member@example.com"}, headers=h).json()["id"]
    t = task(client, h, b, p, assignee_id=m)
    assert client.delete(b + "/members/" + m, headers=h).status_code == 204
    assert client.get(b + "/tasks", headers=hm).status_code == 404
    assert client.get(b + "/tasks/" + t["id"], headers=h).json()["assignee_id"] is None
    assert (
        client.post(
            b + "/tasks", json={"title": "Inválido", "project_id": p, "assignee_id": m}, headers=h
        ).status_code
        == 409
    )


def test_pagination_filters_and_archive(client):
    h, b, p = workspace(client)
    t = task(client, h, b, p, priority="HIGH")
    task(client, h, b, p, title="Outra tarefa")
    r = client.get(b + "/tasks?page_size=1", headers=h).json()
    assert r["total"] == 2 and len(r["items"]) == 1
    assert client.get(b + "/tasks?priority=HIGH&q=Entregar", headers=h).json()["total"] == 1
    assert client.get(b + "/tasks?page_size=1000", headers=h).status_code == 422
    assert client.patch(b + "/tasks/" + t["id"], json={"archived": True}, headers=h).status_code == 200
    assert client.get(b + "/tasks", headers=h).json()["total"] == 1
    assert client.get(b + "/tasks?archived=true", headers=h).json()["total"] == 1
    assert (
        client.patch(b + "/tasks/" + t["id"] + "/status", json={"status": "DONE"}, headers=h).status_code
        == 409
    )


def test_foreign_key_rejects_cross_tenant_even_without_api(client):
    h, b, p = workspace(client)
    h2, b2, p2 = workspace(client, "second@example.com")
    with client.db() as db:
        db.add(Task(organization_id=b.split("/")[-1], project_id=p2, title="Cross tenant"))
        with pytest.raises(IntegrityError):
            db.commit()


def test_audit_failure_rolls_back_task(client, monkeypatch):
    import app.main as routes

    h, b, p = workspace(client)

    def broken(*args, **kwargs):
        raise RuntimeError("Falha simulada de auditoria")

    monkeypatch.setattr(routes, "event", broken)
    with pytest.raises(RuntimeError):
        client.post(b + "/tasks", json={"title": "Não pode persistir", "project_id": p}, headers=h)
    assert client.get(b + "/tasks", headers=h).json()["total"] == 0


def test_dashboard_invalid_dates_and_null_fields(client):
    h, b, p = workspace(client)
    t = task(client, h, b, p)
    assert client.get(b + "/dashboard?start=2026-10-02&end=2026-10-01", headers=h).status_code == 422
    assert client.patch(b + "/tasks/" + t["id"], json={"title": None}, headers=h).status_code == 422
    assert client.patch(b + "/tasks/" + t["id"], json={"due_date": None}, headers=h).status_code == 200


def test_version_endpoint(client):
    response = client.get("api/v1/version")
    assert response.status_code == 200
    assert response.json() == {
        "name": "Nexus",
        "version": "0.1.0",
    }