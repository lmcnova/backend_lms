from datetime import datetime
from typing import Tuple, Dict, Any

from config.database import get_database

COMPLETION_THRESHOLD = 0.95
APPRECIATION_THRESHOLD = 0.90

def get_appreciation_threshold() -> float:
    return APPRECIATION_THRESHOLD


def clamp_progress(seconds_watched: int, last_position_sec: int, duration: int) -> Tuple[int, int, bool]:
    if duration <= 0:
        return 0, 0, True
    seconds_watched = max(0, min(seconds_watched, duration))
    last_position_sec = max(0, min(last_position_sec, duration))
    completed = last_position_sec >= int(duration * COMPLETION_THRESHOLD) or seconds_watched >= duration
    return seconds_watched, last_position_sec, completed


def upsert_video_progress(student_uuid: str, video_uuid: str, last_position_sec: int, delta_seconds: int, mark_completed: bool | None = None) -> Dict[str, Any]:
    db = get_database()
    video = db.videos.find_one({"uuid_id": video_uuid})
    if not video:
        raise ValueError("Video not found")
    duration = int(video.get("duration_seconds", 0) or 0)
    course_uuid = video["course_uuid"]
    topic_uuid = video["topic_uuid"]

    existing = db.user_progress.find_one({"student_uuid": student_uuid, "video_uuid": video_uuid})
    if not existing:
        seconds_watched = min(delta_seconds, duration)
        lw = min(last_position_sec, duration)
    else:
        seconds_watched = int(existing.get("seconds_watched", 0)) + int(delta_seconds or 0)
        lw = last_position_sec

    seconds_watched, lw, completed_auto = clamp_progress(seconds_watched, lw, duration)
    completed = bool(mark_completed) if mark_completed is not None else completed_auto

    doc = {
        "student_uuid": student_uuid,
        "course_uuid": course_uuid,
        "topic_uuid": topic_uuid,
        "video_uuid": video_uuid,
        "seconds_watched": seconds_watched,
        "last_position_sec": lw,
        "completed": completed,
        "last_watched_at": datetime.utcnow(),
    }
    db.user_progress.update_one(
        {"student_uuid": student_uuid, "video_uuid": video_uuid},
        {"$set": doc},
        upsert=True,
    )
    doc["video_uuid"] = video_uuid
    return doc


def compute_course_progress(student_uuid: str, course_uuid: str) -> Dict[str, Any]:
    db = get_database()
    videos = list(db.videos.find({"course_uuid": course_uuid}, {"uuid_id": 1, "duration_seconds": 1}))
    if not videos:
        return {"course_uuid": course_uuid, "total_videos": 0, "completed_videos": 0, "progress_percent": 0.0, "learning_seconds": 0, "learning_hours": 0.0}
    video_map = {v["uuid_id"]: int(v.get("duration_seconds", 0) or 0) for v in videos}
    total_duration = sum(video_map.values()) or 1
    progress_docs = list(db.user_progress.find({"student_uuid": student_uuid, "course_uuid": course_uuid}))

    watched_sum = 0
    completed_videos = 0
    for p in progress_docs:
        dur = video_map.get(p["video_uuid"], 0)
        watched_sum += min(int(p.get("seconds_watched", 0)), dur)
        if p.get("completed"):
            completed_videos += 1

    percent = round((watched_sum / total_duration) * 100.0, 2)
    hours = round(watched_sum / 3600.0, 2)
    return {
        "course_uuid": course_uuid,
        "total_videos": len(videos),
        "completed_videos": completed_videos,
        "progress_percent": percent,
        "learning_seconds": watched_sum,
        "learning_hours": hours,
    }
