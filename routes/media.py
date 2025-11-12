from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse
import os
from datetime import datetime, timedelta

from models.media import VideoPlaybackConfig
from config.database import get_database
from utils.dependencies import get_current_identity
from utils.s3_storage import get_s3_storage


router = APIRouter(prefix="/media", tags=["Media"])


@router.get("/video/{video_uuid}", response_model=VideoPlaybackConfig)
async def get_video(video_uuid: str, identity = Depends(get_current_identity)):
    db = get_database()
    video = db.videos.find_one({"uuid_id": video_uuid})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    course_uuid = video["course_uuid"]

    # Access rules
    if identity["role"] == "student":
        assigned = db.user_courses.find_one({"student_uuid": identity["user_uuid"], "course_uuid": course_uuid, "status": "active"})
        if not assigned:
            raise HTTPException(status_code=403, detail="Course not assigned")
    # Admin/Teacher: allowed. Optionally restrict to instructor in future.

    # Build stream url depending on source
    expires = datetime.utcnow() + timedelta(minutes=15)
    storage = get_s3_storage()

    if video.get("source_type") == "upload" and video.get("storage_key"):
        # Check if using S3 or local storage
        if storage.use_s3:
            # Generate presigned URL for S3
            stream_url = storage.get_presigned_url(video["storage_key"], expiration=900)  # 15 minutes
        else:
            # Local storage - use file endpoint
            stream_url = f"/media/file/{video_uuid}"
    elif video.get("video_url"):
        # External URL or S3 public URL
        stream_url = video["video_url"]
    else:
        raise HTTPException(status_code=400, detail="Video has no source configured")
    headers = {"Cache-Control": "no-store"}
    flags = {
        "controlsList": "nodownload",
        "disableContextMenu": True,
        "draggable": False,
        "watermark": True,
        "contentSecurityPolicy": "default-src 'self'; media-src 'self'; frame-ancestors 'none'",
    }
    return VideoPlaybackConfig(
        video_uuid=video_uuid,
        course_uuid=course_uuid,
        stream_url=stream_url,
        expires_at=expires,
        headers=headers,
        client_flags=flags,
    )


@router.get("/file/{video_uuid}")
async def stream_uploaded_video(video_uuid: str, identity = Depends(get_current_identity)):
    db = get_database()
    video = db.videos.find_one({"uuid_id": video_uuid})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    # Access rules (same as get_video)
    if identity["role"] == "student":
        assigned = db.user_courses.find_one({"student_uuid": identity["user_uuid"], "course_uuid": video["course_uuid"], "status": "active"})
        if not assigned:
            raise HTTPException(status_code=403, detail="Course not assigned")

    storage_key = video.get("storage_key")
    if not storage_key:
        raise HTTPException(status_code=400, detail="No uploaded file")
    media_root = os.getenv("MEDIA_ROOT", os.path.join(os.getcwd(), "media"))
    file_path = os.path.join(media_root, storage_key)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File missing")
    headers = {
        "Cache-Control": "no-store",
        "Content-Disposition": "inline"
    }
    return FileResponse(file_path, media_type=video.get("mime_type") or "application/octet-stream", headers=headers)


@router.get("/thumbnail/{video_uuid}")
async def get_thumbnail(video_uuid: str):
    """
    Get thumbnail for a video (public access for preview purposes)
    """
    db = get_database()
    video = db.videos.find_one({"uuid_id": video_uuid})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    storage = get_s3_storage()

    # Check if we have a thumbnail
    if video.get("thumbnail_url"):
        # S3 URL exists, return it
        if storage.use_s3 and video.get("thumbnail_storage_key"):
            # Generate presigned URL for private S3 objects
            thumbnail_url = storage.get_presigned_url(video["thumbnail_storage_key"], expiration=3600)
            return {"thumbnail_url": thumbnail_url}
        else:
            return {"thumbnail_url": video["thumbnail_url"]}
    elif video.get("thumbnail_storage_key") and not storage.use_s3:
        # Local storage - serve file
        media_root = os.getenv("MEDIA_ROOT", os.path.join(os.getcwd(), "media"))
        file_path = os.path.join(media_root, video["thumbnail_storage_key"])
        if os.path.isfile(file_path):
            return FileResponse(file_path, media_type="image/jpeg")
        else:
            raise HTTPException(status_code=404, detail="Thumbnail file not found")
    else:
        raise HTTPException(status_code=404, detail="No thumbnail available")


@router.get("/image/{storage_key:path}")
async def get_image(storage_key: str):
    """
    Get image by storage key (for course thumbnails, profile pictures, etc.)
    """
    storage = get_s3_storage()

    if storage.use_s3:
        # Generate presigned URL for S3
        image_url = storage.get_presigned_url(storage_key, expiration=3600)
        return {"image_url": image_url}
    else:
        # Local storage - serve file
        media_root = os.getenv("MEDIA_ROOT", os.path.join(os.getcwd(), "media"))
        file_path = os.path.join(media_root, storage_key)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        else:
            raise HTTPException(status_code=404, detail="Image file not found")
