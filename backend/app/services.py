"""Regras reutilizadas pelas rotas; a rota confirma a transação uma única vez."""

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from .models import Activity, Membership


def member(db, org_id, user):
    row = db.scalar(
        select(Membership)
        .where(
            Membership.organization_id == org_id, Membership.user_id == user.id, Membership.active.is_(True)
        )
        .with_for_update()
    )
    if not row:
        raise HTTPException(404, "Organização não encontrada")
    return row


def permit(membership, roles=("OWNER", "ADMIN", "MANAGER")):
    if membership.role not in roles:
        raise HTTPException(403, "Ação não permitida para seu papel")


def scoped(db, model, org_id, entity_id):
    row = db.scalar(
        select(model).where(model.organization_id == org_id, model.id == entity_id).with_for_update()
    )
    if not row:
        raise HTTPException(404, "Recurso não encontrado")
    return row


def assignee(db, org_id, entity_id):
    if entity_id is None:
        return
    row = scoped(db, Membership, org_id, entity_id)
    if not row.active:
        raise HTTPException(409, "Responsável inativo")


def active_project(project):
    if project.status != "ACTIVE":
        raise HTTPException(409, "Reabra o projeto para alterá-lo")


def event(db, actor, entity_id, action, changes=None):
    db.add(
        Activity(
            organization_id=actor.organization_id,
            actor_id=actor.id,
            entity_id=entity_id,
            action=action,
            changes=jsonable_encoder(changes or {}),
        )
    )


def page(db, statement, number=1, size=20):
    total = db.scalar(select(func.count()).select_from(statement.order_by(None).subquery()))
    return {
        "items": list(db.scalars(statement.offset((number - 1) * size).limit(size))),
        "total": total,
        "page": number,
        "page_size": size,
    }


def changes(row, payload, nullable=()):
    changed = {}
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is None and key not in nullable:
            raise HTTPException(422, f"{key} não aceita null")
        before = getattr(row, key)
        if before != value:
            changed[key] = {"before": before, "after": value}
            setattr(row, key, value)
    return changed
