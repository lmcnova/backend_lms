from fastapi import APIRouter, HTTPException, status
from typing import List
from uuid import uuid4

from models.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from config.database import get_database


router = APIRouter(prefix="/departments", tags=["Departments"])


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(department: DepartmentCreate):
    """Create a new department"""
    db = get_database()

    # Check if admin exists
    admin_exists = db.admins.find_one({"uuid_id": department.admin_uuid_id})
    if not admin_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Admin with UUID {department.admin_uuid_id} does not exist"
        )

    # Check if department code already exists
    existing_code = db.departments.find_one({"code": department.code})
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department code already exists"
        )

    # Check if department name already exists
    existing_name = db.departments.find_one({"name": department.name})
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department name already exists"
        )

    # Create department document
    department_dict = department.model_dump()
    department_dict["uuid_id"] = str(uuid4())

    # Insert into database
    result = db.departments.insert_one(department_dict)

    if result.inserted_id:
        return DepartmentResponse(**department_dict)

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to create department"
    )


@router.get("/", response_model=List[DepartmentResponse])
async def get_all_departments():
    """Get all departments"""
    db = get_database()
    departments = list(db.departments.find({}, {"_id": 0}))
    return departments


@router.get("/{uuid_id}", response_model=DepartmentResponse)
async def get_department(uuid_id: str):
    """Get department by UUID"""
    db = get_database()
    department = db.departments.find_one(
        {"uuid_id": uuid_id},
        {"_id": 0}
    )

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    return DepartmentResponse(**department)


@router.put("/{uuid_id}", response_model=DepartmentResponse)
async def update_department(uuid_id: str, department_update: DepartmentUpdate):
    """Update department by UUID"""
    db = get_database()

    # Check if department exists
    existing_department = db.departments.find_one({"uuid_id": uuid_id})
    if not existing_department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    # Prepare update data
    update_data = department_update.model_dump(exclude_unset=True)

    # Validate admin_uuid_id if provided
    if "admin_uuid_id" in update_data:
        admin_exists = db.admins.find_one({"uuid_id": update_data["admin_uuid_id"]})
        if not admin_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Admin with UUID {update_data['admin_uuid_id']} does not exist"
            )

    # Check if code is being updated and already exists
    if "code" in update_data:
        code_exists = db.departments.find_one({
            "code": update_data["code"],
            "uuid_id": {"$ne": uuid_id}
        })
        if code_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department code already exists"
            )

    # Check if name is being updated and already exists
    if "name" in update_data:
        name_exists = db.departments.find_one({
            "name": update_data["name"],
            "uuid_id": {"$ne": uuid_id}
        })
        if name_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department name already exists"
            )

    # Update department
    if update_data:
        db.departments.update_one(
            {"uuid_id": uuid_id},
            {"$set": update_data}
        )

    # Get updated department
    updated_department = db.departments.find_one(
        {"uuid_id": uuid_id},
        {"_id": 0}
    )

    return DepartmentResponse(**updated_department)


@router.delete("/{uuid_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(uuid_id: str):
    """Delete department by UUID"""
    db = get_database()

    # Check if department has students
    students_count = db.students.count_documents({"department": {"$exists": True}})
    if students_count > 0:
        # Get department name to check
        dept = db.departments.find_one({"uuid_id": uuid_id})
        if dept:
            students_in_dept = db.students.count_documents({"department": dept["name"]})
            if students_in_dept > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot delete department with {students_in_dept} students. Reassign students first."
                )

    result = db.departments.delete_one({"uuid_id": uuid_id})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    return None
