# Certificate Management System Documentation

## Overview

Complete certificate management system with CRUD operations, automatic certificate generation when students complete courses, certificate file uploads to S3, and certificate verification.

## Features

- ✅ **Automatic Certificate Generation** - Certificates auto-generated when student completes all videos in a course
- ✅ **CRUD Operations** - Create, Read, Update, Delete certificates
- ✅ **Certificate File Upload** - Upload PDF/image certificates to S3
- ✅ **Certificate Verification** - Public endpoint to verify certificates by code
- ✅ **Certificate Revocation** - Revoke and restore certificates
- ✅ **Student Portal** - Students can view and claim their certificates
- ✅ **Admin Management** - Full admin controls for certificate management

## Database Schema

### Certificate Document
```javascript
{
    "certificate_id": "uuid",
    "course_uuid": "course-uuid",
    "student_uuid": "student-uuid",
    "student_name": "John Doe",
    "course_title": "Introduction to Python",
    "issued_at": "2025-11-13T10:30:00Z",
    "code": "ABC123DE",  // Unique verification code
    "url": "https://bucket.s3.amazonaws.com/certificates/uuid/cert.pdf",  // S3 URL
    "certificate_file_key": "certificates/uuid/cert.pdf",  // S3 storage key
    "revoked": false,
    "revoked_at": null,
    "notes": "Auto-generated on course completion",
    "completion_percentage": 100.0
}
```

## API Endpoints

### Student Endpoints

#### 1. Get My Certificates
Get all certificates for the logged-in student.

**Endpoint:** `GET /certificates/my-certificates`

**Authentication:** Student only

**Response:**
```json
[
    {
        "certificate_id": "cert-uuid",
        "course_uuid": "course-uuid",
        "student_uuid": "student-uuid",
        "student_name": "John Doe",
        "course_title": "Python Course",
        "issued_at": "2025-11-13T10:30:00Z",
        "code": "ABC123DE",
        "url": "https://bucket.s3.amazonaws.com/certificates/uuid/cert.pdf",
        "revoked": false,
        "completion_percentage": 100.0
    }
]
```

#### 2. Check Certificate Eligibility
Check if student is eligible to receive certificate for a course.

**Endpoint:** `GET /certificates/course/{course_uuid}/eligibility`

**Authentication:** Student only

**Response:**
```json
{
    "eligible": true,
    "reason": null,
    "certificate": {
        "certificate_id": "cert-uuid",
        "code": "ABC123DE",
        ...
    },
    "completion_percentage": 100.0
}
```

Or if not eligible:
```json
{
    "eligible": false,
    "reason": "Course completion: 75.5%. Complete all videos to earn certificate.",
    "certificate": null,
    "completion_percentage": 75.5
}
```

#### 3. Claim Certificate
Student claims certificate after completing course.

**Endpoint:** `POST /certificates/course/{course_uuid}/claim`

**Authentication:** Student only

**Response:**
```json
{
    "certificate_id": "cert-uuid",
    "course_uuid": "course-uuid",
    "student_uuid": "student-uuid",
    "student_name": "John Doe",
    "course_title": "Python Course",
    "issued_at": "2025-11-13T10:30:00Z",
    "code": "ABC123DE",
    "url": null,
    "revoked": false,
    "completion_percentage": 100.0
}
```

### Public Endpoints

#### 4. Verify Certificate
Public endpoint to verify certificate authenticity by code.

**Endpoint:** `GET /certificates/verify/{code}`

**Authentication:** None (Public)

**Example:** `GET /certificates/verify/ABC123DE`

**Response:**
```json
{
    "certificate_id": "cert-uuid",
    "student_name": "John Doe",
    "course_title": "Python Course",
    "issued_at": "2025-11-13T10:30:00Z",
    "code": "ABC123DE",
    "revoked": false
}
```

### Admin Endpoints

#### 5. List All Certificates
List all certificates with optional filters.

**Endpoint:** `GET /certificates/all`

**Authentication:** Admin or Teacher

**Query Parameters:**
- `course_uuid` (optional) - Filter by course
- `student_uuid` (optional) - Filter by student
- `revoked` (optional) - Filter by revocation status

**Example:**
```bash
GET /certificates/all?course_uuid=course-uuid&revoked=false
```

**Response:**
```json
[
    {
        "certificate_id": "cert-uuid",
        "student_name": "John Doe",
        "course_title": "Python Course",
        "issued_at": "2025-11-13T10:30:00Z",
        "code": "ABC123DE",
        "revoked": false,
        "completion_percentage": 100.0
    }
]
```

#### 6. Get Certificate by ID
Get specific certificate details.

**Endpoint:** `GET /certificates/{certificate_id}`

**Authentication:** Admin, Teacher, or Student (own certificate only)

**Response:**
```json
{
    "certificate_id": "cert-uuid",
    "student_name": "John Doe",
    "course_title": "Python Course",
    "issued_at": "2025-11-13T10:30:00Z",
    "code": "ABC123DE",
    "url": "https://bucket.s3.amazonaws.com/certificates/uuid/cert.pdf",
    "revoked": false
}
```

#### 7. Manually Issue Certificate
Admin manually issues certificate to a student.

**Endpoint:** `POST /certificates/issue`

**Authentication:** Admin or Teacher

**Request Body:**
```json
{
    "course_uuid": "course-uuid",
    "student_uuid": "student-uuid"
}
```

**Response:**
```json
{
    "certificate_id": "cert-uuid",
    "student_name": "John Doe",
    "course_title": "Python Course",
    "issued_at": "2025-11-13T10:30:00Z",
    "code": "ABC123DE",
    "notes": "Manually issued by admin",
    "completion_percentage": 85.5
}
```

#### 8. Update Certificate
Update certificate details.

**Endpoint:** `PUT /certificates/{certificate_id}`

**Authentication:** Admin or Teacher

**Request Body:**
```json
{
    "url": "https://custom-url.com/cert.pdf",
    "notes": "Updated certificate",
    "revoked": false
}
```

**Response:** Updated certificate object

#### 9. Upload Certificate File
Upload certificate PDF or image file to S3.

**Endpoint:** `POST /certificates/{certificate_id}/upload`

**Authentication:** Admin or Teacher

**Request (multipart/form-data):**
- `file`: PDF or image file

**Example:**
```bash
curl -X POST "http://localhost:8000/certificates/{certificate_id}/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@certificate.pdf"
```

**Response:**
```json
{
    "certificate_id": "cert-uuid",
    "url": "https://bucket.s3.amazonaws.com/certificates/uuid/certificate.pdf",
    "certificate_file_key": "certificates/uuid/certificate.pdf"
}
```

#### 10. Revoke Certificate
Revoke a certificate.

**Endpoint:** `POST /certificates/{certificate_id}/revoke`

**Authentication:** Admin or Teacher

**Response:**
```json
{
    "certificate_id": "cert-uuid",
    "revoked": true,
    "revoked_at": "2025-11-13T11:00:00Z"
}
```

#### 11. Restore Certificate
Restore a revoked certificate.

**Endpoint:** `POST /certificates/{certificate_id}/restore`

**Authentication:** Admin or Teacher

**Response:**
```json
{
    "certificate_id": "cert-uuid",
    "revoked": false,
    "revoked_at": null
}
```

#### 12. Delete Certificate
Permanently delete certificate.

**Endpoint:** `DELETE /certificates/{certificate_id}`

**Authentication:** Admin or Teacher

**Response:** `204 No Content`

## Automatic Certificate Generation

Certificates are automatically generated when:

1. Student completes the last video in a course
2. Student marks a video as complete using `/progress/video/{video_uuid}/complete`
3. Student updates video progress to 100% using `/progress/video/{video_uuid}`

### How It Works

```javascript
// When student marks video as complete
PUT /progress/video/{video_uuid}
{
    "last_position_sec": 300,
    "delta_seconds_watched": 50,
    "completed": true  // ← Triggers check
}

// System automatically:
// 1. Checks if all videos in the course are completed
// 2. If yes, generates certificate
// 3. Certificate is available in /certificates/my-certificates
```

### Manual Certificate Generation

Students can also manually claim certificates:

```bash
POST /certificates/course/{course_uuid}/claim
```

## Certificate Verification Flow

### For Students
1. Complete all videos in a course
2. Certificate automatically generated
3. View certificate in `/certificates/my-certificates`
4. Share verification code with employers

### For Employers/Verifiers
1. Receive certificate code from student
2. Visit verification endpoint: `GET /certificates/verify/{code}`
3. Verify student name, course, and issue date
4. Check if certificate is revoked

### Example Verification

```bash
# Verify certificate by code
curl -X GET "http://localhost:8000/certificates/verify/ABC123DE"

# Response
{
    "certificate_id": "cert-uuid",
    "student_name": "John Doe",
    "course_title": "Introduction to Python",
    "issued_at": "2025-11-13T10:30:00Z",
    "code": "ABC123DE",
    "revoked": false,
    "completion_percentage": 100.0
}
```

## S3 Storage

Certificate files are stored in S3:

```
your-s3-bucket/
└── certificates/
    └── {unique-id}/
        └── certificate.pdf
```

**Supported file types:**
- PDF (`.pdf`)
- Images (`.jpg`, `.jpeg`, `.png`)

## Usage Examples

### Student Claims Certificate

```bash
# Check eligibility
curl -X GET "http://localhost:8000/certificates/course/{course_uuid}/eligibility" \
  -H "Authorization: Bearer STUDENT_TOKEN"

# Claim certificate
curl -X POST "http://localhost:8000/certificates/course/{course_uuid}/claim" \
  -H "Authorization: Bearer STUDENT_TOKEN"

# View all certificates
curl -X GET "http://localhost:8000/certificates/my-certificates" \
  -H "Authorization: Bearer STUDENT_TOKEN"
```

### Admin Issues Certificate

```bash
# Manually issue certificate
curl -X POST "http://localhost:8000/certificates/issue" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "course_uuid": "course-uuid",
    "student_uuid": "student-uuid"
  }'

# Upload certificate PDF
curl -X POST "http://localhost:8000/certificates/{cert_id}/upload" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -F "file=@certificate.pdf"
```

### Admin Manages Certificates

```bash
# List all certificates for a course
curl -X GET "http://localhost:8000/certificates/all?course_uuid={course_uuid}" \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Revoke certificate
curl -X POST "http://localhost:8000/certificates/{cert_id}/revoke" \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Restore certificate
curl -X POST "http://localhost:8000/certificates/{cert_id}/restore" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## Certificate Code Format

Certificates have unique verification codes:
- Format: 8 uppercase alphanumeric characters
- Example: `ABC123DE`, `F4E2B9A1`
- Generated from UUID first segment

## Database Indexes

Recommended indexes for performance:

```javascript
db.certificates.createIndex({ "student_uuid": 1, "course_uuid": 1 }, { unique: true })
db.certificates.createIndex({ "code": 1 }, { unique: true })
db.certificates.createIndex({ "course_uuid": 1, "issued_at": -1 })
db.certificates.createIndex({ "revoked": 1 })
```

## Best Practices

1. **Auto-Generation**: Let the system auto-generate certificates when students complete courses
2. **Manual Override**: Use manual issuance only for special cases
3. **File Upload**: Always upload certificate PDF after generation for official records
4. **Verification**: Share verification codes publicly for authenticity
5. **Revocation**: Revoke certificates if issued in error, don't delete
6. **S3 Storage**: Store certificate files in S3 for durability and accessibility

## Security Considerations

1. **Public Verification**: Verification endpoint is public by design
2. **Student Privacy**: Only show student name and course on verification
3. **Revocation**: Check revocation status during verification
4. **Access Control**: Students can only see their own certificates
5. **File Validation**: Only PDF and image files allowed for uploads

## Integration with Progress Tracking

Certificate generation is tightly integrated with progress tracking:

```
Student Progress → Video Completion → Auto Certificate Generation
```

When a student:
1. Watches videos
2. Updates progress
3. Marks video as complete
4. Completes all videos in course
5. **→ Certificate automatically generated**
6. Available in student's certificate list

## Support

For issues or questions:
- Check API documentation at `/docs`
- Review this documentation
- Check certificate status: `GET /certificates/course/{course_uuid}/eligibility`
