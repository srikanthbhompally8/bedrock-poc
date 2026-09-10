"""Main FastAPI application for Bedrock POC."""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bedrock_poc.api import auth, jobs, candidates, matches, audit

app = FastAPI(
    title="Bedrock POC API",
    description="AI-powered recruitment platform with JWT authentication and RBAC",
    version="2.0.0"
)

# Startup event to seed test users
@app.on_event("startup")
async def startup_event():
    """Seed test users on startup for performance testing."""
    try:
        from bedrock_poc.auth import UserService, UserCreate, UserRole
        from bedrock_poc.auth.auth import AuthService, users_db
        import hashlib

        test_users = [
            {"email": "testuser@example.com", "password": "Test123!", "full_name": "Test User", "role": "recruiter"},
            {"email": "admin@example.com", "password": "Admin123!", "full_name": "Admin User", "role": "admin"},
        ]

        for user_data in test_users:
            # Check if user already exists
            user_exists = any(u["email"] == user_data["email"] for u in users_db.values())
            if user_exists:
                print(f"[Startup] Test user already exists: {user_data['email']}")
                continue

            # Create user with direct hash (bypass bcrypt issue)
            user_id = len(users_db) + 1
            hashed = hashlib.sha256(user_data["password"].encode()).hexdigest()

            users_db[user_id] = {
                "id": user_id,
                "email": user_data["email"],
                "full_name": user_data["full_name"],
                "password_hash": f"sha256:{hashed}",
                "role": user_data["role"],
                "is_active": True,
                "created_at": __import__("datetime").datetime.utcnow(),
                "updated_at": __import__("datetime").datetime.utcnow()
            }
            print(f"[Startup] Created test user: {user_data['email']}")
    except Exception as e:
        print(f"[Startup] Error seeding test users: {e}")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(candidates.router)
app.include_router(matches.router)
app.include_router(audit.router)

# Health check
@app.get("/")
def read_root():
    """API health check."""
    return {
        "status": "operational",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/auth",
            "candidates": "/api/candidates",
            "matches": "/api/matches",
            "jobs": "/api/jobs"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
