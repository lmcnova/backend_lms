from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form, Request
from typing import List, Optional
from uuid import uuid4
import json
import os

from models.teacher import TeacherCreate, TeacherUpdate, TeacherResponse
from config.database import get_database
from utils.security import get_password_hash
from utils.dependencies import require_admin
from utils.s3_storage import get_s3_storage


router = APIRouter(prefix="/teachers", tags=["Teachers"])


@router.post("/", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    request: Request,
    teacher: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    email_id: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    skills: Optional[str] = Form(None),  # JSON string
    social_links: Optional[str] = Form(None),  # JSON string
    avatar: Optional[UploadFile] = File(None),
    identity = Depends(require_admin)
):
    """
    Create teacher with optional avatar upload to S3.
    Accepts both JSON (application/json) and multipart/form-data.
    """
    db = get_database()

    # Check if this is a JSON request
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        # Handle JSON request
        body = await request.json()
        teacher_data = body
    elif teacher:
        # Multipart with JSON string in 'teacher' field
        teacher_data = json.loads(teacher)
    elif name or email_id:
        # Multipart with individual fields
        teacher_data = {
            "name": name,
            "email_id": email_id,
            "password": password,
            "bio": bio,
            "skills": json.loads(skills) if skills else [],
            "social_links": json.loads(social_links) if social_links else None,
        }
    else:
        raise HTTPException(status_code=400, detail="No data provided")

    # Validate required fields
    if not teacher_data.get("name"):
        raise HTTPException(status_code=400, detail="Name is required")
    if not teacher_data.get("email_id"):
        raise HTTPException(status_code=400, detail="Email is required")
    if not teacher_data.get("password"):
        raise HTTPException(status_code=400, detail="Password is required")

    # Validate using Pydantic model
    try:
        teacher_obj = TeacherCreate(**teacher_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Check if email already exists
    existing = db.teachers.find_one({"email_id": teacher_obj.email_id})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create teacher document
    doc = teacher_obj.model_dump(exclude={"password"})
    doc["uuid_id"] = str(uuid4())
    doc["hashed_password"] = get_password_hash(teacher_obj.password)
    doc["admin_uuid_id"] = identity["user_uuid"]
    doc["avatar_url"] = None
    doc["avatar_file_key"] = None

    # Upload avatar if provided
    if avatar:
        storage = get_s3_storage()

        # Validate file type
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
        if avatar.content_type and avatar.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Only image files (JPEG, PNG, GIF, WebP) are allowed for avatar"
            )

        # Upload to S3
        safe_name = os.path.basename(avatar.filename or "avatar.jpg")
        storage_key, size, mime, s3_url = await storage.upload_file(
            avatar,
            folder="teachers/avatars",
            custom_filename=f"{doc['uuid_id']}/{safe_name}"
        )

        doc["avatar_url"] = s3_url
        doc["avatar_file_key"] = storage_key

    db.teachers.insert_one(doc)
    return TeacherResponse(**doc)


@router.get("/", response_model=List[TeacherResponse])
async def list_teachers():
    db = get_database()
    return list(db.teachers.find({}, {"_id": 0, "hashed_password": 0}))


@router.get("/{uuid_id}", response_model=TeacherResponse)
async def get_teacher(uuid_id: str):
    db = get_database()
    t = db.teachers.find_one({"uuid_id": uuid_id}, {"_id": 0, "hashed_password": 0})
    if not t:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return TeacherResponse(**t)


@router.put("/{uuid_id}", response_model=TeacherResponse)
async def update_teacher(
    uuid_id: str,
    request: Request,
    teacher: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    email_id: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    skills: Optional[str] = Form(None),  # JSON string
    social_links: Optional[str] = Form(None),  # JSON string
    avatar: Optional[UploadFile] = File(None),
    identity = Depends(require_admin)
):
    """
    Update teacher with optional avatar upload to S3.
    Accepts both JSON (application/json) and multipart/form-data.
    """
    db = get_database()
    existing = db.teachers.find_one({"uuid_id": uuid_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # Check if this is a JSON request
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        # Handle JSON request
        body = await request.json()
        update_data = body
    elif teacher:
        # Multipart with JSON string in 'teacher' field
        update_data = json.loads(teacher)
    else:
        # Multipart with individual fields
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if email_id is not None:
            update_data["email_id"] = email_id
        if password is not None:
            update_data["password"] = password
        if bio is not None:
            update_data["bio"] = bio
        if skills is not None:
            update_data["skills"] = json.loads(skills)
        if social_links is not None:
            update_data["social_links"] = json.loads(social_links)

    # Validate using Pydantic model
    try:
        update_obj = TeacherUpdate(**update_data)
        data = update_obj.model_dump(exclude_unset=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Handle password update
    if "password" in data:
        data["hashed_password"] = get_password_hash(data.pop("password"))

    # Check email uniqueness
    if "email_id" in data:
        conflict = db.teachers.find_one({"email_id": data["email_id"], "uuid_id": {"$ne": uuid_id}})
        if conflict:
            raise HTTPException(status_code=400, detail="Email already registered")

    # Upload avatar if provided
    if avatar:
        storage = get_s3_storage()

        # Validate file type
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
        if avatar.content_type and avatar.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Only image files (JPEG, PNG, GIF, WebP) are allowed for avatar"
            )

        # Delete old avatar if exists
        if existing.get("avatar_file_key"):
            storage.delete_file(existing["avatar_file_key"])

        # Upload new avatar to S3
        safe_name = os.path.basename(avatar.filename or "avatar.jpg")
        storage_key, size, mime, s3_url = await storage.upload_file(
            avatar,
            folder="teachers/avatars",
            custom_filename=f"{uuid_id}/{safe_name}"
        )

        data["avatar_url"] = s3_url
        data["avatar_file_key"] = storage_key

    # Update database
    if data:
        db.teachers.update_one({"uuid_id": uuid_id}, {"$set": data})

    doc = db.teachers.find_one({"uuid_id": uuid_id}, {"_id": 0, "hashed_password": 0})
    return TeacherResponse(**doc)


@router.delete("/{uuid_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_teacher(uuid_id: str, identity = Depends(require_admin)):
    db = get_database()

    # Get teacher record
    teacher = db.teachers.find_one({"uuid_id": uuid_id})
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # Prevent deletion if teacher is instructor
    owns = db.courses.find_one({"instructor_uuid": uuid_id}) or db.courses.find_one({"co_instructor_uuids": uuid_id})
    if owns:
        raise HTTPException(status_code=400, detail="Teacher assigned to a course")

    # Delete avatar from S3 if exists
    if teacher.get("avatar_file_key"):
        storage = get_s3_storage()
        storage.delete_file(teacher["avatar_file_key"])

    # Delete teacher record
    db.teachers.delete_one({"uuid_id": uuid_id})
    return None
