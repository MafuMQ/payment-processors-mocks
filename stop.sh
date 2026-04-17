#!/bin/bash
# Stop the Payshap API

echo "Stopping Payshap Mock API..."
pkill -f 'python3 app.py'

if [ $? -eq 0 ]; then
    echo "✅ API stopped successfully"
else
    echo "⚠️  No running API process found"
fi
