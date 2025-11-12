from fastapi import APIRouter, HTTPException, status, Query, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from typing import List, Optional
from uuid import uuid4
import os
import json

from models.course import CourseCreate, CourseUpdate, CourseResponse
from config.database import get_database
from utils.slug import slugify
from utils.course_stats import recompute_course_counts
from utils.dependencies import require_admin_or_teacher
from utils.auto_assign import auto_assign_existing_students_to_course
from utils.s3_storage import get_s3_storage


router = APIRouter(prefix="/courses", tags=["Courses"])

MEDIA_ROOT = os.getenv("MEDIA_ROOT", os.path.join(os.getcwd(), "media"))


def _ensure_dirs(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _course_public_projection():
    return {"_id": 0}


def _get_course_by_id_or_slug(db, key: str):
    doc = db.courses.find_one({"uuid_id": key})
    if not doc:
        doc = db.courses.find_one({"slug": key})
    return doc


@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    course: str = Form(...),
    thumbnail: Optional[UploadFile] = File(None),
    intro_video: Optional[UploadFile] = File(None),
    identity = Depends(require_admin_or_teacher)
):
    db = get_database()

    # Parse the JSON string to CourseCreate model
    try:
        course_data = json.loads(course)
        course_obj = CourseCreate(**course_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for course data")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid course data: {str(e)}")

    # Validate instructor exists
    if not db.teachers.find_one({"uuid_id": course_obj.instructor_uuid}):
        raise HTTPException(status_code=400, detail="Instructor not found")
    if course_obj.co_instructor_uuids:
        count = db.teachers.count_documents({"uuid_id": {"$in": course_obj.co_instructor_uuids}})
        if count != len(course_obj.co_instructor_uuids):
            raise HTTPException(status_code=400, detail="One or more co-instructors not found")

    course_uuid = str(uuid4())
    storage = get_s3_storage()

    # Handle thumbnail upload
    thumbnail_url = None
    thumbnail_storage_key = None
    if thumbnail:
        if thumbnail.content_type and not thumbnail.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are allowed for thumbnails")
        # Upload to S3 or local storage
        storage_key, size, mime, s3_url = await storage.upload_image(thumbnail, folder="course-thumbnails")
        thumbnail_storage_key = storage_key
        thumbnail_url = s3_url

    # Handle intro video upload
    intro_video_url = None
    intro_video_storage_key = None
    if intro_video:
        if intro_video.content_type and not intro_video.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail="Only video files are allowed for intro videos")
        # Upload to S3 or local storage
        storage_key, size, mime, s3_url = await storage.upload_file(intro_video, folder="course-intro-videos")
        intro_video_storage_key = storage_key
        intro_video_url = s3_url

    doc = course_obj.model_dump()
    doc["uuid_id"] = course_uuid
    doc["slug"] = slugify(course_obj.title)

    # Override with uploaded file paths/URLs if files were provided
    if thumbnail_storage_key:
        doc["thumbnail_url"] = thumbnail_url
        doc["thumbnail_storage_key"] = thumbnail_storage_key
    if intro_video_storage_key:
        doc["intro_video_url"] = intro_video_url
        doc["intro_video_storage_key"] = intro_video_storage_key

    # Ensure unique slug; append suffix if needed
    base_slug = doc["slug"]
    i = 1
    while db.courses.find_one({"slug": doc["slug"]}):
        i += 1
        doc["slug"] = f"{base_slug}-{i}"
    doc.update({
        "total_topics": 0,
        "total_videos": 0,
        "total_comments": 0,
    })
    # metadata mapping
    if identity["role"] == "admin":
        doc["admin_uuid_id"] = identity["user_uuid"]
        doc["teacher_uuid_id"] = None
    else:
        doc["admin_uuid_id"] = None
        doc["teacher_uuid_id"] = identity["user_uuid"]
    db.courses.insert_one(doc)

    # Auto-assign to existing students if auto_assign is enabled
    if course_obj.auto_assign and course_obj.departments:
        auto_assign_existing_students_to_course(doc["uuid_id"], course_obj.departments)

    return CourseResponse(**doc)


@router.get("/", response_model=List[CourseResponse])
async def list_courses(q: Optional[str] = None, category: Optional[str] = None, level: Optional[str] = None, instructor_uuid: Optional[str] = None, department: Optional[str] = None):
    db = get_database()
    filt = {}
    if category:
        filt["category"] = category
    if level:
        filt["level"] = level
    if instructor_uuid:
        filt["instructor_uuid"] = instructor_uuid
    if department:
        filt["departments"] = department
    # Basic q: match in title substring
    if q:
        filt["title"] = {"$regex": q, "$options": "i"}
    docs = list(db.courses.find(filt, _course_public_projection()).sort("title", 1))
    return docs


@router.get("/{course_key}", response_model=CourseResponse)
async def get_course(course_key: str):
    db = get_database()
    doc = _get_course_by_id_or_slug(db, course_key)
    if not doc:
        raise HTTPException(status_code=404, detail="Course not found")
    return CourseResponse(**{k: v for k, v in doc.items() if k != "_id"})


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: str,
    course: Optional[str] = Form(None),
    thumbnail: Optional[UploadFile] = File(None),
    intro_video: Optional[UploadFile] = File(None),
    identity = Depends(require_admin_or_teacher)
):
    db = get_database()
    existing = db.courses.find_one({"uuid_id": course_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Course not found")

    # Parse course data if provided
    data = {}
    if course:
        try:
            course_data = json.loads(course)
            update_obj = CourseUpdate(**course_data)
            data = update_obj.model_dump(exclude_unset=True)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for course data")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid course data: {str(e)}")

    storage = get_s3_storage()

    # Handle thumbnail upload and replacement
    if thumbnail:
        if thumbnail.content_type and not thumbnail.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are allowed for thumbnails")

        # Delete old thumbnail if exists
        if existing.get("thumbnail_storage_key"):
            storage.delete_file(existing["thumbnail_storage_key"])

        # Upload new thumbnail to S3 or local storage
        storage_key, size, mime, s3_url = await storage.upload_image(thumbnail, folder="course-thumbnails")
        data["thumbnail_url"] = s3_url
        data["thumbnail_storage_key"] = storage_key

    # Handle intro video upload and replacement
    if intro_video:
        if intro_video.content_type and not intro_video.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail="Only video files are allowed for intro videos")

        # Delete old intro video if exists
        if existing.get("intro_video_storage_key"):
            storage.delete_file(existing["intro_video_storage_key"])

        # Upload new intro video to S3 or local storage
        storage_key, size, mime, s3_url = await storage.upload_file(intro_video, folder="course-intro-videos")
        data["intro_video_url"] = s3_url
        data["intro_video_storage_key"] = storage_key

    # Handle slug generation if title changed
    if "title" in data:
        new_slug = slugify(data["title"])
        if new_slug != existing.get("slug"):
            base_slug = new_slug
            i = 1
            while db.courses.find_one({"slug": new_slug, "uuid_id": {"$ne": course_id}}):
                i += 1
                new_slug = f"{base_slug}-{i}"
            data["slug"] = new_slug

    # Validate instructor if changed
    if "instructor_uuid" in data and not db.teachers.find_one({"uuid_id": data["instructor_uuid"]}):
        raise HTTPException(status_code=400, detail="Instructor not found")

    if data:
        db.courses.update_one({"uuid_id": course_id}, {"$set": data})

    doc = db.courses.find_one({"uuid_id": course_id})
    return CourseResponse(**{k: v for k, v in doc.items() if k != "_id"})


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(course_id: str, identity = Depends(require_admin_or_teacher)):
    db = get_database()
    exists = db.courses.find_one({"uuid_id": course_id})
    if not exists:
        raise HTTPException(status_code=404, detail="Course not found")
    # cascade delete topics, videos, comments
    db.topics.delete_many({"course_uuid": course_id})
    db.videos.delete_many({"course_uuid": course_id})
    db.comments.delete_many({"course_uuid": course_id})
    # cascade delete assignments & progress
    db.user_courses.delete_many({"course_uuid": course_id})
    db.user_progress.delete_many({"course_uuid": course_id})
    db.courses.delete_one({"uuid_id": course_id})
    return None


@router.get("/{course_key}/outline")
async def course_outline(course_key: str):
    db = get_database()
    course = _get_course_by_id_or_slug(db, course_key)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course_uuid = course["uuid_id"]
    topics = list(db.topics.find({"course_uuid": course_uuid}, {"_id": 0}).sort("order_index", 1))
    topic_ids = [t["uuid_id"] for t in topics]
    videos = list(db.videos.find({"topic_uuid": {"$in": topic_ids}}, {"_id": 0}).sort("order_index", 1))
    by_topic = {}
    for v in videos:
        by_topic.setdefault(v["topic_uuid"], []).append(v)
    for t in topics:
        t["videos"] = by_topic.get(t["uuid_id"], [])
    return {"course": {k: v for k, v in course.items() if k != "_id"}, "topics": topics}


@router.post("/{course_id}/thumbnail")
async def upload_course_thumbnail(course_id: str, file: UploadFile = File(...), identity = Depends(require_admin_or_teacher)):
    """Upload a thumbnail image for a course"""
    db = get_database()
    course = db.courses.find_one({"uuid_id": course_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Validate file type (images only)
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed for thumbnails")

    # Delete old thumbnail if exists
    if course.get("thumbnail_storage_key"):
        storage = get_s3_storage()
        storage.delete_file(course["thumbnail_storage_key"])

    # Upload to S3 or local storage
    storage = get_s3_storage()
    storage_key, size, mime, s3_url = await storage.upload_image(file, folder="course-thumbnails")

    # Update course with thumbnail URL and storage key
    db.courses.update_one(
        {"uuid_id": course_id},
        {"$set": {
            "thumbnail_url": s3_url,
            "thumbnail_storage_key": storage_key
        }}
    )

    return {
        "detail": "Thumbnail uploaded successfully",
        "course_id": course_id,
        "thumbnail_url": s3_url,
        "storage_key": storage_key,
        "size_bytes": size
    }


@router.post("/{course_id}/intro-video")
async def upload_course_intro_video(course_id: str, file: UploadFile = File(...), identity = Depends(require_admin_or_teacher)):
    """Upload an intro video for a course"""
    db = get_database()
    course = db.courses.find_one({"uuid_id": course_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Validate file type (videos only)
    if file.content_type and not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Only video files are allowed for intro videos")

    # Delete old intro video if exists
    if course.get("intro_video_storage_key"):
        storage = get_s3_storage()
        storage.delete_file(course["intro_video_storage_key"])

    # Upload to S3 or local storage
    storage = get_s3_storage()
    storage_key, size, mime, s3_url = await storage.upload_file(file, folder="course-intro-videos")

    # Update course with intro video URL and storage key
    db.courses.update_one(
        {"uuid_id": course_id},
        {"$set": {
            "intro_video_url": s3_url,
            "intro_video_storage_key": storage_key
        }}
    )

    return {
        "detail": "Intro video uploaded successfully",
        "course_id": course_id,
        "intro_video_url": s3_url,
        "storage_key": storage_key,
        "mime_type": mime,
        "size_bytes": size
    }


@router.get("/{course_id}/thumbnail/file")
async def serve_course_thumbnail(course_id: str):
    """Serve the thumbnail file for a course"""
    db = get_database()
    course = db.courses.find_one({"uuid_id": course_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    storage = get_s3_storage()

    # Check if we have a thumbnail
    if course.get("thumbnail_url"):
        # S3 URL exists, return it
        if storage.use_s3 and course.get("thumbnail_storage_key"):
            # Generate presigned URL for private S3 objects
            thumbnail_url = storage.get_presigned_url(course["thumbnail_storage_key"], expiration=3600)
            return {"thumbnail_url": thumbnail_url}
        else:
            return {"thumbnail_url": course["thumbnail_url"]}
    elif course.get("thumbnail_storage_key") and not storage.use_s3:
        # Local storage - serve file
        file_path = os.path.join(MEDIA_ROOT, course["thumbnail_storage_key"])
        if os.path.isfile(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            mime_types = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp"
            }
            mime_type = mime_types.get(ext, "image/jpeg")
            return FileResponse(file_path, media_type=mime_type)
        else:
            raise HTTPException(status_code=404, detail="Thumbnail file not found")
    else:
        raise HTTPException(status_code=404, detail="No thumbnail available")


@router.get("/{course_id}/intro-video/file")
async def serve_course_intro_video(course_id: str):
    """Serve the intro video file for a course"""
    db = get_database()
    course = db.courses.find_one({"uuid_id": course_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    storage = get_s3_storage()

    # Check if we have an intro video
    if course.get("intro_video_url"):
        # S3 URL exists, return it
        if storage.use_s3 and course.get("intro_video_storage_key"):
            # Generate presigned URL for private S3 objects (15 minutes for videos)
            intro_video_url = storage.get_presigned_url(course["intro_video_storage_key"], expiration=900)
            return {"intro_video_url": intro_video_url}
        else:
            return {"intro_video_url": course["intro_video_url"]}
    elif course.get("intro_video_storage_key") and not storage.use_s3:
        # Local storage - serve file
        file_path = os.path.join(MEDIA_ROOT, course["intro_video_storage_key"])
        if os.path.isfile(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            mime_types = {
                ".mp4": "video/mp4",
                ".webm": "video/webm",
                ".ogg": "video/ogg",
                ".mov": "video/quicktime",
                ".avi": "video/x-msvideo"
            }
            mime_type = mime_types.get(ext, "video/mp4")
            headers = {
                "Cache-Control": "public, max-age=3600",
                "Content-Disposition": "inline"
            }
            return FileResponse(file_path, media_type=mime_type, headers=headers)
        else:
            raise HTTPException(status_code=404, detail="Intro video file not found")
    else:
        raise HTTPException(status_code=404, detail="No intro video available")
