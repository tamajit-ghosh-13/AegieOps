"""Authentication and RBAC data models (AegisOps Slice 6)."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, EmailStr, Field


class Role(str, Enum):
    viewer = "viewer"
    responder = "responder"
    admin = "admin"


class User(BaseModel):
    id: str
    email: str
    name: str
    role: Role
    team_id: str
    is_active: bool = True
    created_at: str


class UserInDB(User):
    hashed_password: str
    salt: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User


class LoginRequest(BaseModel):
    email: str
    password: str
