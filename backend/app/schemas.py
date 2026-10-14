"""Contratos: entrada explícita evita alterações em campos não autorizados."""

from datetime import date
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints

Short = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Description = Annotated[str, StringConstraints(max_length=5000)]
Role = Literal["ADMIN", "MANAGER", "MEMBER"]
Status = Literal["TODO", "IN_PROGRESS", "DONE"]
Priority = Literal["LOW", "MEDIUM", "HIGH"]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Login(Input):
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=12, max_length=128)]


class Register(Login):
    name: Short


class Name(Input):
    name: Short


class AddMember(Input):
    email: EmailStr
    role: Role = "MEMBER"


class ChangeRole(Input):
    role: Role


class ProjectCreate(Name):
    description: Description = ""


class ProjectPatch(Input):
    name: Short | None = None
    description: Description | None = None
    status: Literal["ACTIVE", "COMPLETED", "ARCHIVED"] | None = None


class TaskCreate(Input):
    project_id: str
    title: Short
    description: Description = ""
    priority: Priority = "MEDIUM"
    assignee_id: str | None = None
    due_date: date | None = None


class TaskPatch(Input):
    title: Short | None = None
    description: Description | None = None
    priority: Priority | None = None
    assignee_id: str | None = None
    due_date: date | None = None
    archived: bool | None = None


class TaskStatus(Input):
    status: Status


class CommentCreate(Input):
    body: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
