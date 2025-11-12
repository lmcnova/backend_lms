@echo off
echo Starting Online Course Management API...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

REM Check if .env exists
if not exist ".env" (
    echo Creating .env file from .env.example...
    copy .env.example .env
    echo Please edit .env file with your settings
    echo.
)

REM Start the application
echo Starting FastAPI server...
echo API will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
python main.py
