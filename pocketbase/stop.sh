#!/bin/bash
# Stop PocketBase server

echo "Stopping PocketBase..."
pkill -f 'pocketbase serve'

if [ $? -eq 0 ]; then
    echo "✅ PocketBase stopped successfully"
else
    echo "⚠️  No running PocketBase process found"
fi