#!/bin/bash

# Backend restart script
# Kills any existing process on port 8000 and starts the Flask app

echo "🛑 Stopping backend server..."

# Kill any process using port 8000
PID=$(lsof -ti:8000)
if [ ! -z "$PID" ]; then
    kill $PID 2>/dev/null
    sleep 1
    echo "✅ Backend stopped (PID: $PID)"
else
    echo "ℹ️  No backend process found on port 8000"
fi

# Make sure we're in the backend directory
cd "$(dirname "$0")"

echo "🚀 Starting backend server..."
echo "📍 Backend will be available at http://localhost:8000"
echo ""

# Start the Flask app
python3 app.py

