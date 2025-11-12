from fastapi import APIRouter, HTTPException, status
from typing import List
from uuid import uuid4

from models.admin import AdminCreate, AdminUpdate, AdminResponse
from config.database import get_database
from utils.security import get_password_hash

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(admin: AdminCreate):
    """Create a new admin"""
    db = get_database()

    # Check if email already exists
    existing_admin = db.admins.find_one({"email_id": admin.email_id})
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create admin document
    admin_dict = admin.model_dump(exclude={"password"})
    admin_dict["uuid_id"] = str(uuid4())
    admin_dict["hashed_password"] = get_password_hash(admin.password)
    admin_dict["role"] = "admin"

    # Insert into database
    result = db.admins.insert_one(admin_dict)

    if result.inserted_id:
        return AdminResponse(**admin_dict)

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to create admin"
    )

@router.get("/", response_model=List[AdminResponse])
async def get_all_admins():
    """Get all admins"""
    db = get_database()
    admins = list(db.admins.find({}, {"_id": 0, "hashed_password": 0}))
    return admins

@router.get("/{uuid_id}", response_model=AdminResponse)
async def get_admin(uuid_id: str):
    """Get admin by UUID"""
    db = get_database()
    admin = db.admins.find_one(
        {"uuid_id": uuid_id},
        {"_id": 0, "hashed_password": 0}
    )

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )

    return AdminResponse(**admin)

@router.put("/{uuid_id}", response_model=AdminResponse)
async def update_admin(uuid_id: str, admin_update: AdminUpdate):
    """Update admin by UUID"""
    db = get_database()

    # Check if admin exists
    existing_admin = db.admins.find_one({"uuid_id": uuid_id})
    if not existing_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )

    # Prepare update data
    update_data = admin_update.model_dump(exclude_unset=True)

    # Hash password if provided
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    # Check if email is being updated and already exists
    if "email_id" in update_data:
        email_exists = db.admins.find_one({
            "email_id": update_data["email_id"],
            "uuid_id": {"$ne": uuid_id}
        })
        if email_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # Update admin
    if update_data:
        db.admins.update_one(
            {"uuid_id": uuid_id},
            {"$set": update_data}
        )

    # Get updated admin
    updated_admin = db.admins.find_one(
        {"uuid_id": uuid_id},
        {"_id": 0, "hashed_password": 0}
    )

    return AdminResponse(**updated_admin)

@router.delete("/{uuid_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin(uuid_id: str):
    """Delete admin by UUID"""
    db = get_database()

    result = db.admins.delete_one({"uuid_id": uuid_id})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )

    return None
