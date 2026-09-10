#!/usr/bin/env python3
"""
Create test users for performance testing by directly using the auth service.
"""

from bedrock_poc.auth import UserService, UserCreate, UserRole

def create_test_users():
    """Create test users directly."""

    test_users = [
        UserCreate(
            email="testuser@example.com",
            password="TestPassword123!",
            full_name="Test User",
            role=UserRole.RECRUITER
        ),
        UserCreate(
            email="admin@example.com",
            password="AdminPassword123!",
            full_name="Admin User",
            role=UserRole.ADMIN
        ),
    ]

    for user_data in test_users:
        user, success = UserService.register_user(user_data)
        if success:
            print(f"[OK] Created test user: {user.email}")
        else:
            print(f"[OK] Test user already exists: {user_data.email}")

if __name__ == "__main__":
    create_test_users()
