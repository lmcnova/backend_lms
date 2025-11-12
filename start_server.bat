@echo off
echo ============================================
echo Starting FastAPI Server with Auto-Reload
echo ============================================
echo.
echo Server will automatically restart when code changes are detected.
echo Press Ctrl+C to stop the server.
echo.

cd /d "%~dp0"

REM Check if MongoDB is running
echo Checking MongoDB connection...
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000); client.server_info(); print('MongoDB is running!')" 2>nul
if errorlevel 1 (
    echo WARNING: MongoDB might not be running!
    echo Please start MongoDB service before running this server.
    echo.
    pause
)

echo Starting FastAPI server on http://localhost:8000
echo API Documentation will be available at http://localhost:8000/docs
echo.

python main.py

pause
