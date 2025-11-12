from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from typing import List, Optional
from uuid import uuid4
import os
import json

from models.video import VideoCreate, VideoUpdate, VideoResponse
from config.database import get_database
from utils.course_stats import recompute_course_counts
from utils.dependencies import require_admin_or_teacher
from utils.s3_storage import get_s3_storage


router = APIRouter(prefix="/videos", tags=["Videos"])

MEDIA_ROOT = os.getenv("MEDIA_ROOT", os.path.join(os.getcwd(), "media"))


def _ensure_dirs(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


@router.get("/topic/{topic_id}", response_model=List[VideoResponse])
async def list_videos(topic_id: str):
    db = get_database()
    topic = db.topics.find_one({"uuid_id": topic_id})
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    docs = list(db.videos.find({"topic_uuid": topic_id}, {"_id": 0}).sort("order_index", 1))
    return docs


@router.post("/topic/{topic_id}", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def create_video(
    topic_id: str,
    video: str = Form(...),
    video_file: Optional[UploadFile] = File(None),
    thumbnail: Optional[UploadFile] = File(None),
    identity = Depends(require_admin_or_teacher)
):
    db = get_database()
    topic = db.topics.find_one({"uuid_id": topic_id})
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    course_uuid = topic["course_uuid"]

    # Parse the JSON string to VideoCreate model
    try:
        video_data = json.loads(video)
        video_obj = VideoCreate(**video_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for video data")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid video data: {str(e)}")

    order = video_obj.order_index
    if order is None:
        last = db.videos.find({"topic_uuid": topic_id}).sort("order_index", -1).limit(1)
        try:
            order = list(last)[0]["order_index"] + 1
        except IndexError:
            order = 1

    video_uuid = str(uuid4())
    storage = get_s3_storage()

    # Handle video file upload
    video_url = None
    storage_key = None
    mime_type = None
    size_bytes = None
    original_filename = None

    if video_file:
        if video_file.content_type and not video_file.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail="Only video files are allowed")
        # Upload to S3 or local storage
        storage_key, size_bytes, mime_type, s3_url = await storage.upload_video(video_file, video_uuid)
        video_url = s3_url
        original_filename = os.path.basename(video_file.filename or "video.mp4")

    # Handle thumbnail upload
    thumbnail_url = None
    thumbnail_storage_key = None
    if thumbnail:
        if thumbnail.content_type and not thumbnail.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are allowed for thumbnails")
        # Upload to S3 or local storage
        thumbnail_storage_key, thumb_size, thumb_mime, thumb_s3_url = await storage.upload_thumbnail(thumbnail, video_uuid)
        thumbnail_url = thumb_s3_url

    doc = video_obj.model_dump()
    doc.update({
        "uuid_id": video_uuid,
        "course_uuid": course_uuid,
        "topic_uuid": topic_id,
        "order_index": order,
    })

    # Override with uploaded file data if files were provided
    if video_file and storage_key:
        doc["video_url"] = video_url  # S3 URL or None for local storage
        doc["source_type"] = "upload"
        doc["storage_key"] = storage_key
        doc["mime_type"] = mime_type
        doc["size_bytes"] = size_bytes
        doc["original_filename"] = original_filename

    if thumbnail and thumbnail_storage_key:
        doc["thumbnail_url"] = thumbnail_url  # S3 URL or None for local storage
        doc["thumbnail_storage_key"] = thumbnail_storage_key

    if identity["role"] == "admin":
        doc["admin_uuid_id"] = identity["user_uuid"]
        doc["teacher_uuid_id"] = None
    else:
        doc["admin_uuid_id"] = None
        doc["teacher_uuid_id"] = identity["user_uuid"]

    # Shift on conflict
    conflict = db.videos.find_one({"topic_uuid": topic_id, "order_index": order})
    if conflict:
        db.videos.update_many({"topic_uuid": topic_id, "order_index": {"$gte": order}}, {"$inc": {"order_index": 1}})
    db.videos.insert_one(doc)
    recompute_course_counts(course_uuid)
    return VideoResponse(**doc)


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(video_id: str):
    db = get_database()
    doc = db.videos.find_one({"uuid_id": video_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Video not found")
    return VideoResponse(**{k: v for k, v in doc.items() if k != "_id"})


@router.put("/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: str,
    video: Optional[str] = Form(None),
    video_file: Optional[UploadFile] = File(None),
    thumbnail: Optional[UploadFile] = File(None),
    identity = Depends(require_admin_or_teacher)
):
    db = get_database()
    existing = db.videos.find_one({"uuid_id": video_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Video not found")
    topic_uuid = existing["topic_uuid"]

    # Parse video data if provided
    data = {}
    if video:
        try:
            video_data = json.loads(video)
            update_obj = VideoUpdate(**video_data)
            data = update_obj.model_dump(exclude_unset=True)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for video data")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid video data: {str(e)}")

    storage = get_s3_storage()

    # Handle video file upload and replacement
    if video_file:
        if video_file.content_type and not video_file.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail="Only video files are allowed")

        # Delete old video file if exists
        if existing.get("storage_key"):
            storage.delete_file(existing["storage_key"])

        # Upload new video to S3 or local storage
        storage_key, size_bytes, mime_type, s3_url = await storage.upload_video(video_file, video_id)
        data["video_url"] = s3_url  # S3 URL or None for local storage
        data["source_type"] = "upload"
        data["storage_key"] = storage_key
        data["mime_type"] = mime_type
        data["size_bytes"] = size_bytes
        data["original_filename"] = os.path.basename(video_file.filename or "video.mp4")

    # Handle thumbnail upload and replacement
    if thumbnail:
        if thumbnail.content_type and not thumbnail.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are allowed for thumbnails")

        # Delete old thumbnail if exists
        if existing.get("thumbnail_storage_key"):
            storage.delete_file(existing["thumbnail_storage_key"])

        # Upload new thumbnail to S3 or local storage
        thumbnail_storage_key, thumb_size, thumb_mime, thumb_s3_url = await storage.upload_thumbnail(thumbnail, video_id)
        data["thumbnail_url"] = thumb_s3_url  # S3 URL or None for local storage
        data["thumbnail_storage_key"] = thumbnail_storage_key

    # Handle order_index changes
    if "order_index" in data and data["order_index"] != existing["order_index"]:
        new = data["order_index"]
        if new < existing["order_index"]:
            db.videos.update_many({"topic_uuid": topic_uuid, "order_index": {"$gte": new, "$lt": existing["order_index"]}}, {"$inc": {"order_index": 1}})
        else:
            db.videos.update_many({"topic_uuid": topic_uuid, "order_index": {"$gt": existing["order_index"], "$lte": new}}, {"$inc": {"order_index": -1}})

    if data:
        db.videos.update_one({"uuid_id": video_id}, {"$set": data})

    doc = db.videos.find_one({"uuid_id": video_id})
    return VideoResponse(**{k: v for k, v in doc.items() if k != "_id"})


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(video_id: str, identity = Depends(require_admin_or_teacher)):
    db = get_database()
    existing = db.videos.find_one({"uuid_id": video_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Video not found")
    course_uuid = existing["course_uuid"]
    # delete comments under video
    db.comments.delete_many({"parent_type": "video", "parent_uuid": video_id})
    # delete progress under video
    db.user_progress.delete_many({"video_uuid": video_id})
    db.videos.delete_one({"uuid_id": video_id})
    recompute_course_counts(course_uuid)
    return None
