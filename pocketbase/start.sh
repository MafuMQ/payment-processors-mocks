#!/bin/bash
# PocketBase setup and start script

VERSION="0.22.8"
POCKETBASE_URL="https://github.com/pocketbase/pocketbase/releases/download/v${VERSION}/pocketbase_${VERSION}_linux_amd64.zip"
ZIP_FILE="pocketbase_${VERSION}_linux_amd64.zip"

cd "$(dirname "$0")"

echo "Starting PocketBase setup..."

# Check if pocketbase binary already exists
if [ -f "pocketbase" ]; then
    echo "✅ PocketBase binary found"
else
    echo "⬇️  PocketBase not found, downloading..."
    
    # Check if wget or curl is available
    if command -v wget &> /dev/null; then
        wget -q --show-progress "$POCKETBASE_URL"
    elif command -v curl &> /dev/null; then
        curl -L -o "$ZIP_FILE" "$POCKETBASE_URL"
    else
        echo "❌ Error: wget or curl is required to download PocketBase"
        exit 1
    fi
    
    # Check if download was successful
    if [ ! -f "$ZIP_FILE" ]; then
        echo "❌ Error: Failed to download PocketBase"
        exit 1
    fi
    
    echo "📦 Unzipping PocketBase..."
    
    # Check if unzip is available
    if ! command -v unzip &> /dev/null; then
        echo "❌ Error: unzip is not installed"
        echo "Install it with: sudo apt install unzip"
        exit 1
    fi
    
    unzip -q "$ZIP_FILE"
    
    # Clean up zip file
    rm "$ZIP_FILE"
    
    # Make executable
    chmod +x pocketbase
    
    echo "✅ PocketBase installed successfully"
fi

# Check if already running
if pgrep -f "pocketbase serve" > /dev/null; then
    echo "⚠️  PocketBase is already running"
    echo "Stop it first with: pkill -f 'pocketbase serve'"
    exit 1
fi

# Start PocketBase
echo "🚀 Starting PocketBase server..."
nohup ./pocketbase serve --http=0.0.0.0:8090 > pb_log.txt 2>&1 &

PID=$!
sleep 2

# Verify it started
if pgrep -f "pocketbase serve" > /dev/null; then
    echo "✅ PocketBase is running (PID: $PID)"
    echo ""
    echo "Access PocketBase:"
    echo "  Admin UI: http://localhost:8090/_/"
    echo "  API:      http://localhost:8090/api/"
    echo ""
    echo "View logs:  tail -f pb_log.txt"
    echo "Stop:       pkill -f 'pocketbase serve'"
else
    echo "❌ Failed to start PocketBase. Check logs:"
    tail -20 pb_log.txt
    exit 1
fi