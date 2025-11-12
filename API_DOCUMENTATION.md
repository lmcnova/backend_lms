# Online Course Management API - Complete Documentation

**Version:** 1.0.0
**Base URL:** `http://localhost:8000`
**API Documentation:** `http://localhost:8000/docs`
**ReDoc:** `http://localhost:8000/redoc`

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Database Schema](#database-schema)
4. [API Endpoints](#api-endpoints)
   - [Root & Health](#root--health)
   - [Authentication](#authentication-endpoints)
   - [Admin Management](#admin-management)
   - [Department Management](#department-management)
   - [Student Management](#student-management)
   - [Teacher Management](#teacher-management)
   - [Course Management](#course-management)
   - [Topic Management](#topic-management)
   - [Video Management](#video-management)
   - [Comment Management](#comment-management)
   - [Assignment Management](#assignment-management)
   - [Progress Tracking](#progress-tracking)
   - [Certificate Management](#certificate-management)
   - [Media/Video Playback](#media--video-playback)
   - [Device Management](#device-management)
5. [Response Codes](#response-codes)
6. [Error Handling](#error-handling)

---

## Overview

This is a FastAPI-based backend for an **Online Course Management System** with the following features:

- **Role-based Access Control**: Admin, Teacher, Student
- **Course Hierarchy**: Courses → Topics → Videos
- **Progress Tracking**: Track student video watch progress
- **Commenting System**: Comments on topics and videos
- **Certificate Generation**: Auto-generated certificates upon course completion
- **Session Management**: Multi-device support with session tracking
- **Device Reset Requests**: Students can request device resets (admin approval required)
- **JWT Authentication**: Secure token-based authentication
- **MongoDB Database**: NoSQL document storage

---

## Authentication

### JWT Token Authentication

All protected endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

**Token Expiry:** 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)

**Token Payload:**
```json
{
  "sub": "user@example.com",
  "role": "admin|teacher|student",
  "sid": "session_id",
  "uuid": "user_uuid_id",
  "exp": 1234567890,
  "iat": 1234567890,
  "jti": "jwt_id"
}
```

### Session Management

- **Max Active Devices:** 5 (configurable via `MAX_ACTIVE_DEVICES`)
- **Single Session Mode:** Can be enabled to allow only one active session per user
- Sessions are tracked in `sessions` collection with device info

---

## Database Schema

### Collections

#### 1. **admins**
```json
{
  "_id": ObjectId,
  "uuid_id": "string (UUID v4)",
  "college_name": "string (1-200 chars)",
  "email_id": "string (email)",
  "total_student_allow_count": "integer (≥0)",
  "role": "admin",
  "hashed_password": "string (bcrypt)"
}
```

#### 2. **students**
```json
{
  "_id": ObjectId,
  "uuid_id": "string (UUID v4)",
  "student_name": "string (1-200 chars)",
  "department": "string (1-100 chars)",
  "email_id": "string (email)",
  "sub_department": "string (optional, max 100 chars)",
  "admin_uuid_id": "string (Foreign Key to admins.uuid_id)",
  "role": "student",
  "hashed_password": "string (bcrypt)"
}
```

#### 3. **teachers**
```json
{
  "_id": ObjectId,
  "uuid_id": "string (UUID v4)",
  "name": "string (1-150 chars)",
  "email_id": "string (email)",
  "bio": "string (optional)",
  "avatar_url": "string (optional)",
  "skills": ["array of strings"],
  "social_links": {"object (optional)"},
  "role": "teacher",
  "admin_uuid_id": "string (FK to admins.uuid_id)",
  "hashed_password": "string (bcrypt)"
}
```

#### 4. **courses**
```json
{
  "_id": ObjectId,
  "uuid_id": "string (UUID v4)",
  "slug": "string (auto-generated from title)",
  "title": "string (1-150 chars)",
  "category": "string (1-50 chars)",
  "level": "beginner|intermediate|advanced",
  "description": "string (optional)",
  "tags": ["array of strings"],
  "thumbnail_url": "string (optional)",
  "intro_video_url": "string (optional)",
  "instructor_uuid": "string (FK to teachers.uuid_id)",
  "co_instructor_uuids": ["array of teacher UUIDs"],
  "total_topics": "integer",
  "total_videos": "integer",
  "total_comments": "integer",
  "admin_uuid_id": "string (nullable)",
  "teacher_uuid_id": "string (nullable)"
}
```

#### 5. **topics**
```json
{
  "_id": ObjectId,
  "uuid_id": "string (UUID v4)",
  "course_uuid": "string (FK to courses.uuid_id)",
  "title": "string (1-150 chars)",
  "description": "string (optional)",
  "order_index": "integer (≥1)",
  "admin_uuid_id": "string (nullable)",
  "teacher_uuid_id": "string (nullable)"
}
```

#### 6. **videos**
```json
{
  "_id": ObjectId,
  "uuid_id": "string (UUID v4)",
  "course_uuid": "string (FK to courses.uuid_id)",
  "topic_uuid": "string (FK to topics.uuid_id)",
  "title": "string (1-150 chars)",
  "description": "string (optional)",
  "video_url": "string",
  "thumbnail_url": "string (optional)",
  "duration_seconds": "integer (≥0)",
  "is_preview": "boolean",
  "order_index": "integer (≥1)",
  "admin_uuid_id": "string (nullable)",
  "teacher_uuid_id": "string (nullable)"
}
```

#### 7. **comments**
```json
{
  "_id": ObjectId,
  "uuid_id": "string (UUID v4)",
  "parent_type": "topic|video",
  "parent_uuid": "string (FK to topic/video uuid_id)",
  "course_uuid": "string (FK to courses.uuid_id)",
  "author_role": "admin|teacher|student",
  "author_uuid": "string (FK to user uuid_id)",
  "content": "string (1-2000 chars)",
  "status": "visible|hidden|deleted",
  "created_at": "datetime",
  "updated_at": "datetime",
  "admin_uuid_id": "string (optional)"
}
```

#### 8. **user_courses** (Assignments)
```json
{
  "_id": ObjectId,
  "uuid_id": "string (UUID v4)",
  "student_uuid": "string (FK to students.uuid_id)",
  "course_uuid": "string (FK to courses.uuid_id)",
  "assigned_by_role": "admin|teacher",
  "assigned_by_uuid": "string",
  "assigned_at": "datetime",
  "status": "active|completed|revoked",
  "appreciation_status": "none|appreciated",
  "appreciation_at": "datetime (optional)"
}
```

#### 9. **user_progress**
```json
{
  "_id": ObjectId,
  "student_uuid": "string (FK to students.uuid_id)",
  "course_uuid": "string (FK to courses.uuid_id)",
  "topic_uuid": "string (FK to topics.uuid_id)",
  "video_uuid": "string (FK to videos.uuid_id)",
  "seconds_watched": "integer",
  "last_position_sec": "integer",
  "completed": "boolean"
}
```

#### 10. **certificates**
```json
{
  "_id": ObjectId,
  "certificate_id": "string (UUID v4)",
  "course_uuid": "string (FK to courses.uuid_id)",
  "student_uuid": "string (FK to students.uuid_id)",
  "issued_at": "datetime",
  "code": "string (8-char uppercase)",
  "url": "string (nullable)"
}
```

#### 11. **sessions**
```json
{
  "_id": ObjectId,
  "session_id": "string (UUID v4)",
  "user_uuid": "string",
  "role": "admin|teacher|student",
  "device_name": "string (optional)",
  "user_agent": "string",
  "ip_address": "string",
  "created_at": "datetime",
  "last_used_at": "datetime",
  "revoked": "boolean"
}
```

#### 12. **device_resets**
```json
{
  "_id": ObjectId,
  "request_id": "string (UUID v4)",
  "student_uuid": "string (FK to students.uuid_id)",
  "status": "pending|approved|rejected",
  "reason": "string (optional, max 500 chars)",
  "created_at": "datetime",
  "resolved_at": "datetime (nullable)",
  "resolved_by_uuid": "string (nullable)",
  "resolved_by_role": "string (nullable)"
}
```

---

## API Endpoints

### Root & Health

#### Get Root
```
GET /
```
**Authentication:** Not required
**Response:**
```json
{
  "message": "Welcome to Online Course Management API",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

#### Health Check
```
GET /health
```
**Authentication:** Not required
**Response:**
```json
{
  "status": "healthy"
}
```

---

### Authentication Endpoints

#### Login
```
POST /auth/login
```
**Authentication:** Not required
**Description:** Login for Admin, Teacher, or Student. Role is automatically detected.

**Request Body:**
```json
{
  "email_id": "user@example.com",
  "password": "password123"
}
```

**Optional Headers:**
- `X-Device-Name`: Device identifier (e.g., "iPhone 13")

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role": "admin|teacher|student",
  "user_data": {
    "uuid_id": "550e8400-e29b-41d4-a716-446655440000",
    "email_id": "user@example.com",
    // Role-specific fields
  }
}
```

**User Data by Role:**
- **Admin:** `college_name`, `total_student_allow_count`
- **Student:** `student_name`, `department`, `sub_department`
- **Teacher:** `name`, `bio`

**Errors:**
- `401 Unauthorized`: Invalid credentials

---

#### List Sessions
```
GET /auth/sessions
```
**Authentication:** Required (any role)
**Description:** List all active sessions for the current user

**Response (200):**
```json
{
  "sessions": [
    {
      "session_id": "abc123",
      "user_uuid": "user-uuid",
      "role": "student",
      "device_name": "iPhone 13",
      "user_agent": "Mozilla/5.0...",
      "ip_address": "192.168.1.1",
      "created_at": "2025-01-01T10:00:00",
      "last_used_at": "2025-01-01T12:30:00",
      "revoked": false
    }
  ]
}
```

---

#### Logout Current Session
```
POST /auth/logout
```
**Authentication:** Required (any role)
**Description:** Logout from the current session

**Response (200):**
```json
{
  "detail": "Logged out"
}
```

---

#### Logout All Sessions
```
POST /auth/logout-all
```
**Authentication:** Required (any role)
**Description:** Logout from all active sessions

**Response (200):**
```json
{
  "detail": "Logged out of 3 sessions"
}
```

---

### Admin Management

#### Create Admin
```
POST /admin/
```
**Authentication:** Not required
**Description:** Register a new admin

**Request Body:**
```json
{
  "college_name": "XYZ University",
  "email_id": "admin@university.edu",
  "total_student_allow_count": 500,
  "password": "admin123"
}
```

**Response (201):**
```json
{
  "uuid_id": "550e8400-e29b-41d4-a716-446655440000",
  "college_name": "XYZ University",
  "email_id": "admin@university.edu",
  "total_student_allow_count": 500,
  "role": "admin"
}
```

**Errors:**
- `400 Bad Request`: Email already registered

---

#### Get All Admins
```
GET /admin/
```
**Authentication:** Not required
**Response (200):** Array of admin objects

---

#### Get Admin by UUID
```
GET /admin/{uuid_id}
```
**Authentication:** Not required
**Path Parameters:**
- `uuid_id`: Admin UUID

**Response (200):** Admin object
**Errors:**
- `404 Not Found`: Admin not found

---

#### Update Admin
```
PUT /admin/{uuid_id}
```
**Authentication:** Not required
**Path Parameters:**
- `uuid_id`: Admin UUID

**Request Body (all fields optional):**
```json
{
  "college_name": "Updated University",
  "email_id": "newemail@university.edu",
  "total_student_allow_count": 600,
  "password": "newpassword123"
}
```

**Response (200):** Updated admin object
**Errors:**
- `404 Not Found`: Admin not found
- `400 Bad Request`: Email already registered

---

#### Delete Admin
```
DELETE /admin/{uuid_id}
```
**Authentication:** Not required
**Path Parameters:**
- `uuid_id`: Admin UUID

**Response (204):** No content
**Errors:**
- `404 Not Found`: Admin not found

---

### Department Management

#### Create Department
```
POST /departments/
```
**Authentication:** Not required
**Description:** Create a new department

**Request Body:**
```json
{
  "name": "Computer Science",
  "code": "CS",
  "description": "Computer Science and Engineering Department",
  "admin_uuid_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (201):**
```json
{
  "uuid_id": "dept-550e8400-e29b-41d4-a716-446655440000",
  "name": "Computer Science",
  "code": "CS",
  "description": "Computer Science and Engineering Department",
  "admin_uuid_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Errors:**
- `400 Bad Request`: Department code already exists
- `400 Bad Request`: Department name already exists
- `400 Bad Request`: Admin with UUID does not exist

---

#### Get All Departments
```
GET /departments/
```
**Authentication:** Not required
**Response (200):** Array of department objects

```json
[
  {
    "uuid_id": "dept-550e8400-e29b-41d4-a716-446655440000",
    "name": "Computer Science",
    "code": "CS",
    "description": "Computer Science and Engineering Department",
    "admin_uuid_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  {
    "uuid_id": "dept-550e8400-e29b-41d4-a716-446655440001",
    "name": "Mechanical Engineering",
    "code": "MECH",
    "description": "Mechanical Engineering Department",
    "admin_uuid_id": "550e8400-e29b-41d4-a716-446655440000"
  }
]
```

---

#### Get Department by UUID
```
GET /departments/{uuid_id}
```
**Authentication:** Not required
**Path Parameters:**
- `uuid_id`: Department UUID

**Response (200):** Department object

```json
{
  "uuid_id": "dept-550e8400-e29b-41d4-a716-446655440000",
  "name": "Computer Science",
  "code": "CS",
  "description": "Computer Science and Engineering Department",
  "admin_uuid_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Errors:**
- `404 Not Found`: Department not found

---

#### Update Department
```
PUT /departments/{uuid_id}
```
**Authentication:** Not required
**Path Parameters:**
- `uuid_id`: Department UUID

**Request Body (all fields optional):**
```json
{
  "name": "Computer Science & Engineering",
  "code": "CSE",
  "description": "Updated description",
  "admin_uuid_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (200):** Updated department object

```json
{
  "uuid_id": "dept-550e8400-e29b-41d4-a716-446655440000",
  "name": "Computer Science & Engineering",
  "code": "CSE",
  "description": "Updated description",
  "admin_uuid_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Errors:**
- `404 Not Found`: Department not found
- `400 Bad Request`: Department code already exists
- `400 Bad Request`: Department name already exists
- `400 Bad Request`: Admin with UUID does not exist

---

#### Delete Department
```
DELETE /departments/{uuid_id}
```
**Authentication:** Not required
**Path Parameters:**
- `uuid_id`: Department UUID

**Response (204):** No content

**Errors:**
- `404 Not Found`: Department not found
- `400 Bad Request`: Cannot delete department with students. Reassign students first.

---

### Student Management

#### Create Student
```
POST /student/
```
**Authentication:** Not required
**Description:** Register a new student with admin foreign key

**Request Body:**
```json
{
  "student_name": "John Doe",
  "department": "Computer Science",
  "email_id": "john.doe@university.edu",
  "sub_department": "AI & ML",
  "admin_uuid_id": "550e8400-e29b-41d4-a716-446655440000",
  "password": "student123"
}
```

**Response (201):**
```json
{
  "uuid_id": "660e8400-e29b-41d4-a716-446655440001",
  "student_name": "John Doe",
  "department": "Computer Science",
  "email_id": "john.doe@university.edu",
  "sub_department": "AI & ML",
  "admin_uuid_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "student"
}
```

**Errors:**
- `400 Bad Request`: Email already registered OR Admin UUID does not exist

---

#### Get All Students
```
GET /student/
```
**Authentication:** Not required
**Response (200):** Array of student objects

---

#### Get Student by UUID
```
GET /student/{uuid_id}
```
**Authentication:** Not required
**Path Parameters:**
- `uuid_id`: Student UUID

**Response (200):** Student object
**Errors:**
- `404 Not Found`: Student not found

---

#### Update Student
```
PUT /student/{uuid_id}
```
**Authentication:** Not required
**Path Parameters:**
- `uuid_id`: Student UUID

**Request Body (all fields optional):**
```json
{
  "student_name": "Jane Doe",
  "department": "Mathematics",
  "email_id": "jane.doe@university.edu",
  "sub_department": "Pure Math",
  "admin_uuid_id": "new-admin-uuid",
  "password": "newpassword123"
}
```

**Response (200):** Updated student object
**Errors:**
- `404 Not Found`: Student not found
- `400 Bad Request`: Email already registered OR Admin UUID does not exist

---

#### Delete Student
```
DELETE /student/{uuid_id}
```
**Authentication:** Not required
**Path Parameters:**
- `uuid_id`: Student UUID

**Response (204):** No content
**Errors:**
- `404 Not Found`: Student not found

---

### Teacher Management

#### Create Teacher
```
POST /teachers/
```
**Authentication:** Required (Admin only)
**Description:** Create a new teacher (automatically linked to the admin)

**Request Body:**
```json
{
  "name": "Prof. Smith",
  "email_id": "smith@university.edu",
  "bio": "Expert in AI and Machine Learning",
  "avatar_url": "https://example.com/avatar.jpg",
  "skills": ["Python", "Machine Learning", "Deep Learning"],
  "social_links": {
    "linkedin": "https://linkedin.com/in/profsmith",
    "twitter": "@profsmith"
  },
  "password": "teacher123"
}
```

**Response (201):**
```json
{
  "uuid_id": "teacher-uuid",
  "name": "Prof. Smith",
  "email_id": "smith@university.edu",
  "bio": "Expert in AI and Machine Learning",
  "avatar_url": "https://example.com/avatar.jpg",
  "skills": ["Python", "Machine Learning", "Deep Learning"],
  "social_links": {...},
  "role": "teacher"
}
```

**Errors:**
- `400 Bad Request`: Email already registered
- `403 Forbidden`: Not an admin

---

#### Get All Teachers
```
GET /teachers/
```
**Authentication:** Not required
**Response (200):** Array of teacher objects

---

#### Get Teacher by UUID
```
GET /teachers/{uuid_id}
```
**Authentication:** Not required
**Response (200):** Teacher object
**Errors:**
- `404 Not Found`: Teacher not found

---

#### Update Teacher
```
PUT /teachers/{uuid_id}
```
**Authentication:** Required (Admin only)
**Request Body:** Same as create (all fields optional)
**Response (200):** Updated teacher object
**Errors:**
- `404 Not Found`: Teacher not found
- `400 Bad Request`: Email already registered

---

#### Delete Teacher
```
DELETE /teachers/{uuid_id}
```
**Authentication:** Required (Admin only)
**Description:** Delete teacher (only if not assigned to any course)

**Response (204):** No content
**Errors:**
- `404 Not Found`: Teacher not found
- `400 Bad Request`: Teacher assigned to a course

---

### Course Management

#### Create Course
```
POST /courses/
```
**Authentication:** Required (Admin or Teacher)
**Description:** Create a new course with unique slug

**Request Body:**
```json
{
  "title": "Introduction to Machine Learning",
  "category": "Technology",
  "level": "beginner",
  "description": "Learn the basics of ML",
  "tags": ["ML", "AI", "Python"],
  "thumbnail_url": "https://example.com/thumbnail.jpg",
  "intro_video_url": "https://example.com/intro.mp4",
  "instructor_uuid": "teacher-uuid",
  "co_instructor_uuids": ["teacher-uuid-2"]
}
```

**Response (201):**
```json
{
  "uuid_id": "course-uuid",
  "slug": "introduction-to-machine-learning",
  "title": "Introduction to Machine Learning",
  "category": "Technology",
  "level": "beginner",
  "description": "Learn the basics of ML",
  "tags": ["ML", "AI", "Python"],
  "thumbnail_url": "https://example.com/thumbnail.jpg",
  "intro_video_url": "https://example.com/intro.mp4",
  "instructor_uuid": "teacher-uuid",
  "co_instructor_uuids": ["teacher-uuid-2"],
  "total_topics": 0,
  "total_videos": 0,
  "total_comments": 0
}
```

**Errors:**
- `400 Bad Request`: Instructor not found OR Co-instructors not found

---

#### Get All Courses
```
GET /courses/
```
**Authentication:** Not required
**Query Parameters:**
- `q`: Search query (searches in title)
- `category`: Filter by category
- `level`: Filter by level (beginner/intermediate/advanced)
- `instructor_uuid`: Filter by instructor

**Response (200):** Array of course objects

---

#### Get Course by UUID or Slug
```
GET /courses/{course_key}
```
**Authentication:** Not required
**Path Parameters:**
- `course_key`: Course UUID or slug

**Response (200):** Course object
**Errors:**
- `404 Not Found`: Course not found

---

#### Update Course
```
PUT /courses/{course_id}
```
**Authentication:** Required (Admin or Teacher)
**Request Body:** Same as create (all fields optional)
**Response (200):** Updated course object
**Errors:**
- `404 Not Found`: Course not found
- `400 Bad Request`: Instructor not found

---

#### Delete Course
```
DELETE /courses/{course_id}
```
**Authentication:** Required (Admin or Teacher)
**Description:** Cascade deletes topics, videos, comments, assignments, and progress

**Response (204):** No content
**Errors:**
- `404 Not Found`: Course not found

---

#### Get Course Outline
```
GET /courses/{course_key}/outline
```
**Authentication:** Not required
**Description:** Get course with all topics and their videos

**Response (200):**
```json
{
  "course": {
    "uuid_id": "course-uuid",
    "title": "Course Title",
    ...
  },
  "topics": [
    {
      "uuid_id": "topic-uuid",
      "title": "Topic 1",
      "order_index": 1,
      "videos": [
        {
          "uuid_id": "video-uuid",
          "title": "Video 1",
          "order_index": 1,
          ...
        }
      ]
    }
  ]
}
```

---

### Topic Management

#### Get Topics for Course
```
GET /topics/course/{course_id}
```
**Authentication:** Not required
**Response (200):** Array of topic objects (sorted by order_index)
**Errors:**
- `404 Not Found`: Course not found

---

#### Create Topic
```
POST /topics/course/{course_id}
```
**Authentication:** Required (Admin or Teacher)
**Description:** Create a new topic in a course

**Request Body:**
```json
{
  "title": "Introduction to Python",
  "description": "Learn Python basics",
  "order_index": 1
}
```

**Response (201):** Topic object
**Note:** If `order_index` is null, it's auto-assigned. If it conflicts, other topics are shifted.

---

#### Update Topic
```
PUT /topics/{topic_id}
```
**Authentication:** Required (Admin or Teacher)
**Request Body:** Same as create (all fields optional)
**Response (200):** Updated topic object
**Note:** Reordering is supported; other topics are automatically adjusted.

---

#### Delete Topic
```
DELETE /topics/{topic_id}
```
**Authentication:** Required (Admin or Teacher)
**Description:** Cascade deletes videos, comments, and progress

**Response (204):** No content
**Errors:**
- `404 Not Found`: Topic not found

---

### Video Management

#### Get Videos for Topic
```
GET /videos/topic/{topic_id}
```
**Authentication:** Not required
**Response (200):** Array of video objects (sorted by order_index)
**Errors:**
- `404 Not Found`: Topic not found

---

#### Create Video
```
POST /videos/topic/{topic_id}
```
**Authentication:** Required (Admin or Teacher)
**Description:** Create a new video in a topic

**Request Body:**
```json
{
  "title": "Python Variables",
  "description": "Understanding variables in Python",
  "video_url": "https://example.com/video.mp4",
  "thumbnail_url": "https://example.com/thumb.jpg",
  "duration_seconds": 600,
  "is_preview": false,
  "order_index": 1
}
```

**Response (201):** Video object
**Note:** Auto-assigns `order_index` if null; handles conflicts.

---

#### Get Video by UUID
```
GET /videos/{video_id}
```
**Authentication:** Not required
**Response (200):** Video object
**Errors:**
- `404 Not Found`: Video not found

---

#### Update Video
```
PUT /videos/{video_id}
```
**Authentication:** Required (Admin or Teacher)
**Request Body:** Same as create (all fields optional)
**Response (200):** Updated video object

---

#### Delete Video
```
DELETE /videos/{video_id}
```
**Authentication:** Required (Admin or Teacher)
**Description:** Cascade deletes comments and progress

**Response (204):** No content
**Errors:**
- `404 Not Found`: Video not found

---

### Comment Management

#### Get Comments for Topic
```
GET /comments/topic/{topic_id}
```
**Authentication:** Not required
**Response (200):** Array of comment objects (sorted by created_at)
**Errors:**
- `404 Not Found`: Topic not found

---

#### Get Comments for Video
```
GET /comments/video/{video_id}
```
**Authentication:** Not required
**Response (200):** Array of comment objects
**Errors:**
- `404 Not Found`: Video not found

---

#### Create Comment
```
POST /comments/
```
**Authentication:** Required (any role)
**Description:** Post a comment on a topic or video

**Request Body:**
```json
{
  "parent_type": "video",
  "parent_uuid": "video-uuid",
  "content": "Great explanation!"
}
```

**Response (201):**
```json
{
  "uuid_id": "comment-uuid",
  "parent_type": "video",
  "parent_uuid": "video-uuid",
  "course_uuid": "course-uuid",
  "author_role": "student",
  "author_uuid": "student-uuid",
  "content": "Great explanation!",
  "status": "visible"
}
```

**Errors:**
- `404 Not Found`: Parent (topic/video) not found
- `400 Bad Request`: Invalid parent type

---

#### Update Comment
```
PUT /comments/{comment_id}
```
**Authentication:** Required
**Description:** Update comment content or status (author can update content; admin/teacher can update status)

**Request Body:**
```json
{
  "content": "Updated comment",
  "status": "hidden"
}
```

**Response (200):** Updated comment object
**Errors:**
- `404 Not Found`: Comment not found
- `403 Forbidden`: Not allowed

---

#### Delete Comment
```
DELETE /comments/{comment_id}
```
**Authentication:** Required
**Description:** Soft delete (sets status to "deleted")

**Response (204):** No content
**Errors:**
- `404 Not Found`: Comment not found
- `403 Forbidden`: Not allowed

---

### Assignment Management

#### Assign Course to Students
```
POST /assignments/
```
**Authentication:** Required (Admin or Teacher)
**Description:** Assign a course to one or multiple students

**Request Body (Option 1 - Single Student):**
```json
{
  "course_uuid": "course-uuid",
  "student_uuid": "student-uuid"
}
```

**Request Body (Option 2 - Multiple Students):**
```json
{
  "course_uuid": "course-uuid",
  "student_uuids": ["student-uuid-1", "student-uuid-2"]
}
```

**Response (201):** Array of assignment objects
**Errors:**
- `404 Not Found`: Course not found
- `400 Bad Request`: Students not found OR Invalid request (must provide student_uuid or student_uuids)

---

#### Get Assignments
```
GET /assignments/
```
**Authentication:** Required (Admin or Teacher)
**Query Parameters:**
- `student_uuid`: Filter by student
- `course_uuid`: Filter by course

**Response (200):** Array of assignment objects

---

#### Get My Assignments (Student)
```
GET /assignments/me
```
**Authentication:** Required (Student only)
**Response (200):** Array of active assignment objects
**Errors:**
- `403 Forbidden`: Not a student

---

#### Revoke Assignment
```
DELETE /assignments/{assignment_id}
```
**Authentication:** Required (Admin or Teacher)
**Description:** Revoke a course assignment (sets status to "revoked")

**Response (204):** No content
**Errors:**
- `404 Not Found`: Assignment not found

---

### Progress Tracking

#### Update Video Progress
```
PUT /progress/video/{video_uuid}
```
**Authentication:** Required (Student only)
**Description:** Update watch progress for a video

**Request Body:**
```json
{
  "last_position_sec": 120,
  "delta_seconds_watched": 10,
  "completed": false
}
```

**Response (200):**
```json
{
  "video_uuid": "video-uuid",
  "course_uuid": "course-uuid",
  "topic_uuid": "topic-uuid",
  "seconds_watched": 120,
  "last_position_sec": 120,
  "completed": false
}
```

**Errors:**
- `404 Not Found`: Video not found
- `403 Forbidden`: Not a student OR Course not assigned

---

#### Track Video Progress Event
```
POST /progress/video/{video_uuid}/events
```
**Authentication:** Required (Student only)
**Description:** Same as update progress (alternative endpoint)

---

#### Mark Video as Complete
```
POST /progress/video/{video_uuid}/complete
```
**Authentication:** Required (Student only)
**Description:** Mark a video as fully watched

**Response (200):** Video progress object
**Errors:**
- `404 Not Found`: Video not found
- `403 Forbidden`: Not a student OR Course not assigned

---

#### Get Course Progress
```
GET /progress/course/{course_uuid}
```
**Authentication:** Required (Student only)
**Response (200):**
```json
{
  "course_uuid": "course-uuid",
  "total_videos": 10,
  "completed_videos": 7,
  "progress_percent": 70.0,
  "learning_seconds": 3600,
  "learning_hours": 1.0
}
```

**Errors:**
- `403 Forbidden`: Not a student OR Course not assigned

---

#### Get All My Progress
```
GET /progress/me
```
**Authentication:** Required (Student only)
**Response (200):** Array of course progress objects

---

#### Get Appreciation Status
```
GET /progress/course/{course_uuid}/appreciation
```
**Authentication:** Required (Student only)
**Response (200):**
```json
{
  "course_uuid": "course-uuid",
  "student_uuid": "student-uuid",
  "appreciation_status": "appreciated",
  "appreciation_at": "2025-01-01T12:00:00"
}
```

**Errors:**
- `403 Forbidden`: Not a student
- `404 Not Found`: Assignment not found

---

#### Set Appreciation Status
```
POST /progress/course/{student_uuid}/{course_uuid}/appreciate
```
**Authentication:** Required (Admin or Teacher)
**Description:** Mark a student's course progress as "appreciated" (requires minimum progress threshold)

**Response (200):**
```json
{
  "detail": "Appreciation set",
  "course_uuid": "course-uuid",
  "student_uuid": "student-uuid"
}
```

**Errors:**
- `404 Not Found`: Assignment not found
- `400 Bad Request`: Progress below appreciation threshold

---

### Certificate Management

#### Get Certificate Status
```
GET /certificates/course/{course_uuid}
```
**Authentication:** Required (Student only)
**Description:** Check if student is eligible for certificate

**Response (200 - Eligible with Certificate):**
```json
{
  "eligible": true,
  "reason": null,
  "certificate": {
    "certificate_id": "cert-uuid",
    "course_uuid": "course-uuid",
    "student_uuid": "student-uuid",
    "issued_at": "2025-01-01T12:00:00",
    "code": "ABC12345",
    "url": null
  }
}
```

**Response (200 - Eligible but Not Issued):**
```json
{
  "eligible": true,
  "reason": null,
  "certificate": null
}
```

**Response (200 - Not Eligible):**
```json
{
  "eligible": false,
  "reason": "Course not fully completed",
  "certificate": null
}
```

**Errors:**
- `403 Forbidden`: Not a student OR Course not assigned

---

#### Issue Certificate (Student)
```
POST /certificates/course/{course_uuid}
```
**Authentication:** Required (Student only)
**Description:** Request certificate issuance (requires 100% completion)

**Response (200):** Certificate object
**Errors:**
- `403 Forbidden`: Not a student OR Course not assigned
- `400 Bad Request`: Completion not 100%

---

#### Issue Certificate (Admin)
```
POST /certificates/admin/issue/{student_uuid}/{course_uuid}
```
**Authentication:** Required (Admin or Teacher)
**Description:** Manually issue certificate to a student

**Response (200):** Certificate object
**Errors:**
- `400 Bad Request`: Completion not 100%

---

### Media / Video Playback

#### Get Video Playback Config
```
GET /media/video/{video_uuid}
```
**Authentication:** Required (any role)
**Description:** Get secure playback configuration for a video

**Response (200):**
```json
{
  "video_uuid": "video-uuid",
  "course_uuid": "course-uuid",
  "stream_url": "/stream/videos/video-uuid",
  "expires_at": "2025-01-01T12:15:00",
  "headers": {
    "Cache-Control": "no-store"
  },
  "client_flags": {
    "controlsList": "nodownload",
    "disableContextMenu": true,
    "draggable": false,
    "watermark": true,
    "contentSecurityPolicy": "default-src 'self'; media-src 'self'; frame-ancestors 'none'"
  }
}
```

**Errors:**
- `404 Not Found`: Video not found
- `403 Forbidden`: Course not assigned (for students)

**Note:** Stream URL is temporary (15 minutes expiry)

---

### Device Management

#### Request Device Reset
```
POST /devices/reset-request
```
**Authentication:** Required (Student only)
**Description:** Request admin approval to reset all active devices/sessions

**Request Body:**
```json
{
  "reason": "Lost my phone, need to reset devices"
}
```

**Response (201):**
```json
{
  "request_id": "request-uuid",
  "student_uuid": "student-uuid",
  "status": "pending",
  "reason": "Lost my phone, need to reset devices",
  "created_at": "2025-01-01T10:00:00",
  "resolved_at": null,
  "resolved_by_uuid": null,
  "resolved_by_role": null
}
```

**Errors:**
- `403 Forbidden`: Not a student

**Note:** If a pending request already exists, it returns the existing request.

---

#### List Device Reset Requests
```
GET /devices/reset-requests
```
**Authentication:** Required (Admin only)
**Query Parameters:**
- `status_filter`: Filter by status (pending/approved/rejected)

**Response (200):** Array of device reset request objects

---

#### Approve Device Reset
```
POST /devices/reset-requests/{request_id}/approve
```
**Authentication:** Required (Admin only)
**Description:** Approve request and revoke all student sessions

**Response (200):** Updated request object
**Errors:**
- `404 Not Found`: Request not found
- `400 Bad Request`: Request already resolved

---

#### Reject Device Reset
```
POST /devices/reset-requests/{request_id}/reject
```
**Authentication:** Required (Admin only)
**Description:** Reject the device reset request

**Response (200):** Updated request object
**Errors:**
- `404 Not Found`: Request not found
- `400 Bad Request`: Request already resolved

---

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 204 | No Content - Request successful, no content to return |
| 400 | Bad Request - Invalid request data |
| 401 | Unauthorized - Missing or invalid authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error - Server error |

---

## Error Handling

All errors return a JSON response with the following structure:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Example Error Responses:**

```json
// 401 Unauthorized
{
  "detail": "Invalid credentials"
}

// 403 Forbidden
{
  "detail": "Students only"
}

// 404 Not Found
{
  "detail": "Course not found"
}

// 400 Bad Request
{
  "detail": "Email already registered"
}
```

---

## Security Features

### Password Security
- **Algorithm:** Bcrypt with automatic salt generation
- **Password Length:** Minimum 6 characters
- **Bcrypt Limitation:** Passwords truncated to 72 bytes for compatibility

### JWT Token Security
- **Algorithm:** HS256 (HMAC with SHA-256)
- **Token Expiry:** 30 minutes (configurable)
- **Claims:** Includes user email, role, session ID, UUID, expiry, issued-at, and JWT ID
- **Session Tracking:** All logins create session records with device info

### Session Management
- **Multi-Device Support:** Up to 5 active devices per user (configurable)
- **Single Session Mode:** Optional - revokes all other sessions on new login
- **Device Tracking:** Records device name, user agent, IP address, and timestamps
- **Manual Logout:** Users can logout from current session or all sessions

### Content Protection (Videos)
- **Temporary URLs:** Stream URLs expire in 15 minutes
- **Access Control:** Students must be assigned to course
- **Client-Side Flags:** No download, context menu disabled, watermark enabled
- **CSP Headers:** Strict content security policy

---

## Environment Variables

Create a `.env` file in the root directory:

```env
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=online_course_db

# Security
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Session Management
MAX_ACTIVE_DEVICES=5
SINGLE_SESSION=false
```

---

## Development

### Running the Server

**Option 1: Direct Python**
```bash
python main.py
```

**Option 2: Development Script with Auto-Reload**
```bash
python start_dev.py
```

**Option 3: Batch File (Windows)**
```bash
start_server.bat
```

### Auto-Reload Features
- Detects changes in Python files automatically
- Restarts server with 0.5 second delay
- Monitors all `.py` files in the project

### API Documentation
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Database Relationships

```
admins (uuid_id)
  ├── students (admin_uuid_id → admins.uuid_id)
  └── teachers (admin_uuid_id → admins.uuid_id)
      └── courses (instructor_uuid → teachers.uuid_id)
          ├── topics (course_uuid → courses.uuid_id)
          │   └── videos (topic_uuid → topics.uuid_id)
          │       ├── comments (parent_uuid → videos.uuid_id)
          │       └── user_progress (video_uuid → videos.uuid_id)
          ├── user_courses (course_uuid → courses.uuid_id)
          └── certificates (course_uuid → courses.uuid_id)
```

---

## Notes

1. **Foreign Key Validation:** All foreign key references are validated at the application level (not database level)
2. **Cascade Deletes:** Implemented manually in route handlers
3. **Unique Constraints:** Email uniqueness enforced at application level
4. **Slug Generation:** Course slugs are auto-generated from titles with conflict resolution
5. **Order Management:** Topics and videos support reordering with automatic index adjustment
6. **Soft Deletes:** Comments use soft delete (status = "deleted")
7. **Progress Tracking:** Real-time tracking with upsert operations
8. **Certificate Codes:** 8-character uppercase codes generated from UUID

---

## Testing

A test script is provided for testing the student-admin foreign key relationship:

```bash
python test_student_admin_fk.py
```

This script tests:
- Admin creation
- Student creation with valid admin UUID
- Foreign key validation with invalid admin UUID
- Student retrieval
- Admin UUID updates
- Listing students with admin references

---

## Future Enhancements

- Database-level unique indexes for email_id and uuid_id
- MongoDB TTL indexes for expired sessions
- File upload support for thumbnails and videos
- Search indexing for full-text search
- Rate limiting for API endpoints
- Email notifications for device resets and certificates
- PDF certificate generation
- Real-time notifications using WebSockets
- Analytics dashboard for admins

---

**Last Updated:** 2025-11-01
**Author:** Claude Code
**Version:** 1.0.0
