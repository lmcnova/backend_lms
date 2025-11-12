"""
Test script to verify student-admin foreign key relationship
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_student_admin_relationship():
    print("=" * 60)
    print("Testing Student-Admin Foreign Key Relationship")
    print("=" * 60)

    # Step 1: Create an admin first
    print("\n1. Creating an admin...")
    admin_data = {
        "college_name": "Test University",
        "email_id": "admin@testuniversity.edu",
        "total_student_allow_count": 100,
        "password": "admin123"
    }

    response = requests.post(f"{BASE_URL}/admin/", json=admin_data)

    if response.status_code == 201:
        admin = response.json()
        admin_uuid = admin["uuid_id"]
        print(f"✓ Admin created successfully!")
        print(f"  Admin UUID: {admin_uuid}")
        print(f"  College: {admin['college_name']}")
        print(f"  Email: {admin['email_id']}")
    else:
        print(f"✗ Failed to create admin: {response.status_code}")
        print(f"  Response: {response.text}")
        return

    # Step 2: Create a student with valid admin_uuid_id
    print("\n2. Creating a student with valid admin UUID...")
    student_data = {
        "student_name": "John Doe",
        "department": "Computer Science",
        "email_id": "john.doe@testuniversity.edu",
        "sub_department": "AI & ML",
        "admin_uuid_id": admin_uuid,
        "password": "student123"
    }

    response = requests.post(f"{BASE_URL}/student/", json=student_data)

    if response.status_code == 201:
        student = response.json()
        student_uuid = student["uuid_id"]
        print(f"✓ Student created successfully!")
        print(f"  Student UUID: {student_uuid}")
        print(f"  Name: {student['student_name']}")
        print(f"  Email: {student['email_id']}")
        print(f"  Admin UUID: {student['admin_uuid_id']}")
    else:
        print(f"✗ Failed to create student: {response.status_code}")
        print(f"  Response: {response.text}")
        return

    # Step 3: Try to create a student with invalid admin_uuid_id
    print("\n3. Testing foreign key constraint (invalid admin UUID)...")
    invalid_student_data = {
        "student_name": "Jane Smith",
        "department": "Mathematics",
        "email_id": "jane.smith@testuniversity.edu",
        "sub_department": "Pure Math",
        "admin_uuid_id": "00000000-0000-0000-0000-000000000000",  # Invalid UUID
        "password": "student456"
    }

    response = requests.post(f"{BASE_URL}/student/", json=invalid_student_data)

    if response.status_code == 400:
        print(f"✓ Foreign key validation working correctly!")
        print(f"  Error message: {response.json()['detail']}")
    else:
        print(f"✗ Foreign key validation failed!")
        print(f"  Expected 400, got: {response.status_code}")

    # Step 4: Get student details to verify admin_uuid_id is stored
    print(f"\n4. Retrieving student details...")
    response = requests.get(f"{BASE_URL}/student/{student_uuid}")

    if response.status_code == 200:
        student = response.json()
        print(f"✓ Student retrieved successfully!")
        print(f"  Student: {student['student_name']}")
        print(f"  Admin UUID: {student['admin_uuid_id']}")
        print(f"  Department: {student['department']}")
    else:
        print(f"✗ Failed to retrieve student: {response.status_code}")

    # Step 5: Update student with new admin_uuid_id
    print("\n5. Creating second admin for testing update...")
    admin_data_2 = {
        "college_name": "Second University",
        "email_id": "admin2@seconduniversity.edu",
        "total_student_allow_count": 50,
        "password": "admin456"
    }

    response = requests.post(f"{BASE_URL}/admin/", json=admin_data_2)

    if response.status_code == 201:
        admin2 = response.json()
        admin2_uuid = admin2["uuid_id"]
        print(f"✓ Second admin created!")
        print(f"  Admin UUID: {admin2_uuid}")

        # Update student with new admin
        print("\n6. Updating student with new admin UUID...")
        update_data = {
            "admin_uuid_id": admin2_uuid
        }

        response = requests.put(f"{BASE_URL}/student/{student_uuid}", json=update_data)

        if response.status_code == 200:
            updated_student = response.json()
            print(f"✓ Student updated successfully!")
            print(f"  New Admin UUID: {updated_student['admin_uuid_id']}")
        else:
            print(f"✗ Failed to update student: {response.status_code}")
            print(f"  Response: {response.text}")

    # Step 7: Try to update student with invalid admin_uuid_id
    print("\n7. Testing update with invalid admin UUID...")
    invalid_update_data = {
        "admin_uuid_id": "99999999-9999-9999-9999-999999999999"
    }

    response = requests.put(f"{BASE_URL}/student/{student_uuid}", json=invalid_update_data)

    if response.status_code == 400:
        print(f"✓ Update validation working correctly!")
        print(f"  Error message: {response.json()['detail']}")
    else:
        print(f"✗ Update validation failed!")
        print(f"  Expected 400, got: {response.status_code}")

    # Step 8: Get all students to see the foreign key field
    print("\n8. Retrieving all students...")
    response = requests.get(f"{BASE_URL}/student/")

    if response.status_code == 200:
        students = response.json()
        print(f"✓ Retrieved {len(students)} student(s)")
        for s in students:
            print(f"  - {s['student_name']} (Admin: {s['admin_uuid_id']})")

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_student_admin_relationship()
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to the API server.")
        print("  Please ensure the FastAPI server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
