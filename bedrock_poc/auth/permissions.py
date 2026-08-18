"""Role-Based Access Control (RBAC) permissions framework."""

from enum import Enum
from typing import Set, Dict, List
from bedrock_poc.auth.models import UserRole


class Permission(str, Enum):
    """Permission definitions for RBAC."""

    # User management permissions
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    MANAGE_USERS = "manage_users"

    # Job management permissions
    CREATE_JOB = "create_job"
    READ_JOB = "read_job"
    UPDATE_JOB = "update_job"
    DELETE_JOB = "delete_job"
    MANAGE_JOBS = "manage_jobs"

    # Candidate management permissions
    CREATE_CANDIDATE = "create_candidate"
    READ_CANDIDATE = "read_candidate"
    UPDATE_CANDIDATE = "update_candidate"
    DELETE_CANDIDATE = "delete_candidate"
    MANAGE_CANDIDATES = "manage_candidates"

    # Match management permissions
    CREATE_MATCH = "create_match"
    READ_MATCH = "read_match"
    UPDATE_MATCH = "update_match"
    DELETE_MATCH = "delete_match"
    MANAGE_MATCHES = "manage_matches"

    # System permissions
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_SYSTEM = "manage_system"


class RolePermissions:
    """Role-to-permission mapping for RBAC."""

    _permissions: Dict[UserRole, Set[Permission]] = {
        UserRole.ADMIN: {
            # Admins have all permissions
            Permission.CREATE_USER,
            Permission.READ_USER,
            Permission.UPDATE_USER,
            Permission.DELETE_USER,
            Permission.MANAGE_USERS,
            Permission.CREATE_JOB,
            Permission.READ_JOB,
            Permission.UPDATE_JOB,
            Permission.DELETE_JOB,
            Permission.MANAGE_JOBS,
            Permission.CREATE_CANDIDATE,
            Permission.READ_CANDIDATE,
            Permission.UPDATE_CANDIDATE,
            Permission.DELETE_CANDIDATE,
            Permission.MANAGE_CANDIDATES,
            Permission.CREATE_MATCH,
            Permission.READ_MATCH,
            Permission.UPDATE_MATCH,
            Permission.DELETE_MATCH,
            Permission.MANAGE_MATCHES,
            Permission.VIEW_AUDIT_LOGS,
            Permission.MANAGE_SYSTEM,
        },
        UserRole.RECRUITER: {
            # Recruiters can manage jobs, candidates, and matches
            Permission.READ_USER,
            Permission.UPDATE_USER,
            Permission.CREATE_JOB,
            Permission.READ_JOB,
            Permission.UPDATE_JOB,
            Permission.DELETE_JOB,
            Permission.CREATE_CANDIDATE,
            Permission.READ_CANDIDATE,
            Permission.UPDATE_CANDIDATE,
            Permission.CREATE_MATCH,
            Permission.READ_MATCH,
            Permission.UPDATE_MATCH,
            Permission.VIEW_AUDIT_LOGS,
        },
        UserRole.CANDIDATE: {
            # Candidates can only read their own profile and view matches
            Permission.READ_USER,
            Permission.UPDATE_USER,
            Permission.READ_CANDIDATE,
            Permission.UPDATE_CANDIDATE,
            Permission.READ_MATCH,
        },
    }

    @classmethod
    def get_permissions(cls, role: UserRole) -> Set[Permission]:
        """Get all permissions for a given role.

        Args:
            role: User role

        Returns:
            Set of permissions for the role
        """
        return cls._permissions.get(role, set())

    @classmethod
    def has_permission(cls, role: UserRole, permission: Permission) -> bool:
        """Check if a role has a specific permission.

        Args:
            role: User role
            permission: Permission to check

        Returns:
            True if role has the permission, False otherwise
        """
        return permission in cls.get_permissions(role)

    @classmethod
    def has_any_permission(cls, role: UserRole, permissions: List[Permission]) -> bool:
        """Check if a role has any of the given permissions.

        Args:
            role: User role
            permissions: List of permissions to check

        Returns:
            True if role has any of the permissions, False otherwise
        """
        role_permissions = cls.get_permissions(role)
        return any(perm in role_permissions for perm in permissions)

    @classmethod
    def has_all_permissions(cls, role: UserRole, permissions: List[Permission]) -> bool:
        """Check if a role has all of the given permissions.

        Args:
            role: User role
            permissions: List of permissions to check

        Returns:
            True if role has all the permissions, False otherwise
        """
        role_permissions = cls.get_permissions(role)
        return all(perm in role_permissions for perm in permissions)
