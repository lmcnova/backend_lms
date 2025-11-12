# S3 Upload Implementation Summary

## Overview
Successfully implemented AWS S3 storage for all image and video uploads in the Online Course Management API. The system supports both S3 and local storage, configurable via environment variables.

## Files Modified/Created

### 1. Core Files

#### `requirements.txt`
- Added `boto3==1.35.36` for AWS S3 integration

#### `.env.example`
- Added AWS S3 configuration variables:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_REGION`
  - `S3_BUCKET_NAME`
  - `USE_S3` (toggle between S3 and local storage)

### 2. Utility Files

#### `utils/s3_storage.py` (NEW)
Complete S3 storage service with:
- Upload methods for videos, images, and thumbnails
- Presigned URL generation for secure access
- File deletion functionality
- Support for both S3 and local storage
- Automatic folder organization

### 3. Route Files

#### `routes/uploads.py`
Updated all upload endpoints to use S3:
- `POST /uploads/video/topic/{topic_uuid}` - Upload video with S3 support
- `POST /uploads/video/{video_uuid}` - Replace video with S3 support
- `POST /uploads/thumbnail/{video_uuid}` - Upload video thumbnail to S3
- `POST /uploads/course-thumbnail/{course_uuid}` - Upload course thumbnail to S3
- `POST /uploads/image` - Upload general images to S3

#### `routes/media.py`
Updated media serving endpoints:
- `GET /media/video/{video_uuid}` - Generate presigned URLs for S3 videos
- `GET /media/thumbnail/{video_uuid}` - Get thumbnail with S3 support
- `GET /media/image/{storage_key}` - Get images with S3 support

#### `routes/courses.py`
Updated course endpoints for S3:
- `POST /courses/` - Create course with thumbnail and intro_video uploads to S3
- `POST /courses/{course_id}/thumbnail` - Upload course thumbnail to S3
- `POST /courses/{course_id}/intro-video` - Upload intro video to S3
- `GET /courses/{course_id}/thumbnail/file` - Serve thumbnail with S3 presigned URLs
- `GET /courses/{course_id}/intro-video/file` - Serve intro video with S3 presigned URLs

#### `routes/videos.py`
Updated video creation endpoint:
- `POST /videos/topic/{topic_id}` - Create video with video_file and thumbnail uploads to S3

### 4. Model Files

#### `models/video.py`
- Added `thumbnail_storage_key` field to track S3 storage keys for thumbnails

#### `models/course.py`
- Added `thumbnail_storage_key` field for course thumbnails
- Added `intro_video_storage_key` field for course intro videos

### 5. Documentation

#### `docs/S3_UPLOAD_SETUP.md` (NEW)
Comprehensive documentation covering:
- AWS S3 setup instructions
- IAM policy configuration
- API endpoint documentation
- Database schema
- Security best practices
- Troubleshooting guide
- Example usage

## S3 Folder Structure

```
your-s3-bucket/
├── videos/
│   └── {video-uuid}/
│       └── video-file.mp4
├── thumbnails/
│   └── {video-uuid}/
│       └── thumbnail.jpg
├── course-thumbnails/
│   └── {unique-id}/
│       └── course-thumb.jpg
├── course-intro-videos/
│   └── {unique-id}/
│       └── intro.mp4
└── images/
    └── {unique-id}/
        └── image.jpg
```

## Database Schema Changes

### Video Document
```javascript
{
    "uuid_id": "video-uuid",
    "video_url": "https://bucket.s3.region.amazonaws.com/videos/uuid/file.mp4",  // S3 URL
    "thumbnail_url": "https://bucket.s3.region.amazonaws.com/thumbnails/uuid/thumb.jpg",  // S3 URL
    "storage_key": "videos/uuid/file.mp4",  // S3 key
    "thumbnail_storage_key": "thumbnails/uuid/thumb.jpg",  // S3 key
    // ... other fields
}
```

### Course Document
```javascript
{
    "uuid_id": "course-uuid",
    "thumbnail_url": "https://bucket.s3.region.amazonaws.com/course-thumbnails/uuid/thumb.jpg",  // S3 URL
    "thumbnail_storage_key": "course-thumbnails/uuid/thumb.jpg",  // S3 key
    "intro_video_url": "https://bucket.s3.region.amazonaws.com/course-intro-videos/uuid/intro.mp4",  // S3 URL
    "intro_video_storage_key": "course-intro-videos/uuid/intro.mp4",  // S3 key
    // ... other fields
}
```

## API Endpoints Summary

### Video Uploads
1. **POST /videos/topic/{topic_id}** (Recommended)
   - Create video with video_file and thumbnail
   - Both uploaded to S3
   - S3 URLs stored in database

2. **POST /uploads/video/topic/{topic_uuid}**
   - Alternative video upload method
   - Uploads to S3

3. **POST /uploads/video/{video_uuid}**
   - Replace existing video
   - Deletes old file from S3

4. **POST /uploads/thumbnail/{video_uuid}**
   - Upload video thumbnail to S3
   - Deletes old thumbnail

### Course Uploads
1. **POST /courses/**
   - Create course with thumbnail and intro_video
   - Both uploaded to S3
   - S3 URLs stored in database

2. **POST /courses/{course_id}/thumbnail**
   - Upload course thumbnail to S3

3. **POST /courses/{course_id}/intro-video**
   - Upload course intro video to S3

### Image Uploads
1. **POST /uploads/image**
   - General image upload to S3

### Media Serving
1. **GET /media/video/{video_uuid}**
   - Returns presigned S3 URL (15 min expiration)

2. **GET /media/thumbnail/{video_uuid}**
   - Returns presigned S3 URL (1 hour expiration)

3. **GET /courses/{course_id}/thumbnail/file**
   - Returns presigned S3 URL for course thumbnail

4. **GET /courses/{course_id}/intro-video/file**
   - Returns presigned S3 URL for intro video

## Key Features

1. **Flexible Storage**
   - Toggle between S3 and local storage with `USE_S3` environment variable
   - Seamless switching without code changes

2. **Secure Access**
   - Private S3 bucket with presigned URLs
   - Configurable expiration times (15 min for videos, 1 hour for images)

3. **Organized Structure**
   - Files organized in folders by type
   - Unique identifiers prevent conflicts

4. **URL Storage**
   - S3 URLs stored in database for easy access
   - Storage keys stored for file management

5. **Automatic Cleanup**
   - Old files deleted when replaced
   - Prevents storage waste

6. **Backward Compatible**
   - Works with existing local storage setup
   - No breaking changes to API

## Configuration

### Environment Variables
```env
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
USE_S3=true  # Set to 'true' to use S3, 'false' for local storage
```

### Installation
```bash
pip install -r requirements.txt
```

## Usage Example

### Create Video with Upload
```bash
curl -X POST "http://localhost:8000/videos/topic/{topic_id}" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F 'video={"title":"Introduction to Python","description":"Learn Python basics","duration_seconds":600}' \
  -F "video_file=@video.mp4" \
  -F "thumbnail=@thumbnail.jpg"
```

### Create Course with Files
```bash
curl -X POST "http://localhost:8000/courses/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F 'course={"title":"Python Course","category":"Programming","level":"beginner","instructor_uuid":"teacher-uuid"}' \
  -F "thumbnail=@course-thumb.jpg" \
  -F "intro_video=@intro.mp4"
```

## Security Considerations

1. **Private Bucket**: S3 bucket should be private
2. **Presigned URLs**: Temporary URLs with expiration
3. **IAM Permissions**: Least-privilege access policy
4. **Access Control**: Upload endpoints require authentication
5. **File Validation**: MIME type checking before upload

## Testing Checklist

- [ ] Set AWS credentials in .env
- [ ] Set USE_S3=true
- [ ] Test video upload with thumbnail
- [ ] Test course creation with files
- [ ] Verify files appear in S3 bucket
- [ ] Test presigned URL generation
- [ ] Test video playback
- [ ] Test file replacement (old files deleted)
- [ ] Test with USE_S3=false (local storage fallback)

## Migration Notes

### From Local to S3
1. Configure AWS S3 bucket and IAM user
2. Update .env with AWS credentials
3. Set USE_S3=true
4. Restart application
5. New uploads automatically go to S3
6. Existing local files continue to work
7. Optionally migrate existing files manually

## Support

For detailed documentation, see:
- `docs/S3_UPLOAD_SETUP.md` - Complete S3 setup guide
- API documentation at `/docs` endpoint
- AWS S3 documentation

## Summary

All image and video upload endpoints now support S3 storage:
- ✅ Video files → S3
- ✅ Video thumbnails → S3
- ✅ Course thumbnails → S3
- ✅ Course intro videos → S3
- ✅ General images → S3
- ✅ Presigned URLs for secure access
- ✅ Database stores S3 URLs
- ✅ Automatic file cleanup
- ✅ Backward compatible with local storage
