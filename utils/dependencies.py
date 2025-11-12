from fastapi import Header, HTTPException, status, Depends
from jose import JWTError, jwt
from typing import Optional
from datetime import datetime

from utils.security import SECRET_KEY, ALGORITHM
from utils.sessions import is_session_active
from config.database import get_database


def get_current_identity(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    session_id = payload.get("sid")
    email_id = payload.get("sub")
    role = payload.get("role")
    user_uuid = payload.get("uuid")

    if not session_id or not role or not user_uuid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims")

    # Session must be active (not revoked)
    if not is_session_active(session_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or revoked")

    # Touch session last_used_at
    db = get_database()
    try:
        db.sessions.update_one({"session_id": session_id}, {"$set": {"last_used_at": datetime.utcnow()}})
    except Exception:
        pass

    return {"session_id": session_id, "email_id": email_id, "role": role, "user_uuid": user_uuid}


def require_admin(identity = Depends(get_current_identity)):
    if identity["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return identity


def require_admin_or_teacher(identity = Depends(get_current_identity)):
    if identity["role"] not in ("admin", "teacher"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or Teacher only")
    return identity
