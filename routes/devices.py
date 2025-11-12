from fastapi import APIRouter, HTTPException, status, Depends
from uuid import uuid4
from datetime import datetime

from models.device_reset import DeviceResetRequestCreate, DeviceResetRequestResponse
from config.database import get_database
from utils.dependencies import get_current_identity, require_admin
from utils.sessions import revoke_all_sessions


router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post("/reset-request", response_model=DeviceResetRequestResponse, status_code=status.HTTP_201_CREATED)
async def request_device_reset(payload: DeviceResetRequestCreate, identity = Depends(get_current_identity)):
    if identity["role"] != "student":
        raise HTTPException(status_code=403, detail="Students only")
    db = get_database()
    existing = db.device_resets.find_one({"student_uuid": identity["user_uuid"], "status": "pending"})
    if existing:
        return DeviceResetRequestResponse(**{k: v for k, v in existing.items() if k != "_id"})
    doc = {
        "request_id": str(uuid4()),
        "student_uuid": identity["user_uuid"],
        "status": "pending",
        "reason": payload.reason,
        "created_at": datetime.utcnow(),
        "resolved_at": None,
        "resolved_by_uuid": None,
        "resolved_by_role": None,
    }
    db.device_resets.insert_one(doc)
    return DeviceResetRequestResponse(**doc)


@router.get("/reset-requests", response_model=list[DeviceResetRequestResponse])
async def list_device_reset_requests(status_filter: str | None = None, identity = Depends(require_admin)):
    db = get_database()
    filt = {}
    if status_filter:
        filt["status"] = status_filter
    docs = list(db.device_resets.find(filt, {"_id": 0}).sort("created_at", 1))
    return [DeviceResetRequestResponse(**d) for d in docs]


@router.post("/reset-requests/{request_id}/approve", response_model=DeviceResetRequestResponse)
async def approve_device_reset(request_id: str, identity = Depends(require_admin)):
    db = get_database()
    req = db.device_resets.find_one({"request_id": request_id})
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Request already resolved")
    # Revoke all sessions for student
    revoke_all_sessions(req["student_uuid"])
    db.device_resets.update_one({"request_id": request_id}, {"$set": {
        "status": "approved",
        "resolved_at": datetime.utcnow(),
        "resolved_by_uuid": identity["user_uuid"],
        "resolved_by_role": identity["role"],
    }})
    doc = db.device_resets.find_one({"request_id": request_id}, {"_id": 0})
    return DeviceResetRequestResponse(**doc)


@router.post("/reset-requests/{request_id}/reject", response_model=DeviceResetRequestResponse)
async def reject_device_reset(request_id: str, identity = Depends(require_admin)):
    db = get_database()
    req = db.device_resets.find_one({"request_id": request_id})
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Request already resolved")
    db.device_resets.update_one({"request_id": request_id}, {"$set": {
        "status": "rejected",
        "resolved_at": datetime.utcnow(),
        "resolved_by_uuid": identity["user_uuid"],
        "resolved_by_role": identity["role"],
    }})
    doc = db.device_resets.find_one({"request_id": request_id}, {"_id": 0})
    return DeviceResetRequestResponse(**doc)

