from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form, Request
from typing import List, Optional
from uuid import uuid4
import json
import os

from models.student import StudentCreate, StudentUpdate, StudentResponse
from config.database import get_database
from utils.security import get_password_hash
from utils.auto_assign import auto_assign_courses_to_student, get_available_courses_for_student
from utils.dependencies import get_current_identity
from utils.s3_storage import get_s3_storage

router = APIRouter(prefix="/student", tags=["Student"])

@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    request: Request,
    student: Optional[str] = Form(None),
    student_name: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    email_id: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    sub_department: Optional[str] = Form(None),
    admin_uuid_id: Optional[str] = Form(None),
    avatar: Optional[UploadFile] = File(None)
):
    """
    Create a new student with optional avatar upload to S3.
    Accepts both JSON (application/json) and multipart/form-data.
    """
    db = get_database()

    # Check if this is a JSON request
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        # Handle JSON request
        body = await request.json()
        student_data = body
    elif student:
        # Multipart with JSON string in 'student' field
        student_data = json.loads(student)
    elif student_name or department or email_id:
        # Multipart with individual fields
        student_data = {
            "student_name": student_name,
            "department": department,
            "email_id": email_id,
            "password": password,
            "sub_department": sub_department,
            "admin_uuid_id": admin_uuid_id,
        }
    else:
        raise HTTPException(status_code=400, detail="No data provided")

    # Validate required fields
    if not student_data.get("student_name"):
        raise HTTPException(status_code=400, detail="Student name is required")
    if not student_data.get("department"):
        raise HTTPException(status_code=400, detail="Department is required")
    if not student_data.get("email_id"):
        raise HTTPException(status_code=400, detail="Email is required")
    if not student_data.get("password"):
        raise HTTPException(status_code=400, detail="Password is required")
    if not student_data.get("admin_uuid_id"):
        raise HTTPException(status_code=400, detail="Admin UUID is required")

    # Validate using Pydantic model
    try:
        student_obj = StudentCreate(**student_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Validate that the admin exists
    admin_exists = db.admins.find_one({"uuid_id": student_obj.admin_uuid_id})
    if not admin_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Admin with UUID {student_obj.admin_uuid_id} does not exist"
        )

    # Check if email already exists
    existing_student = db.students.find_one({"email_id": student_obj.email_id})
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create student document
    student_dict = student_obj.model_dump(exclude={"password"})
    student_dict["uuid_id"] = str(uuid4())
    student_dict["hashed_password"] = get_password_hash(student_obj.password)
    student_dict["role"] = "student"
    student_dict["avatar_url"] = None
    student_dict["avatar_file_key"] = None

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
            folder="students/avatars",
            custom_filename=f"{student_dict['uuid_id']}/{safe_name}"
        )

        student_dict["avatar_url"] = s3_url
        student_dict["avatar_file_key"] = storage_key

    # Insert into database
    result = db.students.insert_one(student_dict)

    if result.inserted_id:
        # Auto-assign courses based on department
        auto_assign_courses_to_student(
            student_dict["uuid_id"],
            student_dict["department"],
            student_dict.get("sub_department")
        )
        return StudentResponse(**student_dict)

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to create student"
    )

@router.get("/", response_model=List[StudentResponse])
async def get_all_students():
    """Get all students"""
    db = get_database()
    students = list(db.students.find({}, {"_id": 0, "hashed_password": 0}))
    return students

@router.get("/{uuid_id}", response_model=StudentResponse)
async def get_student(uuid_id: str):
    """Get student by UUID"""
    db = get_database()
    student = db.students.find_one(
        {"uuid_id": uuid_id},
        {"_id": 0, "hashed_password": 0}
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    return StudentResponse(**student)

@router.put("/{uuid_id}", response_model=StudentResponse)
async def update_student(
    uuid_id: str,
    request: Request,
    student: Optional[str] = Form(None),
    student_name: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    email_id: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    sub_department: Optional[str] = Form(None),
    admin_uuid_id: Optional[str] = Form(None),
    avatar: Optional[UploadFile] = File(None)
):
    """
    Update student with optional avatar upload to S3.
    Accepts both JSON (application/json) and multipart/form-data.
    """
    db = get_database()

    # Check if student exists
    existing_student = db.students.find_one({"uuid_id": uuid_id})
    if not existing_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    # Check if this is a JSON request
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        # Handle JSON request
        body = await request.json()
        update_data = body
    elif student:
        # Multipart with JSON string in 'student' field
        update_data = json.loads(student)
    else:
        # Multipart with individual fields
        update_data = {}
        if student_name is not None:
            update_data["student_name"] = student_name
        if department is not None:
            update_data["department"] = department
        if email_id is not None:
            update_data["email_id"] = email_id
        if password is not None:
            update_data["password"] = password
        if sub_department is not None:
            update_data["sub_department"] = sub_department
        if admin_uuid_id is not None:
            update_data["admin_uuid_id"] = admin_uuid_id

    # Validate using Pydantic model
    try:
        update_obj = StudentUpdate(**update_data)
        data = update_obj.model_dump(exclude_unset=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Validate admin_uuid_id if provided
    if "admin_uuid_id" in data:
        admin_exists = db.admins.find_one({"uuid_id": data["admin_uuid_id"]})
        if not admin_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Admin with UUID {data['admin_uuid_id']} does not exist"
            )

    # Hash password if provided
    if "password" in data:
        data["hashed_password"] = get_password_hash(data.pop("password"))

    # Check if email is being updated and already exists
    if "email_id" in data:
        email_exists = db.students.find_one({
            "email_id": data["email_id"],
            "uuid_id": {"$ne": uuid_id}
        })
        if email_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

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
        if existing_student.get("avatar_file_key"):
            storage.delete_file(existing_student["avatar_file_key"])

        # Upload new avatar to S3
        safe_name = os.path.basename(avatar.filename or "avatar.jpg")
        storage_key, size, mime, s3_url = await storage.upload_file(
            avatar,
            folder="students/avatars",
            custom_filename=f"{uuid_id}/{safe_name}"
        )

        data["avatar_url"] = s3_url
        data["avatar_file_key"] = storage_key

    # Update student
    if data:
        db.students.update_one(
            {"uuid_id": uuid_id},
            {"$set": data}
        )

    # Get updated student
    updated_student = db.students.find_one(
        {"uuid_id": uuid_id},
        {"_id": 0, "hashed_password": 0}
    )

    return StudentResponse(**updated_student)

@router.delete("/{uuid_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(uuid_id: str):
    """Delete student by UUID and cleanup avatar from S3"""
    db = get_database()

    # Get student record
    student = db.students.find_one({"uuid_id": uuid_id})
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    # Delete avatar from S3 if exists
    if student.get("avatar_file_key"):
        storage = get_s3_storage()
        storage.delete_file(student["avatar_file_key"])

    # Delete student record
    db.students.delete_one({"uuid_id": uuid_id})

    return None


@router.get("/me/courses")
async def get_my_department_courses(identity = Depends(get_current_identity)):
    """Get all courses available for the logged-in student's department"""
    if identity["role"] != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students only"
        )

    courses = get_available_courses_for_student(identity["user_uuid"])
    return {"courses": courses, "total": len(courses)}
