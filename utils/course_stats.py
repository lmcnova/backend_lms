from config.database import get_database


def recompute_course_counts(course_uuid: str):
    db = get_database()
    topics_count = db.topics.count_documents({"course_uuid": course_uuid})
    videos_count = db.videos.count_documents({"course_uuid": course_uuid})
    comments_count = db.comments.count_documents({"course_uuid": course_uuid, "status": {"$ne": "deleted"}})
    db.courses.update_one(
        {"uuid_id": course_uuid},
        {"$set": {
            "total_topics": topics_count,
            "total_videos": videos_count,
            "total_comments": comments_count,
        }}
    )

