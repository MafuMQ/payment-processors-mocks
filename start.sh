#!/bin/bash
# Run the Payshap API with nohup (survives SSH disconnect)

cd ~/payment-processors-mocks
source venv/bin/activate

echo "Starting Payshap Mock API..."
nohup python3 app.py > api.log 2>&1 &

PID=$!
echo "API started with PID: $PID"
echo "Waiting for API to be ready..."
sleep 2

# Test if API is responding
if curl -s http://localhost:8080/health > /dev/null; then
    echo "✅ API is running successfully!"
    echo ""
    echo "View logs: tail -f ~/payment-processors-mocks/api.log"
    echo "Stop API: kill $PID"
    echo "         or: pkill -f 'python3 app.py'"
else
    echo "❌ API failed to start. Check logs:"
    echo "tail ~/payment-processors-mocks/api.log"
fi
