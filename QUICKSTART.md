# Quick Start Guide

## Prerequisites
- Python 3.8 or higher installed
- MongoDB Atlas account (already configured)

## Installation Steps

### 1. Install Dependencies

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Your `.env` file is already configured with MongoDB Atlas connection.

**Database:** online_course_db
**Connection:** MongoDB Atlas Cloud

### 3. Start the Server

**Option 1 - Using the run script (Windows):**
```bash
run.bat
```

**Option 2 - Using uvicorn directly:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Option 3 - Using Python:**
```bash
python main.py
```

### 4. Access the API

- **API Base URL:** http://localhost:8000
- **Interactive Docs (Swagger):** http://localhost:8000/docs
- **Alternative Docs (ReDoc):** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## Testing the API

### Method 1: Using Swagger UI (Easiest)
1. Go to http://localhost:8000/docs
2. Click on any endpoint
3. Click "Try it out"
4. Fill in the request body
5. Click "Execute"

### Method 2: Using the Test Script
```bash
pip install requests
python test_api.py
```

### Method 3: Using Postman
1. Import `postman_collection.json` into Postman
2. Use the pre-configured requests

### Method 4: Using cURL

**Create Admin:**
```bash
curl -X POST "http://localhost:8000/admin/" -H "Content-Type: application/json" -d "{\"college_name\":\"Test College\",\"email_id\":\"admin@test.com\",\"password\":\"admin123\",\"total_student_allow_count\":50}"
```

**Admin Login:**
```bash
curl -X POST "http://localhost:8000/auth/login" -H "Content-Type: application/json" -d "{\"email_id\":\"admin@test.com\",\"password\":\"admin123\",\"role\":\"admin\"}"
```

**Create Student:**
```bash
curl -X POST "http://localhost:8000/student/" -H "Content-Type: application/json" -d "{\"student_name\":\"John Doe\",\"department\":\"CS\",\"email_id\":\"john@test.com\",\"password\":\"student123\",\"sub_department\":\"AI\"}"
```

**Student Login:**
```bash
curl -X POST "http://localhost:8000/auth/login" -H "Content-Type: application/json" -d "{\"email_id\":\"john@test.com\",\"password\":\"student123\",\"role\":\"student\"}"
```

## API Endpoints Summary

### Authentication
- `POST /auth/login` - Role-based login (admin/student)

### Admin Management
- `POST /admin/` - Create admin
- `GET /admin/` - Get all admins
- `GET /admin/{uuid_id}` - Get specific admin
- `PUT /admin/{uuid_id}` - Update admin
- `DELETE /admin/{uuid_id}` - Delete admin

### Student Management
- `POST /student/` - Create student
- `GET /student/` - Get all students
- `GET /student/{uuid_id}` - Get specific student
- `PUT /student/{uuid_id}` - Update student
- `DELETE /student/{uuid_id}` - Delete student

## Example Request/Response

### Create Admin
**Request:**
```json
POST /admin/
{
  "college_name": "ABC University",
  "email_id": "admin@abc.edu",
  "password": "securepass123",
  "total_student_allow_count": 100
}
```

**Response:**
```json
{
  "college_name": "ABC University",
  "email_id": "admin@abc.edu",
  "total_student_allow_count": 100,
  "uuid_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Login
**Request:**
```json
POST /auth/login
{
  "email_id": "admin@abc.edu",
  "password": "securepass123",
  "role": "admin"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role": "admin",
  "user_data": {
    "uuid_id": "550e8400-e29b-41d4-a716-446655440000",
    "email_id": "admin@abc.edu",
    "college_name": "ABC University",
    "total_student_allow_count": 100
  }
}
```

## Database Collections

Your MongoDB Atlas database will have two collections:

1. **admins** - Stores admin information
2. **students** - Stores student information

## Troubleshooting

### Port Already in Use
If port 8000 is busy, change the port:
```bash
uvicorn main:app --reload --port 8001
```

### MongoDB Connection Error
- Check your internet connection
- Verify MongoDB Atlas credentials
- Ensure your IP is whitelisted in MongoDB Atlas

### Import Errors
```bash
pip install -r requirements.txt --upgrade
```

## Security Notes

**IMPORTANT:** Your `.env` file contains sensitive credentials. Make sure:
- Never commit `.env` to version control
- Change the SECRET_KEY in production
- Use environment-specific configurations

## Next Steps

1. Test the API using Swagger UI at http://localhost:8000/docs
2. Create an admin account
3. Create student accounts
4. Test the login functionality
5. Explore all CRUD operations

For detailed documentation, see `README.md`
