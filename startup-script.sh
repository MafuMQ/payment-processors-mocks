#!/bin/bash
# GCP Compute Engine startup script

# Update system
apt-get update
apt-get install -y python3-pip python3-venv git

# Create app directory
mkdir -p /opt/payshap-mock
cd /opt/payshap-mock

# Clone or copy application files
# If deploying from local, you would upload files instead
# For now, we'll assume files are already present

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create systemd service file
cat > /etc/systemd/system/payshap-mock.service << 'EOF'
[Unit]
Description=Payshap Mock API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/payshap-mock
Environment="PATH=/opt/payshap-mock/venv/bin"
ExecStart=/opt/payshap-mock/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start and enable service
systemctl daemon-reload
systemctl enable payshap-mock
systemctl start payshap-mock

# Check status
systemctl status payshap-mock
