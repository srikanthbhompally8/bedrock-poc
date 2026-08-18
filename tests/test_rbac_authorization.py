"""Tests for RBAC and authorization functionality."""

import pytest
from bedrock_poc.auth import (
    UserRole,
    User,
    UserCreate,
    UserService,
    AuthService,
    Permission,
    RolePermissions,
)
from bedrock_poc.auth.authorization import (
    has_permission,
    has_any_permission,
    has_all_permissions,
)


class TestPermissions:
    """Test permission checking."""

    def test_admin_has_all_permissions(self):
        """Test that admin role has all permissions."""
        admin_perms = RolePermissions.get_permissions(UserRole.ADMIN)
        assert Permission.MANAGE_USERS in admin_perms
        assert Permission.MANAGE_JOBS in admin_perms
        assert Permission.MANAGE_CANDIDATES in admin_perms
        assert Permission.MANAGE_MATCHES in admin_perms
        assert Permission.VIEW_AUDIT_LOGS in admin_perms

    def test_recruiter_has_correct_permissions(self):
        """Test that recruiter role has appropriate permissions."""
        recruiter_perms = RolePermissions.get_permissions(UserRole.RECRUITER)
        assert Permission.CREATE_JOB in recruiter_perms
        assert Permission.READ_CANDIDATE in recruiter_perms
        assert Permission.CREATE_MATCH in recruiter_perms
        assert Permission.MANAGE_USERS not in recruiter_perms

    def test_candidate_has_limited_permissions(self):
        """Test that candidate role has limited permissions."""
        candidate_perms = RolePermissions.get_permissions(UserRole.CANDIDATE)
        assert Permission.READ_USER in candidate_perms
        assert Permission.UPDATE_USER in candidate_perms
        assert Permission.READ_MATCH in candidate_perms
        assert Permission.CREATE_MATCH not in candidate_perms
        assert Permission.MANAGE_JOBS not in candidate_perms

    def test_admin_has_permission(self):
        """Test admin permission checking."""
        assert RolePermissions.has_permission(UserRole.ADMIN, Permission.MANAGE_USERS)
        assert RolePermissions.has_permission(UserRole.ADMIN, Permission.VIEW_AUDIT_LOGS)

    def test_recruiter_missing_admin_permission(self):
        """Test that recruiter doesn't have admin permissions."""
        assert not RolePermissions.has_permission(UserRole.RECRUITER, Permission.MANAGE_SYSTEM)
        assert not RolePermissions.has_permission(UserRole.RECRUITER, Permission.DELETE_USER)

    def test_candidate_cannot_create_job(self):
        """Test that candidate cannot create jobs."""
        assert not RolePermissions.has_permission(UserRole.CANDIDATE, Permission.CREATE_JOB)
        assert not RolePermissions.has_permission(UserRole.CANDIDATE, Permission.MANAGE_JOBS)

    def test_has_any_permission_positive(self):
        """Test has_any_permission with at least one valid permission."""
        perms = [Permission.CREATE_JOB, Permission.MANAGE_USERS]
        assert RolePermissions.has_any_permission(UserRole.RECRUITER, perms)

    def test_has_any_permission_negative(self):
        """Test has_any_permission with no valid permissions."""
        perms = [Permission.MANAGE_SYSTEM, Permission.DELETE_USER]
        assert not RolePermissions.has_any_permission(UserRole.CANDIDATE, perms)

    def test_has_all_permissions_positive(self):
        """Test has_all_permissions with all valid permissions."""
        perms = [Permission.CREATE_JOB, Permission.READ_CANDIDATE]
        assert RolePermissions.has_all_permissions(UserRole.RECRUITER, perms)

    def test_has_all_permissions_negative(self):
        """Test has_all_permissions missing at least one permission."""
        perms = [Permission.CREATE_JOB, Permission.MANAGE_USERS]
        assert not RolePermissions.has_all_permissions(UserRole.RECRUITER, perms)


class TestRolePermissionIntegration:
    """Test permission integration with user roles."""

    def test_admin_user_helper_functions(self):
        """Test permission checking helper functions for admin."""
        admin = User(
            id=1,
            email="admin@example.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True,
        )
        assert has_permission(admin, Permission.MANAGE_USERS)
        assert has_any_permission(admin, [Permission.MANAGE_USERS, Permission.MANAGE_JOBS])
        assert has_all_permissions(admin, [Permission.MANAGE_USERS, Permission.MANAGE_JOBS])

    def test_recruiter_user_helper_functions(self):
        """Test permission checking helper functions for recruiter."""
        recruiter = User(
            id=2,
            email="recruiter@example.com",
            full_name="Recruiter User",
            role=UserRole.RECRUITER,
            is_active=True,
        )
        assert has_permission(recruiter, Permission.CREATE_JOB)
        assert not has_permission(recruiter, Permission.MANAGE_USERS)
        assert has_any_permission(recruiter, [Permission.MANAGE_USERS, Permission.CREATE_JOB])
        assert not has_all_permissions(recruiter, [Permission.MANAGE_USERS, Permission.CREATE_JOB])

    def test_candidate_user_helper_functions(self):
        """Test permission checking helper functions for candidate."""
        candidate = User(
            id=3,
            email="candidate@example.com",
            full_name="Candidate User",
            role=UserRole.CANDIDATE,
            is_active=True,
        )
        assert has_permission(candidate, Permission.READ_USER)
        assert not has_permission(candidate, Permission.CREATE_JOB)
        assert has_any_permission(candidate, [Permission.READ_MATCH, Permission.CREATE_JOB])
        assert not has_all_permissions(candidate, [Permission.READ_MATCH, Permission.CREATE_JOB])


class TestUserAuthentication:
    """Test user authentication with roles."""

    def test_register_admin_user(self):
        """Test registering admin user."""
        user_create = UserCreate(
            email="admin@example.com",
            password="securepassword123",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        user, success = UserService.register_user(user_create)
        assert success
        assert user.role == UserRole.ADMIN
        assert user.is_active

    def test_register_recruiter_user(self):
        """Test registering recruiter user."""
        user_create = UserCreate(
            email="recruiter@example.com",
            password="securepassword123",
            full_name="Recruiter User",
            role=UserRole.RECRUITER,
        )
        user, success = UserService.register_user(user_create)
        assert success
        assert user.role == UserRole.RECRUITER

    def test_register_candidate_user(self):
        """Test registering candidate user."""
        user_create = UserCreate(
            email="candidate@example.com",
            password="securepassword123",
            full_name="Candidate User",
            role=UserRole.CANDIDATE,
        )
        user, success = UserService.register_user(user_create)
        assert success
        assert user.role == UserRole.CANDIDATE

    def test_token_contains_role(self):
        """Test that JWT token contains user role."""
        user_create = UserCreate(
            email="test@example.com",
            password="securepassword123",
            full_name="Test User",
            role=UserRole.RECRUITER,
        )
        user, _ = UserService.register_user(user_create)
        result = UserService.login_user(user_create.email, user_create.password)

        assert result is not None
        login_user, token = result
        assert login_user.role == UserRole.RECRUITER
        assert token.access_token is not None

        # Verify token contains role
        token_payload = AuthService.verify_token(token.access_token)
        assert token_payload is not None
        assert token_payload.role == UserRole.RECRUITER


class TestPermissionEnforcement:
    """Test that permissions are properly enforced."""

    def test_admin_can_perform_admin_actions(self):
        """Test that admin users can perform admin-only actions."""
        admin = User(
            id=1,
            email="admin@example.com",
            full_name="Admin",
            role=UserRole.ADMIN,
            is_active=True,
        )
        # Should not raise an exception
        assert has_permission(admin, Permission.MANAGE_USERS)
        assert has_permission(admin, Permission.VIEW_AUDIT_LOGS)

    def test_recruiter_cannot_perform_admin_actions(self):
        """Test that recruiters cannot perform admin-only actions."""
        recruiter = User(
            id=2,
            email="recruiter@example.com",
            full_name="Recruiter",
            role=UserRole.RECRUITER,
            is_active=True,
        )
        assert not has_permission(recruiter, Permission.MANAGE_USERS)
        assert not has_permission(recruiter, Permission.MANAGE_SYSTEM)

    def test_candidate_cannot_manage_jobs(self):
        """Test that candidates cannot manage jobs."""
        candidate = User(
            id=3,
            email="candidate@example.com",
            full_name="Candidate",
            role=UserRole.CANDIDATE,
            is_active=True,
        )
        assert not has_permission(candidate, Permission.CREATE_JOB)
        assert not has_permission(candidate, Permission.MANAGE_JOBS)
        assert not has_permission(candidate, Permission.CREATE_MATCH)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
