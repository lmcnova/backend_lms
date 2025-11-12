from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class VideoPlaybackConfig(BaseModel):
    video_uuid: str
    course_uuid: str
    stream_url: str
    expires_at: Optional[datetime] = None
    headers: Optional[Dict[str, str]] = None
    client_flags: Dict[str, Any] = {
        "controlsList": "nodownload",
        "disableContextMenu": True,
        "draggable": False,
        "watermark": True,
    }

