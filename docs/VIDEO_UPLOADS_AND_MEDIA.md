# Video Uploads and Media Playback

This document describes how to upload videos, replace existing video files, and retrieve playback configurations with anti-download client flags.

## Video Model (Updated)

Videos can be either URL-based or file-upload based.

```
{
  "uuid_id": "string",
  "course_uuid": "string",
  "topic_uuid": "string",
  "title": "string",
  "description": "string|null",
  "duration_seconds": 0,
  "is_preview": false,
  "order_index": 1,
  "source_type": "url|upload",
  "video_url": "string|null",           // when source_type = "url"
  "storage_key": "string|null",         // when source_type = "upload"
  "mime_type": "string|null",
  "size_bytes": 0,
  "original_filename": "string|null"
}
```

## Upload Endpoints

- Upload new video and create a Video under a Topic
  - POST `/uploads/video/topic/{topic_uuid}`
  - Headers: `Authorization: Bearer <token>` (admin/teacher)
  - Body: `multipart/form-data` with one field `file`
  - Response: `{ detail, video_uuid, storage_key, size_bytes }`

- Replace existing Video file
  - POST `/uploads/video/{video_uuid}`
  - Headers: `Authorization: Bearer <token>` (admin/teacher)
  - Body: `multipart/form-data` with `file`
  - Response: `{ detail, video_uuid, storage_key, size_bytes }`

Files are stored under `MEDIA_ROOT` (default `media`). Ensure the server process has write permission.

## Media Playback (API 3)

- Get playback configuration
  - GET `/media/video/{video_uuid}`
  - Auth required. Students must be assigned to the course.
  - Returns `VideoPlaybackConfig` with:
    - `stream_url`: `/media/file/{video_uuid}` for uploads, or `video_url` for URL-based videos
    - `expires_at`: short-lived expiry hint
    - `headers`: `{ "Cache-Control": "no-store" }`
    - `client_flags`: suggests UI to deter downloading (e.g., `controlsList="nodownload"`, disable context menu, watermark)

- Stream uploaded file
  - GET `/media/file/{video_uuid}`
  - Auth required. Students must be assigned to the course.
  - Serves file with `inline` disposition and `no-store` caching.

## Front-End Guidance

- Apply client flags from `VideoPlaybackConfig` to the video player
- Disable right-click context menu on video container
- Set `controlsList="nodownload"` on the video element when supported
- Overlay a dynamic watermark with user email/time (prevents clean screen recordings)

Note: Full prevention of downloads/screenshots is not possible without DRM; this design implements practical deterrents.

