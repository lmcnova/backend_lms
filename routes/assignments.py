from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from uuid import uuid4
from datetime import datetime

from models.assignment import AssignRequest, AssignmentResponse
from config.database import get_database
from utils.dependencies import require_admin_or_teacher, get_current_identity


router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.post("/", response_model=List[AssignmentResponse], status_code=status.HTTP_201_CREATED)
async def assign_course(payload: AssignRequest, identity = Depends(require_admin_or_teacher)):
    db = get_database()
    course = db.courses.find_one({"uuid_id": payload.course_uuid})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    students = []
    if payload.student_uuid:
        students = [payload.student_uuid]
    elif payload.student_uuids:
        students = payload.student_uuids
    else:
        raise HTTPException(status_code=400, detail="Provide student_uuid or student_uuids")

    # validate students exist
    count = db.students.count_documents({"uuid_id": {"$in": students}})
    if count != len(students):
        raise HTTPException(status_code=400, detail="One or more students not found")

    responses = []
    for sid in students:
        # upsert with unique (student_uuid, course_uuid)
        existing = db.user_courses.find_one({"student_uuid": sid, "course_uuid": payload.course_uuid})
        if existing:
            if existing.get("status") == "revoked":
                db.user_courses.update_one({"_id": existing["_id"]}, {"$set": {"status": "active", "assigned_at": datetime.utcnow(), "assigned_by_role": identity["role"], "assigned_by_uuid": identity["user_uuid"]}})
                assignment_id = existing.get("uuid_id") or str(uuid4())
                db.user_courses.update_one({"_id": existing["_id"]}, {"$set": {"uuid_id": assignment_id}})
                doc = db.user_courses.find_one({"_id": existing["_id"]})
            else:
                doc = existing
        else:
            doc = {
                "uuid_id": str(uuid4()),
                "student_uuid": sid,
                "course_uuid": payload.course_uuid,
                "assigned_by_role": identity["role"],
                "assigned_by_uuid": identity["user_uuid"],
                "assigned_at": datetime.utcnow(),
                "status": "active",
            }
            db.user_courses.insert_one(doc)
        responses.append(AssignmentResponse(**{k: v for k, v in doc.items() if k != "_id"}))
    return responses


@router.get("/", response_model=List[AssignmentResponse])
async def list_assignments(student_uuid: str | None = None, course_uuid: str | None = None, identity = Depends(require_admin_or_teacher)):
    db = get_database()
    filt = {}
    if student_uuid:
        filt["student_uuid"] = student_uuid
    if course_uuid:
        filt["course_uuid"] = course_uuid
    docs = list(db.user_courses.find(filt, {"_id": 0}))
    return [AssignmentResponse(**d) for d in docs]


@router.get("/me", response_model=List[AssignmentResponse])
async def my_assignments(identity = Depends(get_current_identity)):
    if identity["role"] != "student":
        raise HTTPException(status_code=403, detail="Students only")
    db = get_database()
    docs = list(db.user_courses.find({"student_uuid": identity["user_uuid"], "status": "active"}, {"_id": 0}))
    return [AssignmentResponse(**d) for d in docs]


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_assignment(assignment_id: str, identity = Depends(require_admin_or_teacher)):
    db = get_database()
    doc = db.user_courses.find_one({"uuid_id": assignment_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Assignment not found")
    db.user_courses.update_one({"uuid_id": assignment_id}, {"$set": {"status": "revoked"}})
    return None

