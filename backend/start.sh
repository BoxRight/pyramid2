#!/bin/bash
# Start the LAML Contract API development server

cd "$(dirname "$0")/.."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q -r backend/requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Create one with ANTHROPIC_API_KEY for natural language generation."
fi

# Start server
echo "Starting LAML Contract API server..."
echo "Server will be available at http://localhost:8000"
echo "API documentation at http://localhost:8000/docs"
echo ""
cd backend
python main.py

