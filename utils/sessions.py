from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from config.database import get_database


def create_session(user_uuid: str, role: str, device_name: Optional[str], user_agent: Optional[str], ip_address: Optional[str]) -> dict:
    db = get_database()
    session = {
        "session_id": str(uuid4()),
        "user_uuid": user_uuid,
        "role": role,
        "device_name": device_name,
        "user_agent": user_agent,
        "ip_address": ip_address,
        "created_at": datetime.utcnow(),
        "last_used_at": datetime.utcnow(),
        "revoked": False,
    }
    db.sessions.insert_one(session)
    return session


def get_active_sessions(user_uuid: str) -> List[dict]:
    db = get_database()
    return list(db.sessions.find({"user_uuid": user_uuid, "revoked": False}).sort("last_used_at", 1))


def revoke_session(session_id: str) -> int:
    db = get_database()
    result = db.sessions.update_one({"session_id": session_id}, {"$set": {"revoked": True}})
    return result.modified_count


def revoke_all_sessions(user_uuid: str) -> int:
    db = get_database()
    result = db.sessions.update_many({"user_uuid": user_uuid, "revoked": False}, {"$set": {"revoked": True}})
    return result.modified_count


def enforce_device_limit(user_uuid: str, max_devices: int) -> Optional[str]:
    """Ensure active sessions do not exceed max_devices. If exceeded, revoke oldest and return its id."""
    sessions = get_active_sessions(user_uuid)
    if len(sessions) <= max_devices:
        return None
    # Revoke oldest session (first in asc sort)
    oldest = sessions[0]
    revoke_session(oldest["session_id"])
    return oldest["session_id"]


def is_session_active(session_id: str) -> bool:
    db = get_database()
    session = db.sessions.find_one({"session_id": session_id})
    return bool(session and not session.get("revoked"))

