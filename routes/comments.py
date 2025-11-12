from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from uuid import uuid4
from datetime import datetime

from models.comment import CommentCreate, CommentUpdate, CommentResponse
from config.database import get_database
from utils.dependencies import get_current_identity
from utils.course_stats import recompute_course_counts


router = APIRouter(prefix="/comments", tags=["Comments"])


@router.get("/topic/{topic_id}", response_model=List[CommentResponse])
async def list_topic_comments(topic_id: str):
    db = get_database()
    if not db.topics.find_one({"uuid_id": topic_id}):
        raise HTTPException(status_code=404, detail="Topic not found")
    docs = list(db.comments.find({"parent_type": "topic", "parent_uuid": topic_id, "status": {"$ne": "deleted"}}, {"_id": 0}).sort("created_at", 1))
    return docs


@router.get("/video/{video_id}", response_model=List[CommentResponse])
async def list_video_comments(video_id: str):
    db = get_database()
    if not db.videos.find_one({"uuid_id": video_id}):
        raise HTTPException(status_code=404, detail="Video not found")
    docs = list(db.comments.find({"parent_type": "video", "parent_uuid": video_id, "status": {"$ne": "deleted"}}, {"_id": 0}).sort("created_at", 1))
    return docs


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(payload: CommentCreate, identity = Depends(get_current_identity)):
    db = get_database()
    parent_type = payload.parent_type
    if parent_type == "topic":
        parent = db.topics.find_one({"uuid_id": payload.parent_uuid})
        if not parent:
            raise HTTPException(status_code=404, detail="Topic not found")
        course_uuid = parent["course_uuid"]
    elif parent_type == "video":
        parent = db.videos.find_one({"uuid_id": payload.parent_uuid})
        if not parent:
            raise HTTPException(status_code=404, detail="Video not found")
        course_uuid = parent["course_uuid"]
    else:
        raise HTTPException(status_code=400, detail="Invalid parent type")

    doc = {
        "uuid_id": str(uuid4()),
        "parent_type": parent_type,
        "parent_uuid": payload.parent_uuid,
        "course_uuid": course_uuid,
        "author_role": identity["role"],
        "author_uuid": identity["user_uuid"],
        "content": payload.content,
        "status": "visible",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    if identity["role"] == "admin":
        doc["admin_uuid_id"] = identity["user_uuid"]
    db.comments.insert_one(doc)
    recompute_course_counts(course_uuid)
    return CommentResponse(**doc)


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(comment_id: str, update: CommentUpdate, identity = Depends(get_current_identity)):
    db = get_database()
    existing = db.comments.find_one({"uuid_id": comment_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Comment not found")
    # Only author or admin/teacher can change status; content editable by author
    data = update.model_dump(exclude_unset=True)
    if identity["user_uuid"] != existing["author_uuid"] and identity["role"] not in ("admin", "teacher"):
        # Allow changing only content if same author; others forbidden
        if "content" in data and len(data) == 1:
            pass
        else:
            raise HTTPException(status_code=403, detail="Not allowed")
    data["updated_at"] = datetime.utcnow()
    db.comments.update_one({"uuid_id": comment_id}, {"$set": data})
    doc = db.comments.find_one({"uuid_id": comment_id})
    return CommentResponse(**{k: v for k, v in doc.items() if k != "_id"})


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: str, identity = Depends(get_current_identity)):
    db = get_database()
    existing = db.comments.find_one({"uuid_id": comment_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Comment not found")
    if identity["user_uuid"] != existing["author_uuid"] and identity["role"] not in ("admin", "teacher"):
        raise HTTPException(status_code=403, detail="Not allowed")
    db.comments.update_one({"uuid_id": comment_id}, {"$set": {"status": "deleted", "updated_at": datetime.utcnow()}})
    recompute_course_counts(existing["course_uuid"])
    return None
