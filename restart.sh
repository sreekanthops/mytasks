#!/bin/bash
# Restart script for MyTasks application

echo "🔄 Restarting MyTasks application..."

# Kill any existing Flask processes
pkill -f "python3 app.py" 2>/dev/null
pkill -f "python app.py" 2>/dev/null

echo "✅ Stopped existing processes"
echo "🚀 Starting application..."

# Start the application
cd /Users/sreekanthchityala/nettools/mytasks
python3 app.py &

echo "✅ Application started!"
echo "📱 Access at: http://127.0.0.1:5000"
echo ""
echo "To stop: pkill -f 'python3 app.py'"

# Made with Bob
