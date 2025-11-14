#!/bin/bash

echo "Starting IT Lab Scheduler..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "Creating virtual environment..."
    cd backend && python3 -m venv venv && cd ..
fi

# Activate virtual environment
echo "Activating virtual environment..."
source backend/venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r backend/requirements.txt

# Run setup
echo "Running setup..."
python setup.py

# Start the application
echo "Starting application..."
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000