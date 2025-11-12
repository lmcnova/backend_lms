from fastapi import APIRouter, HTTPException, status, Request, Depends
from datetime import timedelta

from models.auth import LoginRequest, Token
from config.database import get_database
from utils.security import (
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    MAX_ACTIVE_DEVICES,
    SINGLE_SESSION,
)
from utils.sessions import create_session, enforce_device_limit, revoke_all_sessions
from utils.dependencies import get_current_identity

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, request: Request):
    """
    Login for Admin or Student without specifying role.
    Determines role automatically based on matching collection.
    """
    db = get_database()

    # Try admin collection first
    user = db.admins.find_one({"email_id": login_data.email_id})
    role = "admin" if user else None

    # If not found in admins, try students
    if not user:
        user = db.students.find_one({"email_id": login_data.email_id})
        role = "student" if user else None
    # If still not found, try teachers
    if not user:
        user = db.teachers.find_one({"email_id": login_data.email_id})
        role = "teacher" if user else None

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Session handling
    user_uuid = user["uuid_id"]
    if SINGLE_SESSION:
        revoke_all_sessions(user_uuid)

    device_name = request.headers.get("X-Device-Name")
    user_agent = request.headers.get("user-agent")
    ip_addr = request.client.host if request.client else None
    session = create_session(user_uuid, role, device_name, user_agent, ip_addr)

    # Enforce max devices (revoke oldest if exceeding)
    enforce_device_limit(user_uuid, MAX_ACTIVE_DEVICES)

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user["email_id"],
            "role": role,
            "sid": session["session_id"],
            "uuid": user_uuid,
        },
        expires_delta=access_token_expires,
    )

    # Prepare user data (exclude sensitive information)
    user_data = {
        "uuid_id": user["uuid_id"],
        "email_id": user["email_id"],
    }

    if role == "admin":
        user_data["college_name"] = user["college_name"]
        user_data["total_student_allow_count"] = user["total_student_allow_count"]
    elif role == "student":
        user_data["student_name"] = user["student_name"]
        user_data["department"] = user["department"]
        user_data["sub_department"] = user.get("sub_department")
    elif role == "teacher":
        user_data["name"] = user["name"]
        user_data["bio"] = user.get("bio")

    return Token(
        access_token=access_token,
        token_type="bearer",
        role=role,
        user_data=user_data,
    )


@router.get("/sessions")
async def list_sessions(identity = Depends(get_current_identity)):
    """List active sessions for current user"""
    db = get_database()
    sessions = list(
        db.sessions.find({"user_uuid": identity["user_uuid"], "revoked": False}, {"_id": 0})
        .sort("last_used_at", 1)
    )
    return {"sessions": sessions}


@router.post("/logout")
async def logout_current(identity = Depends(get_current_identity)):
    """Logout current session"""
    db = get_database()
    db.sessions.update_one({"session_id": identity["session_id"]}, {"$set": {"revoked": True}})
    return {"detail": "Logged out"}


@router.post("/logout-all")
async def logout_all(identity = Depends(get_current_identity)):
    """Logout all sessions for current user"""
    count = revoke_all_sessions(identity["user_uuid"])
    return {"detail": f"Logged out of {count} sessions"}
