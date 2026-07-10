"""Role-based access control and policy validation checks."""

from __future__ import annotations

from typing import List

from src.database.models import User


class RBACManager:
    """Verifies user privileges and role-based permissions against required scopes."""

    @staticmethod
    def has_permission(user: User, required_permission: str) -> bool:
        """Verify if a user holds a specific permission scope."""
        if not user or not user.permissions:
            return False

        # Cast user permissions to list of strings
        permissions_list: List[str] = user.permissions  # type: ignore

        # Admin user bypass
        if user.role == "admin" or "*" in permissions_list:
            return True

        return required_permission in permissions_list

    @staticmethod
    def has_any_permission(user: User, required_permissions: List[str]) -> bool:
        """Verify if a user holds any of the listed permission scopes."""
        if not user or not user.permissions:
            return False

        permissions_list: List[str] = user.permissions  # type: ignore

        if user.role == "admin" or "*" in permissions_list:
            return True

        return any(perm in permissions_list for perm in required_permissions)
