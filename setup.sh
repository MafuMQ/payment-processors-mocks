#!/bin/bash
# Simple setup script - runs in home directory (no sudo required)

echo "Setting up Payshap Mock API..."

# Install python3-venv (needs sudo once)
echo "Installing python3-venv..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv

# Setup in current directory (already in ~/payment-processors-mocks)
echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the API and keep it running after logout:"
echo ""
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Run with nohup (survives SSH disconnect):"
echo "   nohup python3 app.py > api.log 2>&1 &"
echo ""
echo "3. Check it's running:"
echo "   curl http://localhost:8080/health"
echo ""
echo "4. View logs:"
echo "   tail -f api.log"
echo ""
echo "5. Stop the service:"
echo "   pkill -f 'python3 app.py'"
