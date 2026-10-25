"""Authentication and user management service (AegisOps Slice 6)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from auth.models import Role, User, UserInDB
from auth.security import hash_password, verify_password


class AuthService:
    def __init__(self) -> None:
        self._users: dict[str, UserInDB] = {}
        self._seed_default_users()

    def _seed_default_users(self) -> None:
        """Seed default enterprise personas for hackathon demonstration."""
        now = datetime.now(timezone.utc).isoformat()
        defaults = [
            (
                "usr-admin-1",
                "admin@aegisops.io",
                "Alex Rivers (Lead SRE)",
                "admin123",
                Role.admin,
                "team-core-infra",
            ),
            (
                "usr-sre-1",
                "sre@aegisops.io",
                "Sam Chen (SRE Responder)",
                "sre123",
                Role.responder,
                "team-core-infra",
            ),
            (
                "usr-viewer-1",
                "viewer@aegisops.io",
                "Jordan Lee (Product Ops)",
                "viewer123",
                Role.viewer,
                "team-core-infra",
            ),
        ]
        for uid, email, name, pwd, role, team in defaults:
            hashed, salt = hash_password(pwd)
            self._users[email.lower()] = UserInDB(
                id=uid,
                email=email.lower(),
                name=name,
                role=role,
                team_id=team,
                is_active=True,
                created_at=now,
                hashed_password=hashed,
                salt=salt,
            )

    def authenticate(self, email: str, password: str) -> User | None:
        """Verify user credentials and return clean User object without secret hashes."""
        user_db = self._users.get(email.lower())
        if user_db is None or not user_db.is_active:
            return None
        if not verify_password(password, user_db.hashed_password, user_db.salt):
            return None
        return User(
            id=user_db.id,
            email=user_db.email,
            name=user_db.name,
            role=user_db.role,
            team_id=user_db.team_id,
            is_active=user_db.is_active,
            created_at=user_db.created_at,
        )

    def get_user_by_id(self, user_id: str) -> User | None:
        for u in self._users.values():
            if u.id == user_id:
                return User(
                    id=u.id,
                    email=u.email,
                    name=u.name,
                    role=u.role,
                    team_id=u.team_id,
                    is_active=u.is_active,
                    created_at=u.created_at,
                )
        return None

    def get_user_by_email(self, email: str) -> User | None:
        u = self._users.get(email.lower())
        if u is None:
            return None
        return User(
            id=u.id,
            email=u.email,
            name=u.name,
            role=u.role,
            team_id=u.team_id,
            is_active=u.is_active,
            created_at=u.created_at,
        )

    def list_users(self, team_id: str | None = None) -> list[User]:
        users = []
        for u in self._users.values():
            if team_id is None or u.team_id == team_id:
                users.append(
                    User(
                        id=u.id,
                        email=u.email,
                        name=u.name,
                        role=u.role,
                        team_id=u.team_id,
                        is_active=u.is_active,
                        created_at=u.created_at,
                    )
                )
        return users

    def can_approve(self, user: User, action: str, blast_radius: str = "low") -> tuple[bool, str | None]:
        """Enforce Role-Based Access Control rules on remediation authorization."""
        if user.role == Role.viewer:
            return False, "Viewers have read-only access and cannot authorize remediation actions."

        is_high_risk = blast_radius.lower() == "high" or action in ("patch_code", "rollback")

        if is_high_risk and user.role != Role.admin:
            return False, f"Action '{action}' with high blast radius requires Lead SRE / Admin authorization."

        return True, None


_AUTH_SERVICE: AuthService | None = None


def get_auth_service() -> AuthService:
    global _AUTH_SERVICE
    if _AUTH_SERVICE is None:
        _AUTH_SERVICE = AuthService()
    return _AUTH_SERVICE
