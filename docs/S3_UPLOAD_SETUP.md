# S3 Upload Configuration Guide

This guide explains how to configure and use AWS S3 for storing uploaded images and videos in the Online Course Management API.

## Features

- Upload videos and images to AWS S3 or local storage
- Automatic file organization by type (videos, images, thumbnails, course-thumbnails)
- Presigned URL generation for secure access to private S3 objects
- Fallback to local storage when S3 is not configured
- Support for video thumbnails and course thumbnails
- Automatic cleanup of old files when replacing uploads

## Configuration

### Environment Variables

Add the following variables to your `.env` file:

```env
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
USE_S3=true
```

### Configuration Options

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `USE_S3` | No | `false` | Enable S3 storage. Set to `true` to use S3, `false` for local storage |
| `AWS_ACCESS_KEY_ID` | Yes (if USE_S3=true) | - | AWS access key ID |
| `AWS_SECRET_ACCESS_KEY` | Yes (if USE_S3=true) | - | AWS secret access key |
| `AWS_REGION` | No | `us-east-1` | AWS region where your S3 bucket is located |
| `S3_BUCKET_NAME` | Yes (if USE_S3=true) | - | Name of your S3 bucket |
| `MEDIA_ROOT` | No | `media` | Local directory for file storage when USE_S3=false |

## AWS S3 Setup

### 1. Create an S3 Bucket

1. Go to [AWS S3 Console](https://s3.console.aws.amazon.com/)
2. Click "Create bucket"
3. Choose a unique bucket name
4. Select your preferred region
5. Configure bucket settings:
   - Block all public access: **Recommended** (files will use presigned URLs)
   - Versioning: Optional
   - Server-side encryption: Recommended

### 2. Create IAM User

1. Go to [AWS IAM Console](https://console.aws.amazon.com/iam/)
2. Create a new user with programmatic access
3. Attach the following policy (replace `YOUR-BUCKET-NAME`):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::YOUR-BUCKET-NAME/*",
                "arn:aws:s3:::YOUR-BUCKET-NAME"
            ]
        }
    ]
}
```

4. Save the Access Key ID and Secret Access Key

### 3. Configure CORS (Optional)

If you need to access files directly from a web browser, configure CORS on your bucket:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "HEAD"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": ["ETag"],
        "MaxAgeSeconds": 3000
    }
]
```

## Installation

Install boto3 (AWS SDK for Python):

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install boto3==1.35.36
```

## API Endpoints

### Create Video with Upload (Recommended)

Create a new video with file upload and optional thumbnail.

**Endpoint:** `POST /videos/topic/{topic_id}`

**Authentication:** Admin or Teacher required

**Request (multipart/form-data):**
- `topic_id`: UUID of the topic
- `video`: JSON string with video metadata (title, description, etc.)
- `video_file`: Video file (optional)
- `thumbnail`: Thumbnail image file (optional)

**Example JSON for `video` field:**
```json
{
    "title": "Introduction to Python",
    "description": "Learn Python basics",
    "duration_seconds": 600,
    "is_preview": false
}
```

**Response:**
```json
{
    "uuid_id": "video-uuid",
    "course_uuid": "course-uuid",
    "topic_uuid": "topic-uuid",
    "title": "Introduction to Python",
    "description": "Learn Python basics",
    "video_url": "https://bucket.s3.region.amazonaws.com/videos/uuid/video.mp4",
    "thumbnail_url": "https://bucket.s3.region.amazonaws.com/thumbnails/uuid/thumb.jpg",
    "storage_key": "videos/uuid/video.mp4",
    "thumbnail_storage_key": "thumbnails/uuid/thumb.jpg",
    "source_type": "upload",
    "mime_type": "video/mp4",
    "size_bytes": 1024000,
    "order_index": 1
}
```

### Upload Video to Topic (Alternative)

Upload a new video file for a specific topic.

**Endpoint:** `POST /uploads/video/topic/{topic_uuid}`

**Authentication:** Admin or Teacher required

**Request:**
- `topic_uuid`: UUID of the topic
- `file`: Video file (multipart/form-data)

**Response:**
```json
{
    "detail": "uploaded",
    "video_uuid": "uuid-here",
    "storage_key": "videos/uuid/filename.mp4",
    "video_url": "https://bucket.s3.region.amazonaws.com/videos/uuid/filename.mp4",
    "size_bytes": 1024000
}
```

### Replace Video

Replace an existing video file.

**Endpoint:** `POST /uploads/video/{video_uuid}`

**Authentication:** Admin or Teacher required

**Request:**
- `video_uuid`: UUID of the video to replace
- `file`: Video file (multipart/form-data)

**Response:**
```json
{
    "detail": "uploaded",
    "video_uuid": "uuid-here",
    "storage_key": "videos/uuid/filename.mp4",
    "video_url": "https://bucket.s3.region.amazonaws.com/videos/uuid/filename.mp4",
    "size_bytes": 1024000
}
```

### Upload Video Thumbnail

Upload a thumbnail image for a video.

**Endpoint:** `POST /uploads/thumbnail/{video_uuid}`

**Authentication:** Admin or Teacher required

**Request:**
- `video_uuid`: UUID of the video
- `file`: Image file (multipart/form-data)

**Response:**
```json
{
    "detail": "thumbnail uploaded",
    "video_uuid": "uuid-here",
    "thumbnail_url": "https://bucket.s3.region.amazonaws.com/thumbnails/uuid/image.jpg",
    "storage_key": "thumbnails/uuid/image.jpg",
    "size_bytes": 50000
}
```

### Upload Course Thumbnail

Upload a thumbnail image for a course.

**Endpoint:** `POST /uploads/course-thumbnail/{course_uuid}`

**Authentication:** Admin or Teacher required

**Request:**
- `course_uuid`: UUID of the course
- `file`: Image file (multipart/form-data)

**Response:**
```json
{
    "detail": "course thumbnail uploaded",
    "course_uuid": "uuid-here",
    "thumbnail_url": "https://bucket.s3.region.amazonaws.com/course-thumbnails/uuid/image.jpg",
    "storage_key": "course-thumbnails/uuid/image.jpg",
    "size_bytes": 50000
}
```

### Upload General Image

Upload a general image (for profile pictures, etc.).

**Endpoint:** `POST /uploads/image`

**Authentication:** Admin or Teacher required

**Request:**
- `file`: Image file (multipart/form-data)

**Response:**
```json
{
    "detail": "image uploaded",
    "storage_key": "images/uuid/image.jpg",
    "image_url": "https://bucket.s3.region.amazonaws.com/images/uuid/image.jpg",
    "size_bytes": 50000,
    "mime_type": "image/jpeg"
}
```

### Get Video Playback URL

Get a presigned URL for video playback.

**Endpoint:** `GET /media/video/{video_uuid}`

**Authentication:** Required (Student must be enrolled in course)

**Response:**
```json
{
    "video_uuid": "uuid-here",
    "course_uuid": "course-uuid",
    "stream_url": "presigned-url-or-local-path",
    "expires_at": "2025-11-13T12:00:00",
    "headers": {"Cache-Control": "no-store"},
    "client_flags": {
        "controlsList": "nodownload",
        "disableContextMenu": true,
        "draggable": false,
        "watermark": true,
        "contentSecurityPolicy": "default-src 'self'; media-src 'self'; frame-ancestors 'none'"
    }
}
```

### Get Thumbnail

Get thumbnail URL for a video.

**Endpoint:** `GET /media/thumbnail/{video_uuid}`

**Authentication:** Public (no authentication required)

**Response:**
```json
{
    "thumbnail_url": "presigned-url-or-local-path"
}
```

### Get Image

Get image by storage key.

**Endpoint:** `GET /media/image/{storage_key}`

**Authentication:** Public (no authentication required)

**Response:**
```json
{
    "image_url": "presigned-url-or-local-path"
}
```

## Storage Structure

### S3 Folder Organization

```
bucket-name/
├── videos/
│   └── {video-uuid}/
│       └── {filename}.mp4
├── thumbnails/
│   └── {video-uuid}/
│       └── {filename}.jpg
├── course-thumbnails/
│   └── {unique-id}/
│       └── {filename}.jpg
└── images/
    └── {unique-id}/
        └── {filename}.jpg
```

### Local Storage Organization

When `USE_S3=false`, files are stored locally in the `MEDIA_ROOT` directory with the same structure.

## Database Schema

### Video Document

```javascript
{
    "uuid_id": "video-uuid",
    "course_uuid": "course-uuid",
    "topic_uuid": "topic-uuid",
    "title": "Video Title",
    "description": "Video description",
    "video_url": "https://bucket.s3.region.amazonaws.com/videos/uuid/file.mp4",  // S3 URL or null
    "thumbnail_url": "https://bucket.s3.region.amazonaws.com/thumbnails/uuid/thumb.jpg",  // S3 URL or null
    "storage_key": "videos/uuid/file.mp4",  // S3 key or local path
    "thumbnail_storage_key": "thumbnails/uuid/thumb.jpg",  // S3 key or local path
    "source_type": "upload",  // "upload" or "url"
    "mime_type": "video/mp4",
    "size_bytes": 1024000,
    "original_filename": "file.mp4",
    "duration_seconds": 600,
    "is_preview": false,
    "order_index": 1,
    "admin_uuid_id": "admin-uuid",
    "teacher_uuid_id": null
}
```

### Course Document

```javascript
{
    "uuid_id": "course-uuid",
    "title": "Course Title",
    "thumbnail_url": "https://bucket.s3.region.amazonaws.com/course-thumbnails/uuid/thumb.jpg",  // S3 URL or null
    "thumbnail_storage_key": "course-thumbnails/uuid/thumb.jpg",  // S3 key or local path
    // ... other fields
}
```

## Migration from Local to S3

To migrate from local storage to S3:

1. Set up your S3 bucket and IAM credentials
2. Update your `.env` file with S3 configuration
3. Set `USE_S3=true`
4. Restart your application
5. New uploads will automatically go to S3
6. Optionally, manually migrate existing files:
   - Upload existing files to S3
   - Update database records with S3 URLs and storage keys

## Security Considerations

1. **Private Bucket**: Keep your S3 bucket private and use presigned URLs for access
2. **Presigned URLs**: URLs expire after 15 minutes for videos and 1 hour for images
3. **IAM Permissions**: Use least-privilege IAM policy
4. **Access Control**: Upload endpoints require admin/teacher authentication
5. **File Validation**: Validate file types and sizes before upload
6. **CORS**: Only configure CORS if necessary for your use case

## Troubleshooting

### Error: "AWS credentials and S3_BUCKET_NAME must be set when USE_S3=true"

Make sure all required environment variables are set in your `.env` file.

### Error: "Failed to upload to S3"

Check:
- AWS credentials are correct
- S3 bucket exists and is accessible
- IAM user has required permissions
- Bucket region matches `AWS_REGION` setting

### Video playback not working

For S3 storage:
- Ensure presigned URLs are being generated correctly
- Check that URLs haven't expired
- Verify bucket permissions

For local storage:
- Ensure `MEDIA_ROOT` directory exists and is writable
- Check file paths are correct

## Performance Optimization

1. **CDN**: Use CloudFront CDN in front of S3 for better performance
2. **Multipart Upload**: For large files, consider implementing multipart upload
3. **Compression**: Compress videos before upload
4. **Thumbnails**: Generate thumbnails automatically using AWS Lambda
5. **Caching**: Implement caching headers for static assets

## Cost Considerations

AWS S3 pricing includes:
- Storage costs (per GB per month)
- Request costs (PUT, GET, DELETE)
- Data transfer costs (egress)

Presigned URLs generate GET requests which have minimal cost. Monitor your usage in AWS Cost Explorer.

## Example Usage

### Python Client

```python
import requests

# Upload video
with open('video.mp4', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/uploads/video/topic/{topic_uuid}',
        files={'file': f},
        headers={'Authorization': 'Bearer YOUR_TOKEN'}
    )
    print(response.json())

# Upload thumbnail
with open('thumbnail.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/uploads/thumbnail/{video_uuid}',
        files={'file': f},
        headers={'Authorization': 'Bearer YOUR_TOKEN'}
    )
    print(response.json())
```

### cURL

```bash
# Create video with file and thumbnail upload (Recommended)
curl -X POST "http://localhost:8000/videos/topic/{topic_id}" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F 'video={"title":"Introduction to Python","description":"Learn Python basics","duration_seconds":600,"is_preview":false}' \
  -F "video_file=@video.mp4" \
  -F "thumbnail=@thumbnail.jpg"

# Upload video (Alternative method)
curl -X POST "http://localhost:8000/uploads/video/topic/{topic_uuid}" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@video.mp4"

# Upload thumbnail separately
curl -X POST "http://localhost:8000/uploads/thumbnail/{video_uuid}" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@thumbnail.jpg"

# Upload course thumbnail
curl -X POST "http://localhost:8000/courses/{course_id}/thumbnail" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@course-thumb.jpg"

# Upload course intro video
curl -X POST "http://localhost:8000/courses/{course_id}/intro-video" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@intro.mp4"

# Get video playback URL
curl -X GET "http://localhost:8000/media/video/{video_uuid}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Support

For issues or questions:
- Check the API documentation at `/docs`
- Review AWS S3 documentation
- Check application logs for error details
