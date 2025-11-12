# Teacher Avatar S3 Upload

## Overview

The teacher endpoints now support **avatar image uploads to S3** for both creating and updating teacher profiles. Avatar files are automatically uploaded to S3 and URLs are stored in the database.

## What Changed

### Before
- Teachers could only have avatar URLs (manual entry)
- No file upload support
- No S3 integration

### After
- **Automatic S3 upload** for teacher avatar images
- Multipart/form-data support for file uploads
- Old avatars automatically deleted when updating
- Avatar cleanup on teacher deletion

## API Changes

### 1. Create Teacher - POST /teachers/

**Now accepts multipart/form-data** instead of JSON.

#### Request Format

**Option A: All fields as form data**
```bash
POST /teachers/
Content-Type: multipart/form-data

name: Vimal Raj L
email_id: vr.vimalraj04@gmail.com
password: 123456789
bio: Python Expert
skills: ["Python", "FastAPI", "MongoDB"]  # JSON string
avatar: <binary file>
```

**Option B: JSON + avatar file**
```bash
POST /teachers/
Content-Type: multipart/form-data

teacher: {"name":"Vimal Raj L","email_id":"vr.vimalraj04@gmail.com","bio":"Python Expert","skills":[],"password":"123456789"}
avatar: <binary file>
```

#### Example with cURL

```bash
# Option A: Individual fields
curl -X POST "http://localhost:8000/teachers/" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -F "name=Vimal Raj L" \
  -F "email_id=vr.vimalraj04@gmail.com" \
  -F "password=123456789" \
  -F "bio=Python Expert" \
  -F 'skills=["Python","FastAPI","MongoDB"]' \
  -F "avatar=@avatar.jpg"

# Option B: JSON string + file
curl -X POST "http://localhost:8000/teachers/" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -F 'teacher={"name":"Vimal Raj L","email_id":"vr.vimalraj04@gmail.com","bio":"Python Expert","skills":[],"password":"123456789"}' \
  -F "avatar=@avatar.jpg"
```

#### Response

```json
{
    "uuid_id": "teacher-uuid-123",
    "name": "Vimal Raj L",
    "email_id": "vr.vimalraj04@gmail.com",
    "bio": "Python Expert",
    "avatar_url": "https://bucket.s3.amazonaws.com/teachers/avatars/teacher-uuid-123/avatar.jpg",
    "avatar_file_key": "teachers/avatars/teacher-uuid-123/avatar.jpg",
    "skills": ["Python", "FastAPI", "MongoDB"],
    "social_links": null,
    "role": "teacher"
}
```

### 2. Update Teacher - PUT /teachers/{uuid_id}

**Now accepts multipart/form-data** for avatar updates.

#### Request Format

**Option A: Individual fields**
```bash
PUT /teachers/{uuid_id}
Content-Type: multipart/form-data

name: Updated Name
bio: Updated Bio
avatar: <new binary file>
```

**Option B: JSON + avatar**
```bash
PUT /teachers/{uuid_id}
Content-Type: multipart/form-data

teacher: {"name":"Updated Name","bio":"Updated Bio"}
avatar: <new binary file>
```

#### Example with cURL

```bash
# Update only avatar
curl -X PUT "http://localhost:8000/teachers/teacher-uuid-123" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -F "avatar=@new-avatar.jpg"

# Update name and avatar
curl -X PUT "http://localhost:8000/teachers/teacher-uuid-123" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -F "name=New Name" \
  -F "avatar=@new-avatar.jpg"

# Update using JSON string
curl -X PUT "http://localhost:8000/teachers/teacher-uuid-123" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -F 'teacher={"name":"New Name","bio":"Updated Bio"}' \
  -F "avatar=@new-avatar.jpg"
```

#### Response

```json
{
    "uuid_id": "teacher-uuid-123",
    "name": "New Name",
    "email_id": "vr.vimalraj04@gmail.com",
    "bio": "Updated Bio",
    "avatar_url": "https://bucket.s3.amazonaws.com/teachers/avatars/teacher-uuid-123/new-avatar.jpg",
    "avatar_file_key": "teachers/avatars/teacher-uuid-123/new-avatar.jpg",
    "skills": ["Python", "FastAPI", "MongoDB"],
    "role": "teacher"
}
```

### 3. Delete Teacher - DELETE /teachers/{uuid_id}

**Enhanced with S3 cleanup** - automatically deletes avatar from S3 when teacher is deleted.

```bash
DELETE /teachers/{uuid_id}
Authorization: Bearer ADMIN_TOKEN
```

## Technical Implementation

### Model Changes (models/teacher.py)

Added `avatar_file_key` field to track S3 storage:

```python
class TeacherBase(BaseModel):
    name: str
    email_id: EmailStr
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_file_key: Optional[str] = None  # NEW: S3 storage key
    skills: list[str] = []
    social_links: Optional[dict] = None
    role: Literal["teacher"] = "teacher"
```

### Route Changes (routes/teachers.py)

#### POST /teachers/ - Line 16
- Accepts `multipart/form-data` with avatar file
- Parses JSON data from form fields or JSON string
- Uploads avatar to S3 under `teachers/avatars/` folder
- Stores S3 URL and storage key in database

#### PUT /teachers/{uuid_id} - Line 117
- Accepts `multipart/form-data` for updates
- Deletes old avatar from S3 before uploading new one
- Updates avatar URL and storage key in database

#### DELETE /teachers/{uuid_id} - Line 210
- Cleans up avatar file from S3 before deleting teacher record
- Prevents orphaned files in S3

### S3 Storage Structure

```
your-s3-bucket/
└── teachers/
    └── avatars/
        ├── teacher-uuid-123/
        │   └── avatar.jpg
        ├── teacher-uuid-456/
        │   └── profile.png
        └── teacher-uuid-789/
            └── photo.webp
```

## File Upload Details

### Supported File Types
- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- GIF (`.gif`)
- WebP (`.webp`)

### File Validation
- Content type must be an image
- Invalid file types will return `400 Bad Request`

### Automatic Cleanup
- Old avatars deleted when updating with new avatar
- Avatar deleted when teacher is deleted
- Prevents S3 storage waste

## Testing Examples

### Test 1: Create Teacher with Avatar

```bash
# Prepare data
cat > teacher.json <<EOF
{
    "name": "Vimal Raj L",
    "email_id": "vr.vimalraj04@gmail.com",
    "password": "123456789",
    "bio": "Python Expert",
    "skills": ["Python", "FastAPI", "MongoDB"]
}
EOF

# Create teacher with avatar
curl -X POST "http://localhost:8000/teachers/" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -F "teacher=@teacher.json;type=application/json" \
  -F "avatar=@avatar.jpg;type=image/jpeg"
```

### Test 2: Update Teacher Avatar

```bash
# Update avatar only
curl -X PUT "http://localhost:8000/teachers/teacher-uuid-123" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -F "avatar=@new-avatar.png"

# Expected: Old avatar deleted from S3, new avatar uploaded
```

### Test 3: Update Teacher Info + Avatar

```bash
curl -X PUT "http://localhost:8000/teachers/teacher-uuid-123" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -F "name=Updated Name" \
  -F "bio=Updated Python Expert" \
  -F "avatar=@new-photo.jpg"
```

### Test 4: Delete Teacher (with S3 cleanup)

```bash
curl -X DELETE "http://localhost:8000/teachers/teacher-uuid-123" \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Expected: Teacher deleted from DB, avatar deleted from S3
```

## Backward Compatibility

### Still Supports JSON (without avatar)

If you don't need to upload an avatar, you can still send JSON:

```bash
# This still works (no avatar)
curl -X POST "http://localhost:8000/teachers/" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email_id": "john@example.com",
    "password": "password123",
    "bio": "Teacher",
    "skills": []
  }'
```

However, to upload an avatar, you **must use multipart/form-data**.

## Error Handling

### Invalid File Type
```json
{
    "detail": "Only image files (JPEG, PNG, GIF, WebP) are allowed for avatar"
}
```

### Missing Required Fields
```json
{
    "detail": "Name is required"
}
```

### Email Already Exists
```json
{
    "detail": "Email already registered"
}
```

### Teacher Not Found (Update)
```json
{
    "detail": "Teacher not found"
}
```

### Teacher Assigned to Course (Delete)
```json
{
    "detail": "Teacher assigned to a course"
}
```

## Frontend Integration

### React Example with FormData

```javascript
const createTeacher = async (teacherData, avatarFile) => {
    const formData = new FormData();

    // Option 1: Send as JSON string
    formData.append('teacher', JSON.stringify({
        name: teacherData.name,
        email_id: teacherData.email_id,
        password: teacherData.password,
        bio: teacherData.bio,
        skills: teacherData.skills
    }));

    // Option 2: Send as individual fields
    // formData.append('name', teacherData.name);
    // formData.append('email_id', teacherData.email_id);
    // formData.append('password', teacherData.password);
    // formData.append('bio', teacherData.bio);
    // formData.append('skills', JSON.stringify(teacherData.skills));

    if (avatarFile) {
        formData.append('avatar', avatarFile);
    }

    const response = await fetch('http://localhost:8000/teachers/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    });

    return response.json();
};

// Usage
const avatarFile = document.getElementById('avatar-input').files[0];
const teacher = await createTeacher({
    name: 'Vimal Raj L',
    email_id: 'vr.vimalraj04@gmail.com',
    password: '123456789',
    bio: 'Python Expert',
    skills: ['Python', 'FastAPI']
}, avatarFile);
```

### Update Teacher Example

```javascript
const updateTeacher = async (teacherId, updates, newAvatar) => {
    const formData = new FormData();

    if (updates.name) formData.append('name', updates.name);
    if (updates.bio) formData.append('bio', updates.bio);
    if (updates.skills) formData.append('skills', JSON.stringify(updates.skills));

    if (newAvatar) {
        formData.append('avatar', newAvatar);
    }

    const response = await fetch(`http://localhost:8000/teachers/${teacherId}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    });

    return response.json();
};
```

## Database Schema

### Teacher Document

```javascript
{
    "uuid_id": "teacher-uuid-123",
    "name": "Vimal Raj L",
    "email_id": "vr.vimalraj04@gmail.com",
    "bio": "Python Expert",
    "avatar_url": "https://bucket.s3.amazonaws.com/teachers/avatars/teacher-uuid-123/avatar.jpg",
    "avatar_file_key": "teachers/avatars/teacher-uuid-123/avatar.jpg",  // NEW
    "skills": ["Python", "FastAPI", "MongoDB"],
    "social_links": {
        "linkedin": "https://linkedin.com/in/vimalraj",
        "github": "https://github.com/vimalraj"
    },
    "role": "teacher",
    "hashed_password": "...",
    "admin_uuid_id": "admin-uuid"
}
```

## Benefits

✅ **Automatic S3 Upload** - No manual upload needed
✅ **File Management** - Old files automatically deleted
✅ **Cleanup on Delete** - No orphaned files in S3
✅ **Flexible Input** - Supports both JSON string and individual fields
✅ **Image Validation** - Only allows image file types
✅ **Backward Compatible** - JSON-only requests still work (without avatar)

## Summary

Teacher endpoints now fully support avatar image uploads to S3:

1. **POST /teachers/** - Create teacher with avatar upload
2. **PUT /teachers/{uuid_id}** - Update teacher with avatar upload
3. **DELETE /teachers/{uuid_id}** - Delete teacher and cleanup avatar from S3

Use `multipart/form-data` with the `avatar` field to upload teacher profile pictures!
