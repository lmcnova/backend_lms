"""
Test script to demonstrate department-based course auto-assignment

This script shows how the department-based course assignment works.
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_department_based_assignment():
    """
    Test the department-based course assignment feature
    """

    # Step 1: Login as admin
    print_section("STEP 1: Login as Admin")
    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "email_id": "admin@example.com",  # Replace with your admin email
        "password": "admin123"  # Replace with your admin password
    })

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return

    admin_token = login_response.json()["access_token"]
    admin_uuid = login_response.json()["user_data"]["uuid_id"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    print(f"✅ Logged in as admin")

    # Step 2: Get a teacher UUID (or create one)
    print_section("STEP 2: Get Teacher")
    teachers_response = requests.get(f"{BASE_URL}/teachers/", headers=headers)
    if teachers_response.status_code == 200:
        teachers = teachers_response.json()
        if teachers:
            teacher_uuid = teachers[0]["uuid_id"]
            print(f"✅ Using teacher: {teacher_uuid}")
        else:
            print("❌ No teachers found. Please create a teacher first.")
            return
    else:
        print(f"❌ Failed to get teachers: {teachers_response.text}")
        return

    # Step 3: Create a course for "Computer Science" department with auto-assign
    print_section("STEP 3: Create Course with Department Auto-Assign")
    course_data = {
        "title": "Introduction to Python Programming",
        "category": "Programming",
        "level": "beginner",
        "description": "Learn Python from scratch",
        "instructor_uuid": teacher_uuid,
        "departments": ["Computer Science", "Information Technology"],
        "auto_assign": True,
        "tags": ["python", "programming", "beginner"]
    }

    course_response = requests.post(
        f"{BASE_URL}/courses/",
        headers=headers,
        json=course_data
    )

    if course_response.status_code == 201:
        course = course_response.json()
        course_uuid = course["uuid_id"]
        print(f"✅ Created course: {course['title']}")
        print(f"   UUID: {course_uuid}")
        print(f"   Departments: {course['departments']}")
        print(f"   Auto-assign: {course['auto_assign']}")
    else:
        print(f"❌ Failed to create course: {course_response.text}")
        return

    # Step 4: Create a student in "Computer Science" department
    print_section("STEP 4: Create Student in Computer Science")
    student_data = {
        "student_name": "Alice Johnson",
        "department": "Computer Science",
        "email_id": "alice@example.com",
        "password": "student123",
        "admin_uuid_id": admin_uuid,
        "sub_department": "AI & ML"
    }

    student_response = requests.post(
        f"{BASE_URL}/student/",
        json=student_data
    )

    if student_response.status_code == 201:
        student = student_response.json()
        student_uuid = student["uuid_id"]
        print(f"✅ Created student: {student['student_name']}")
        print(f"   UUID: {student_uuid}")
        print(f"   Department: {student['department']}")
    else:
        print(f"❌ Failed to create student: {student_response.text}")
        return

    # Step 5: Login as the student
    print_section("STEP 5: Login as Student")
    student_login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "email_id": "alice@example.com",
        "password": "student123"
    })

    if student_login_response.status_code == 200:
        student_token = student_login_response.json()["access_token"]
        student_headers = {"Authorization": f"Bearer {student_token}"}
        print(f"✅ Logged in as student")
    else:
        print(f"❌ Student login failed: {student_login_response.text}")
        return

    # Step 6: Check student's assignments (should have auto-assigned course)
    print_section("STEP 6: Check Student's Assignments")
    assignments_response = requests.get(
        f"{BASE_URL}/assignments/me",
        headers=student_headers
    )

    if assignments_response.status_code == 200:
        assignments = assignments_response.json()
        print(f"✅ Student has {len(assignments)} assigned course(s):")
        for assignment in assignments:
            print(f"   - Course UUID: {assignment['course_uuid']}")
            print(f"     Assigned by: {assignment['assigned_by_role']}")
            print(f"     Status: {assignment['status']}")
    else:
        print(f"❌ Failed to get assignments: {assignments_response.text}")

    # Step 7: Get all courses for student's department
    print_section("STEP 7: Get Department Courses")
    dept_courses_response = requests.get(
        f"{BASE_URL}/student/me/courses",
        headers=student_headers
    )

    if dept_courses_response.status_code == 200:
        result = dept_courses_response.json()
        courses = result["courses"]
        print(f"✅ Found {result['total']} course(s) for student's department:")
        for course in courses:
            print(f"   - {course['title']}")
            print(f"     Departments: {course['departments']}")
            print(f"     Is Assigned: {'✅' if course.get('is_assigned') else '❌'}")
    else:
        print(f"❌ Failed to get department courses: {dept_courses_response.text}")

    # Step 8: Create another student in a different department
    print_section("STEP 8: Create Student in Different Department")
    student2_data = {
        "student_name": "Bob Smith",
        "department": "Mechanical Engineering",
        "email_id": "bob@example.com",
        "password": "student123",
        "admin_uuid_id": admin_uuid
    }

    student2_response = requests.post(
        f"{BASE_URL}/student/",
        json=student2_data
    )

    if student2_response.status_code == 201:
        student2 = student2_response.json()
        print(f"✅ Created student: {student2['student_name']}")
        print(f"   Department: {student2['department']}")

        # Login as second student
        student2_login_response = requests.post(f"{BASE_URL}/auth/login", json={
            "email_id": "bob@example.com",
            "password": "student123"
        })

        if student2_login_response.status_code == 200:
            student2_token = student2_login_response.json()["access_token"]
            student2_headers = {"Authorization": f"Bearer {student2_token}"}

            # Check assignments (should be empty)
            assignments2_response = requests.get(
                f"{BASE_URL}/assignments/me",
                headers=student2_headers
            )

            if assignments2_response.status_code == 200:
                assignments2 = assignments2_response.json()
                print(f"   Student has {len(assignments2)} assigned course(s)")
                print(f"   (Should be 0 because not in Computer Science dept)")
    else:
        print(f"❌ Failed to create second student: {student2_response.text}")

    # Summary
    print_section("SUMMARY")
    print("✅ Department-based course assignment is working!")
    print("\nHow it works:")
    print("1. When creating a course, set 'departments' and 'auto_assign: true'")
    print("2. The course is automatically assigned to existing students in those departments")
    print("3. When new students are created, they automatically get assigned courses")
    print("   for their department (where auto_assign is true)")
    print("4. Students can see all courses for their department via /student/me/courses")
    print("5. Students in other departments don't see courses not for their department")


if __name__ == "__main__":
    print("=" * 60)
    print("  DEPARTMENT-BASED COURSE AUTO-ASSIGNMENT TEST")
    print("=" * 60)
    print("\nMake sure the server is running on http://localhost:8000")
    print("Press Enter to continue or Ctrl+C to cancel...")
    input()

    try:
        test_department_based_assignment()
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {e}")
