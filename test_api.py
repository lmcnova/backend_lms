"""
Test script for Online Course Management API
Run this after starting the FastAPI server
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def print_response(response, title):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def test_health_check():
    """Test health check endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print_response(response, "Health Check")
    return response.status_code == 200

def test_create_admin():
    """Test creating an admin"""
    admin_data = {
        "college_name": "Test University",
        "email_id": "admin@test.com",
        "password": "admin123456",
        "total_student_allow_count": 100
    }
    response = requests.post(f"{BASE_URL}/admin/", json=admin_data)
    print_response(response, "Create Admin")
    if response.status_code == 201:
        return response.json()["uuid_id"]
    return None

def test_get_all_admins():
    """Test getting all admins"""
    response = requests.get(f"{BASE_URL}/admin/")
    print_response(response, "Get All Admins")

def test_get_admin(uuid_id):
    """Test getting specific admin"""
    response = requests.get(f"{BASE_URL}/admin/{uuid_id}")
    print_response(response, f"Get Admin {uuid_id}")

def test_update_admin(uuid_id):
    """Test updating admin"""
    update_data = {
        "college_name": "Updated University Name",
        "total_student_allow_count": 150
    }
    response = requests.put(f"{BASE_URL}/admin/{uuid_id}", json=update_data)
    print_response(response, f"Update Admin {uuid_id}")

def test_admin_login():
    """Test admin login"""
    login_data = {
        "email_id": "admin@test.com",
        "password": "admin123456"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print_response(response, "Admin Login")
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_create_student():
    """Test creating a student"""
    student_data = {
        "student_name": "John Doe",
        "department": "Computer Science",
        "email_id": "john@test.com",
        "password": "student123456",
        "sub_department": "Artificial Intelligence"
    }
    response = requests.post(f"{BASE_URL}/student/", json=student_data)
    print_response(response, "Create Student")
    if response.status_code == 201:
        return response.json()["uuid_id"]
    return None

def test_get_all_students():
    """Test getting all students"""
    response = requests.get(f"{BASE_URL}/student/")
    print_response(response, "Get All Students")

def test_get_student(uuid_id):
    """Test getting specific student"""
    response = requests.get(f"{BASE_URL}/student/{uuid_id}")
    print_response(response, f"Get Student {uuid_id}")

def test_update_student(uuid_id):
    """Test updating student"""
    update_data = {
        "student_name": "John Doe Updated",
        "sub_department": "Machine Learning"
    }
    response = requests.put(f"{BASE_URL}/student/{uuid_id}", json=update_data)
    print_response(response, f"Update Student {uuid_id}")

def test_student_login():
    """Test student login"""
    login_data = {
        "email_id": "john@test.com",
        "password": "student123456"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print_response(response, "Student Login")
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_list_sessions(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/auth/sessions", headers=headers)
    print_response(response, "List Sessions")

def test_logout_current(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
    print_response(response, "Logout Current")

def test_delete_admin(uuid_id):
    """Test deleting admin"""
    response = requests.delete(f"{BASE_URL}/admin/{uuid_id}")
    print_response(response, f"Delete Admin {uuid_id}")

def test_delete_student(uuid_id):
    """Test deleting student"""
    response = requests.delete(f"{BASE_URL}/student/{uuid_id}")
    print_response(response, f"Delete Student {uuid_id}")

def run_all_tests():
    """Run all tests in sequence"""
    print("\n" + "="*60)
    print("Starting API Tests")
    print("="*60)
    print("\nMake sure the FastAPI server is running on http://localhost:8000")
    print("Press Enter to continue or Ctrl+C to cancel...")
    input()

    try:
        # Test health check
        if not test_health_check():
            print("\nHealth check failed! Make sure the server is running.")
            return

        # Test Admin Flow
        print("\n" + "#"*60)
        print("# ADMIN TESTS")
        print("#"*60)

        admin_uuid = test_create_admin()
        if admin_uuid:
            test_get_all_admins()
            test_get_admin(admin_uuid)
            test_update_admin(admin_uuid)
            test_get_admin(admin_uuid)  # Check updated data
            admin_token = test_admin_login()
            if admin_token:
                test_list_sessions(admin_token)

        # Test Student Flow
        print("\n" + "#"*60)
        print("# STUDENT TESTS")
        print("#"*60)

        student_uuid = test_create_student()
        if student_uuid:
            test_get_all_students()
            test_get_student(student_uuid)
            test_update_student(student_uuid)
            test_get_student(student_uuid)  # Check updated data
            student_token = test_student_login()
            if student_token:
                test_list_sessions(student_token)

        # Cleanup (optional - uncomment to delete test data)
        # print("\n" + "#"*60)
        # print("# CLEANUP")
        # print("#"*60)
        # if student_uuid:
        #     test_delete_student(student_uuid)
        # if admin_uuid:
        #     test_delete_admin(admin_uuid)

        print("\n" + "="*60)
        print("All tests completed!")
        print("="*60)

    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the API.")
        print("Make sure the FastAPI server is running on http://localhost:8000")
    except KeyboardInterrupt:
        print("\n\nTests cancelled by user.")
    except Exception as e:
        print(f"\nError during testing: {e}")

if __name__ == "__main__":
    run_all_tests()
