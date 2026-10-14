"""API Nexus. Execute com uvicorn app.main:app."""

from datetime import date, datetime, time, timedelta, timezone
import logging
import os
import time as clock
from uuid import uuid4
from zoneinfo import ZoneInfo
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import func, select, text, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from .db import get_db
from .models import Activity, Comment, Membership, Organization, Project, RefreshSession, Task, User, now
from . import schemas as s
from .security import DUMMY_HASH, check_origin, current_user, issue, passwords, refresh_session
from .services import active_project, assignee, changes, event, member, page, permit, scoped

app = FastAPI(title="Nexus API", version="0.1.0", docs_url="/api/docs", openapi_url="/api/openapi.json")
log = logging.getLogger("uvicorn.error")
DB = Depends(get_db)
AUTH = Depends(current_user)
PREFIX = "/api/v1"
ORG = PREFIX + "/organizations/{org_id}"


@app.middleware("http")
async def request_log(request, call_next):
    request_id = str(uuid4())
    started = clock.monotonic()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["Cache-Control"] = "no-store"
    log.info(
        "request=%s method=%s status=%s ms=%.1f",
        request_id,
        request.method,
        response.status_code,
        (clock.monotonic() - started) * 1000,
    )
    return response


@app.exception_handler(IntegrityError)
async def conflict(_, exc):
    return JSONResponse(status_code=409, content={"detail": "Conflito de dados ou relação inválida"})


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.get("/health/ready")
def ready(db: Session = DB):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(503, "Banco indisponível") from None
    return {"status": "ok"}


@app.post(PREFIX + "/auth/register", status_code=201, dependencies=[Depends(check_origin)])
def register(data: s.Register, db: Session = DB):
    if os.environ.get("ALLOW_REGISTRATION", "true").lower() != "true":
        raise HTTPException(403, "Cadastro público desativado")
    user = User(name=data.name, email=str(data.email).lower(), password_hash=passwords.hash(data.password))
    db.add(user)
    db.commit()
    return {"id": user.id, "name": user.name, "email": user.email}


@app.post(PREFIX + "/auth/login", dependencies=[Depends(check_origin)])
def login(data: s.Login, response: Response, db: Session = DB):
    user = db.scalar(select(User).where(User.email == str(data.email).lower()))
    valid = passwords.verify(data.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid:
        raise HTTPException(401, "E-mail ou senha inválidos")
    result = issue(db, user.id, response)
    db.commit()
    return result


@app.post(PREFIX + "/auth/refresh", dependencies=[Depends(check_origin)])
def refresh(request: Request, response: Response, db: Session = DB):
    row = refresh_session(db, request)
    if not row:
        raise HTTPException(401, "Sessão inválida")
    if row.revoked:
        db.execute(
            update(RefreshSession).where(RefreshSession.family_id == row.family_id).values(revoked=True)
        )
        db.commit()
        raise HTTPException(401, "Sessão revogada")
    if row.expires_at <= clock.time():
        raise HTTPException(401, "Sessão expirada")
    row.revoked = True
    result = issue(db, row.user_id, response, row.family_id)
    db.commit()
    return result


@app.post(PREFIX + "/auth/logout", status_code=204, dependencies=[Depends(check_origin)])
def logout(request: Request, response: Response, db: Session = DB):
    row = refresh_session(db, request)
    if row:
        db.execute(
            update(RefreshSession).where(RefreshSession.family_id == row.family_id).values(revoked=True)
        )
        db.commit()
    response.delete_cookie("nexus_refresh", path="/api/v1/auth")


@app.get(PREFIX + "/users/me")
def me(user: User = AUTH):
    return {"id": user.id, "name": user.name, "email": user.email}


@app.get(PREFIX + "/organizations")
def organizations(db: Session = DB, user: User = AUTH):
    rows = db.execute(
        select(Organization, Membership.role, Membership.id)
        .join(Membership, Membership.organization_id == Organization.id)
        .where(Membership.user_id == user.id, Membership.active.is_(True))
        .order_by(Organization.name)
    ).all()
    return [{"id": o.id, "name": o.name, "role": role, "membership_id": mid} for o, role, mid in rows]


@app.post(PREFIX + "/organizations", status_code=201)
def create_organization(data: s.Name, db: Session = DB, user: User = AUTH):
    org = Organization(name=data.name)
    db.add(org)
    db.flush()
    owner = Membership(organization_id=org.id, user_id=user.id, role="OWNER")
    db.add(owner)
    db.flush()
    event(db, owner, org.id, "organization.created")
    db.commit()
    return org


@app.patch(ORG)
def edit_organization(org_id: str, data: s.Name, db: Session = DB, user: User = AUTH):
    actor = member(db, org_id, user)
    permit(actor, ("OWNER", "ADMIN"))
    org = db.get(Organization, org_id)
    event(db, actor, org.id, "organization.updated", changes(org, data))
    db.commit()
    return org


@app.get(ORG + "/members")
def members(org_id: str, db: Session = DB, user: User = AUTH):
    member(db, org_id, user)
    rows = db.execute(
        select(Membership, User)
        .join(User, Membership.user_id == User.id)
        .where(Membership.organization_id == org_id, Membership.active.is_(True))
        .order_by(User.name)
    ).all()
    return [{"id": m.id, "name": u.name, "email": u.email, "role": m.role} for m, u in rows]


@app.post(ORG + "/members", status_code=201)
def add_member(org_id: str, data: s.AddMember, db: Session = DB, user: User = AUTH):
    actor = member(db, org_id, user)
    permit(actor, ("OWNER", "ADMIN"))
    if data.role == "ADMIN" and actor.role != "OWNER":
        raise HTTPException(403, "Somente Owner pode atribuir Admin")
    target = db.scalar(select(User).where(User.email == str(data.email).lower()))
    if not target:
        raise HTTPException(404, "Conta não encontrada; cadastre-a primeiro")
    row = db.scalar(
        select(Membership)
        .where(Membership.organization_id == org_id, Membership.user_id == target.id)
        .with_for_update()
    )
    if row and row.active:
        raise HTTPException(409, "Usuário já participa da organização")
    if row:
        row.active = True
        row.role = data.role
    else:
        row = Membership(organization_id=org_id, user_id=target.id, role=data.role)
        db.add(row)
    db.flush()
    event(db, actor, row.id, "member.added", {"role": data.role})
    db.commit()
    return {"id": row.id, "role": row.role}


def manageable(actor, target):
    permit(actor, ("OWNER", "ADMIN"))
    if target.role == "OWNER" or (actor.role == "ADMIN" and target.role == "ADMIN"):
        raise HTTPException(403, "Este vínculo está protegido")


@app.patch(ORG + "/members/{mid}")
def edit_member(org_id: str, mid: str, data: s.ChangeRole, db: Session = DB, user: User = AUTH):
    actor = member(db, org_id, user)
    target = scoped(db, Membership, org_id, mid)
    manageable(actor, target)
    if not target.active:
        raise HTTPException(404, "Vínculo inativo")
    if data.role == "ADMIN" and actor.role != "OWNER":
        raise HTTPException(403, "Somente Owner pode atribuir Admin")
    event(db, actor, mid, "member.updated", changes(target, data))
    db.commit()
    return {"id": target.id, "role": target.role}


@app.delete(ORG + "/members/{mid}", status_code=204)
def remove_member(org_id: str, mid: str, db: Session = DB, user: User = AUTH):
    actor = member(db, org_id, user)
    target = scoped(db, Membership, org_id, mid)
    manageable(actor, target)
    target.active = False
    tasks = db.scalars(
        select(Task)
        .where(Task.organization_id == org_id, Task.assignee_id == mid, Task.status != "DONE")
        .with_for_update()
    ).all()
    for task in tasks:
        task.assignee_id = None
        event(db, actor, task.id, "task.unassigned", {"previous_assignee": mid})
    event(db, actor, mid, "member.removed")
    db.commit()


@app.get(ORG + "/projects")
def projects(
    org_id: str,
    page_number: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = DB,
    user: User = AUTH,
):
    member(db, org_id, user)
    return page(
        db,
        select(Project).where(Project.organization_id == org_id).order_by(Project.name, Project.id),
        page_number,
        page_size,
    )


@app.post(ORG + "/projects", status_code=201)
def create_project(org_id: str, data: s.ProjectCreate, db: Session = DB, user: User = AUTH):
    actor = member(db, org_id, user)
    permit(actor)
    row = Project(organization_id=org_id, **data.model_dump())
    db.add(row)
    db.flush()
    event(db, actor, row.id, "project.created")
    db.commit()
    return row


@app.patch(ORG + "/projects/{pid}")
def edit_project(org_id: str, pid: str, data: s.ProjectPatch, db: Session = DB, user: User = AUTH):
    actor = member(db, org_id, user)
    permit(actor)
    row = scoped(db, Project, org_id, pid)
    if data.status == "COMPLETED":
        pending = db.scalar(
            select(func.count())
            .select_from(Task)
            .where(
                Task.organization_id == org_id,
                Task.project_id == pid,
                Task.archived.is_(False),
                Task.status != "DONE",
            )
        )
        if pending:
            raise HTTPException(409, "Conclua ou arquive as tarefas pendentes")
    event(db, actor, pid, "project.updated", changes(row, data))
    db.commit()
    return row


@app.get(ORG + "/tasks")
def tasks(
    org_id: str,
    status: s.Status | None = None,
    priority: s.Priority | None = None,
    project_id: str | None = None,
    assignee_id: str | None = None,
    q: str = Query("", max_length=120),
    archived: bool = False,
    page_number: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = DB,
    user: User = AUTH,
):
    member(db, org_id, user)
    stmt = select(Task).where(Task.organization_id == org_id, Task.archived == archived)
    for field, value in [
        (Task.status, status),
        (Task.priority, priority),
        (Task.project_id, project_id),
        (Task.assignee_id, assignee_id),
    ]:
        if value is not None:
            stmt = stmt.where(field == value)
    if q:
        stmt = stmt.where(Task.title.icontains(q, autoescape=True))
    return page(db, stmt.order_by(Task.created_at.desc(), Task.id), page_number, page_size)


@app.post(ORG + "/tasks", status_code=201)
def create_task(org_id: str, data: s.TaskCreate, db: Session = DB, user: User = AUTH):
    actor = member(db, org_id, user)
    permit(actor)
    assignee(db, org_id, data.assignee_id)
    active_project(scoped(db, Project, org_id, data.project_id))
    row = Task(organization_id=org_id, **data.model_dump())
    db.add(row)
    db.flush()
    event(db, actor, row.id, "task.created")
    db.commit()
    return row


@app.get(ORG + "/tasks/{tid}")
def get_task(org_id: str, tid: str, db: Session = DB, user: User = AUTH):
    member(db, org_id, user)
    return scoped(db, Task, org_id, tid)


@app.patch(ORG + "/tasks/{tid}")
def edit_task(org_id: str, tid: str, data: s.TaskPatch, db: Session = DB, user: User = AUTH):
    actor = member(db, org_id, user)
    permit(actor)
    if "assignee_id" in data.model_fields_set:
        assignee(db, org_id, data.assignee_id)
    row = scoped(db, Task, org_id, tid)
    active_project(scoped(db, Project, org_id, row.project_id))
    event(db, actor, tid, "task.updated", changes(row, data, nullable=("assignee_id", "due_date")))
    db.commit()
    return row


@app.patch(ORG + "/tasks/{tid}/status")
def task_status(org_id: str, tid: str, data: s.TaskStatus, db: Session = DB, user: User = AUTH):
    actor = member(db, org_id, user)
    row = scoped(db, Task, org_id, tid)
    if actor.role == "MEMBER" and row.assignee_id != actor.id:
        raise HTTPException(403, "Você só pode mover suas tarefas")
    active_project(scoped(db, Project, org_id, row.project_id))
    if row.archived:
        raise HTTPException(409, "Restaure a tarefa antes de movê-la")
    diff = changes(row, data)
    if diff:
        row.completed_at = now() if row.status == "DONE" else None
        event(db, actor, tid, "task.status", diff)
    db.commit()
    return row


@app.get(ORG + "/tasks/{tid}/comments")
def comments(org_id: str, tid: str, page_number: int = Query(1, ge=1), db: Session = DB, user: User = AUTH):
    member(db, org_id, user)
    scoped(db, Task, org_id, tid)
    return page(
        db,
        select(Comment)
        .where(Comment.organization_id == org_id, Comment.task_id == tid)
        .order_by(Comment.created_at.desc(), Comment.id),
        page_number,
    )


@app.post(ORG + "/tasks/{tid}/comments", status_code=201)
def comment(org_id: str, tid: str, data: s.CommentCreate, db: Session = DB, user: User = AUTH):
    actor = member(db, org_id, user)
    task = scoped(db, Task, org_id, tid)
    active_project(scoped(db, Project, org_id, task.project_id))
    if task.archived:
        raise HTTPException(409, "Tarefa arquivada")
    row = Comment(organization_id=org_id, task_id=tid, author_id=actor.id, body=data.body)
    db.add(row)
    db.flush()
    event(db, actor, tid, "comment.created")
    db.commit()
    return row


@app.get(ORG + "/activity")
def activity(
    org_id: str,
    entity_id: str | None = None,
    page_number: int = Query(1, ge=1),
    db: Session = DB,
    user: User = AUTH,
):
    member(db, org_id, user)
    stmt = select(Activity).where(Activity.organization_id == org_id)
    if entity_id:
        stmt = stmt.where(Activity.entity_id == entity_id)
    return page(db, stmt.order_by(Activity.created_at.desc(), Activity.id), page_number)


@app.get(ORG + "/dashboard")
def dashboard(
    org_id: str, start: date | None = None, end: date | None = None, db: Session = DB, user: User = AUTH
):
    member(db, org_id, user)
    zone = ZoneInfo(db.get(Organization, org_id).timezone)
    today = datetime.now(zone).date()
    start = start or today.replace(day=1)
    end = end or (today + timedelta(days=1))
    if end <= start:
        raise HTTPException(422, "Fim deve ser posterior ao início")
    base = (
        select(func.count())
        .select_from(Task)
        .join(Project, Task.project_id == Project.id)
        .where(Task.organization_id == org_id, Task.archived.is_(False))
    )
    active = base.where(Project.status == "ACTIVE")
    return {
        "active_projects": db.scalar(
            select(func.count())
            .select_from(Project)
            .where(Project.organization_id == org_id, Project.status == "ACTIVE")
        ),
        "pending_tasks": db.scalar(active.where(Task.status != "DONE")),
        "overdue_tasks": db.scalar(active.where(Task.status != "DONE", Task.due_date < today)),
        "completed_tasks": db.scalar(
            base.where(
                Project.status != "ARCHIVED",
                Task.status == "DONE",
                Task.completed_at >= datetime.combine(start, time.min, zone).astimezone(timezone.utc),
                Task.completed_at < datetime.combine(end, time.min, zone).astimezone(timezone.utc),
            )
        ),
        "start": start,
        "end_exclusive": end,
        "timezone": str(zone),
    }
@app.get("/api/v1/version")
def version():
    return {"name": "Nexus", "version": app.version}
