from datetime import datetime
from typing import List
from config.database import get_database


def auto_assign_courses_to_student(student_uuid: str, department: str, sub_department: str = None) -> List[str]:
    """
    Automatically assign courses to a student based on their department.

    Args:
        student_uuid: The UUID of the student
        department: The student's department
        sub_department: The student's sub-department (optional)

    Returns:
        List of assigned course UUIDs
    """
    db = get_database()

    # Find courses that match the department and have auto_assign enabled
    query = {
        "departments": department,
        "auto_assign": True
    }

    courses = list(db.courses.find(query))
    assigned_course_uuids = []

    for course in courses:
        course_uuid = course["uuid_id"]

        # Check if already assigned
        existing = db.user_courses.find_one({
            "student_uuid": student_uuid,
            "course_uuid": course_uuid
        })

        if not existing:
            # Create new assignment
            assignment_doc = {
                "uuid_id": str(__import__("uuid").uuid4()),
                "student_uuid": student_uuid,
                "course_uuid": course_uuid,
                "assigned_by_role": "system",
                "assigned_by_uuid": "auto-assign",
                "assigned_at": datetime.utcnow(),
                "status": "active",
            }
            db.user_courses.insert_one(assignment_doc)
            assigned_course_uuids.append(course_uuid)
        elif existing.get("status") == "revoked":
            # Re-activate revoked assignment
            db.user_courses.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "status": "active",
                        "assigned_at": datetime.utcnow(),
                        "assigned_by_role": "system",
                        "assigned_by_uuid": "auto-assign"
                    }
                }
            )
            assigned_course_uuids.append(course_uuid)

    return assigned_course_uuids


def get_available_courses_for_student(student_uuid: str) -> List[dict]:
    """
    Get all courses available for a student based on their department.
    This includes both assigned and unassigned courses.

    Args:
        student_uuid: The UUID of the student

    Returns:
        List of course documents with assignment status
    """
    db = get_database()

    # Get student info
    student = db.students.find_one({"uuid_id": student_uuid})
    if not student:
        return []

    department = student.get("department")
    if not department:
        return []

    # Find all courses for this department
    courses = list(db.courses.find(
        {"departments": department},
        {"_id": 0}
    ).sort("title", 1))

    # Get student's assignments
    assignments = list(db.user_courses.find({
        "student_uuid": student_uuid,
        "status": "active"
    }))

    assigned_course_uuids = {a["course_uuid"] for a in assignments}

    # Add assignment status to each course
    for course in courses:
        course["is_assigned"] = course["uuid_id"] in assigned_course_uuids

    return courses


def auto_assign_existing_students_to_course(course_uuid: str, departments: List[str]) -> int:
    """
    When a course is created or updated with auto_assign=True,
    automatically assign it to all existing students in matching departments.

    Args:
        course_uuid: The UUID of the course
        departments: List of departments this course is for

    Returns:
        Number of students assigned
    """
    db = get_database()

    # Find all students in matching departments
    students = list(db.students.find({"department": {"$in": departments}}))

    assigned_count = 0

    for student in students:
        student_uuid = student["uuid_id"]

        # Check if already assigned
        existing = db.user_courses.find_one({
            "student_uuid": student_uuid,
            "course_uuid": course_uuid
        })

        if not existing:
            # Create new assignment
            assignment_doc = {
                "uuid_id": str(__import__("uuid").uuid4()),
                "student_uuid": student_uuid,
                "course_uuid": course_uuid,
                "assigned_by_role": "system",
                "assigned_by_uuid": "auto-assign",
                "assigned_at": datetime.utcnow(),
                "status": "active",
            }
            db.user_courses.insert_one(assignment_doc)
            assigned_count += 1
        elif existing.get("status") == "revoked":
            # Re-activate revoked assignment
            db.user_courses.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "status": "active",
                        "assigned_at": datetime.utcnow(),
                        "assigned_by_role": "system",
                        "assigned_by_uuid": "auto-assign"
                    }
                }
            )
            assigned_count += 1

    return assigned_count
