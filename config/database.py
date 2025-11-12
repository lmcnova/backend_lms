from pymongo import MongoClient
from pymongo.database import Database
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "online_course_db")

client: MongoClient = None
database: Database = None

def connect_to_mongo():
    """Connect to MongoDB"""
    global client, database
    try:
        client = MongoClient(MONGODB_URL)
        database = client[DATABASE_NAME]
        print(f"Connected to MongoDB: {DATABASE_NAME}")
        # Backfill role field for existing records
        try:
            database.admins.update_many({"role": {"$exists": False}}, {"$set": {"role": "admin"}})
            database.students.update_many({"role": {"$exists": False}}, {"$set": {"role": "student"}})
            # Helpful indexes
            try:
                database.sessions.create_index([("user_uuid", 1), ("revoked", 1)])
                database.sessions.create_index("last_used_at")
                database.teachers.create_index("email_id", unique=True)
                database.courses.create_index("slug", unique=True)
                database.topics.create_index([("course_uuid", 1), ("order_index", 1)], unique=True)
                database.videos.create_index([("topic_uuid", 1), ("order_index", 1)], unique=True)
                database.videos.create_index("course_uuid")
                database.comments.create_index("parent_uuid")
                database.comments.create_index("course_uuid")
                # Assignments & Progress
                database.user_courses.create_index([("student_uuid", 1), ("course_uuid", 1)], unique=True)
                database.user_courses.create_index("course_uuid")
                database.user_progress.create_index([("student_uuid", 1), ("video_uuid", 1)], unique=True)
                database.user_progress.create_index([("student_uuid", 1), ("course_uuid", 1)])
                # Certificates and device resets
                database.certificates.create_index([("student_uuid", 1), ("course_uuid", 1)], unique=True)
                database.device_resets.create_index([("student_uuid", 1), ("status", 1)])
            except Exception as ie:
                print(f"Warning: could not ensure session indexes: {ie}")
        except Exception as e:
            # Non-fatal; log and continue
            print(f"Warning: could not backfill roles: {e}")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        raise e

def close_mongo_connection():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        print("MongoDB connection closed")

def get_database() -> Database:
    """Get database instance"""
    return database
