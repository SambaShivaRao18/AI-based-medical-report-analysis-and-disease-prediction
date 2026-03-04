#!/bin/bash
echo "🚀 Starting MediAnalyze Application..."

# Start Python Flask server
echo "📁 Starting Python Report Analyzer on port 5001..."
cd modules/report_analyzer
source venv/Scripts/activate  # On Windows
# source venv/bin/activate    # On Mac/Linux
python app.py --port=5001 &
PYTHON_PID=$!

# Wait for Python server to start
sleep 3

# Start Node.js backend
echo "📁 Starting Node.js backend on port 5000..."
cd ../../backend
npm run dev &
NODE_PID=$!

# Wait for Node.js server to start
sleep 2

# Start frontend server
echo "📁 Starting frontend server on port 8000..."
cd ..
python -m http.server 8000

# Kill processes on exit
trap "kill $PYTHON_PID $NODE_PID" EXIT