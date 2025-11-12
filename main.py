from fastapi import FastAPI
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
    """
    Lifespan event handler for startup and shutdown
    """
    # Startup
    connect_to_mongo()
    yield
    # Shutdown
    close_mongo_connection()

# Create FastAPI app
app = FastAPI(
    title="Online Course Management API",
    description="FastAPI backend for managing online courses with admin and student roles",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(student.router)
app.include_router(teachers.router)
app.include_router(courses.router)
app.include_router(topics.router)
app.include_router(videos.router)
app.include_router(comments.router)
app.include_router(assignments.router)
app.include_router(media.router)
app.include_router(progress.router)
app.include_router(certificates.router)
app.include_router(devices.router)
app.include_router(uploads.router)
app.include_router(departments.router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Online Course Management API",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
