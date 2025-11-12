"""
Seed demo data: Teachers, Courses (AI, ML, Python) with Topics and 5 Videos each.
Run: python -m scripts.seed_courses
"""
from uuid import uuid4
from datetime import datetime

from config.database import connect_to_mongo, close_mongo_connection, get_database
from utils.slug import slugify


def upsert_teacher(db, name: str, email: str) -> str:
    t = db.teachers.find_one({"email_id": email})
    if t:
        return t["uuid_id"]
    tid = str(uuid4())
    db.teachers.insert_one({
        "uuid_id": tid,
        "name": name,
        "email_id": email,
        "bio": None,
        "avatar_url": None,
        "skills": [],
        "social_links": None,
        "role": "teacher",
        "hashed_password": "",
    })
    return tid


def upsert_course(db, title: str, category: str, level: str, instructor_uuid: str) -> str:
    slug = slugify(title)
    c = db.courses.find_one({"slug": slug})
    if c:
        return c["uuid_id"]
    cid = str(uuid4())
    db.courses.insert_one({
        "uuid_id": cid,
        "title": title,
        "slug": slug,
        "category": category,
        "level": level,
        "description": f"{title} course",
        "tags": [category.lower(), title.split()[0].lower()],
        "thumbnail_url": None,
        "intro_video_url": None,
        "instructor_uuid": instructor_uuid,
        "co_instructor_uuids": [],
        "total_topics": 0,
        "total_videos": 0,
        "total_comments": 0,
    })
    return cid


def add_topic(db, course_uuid: str, title: str, order_index: int) -> str:
    tid = str(uuid4())
    db.topics.insert_one({
        "uuid_id": tid,
        "course_uuid": course_uuid,
        "title": title,
        "description": None,
        "order_index": order_index,
    })
    return tid


def add_video(db, course_uuid: str, topic_uuid: str, title: str, order_index: int, duration: int = 300):
    vid = str(uuid4())
    db.videos.insert_one({
        "uuid_id": vid,
        "course_uuid": course_uuid,
        "topic_uuid": topic_uuid,
        "title": title,
        "description": f"{title} description",
        "video_url": f"https://example.com/videos/{vid}.mp4",
        "thumbnail_url": None,
        "duration_seconds": duration,
        "is_preview": order_index == 1,
        "order_index": order_index,
    })


def recompute_counts(db, course_uuid: str):
    topics_count = db.topics.count_documents({"course_uuid": course_uuid})
    videos_count = db.videos.count_documents({"course_uuid": course_uuid})
    comments_count = db.comments.count_documents({"course_uuid": course_uuid, "status": {"$ne": "deleted"}})
    db.courses.update_one({"uuid_id": course_uuid}, {"$set": {
        "total_topics": topics_count,
        "total_videos": videos_count,
        "total_comments": comments_count,
    }})


def run():
    connect_to_mongo()
    db = get_database()

    instructor = upsert_teacher(db, "Dr. Ada Lovelace", "ada@demo.local")

    courses = [
        ("Artificial Intelligence (AI)", "AI", "beginner"),
        ("Machine Learning (ML)", "ML", "beginner"),
        ("Python Programming", "Python", "beginner"),
    ]

    for title, category, level in courses:
        cid = upsert_course(db, title, category, level, instructor)
        # Create 3 topics
        t1 = add_topic(db, cid, "Introduction", 1)
        t2 = add_topic(db, cid, "Fundamentals", 2)
        t3 = add_topic(db, cid, "Hands-on", 3)
        topics = [t1, t2, t3]
        # Add 5 videos total across topics
        add_video(db, cid, t1, f"{title} - Welcome", 1, 180)
        add_video(db, cid, t1, f"{title} - Overview", 2, 240)
        add_video(db, cid, t2, f"{title} - Basics", 1, 360)
        add_video(db, cid, t2, f"{title} - Core Concepts", 2, 420)
        add_video(db, cid, t3, f"{title} - Project Setup", 1, 300)
        recompute_counts(db, cid)

    close_mongo_connection()


if __name__ == "__main__":
    run()

