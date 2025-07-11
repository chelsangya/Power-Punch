#!/bin/bash

# Power Punch Boxing Game Startup Script

echo "🥊 Power Punch Boxing Game Startup"
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv venv"
    echo "Then: source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if MongoDB is running
echo "🔍 Checking MongoDB connection..."
python setup_mongodb.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎮 Starting Power Punch Boxing Game..."
    echo "📝 Remember to enter your username when prompted!"
    echo ""
    python boxing.py
else
    echo ""
    echo "❌ Cannot start game - MongoDB setup failed"
    echo "Please make sure MongoDB is installed and running:"
    echo "  brew install mongodb-community"
    echo "  brew services start mongodb-community"
fi
