import os
from uuid import uuid4
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status

from config.database import get_database
from utils.dependencies import require_admin_or_teacher
from utils.s3_storage import get_s3_storage


MEDIA_ROOT = os.getenv("MEDIA_ROOT", os.path.join(os.getcwd(), "media"))

router = APIRouter(prefix="/uploads", tags=["Uploads"])


def _ensure_dirs(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


@router.post("/video/topic/{topic_uuid}")
async def upload_video_new(topic_uuid: str, file: UploadFile = File(...), identity = Depends(require_admin_or_teacher)):
    db = get_database()
    topic = db.topics.find_one({"uuid_id": topic_uuid})
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    course_uuid = topic["course_uuid"]

    # Determine next order
    last = db.videos.find({"topic_uuid": topic_uuid}).sort("order_index", -1).limit(1)
    try:
        order = list(last)[0]["order_index"] + 1
    except IndexError:
        order = 1

    video_uuid = str(uuid4())

    # Upload to S3 or local storage
    storage = get_s3_storage()
    storage_key, size, mime, s3_url = await storage.upload_video(file, video_uuid)

    doc = {
        "uuid_id": video_uuid,
        "course_uuid": course_uuid,
        "topic_uuid": topic_uuid,
        "title": os.path.basename(file.filename or "video.mp4"),
        "description": None,
        "video_url": s3_url,  # S3 URL if using S3, None if local
        "thumbnail_url": None,
        "duration_seconds": 0,
        "is_preview": order == 1,
        "order_index": order,
        "source_type": "upload",
        "storage_key": storage_key,
        "mime_type": mime,
        "size_bytes": size,
        "original_filename": os.path.basename(file.filename or "video.mp4"),
    }
    if identity["role"] == "admin":
        doc["admin_uuid_id"] = identity["user_uuid"]
        doc["teacher_uuid_id"] = None
    else:
        doc["admin_uuid_id"] = None
        doc["teacher_uuid_id"] = identity["user_uuid"]

    db.videos.insert_one(doc)
    return {
        "detail": "uploaded",
        "video_uuid": video_uuid,
        "storage_key": storage_key,
        "video_url": s3_url,
        "size_bytes": size
    }


@router.post("/video/{video_uuid}")
async def upload_video_replace(video_uuid: str, file: UploadFile = File(...), identity = Depends(require_admin_or_teacher)):
    db = get_database()
    v = db.videos.find_one({"uuid_id": video_uuid})
    if not v:
        raise HTTPException(status_code=404, detail="Video not found")

    # Delete old file if exists
    if v.get("storage_key"):
        storage = get_s3_storage()
        storage.delete_file(v["storage_key"])

    # Upload new file to S3 or local storage
    storage = get_s3_storage()
    storage_key, size, mime, s3_url = await storage.upload_video(file, video_uuid)

    db.videos.update_one({"uuid_id": video_uuid}, {"$set": {
        "source_type": "upload",
        "storage_key": storage_key,
        "mime_type": mime,
        "size_bytes": size,
        "original_filename": os.path.basename(file.filename or "video.mp4"),
        "video_url": s3_url,  # S3 URL if using S3, None if local
    }})
    return {
        "detail": "uploaded",
        "video_uuid": video_uuid,
        "storage_key": storage_key,
        "video_url": s3_url,
        "size_bytes": size
    }


@router.post("/thumbnail/{video_uuid}")
async def upload_thumbnail(video_uuid: str, file: UploadFile = File(...), identity = Depends(require_admin_or_teacher)):
    """
    Upload thumbnail image for a video
    """
    db = get_database()
    v = db.videos.find_one({"uuid_id": video_uuid})
    if not v:
        raise HTTPException(status_code=404, detail="Video not found")

    # Delete old thumbnail if exists
    if v.get("thumbnail_storage_key"):
        storage = get_s3_storage()
        storage.delete_file(v["thumbnail_storage_key"])

    # Upload new thumbnail to S3 or local storage
    storage = get_s3_storage()
    storage_key, size, mime, s3_url = await storage.upload_thumbnail(file, video_uuid)

    db.videos.update_one({"uuid_id": video_uuid}, {"$set": {
        "thumbnail_url": s3_url,  # S3 URL if using S3, None if local
        "thumbnail_storage_key": storage_key,
    }})
    return {
        "detail": "thumbnail uploaded",
        "video_uuid": video_uuid,
        "thumbnail_url": s3_url,
        "storage_key": storage_key,
        "size_bytes": size
    }


@router.post("/image")
async def upload_image(file: UploadFile = File(...), identity = Depends(require_admin_or_teacher)):
    """
    Upload a general image (e.g., course thumbnail, profile picture, etc.)
    """
    storage = get_s3_storage()
    storage_key, size, mime, s3_url = await storage.upload_image(file, folder="images")

    return {
        "detail": "image uploaded",
        "storage_key": storage_key,
        "image_url": s3_url,
        "size_bytes": size,
        "mime_type": mime
    }


@router.post("/course-thumbnail/{course_uuid}")
async def upload_course_thumbnail(course_uuid: str, file: UploadFile = File(...), identity = Depends(require_admin_or_teacher)):
    """
    Upload thumbnail image for a course
    """
    db = get_database()
    course = db.courses.find_one({"uuid_id": course_uuid})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Delete old thumbnail if exists
    if course.get("thumbnail_storage_key"):
        storage = get_s3_storage()
        storage.delete_file(course["thumbnail_storage_key"])

    # Upload new thumbnail to S3 or local storage
    storage = get_s3_storage()
    storage_key, size, mime, s3_url = await storage.upload_image(file, folder="course-thumbnails")

    db.courses.update_one({"uuid_id": course_uuid}, {"$set": {
        "thumbnail_url": s3_url,  # S3 URL if using S3, None if local
        "thumbnail_storage_key": storage_key,
    }})
    return {
        "detail": "course thumbnail uploaded",
        "course_uuid": course_uuid,
        "thumbnail_url": s3_url,
        "storage_key": storage_key,
        "size_bytes": size
    }

