# Online Course Management API

FastAPI backend for managing online courses with MongoDB, featuring admin and student management with role-based authentication.

## Features

- Role-based authentication (Admin & Student)
- Complete CRUD operations for Admin and Student
- JWT token-based authentication
- MongoDB database
- Password hashing with bcrypt
- Email validation
- RESTful API design

## Project Structure

```
backend_css/
├── config/
│   ├── __init__.py
│   └── database.py          # MongoDB connection
├── models/
│   ├── __init__.py
│   ├── admin.py             # Admin models
│   ├── student.py           # Student models
│   └── auth.py              # Authentication models
├── routes/
│   ├── __init__.py
│   ├── admin.py             # Admin CRUD endpoints
│   ├── student.py           # Student CRUD endpoints
│   └── auth.py              # Login endpoint
├── utils/
│   ├── __init__.py
│   └── security.py          # Password & JWT utilities
├── main.py                  # FastAPI application
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
└── README.md
```

## Setup Instructions

### 1. Install MongoDB

Make sure MongoDB is installed and running on your system.

**Windows:**
- Download from https://www.mongodb.com/try/download/community
- Install and start MongoDB service

**Linux/Mac:**
```bash
# Install MongoDB
sudo apt-get install mongodb  # Ubuntu/Debian

# Start MongoDB
sudo systemctl start mongodb
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=online_course_db
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 5. Run the Application

```bash
# Using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using Python
python main.py
```

The API will be available at: http://localhost:8000

API Documentation: http://localhost:8000/docs

## API Endpoints

### Authentication

#### Login (Auto role detection + device session)
```http
POST /auth/login
Content-Type: application/json
X-Device-Name: My Laptop  # optional label

{
  "email_id": "admin@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "role": "admin",
  "user_data": {
    "uuid_id": "123e4567-e89b-12d3-a456-426614174000",
    "email_id": "admin@example.com",
    "college_name": "ABC College",
    "total_student_allow_count": 100
  }
}
```

### Device Sessions

- Tracks per-device sessions and limits to max 5 devices (configurable).
- If limit is exceeded, the oldest active session is automatically revoked (logged out).
- Optional single-session mode revokes all other sessions on login.

Endpoints (require `Authorization: Bearer <token>`):
- `GET /auth/sessions` — list active sessions for the logged-in user.
- `POST /auth/logout` — logout current session.
- `POST /auth/logout-all` — logout all sessions for the user.

### Admin Endpoints

#### Create Admin
```http
POST /admin/
Content-Type: application/json

{
  "college_name": "ABC College",
  "email_id": "admin@example.com",
  "password": "password123",
  "total_student_allow_count": 100
}
```

#### Get All Admins
```http
GET /admin/
```

#### Get Admin by UUID
```http
GET /admin/{uuid_id}
```

#### Update Admin
```http
PUT /admin/{uuid_id}
Content-Type: application/json

{
  "college_name": "Updated College Name",
  "total_student_allow_count": 150
}
```

#### Delete Admin
```http
DELETE /admin/{uuid_id}
```

### Student Endpoints

#### Create Student
```http
POST /student/
Content-Type: application/json

{
  "student_name": "John Doe",
  "department": "Computer Science",
  "email_id": "john@example.com",
  "password": "password123",
  "sub_department": "AI & ML"  // optional
}
```

#### Get All Students
```http
GET /student/
```

#### Get Student by UUID
```http
GET /student/{uuid_id}
```

#### Update Student
```http
PUT /student/{uuid_id}
Content-Type: application/json

{
  "student_name": "John Updated",
  "department": "Computer Science",
  "sub_department": "Data Science"
}
```

#### Delete Student
```http
DELETE /student/{uuid_id}
```

## Database Schema

### Admin Collection
```json
{
  "uuid_id": "string",
  "college_name": "string",
  "email_id": "string",
  "hashed_password": "string",
  "total_student_allow_count": "integer",
  "role": "admin"
}
```

### Student Collection
```json
{
  "uuid_id": "string",
  "student_name": "string",
  "department": "string",
  "email_id": "string",
  "hashed_password": "string",
  "sub_department": "string (optional)",
  "role": "student"
}
```

### Sessions Collection
```json
{
  "session_id": "string",
  "user_uuid": "string",
  "role": "admin|student",
  "device_name": "string|null",
  "user_agent": "string|null",
  "ip_address": "string|null",
  "created_at": "datetime",
  "last_used_at": "datetime",
  "revoked": false
}
```

### Environment Variables
- `MAX_ACTIVE_DEVICES` (default 5) — max concurrent device sessions.
- `SINGLE_SESSION` (default false) — if true, new login revokes all other sessions.

## Testing with cURL

### Create Admin
```bash
curl -X POST "http://localhost:8000/admin/" \
  -H "Content-Type: application/json" \
  -d '{
    "college_name": "Test College",
    "email_id": "admin@test.com",
    "password": "admin123",
    "total_student_allow_count": 50
  }'
```

### Login as Admin
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email_id": "admin@test.com",
    "password": "admin123",
    "role": "admin"
  }'
```

### Create Student
```bash
curl -X POST "http://localhost:8000/student/" \
  -H "Content-Type: application/json" \
  -d '{
    "student_name": "John Doe",
    "department": "CS",
    "email_id": "john@test.com",
    "password": "student123",
    "sub_department": "AI"
  }'
```

## Security Features

- Password hashing using bcrypt
- JWT token-based authentication
- Email validation
- UUID for unique identification
- Environment-based configuration
- CORS middleware

## Development

### Access Interactive API Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### MongoDB Indexes (Optional)

For better performance, create indexes:

```javascript
// Connect to MongoDB
use online_course_db

// Create indexes
db.admins.createIndex({ "email_id": 1 }, { unique: true })
db.admins.createIndex({ "uuid_id": 1 }, { unique: true })

db.students.createIndex({ "email_id": 1 }, { unique: true })
db.students.createIndex({ "uuid_id": 1 }, { unique: true })
```

## Error Handling

The API returns standard HTTP status codes:

- `200` - Success
- `201` - Created
- `204` - No Content (successful deletion)
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `500` - Internal Server Error

## Future Enhancements

- Add role-based middleware for protected routes
- Implement refresh tokens
- Add pagination for list endpoints
- Add course management features
- Add enrollment system
- Add file upload for profile pictures
- Add email verification
- Add password reset functionality

## License

MIT License
