#!/bin/bash

echo "Starting Online Course Management API..."
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your settings"
    echo
fi

# Start the application
echo "Starting FastAPI server..."
echo "API will be available at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo
python main.py
