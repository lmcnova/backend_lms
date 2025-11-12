from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime

from models.progress import ProgressUpdate, VideoProgressResponse, CourseProgressResponse
from config.database import get_database
from utils.dependencies import get_current_identity
from utils.progress import upsert_video_progress, compute_course_progress, get_appreciation_threshold
from utils.dependencies import require_admin_or_teacher


router = APIRouter(prefix="/progress", tags=["Progress"])


def _ensure_student(identity):
    if identity["role"] != "student":
        raise HTTPException(status_code=403, detail="Students only")


def _ensure_assignment(db, student_uuid: str, course_uuid: str):
    assigned = db.user_courses.find_one({"student_uuid": student_uuid, "course_uuid": course_uuid, "status": "active"})
    if not assigned:
        raise HTTPException(status_code=403, detail="Course not assigned")


@router.put("/video/{video_uuid}", response_model=VideoProgressResponse)
async def update_video_progress(video_uuid: str, payload: ProgressUpdate, identity = Depends(get_current_identity)):
    _ensure_student(identity)
    db = get_database()
    video = db.videos.find_one({"uuid_id": video_uuid})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    _ensure_assignment(db, identity["user_uuid"], video["course_uuid"])
    doc = upsert_video_progress(identity["user_uuid"], video_uuid, payload.last_position_sec, payload.delta_seconds_watched, payload.completed)

    # Auto-generate certificate if course is completed
    if payload.completed:
        from routes.certificates import _all_videos_completed, _auto_generate_certificate
        is_completed, percentage = _all_videos_completed(db, identity["user_uuid"], video["course_uuid"])
        if is_completed:
            await _auto_generate_certificate(db, identity["user_uuid"], video["course_uuid"])

    return VideoProgressResponse(
        video_uuid=video_uuid,
        course_uuid=doc["course_uuid"],
        topic_uuid=doc["topic_uuid"],
        seconds_watched=doc["seconds_watched"],
        last_position_sec=doc["last_position_sec"],
        completed=doc["completed"],
    )


@router.post("/video/{video_uuid}/events", response_model=VideoProgressResponse)
async def progress_event(video_uuid: str, payload: ProgressUpdate, identity = Depends(get_current_identity)):
    return await update_video_progress(video_uuid, payload, identity)  # reuse logic


@router.get("/course/{course_uuid}", response_model=CourseProgressResponse)
async def get_course_progress(course_uuid: str, identity = Depends(get_current_identity)):
    _ensure_student(identity)
    db = get_database()
    _ensure_assignment(db, identity["user_uuid"], course_uuid)
    summary = compute_course_progress(identity["user_uuid"], course_uuid)
    return CourseProgressResponse(**summary)


@router.get("/me", response_model=List[CourseProgressResponse])
async def my_progress(identity = Depends(get_current_identity)):
    _ensure_student(identity)
    db = get_database()
    assignments = list(db.user_courses.find({"student_uuid": identity["user_uuid"], "status": "active"}))
    results = []
    for a in assignments:
        summary = compute_course_progress(identity["user_uuid"], a["course_uuid"])
        results.append(CourseProgressResponse(**summary))
    return results


@router.post("/video/{video_uuid}/complete", response_model=VideoProgressResponse)
async def mark_video_complete(video_uuid: str, identity = Depends(get_current_identity)):
    _ensure_student(identity)
    db = get_database()
    video = db.videos.find_one({"uuid_id": video_uuid})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    _ensure_assignment(db, identity["user_uuid"], video["course_uuid"])
    duration = int(video.get("duration", 0) or 0)
    doc = upsert_video_progress(identity["user_uuid"], video_uuid, duration, duration, True)

    # Auto-generate certificate if course is completed
    from routes.certificates import _all_videos_completed, _auto_generate_certificate
    is_completed, percentage = _all_videos_completed(db, identity["user_uuid"], video["course_uuid"])
    if is_completed:
        await _auto_generate_certificate(db, identity["user_uuid"], video["course_uuid"])

    return VideoProgressResponse(
        video_uuid=video_uuid,
        course_uuid=doc["course_uuid"],
        topic_uuid=doc["topic_uuid"],
        seconds_watched=doc["seconds_watched"],
        last_position_sec=doc["last_position_sec"],
        completed=doc["completed"],
    )


@router.get("/course/{course_uuid}/appreciation")
async def get_appreciation_status(course_uuid: str, identity = Depends(get_current_identity)):
    if identity["role"] != "student":
        raise HTTPException(status_code=403, detail="Students only")
    db = get_database()
    doc = db.user_courses.find_one({"student_uuid": identity["user_uuid"], "course_uuid": course_uuid})
    if not doc:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return {
        "course_uuid": course_uuid,
        "student_uuid": identity["user_uuid"],
        "appreciation_status": doc.get("appreciation_status", "none"),
        "appreciation_at": doc.get("appreciation_at")
    }


@router.post("/course/{student_uuid}/{course_uuid}/appreciate")
async def set_appreciation_status(student_uuid: str, course_uuid: str, identity = Depends(require_admin_or_teacher)):
    db = get_database()
    assign = db.user_courses.find_one({"student_uuid": student_uuid, "course_uuid": course_uuid, "status": "active"})
    if not assign:
        raise HTTPException(status_code=404, detail="Assignment not found")
    summary = compute_course_progress(student_uuid, course_uuid)
    if summary["progress_percent"] < get_appreciation_threshold() * 100.0:
        raise HTTPException(status_code=400, detail="Progress below appreciation threshold")
    db.user_courses.update_one({"student_uuid": student_uuid, "course_uuid": course_uuid}, {"$set": {"appreciation_status": "appreciated", "appreciation_at": datetime.utcnow()}})
    return {"detail": "Appreciation set", "course_uuid": course_uuid, "student_uuid": student_uuid}
