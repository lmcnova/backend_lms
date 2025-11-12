from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from uuid import uuid4

from models.topic import TopicCreate, TopicUpdate, TopicResponse
from config.database import get_database
from utils.course_stats import recompute_course_counts
from utils.dependencies import require_admin_or_teacher


router = APIRouter(prefix="/topics", tags=["Topics"])


@router.get("/course/{course_id}", response_model=List[TopicResponse])
async def list_topics(course_id: str):
    db = get_database()
    if not db.courses.find_one({"uuid_id": course_id}):
        raise HTTPException(status_code=404, detail="Course not found")
    docs = list(db.topics.find({"course_uuid": course_id}, {"_id": 0}).sort("order_index", 1))
    return docs


@router.post("/course/{course_id}", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(course_id: str, topic: TopicCreate, identity = Depends(require_admin_or_teacher)):
    db = get_database()
    if not db.courses.find_one({"uuid_id": course_id}):
        raise HTTPException(status_code=404, detail="Course not found")
    # Determine order_index
    order = topic.order_index
    if order is None:
        last = db.topics.find({"course_uuid": course_id}).sort("order_index", -1).limit(1)
        try:
            order = list(last)[0]["order_index"] + 1
        except IndexError:
            order = 1
    doc = topic.model_dump()
    doc.update({
        "uuid_id": str(uuid4()),
        "course_uuid": course_id,
        "order_index": order,
    })
    if identity["role"] == "admin":
        doc["admin_uuid_id"] = identity["user_uuid"]
        doc["teacher_uuid_id"] = None
    else:
        doc["admin_uuid_id"] = None
        doc["teacher_uuid_id"] = identity["user_uuid"]
    # Ensure uniqueness by shifting if needed
    conflict = db.topics.find_one({"course_uuid": course_id, "order_index": order})
    if conflict:
        db.topics.update_many({"course_uuid": course_id, "order_index": {"$gte": order}}, {"$inc": {"order_index": 1}})
    db.topics.insert_one(doc)
    recompute_course_counts(course_id)
    return TopicResponse(**doc)


@router.put("/{topic_id}", response_model=TopicResponse)
async def update_topic(topic_id: str, update: TopicUpdate, identity = Depends(require_admin_or_teacher)):
    db = get_database()
    existing = db.topics.find_one({"uuid_id": topic_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Topic not found")
    course_uuid = existing["course_uuid"]
    data = update.model_dump(exclude_unset=True)
    if "order_index" in data and data["order_index"] != existing.get("order_index"):
        new = data["order_index"]
        # Insert at new index: shift others appropriately
        if new < existing["order_index"]:
            db.topics.update_many({"course_uuid": course_uuid, "order_index": {"$gte": new, "$lt": existing["order_index"]}}, {"$inc": {"order_index": 1}})
        else:
            db.topics.update_many({"course_uuid": course_uuid, "order_index": {"$gt": existing["order_index"], "$lte": new}}, {"$inc": {"order_index": -1}})
    if data:
        db.topics.update_one({"uuid_id": topic_id}, {"$set": data})
    doc = db.topics.find_one({"uuid_id": topic_id})
    return TopicResponse(**{k: v for k, v in doc.items() if k != "_id"})


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(topic_id: str, identity = Depends(require_admin_or_teacher)):
    db = get_database()
    existing = db.topics.find_one({"uuid_id": topic_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Topic not found")
    course_uuid = existing["course_uuid"]
    # delete videos under topic and their comments
    vids = list(db.videos.find({"topic_uuid": topic_id}, {"uuid_id": 1, "_id": 0}))
    vid_ids = [v["uuid_id"] for v in vids]
    if vid_ids:
        db.comments.delete_many({"parent_type": "video", "parent_uuid": {"$in": vid_ids}})
        db.user_progress.delete_many({"video_uuid": {"$in": vid_ids}})
    db.videos.delete_many({"topic_uuid": topic_id})
    # delete comments on topic
    db.comments.delete_many({"parent_type": "topic", "parent_uuid": topic_id})
    db.topics.delete_one({"uuid_id": topic_id})
    recompute_course_counts(course_uuid)
    return None
