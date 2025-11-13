from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config.database import connect_to_mongo, close_mongo_connection
from routes import admin, student, auth
from routes import teachers, courses, topics, videos, comments
from routes import assignments, media, progress
from routes import certificates, devices
from routes import uploads, departments

@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_to_mongo()
    yield
    close_mongo_connection()

app = FastAPI(
    title="Online Course Management API",
    description="FastAPI backend for managing online courses with admin and student roles",
    version="1.0.0",
    lifespan=lifespan
)

# ✅ Create a root router (no `/api` prefix — routes are mounted at root)
api_router = APIRouter()

# ✅ Add all sub-routers to the API router
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(student.router)
api_router.include_router(teachers.router)
api_router.include_router(courses.router)
api_router.include_router(topics.router)
api_router.include_router(videos.router)
api_router.include_router(comments.router)
api_router.include_router(assignments.router)
api_router.include_router(media.router)
api_router.include_router(progress.router)
api_router.include_router(certificates.router)
api_router.include_router(devices.router)
api_router.include_router(uploads.router)
api_router.include_router(departments.router)

# ✅ Mount the API router to the app
app.include_router(api_router)

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://43.205.78.243",
    "https://demolmsdsiar.netlify.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to Online Course Management API", "docs": "/docs"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
