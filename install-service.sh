#!/bin/bash
# Install Payshap API as a systemd service (requires sudo)

WORKDIR="$HOME/payment-processors-mocks"
USERNAME=$(whoami)

echo "Installing Payshap Mock API as systemd service..."

# Create service file from template
sed -e "s|%WORKDIR%|$WORKDIR|g" -e "s|%USERNAME%|$USERNAME|g" \
    payshap-mock.service > /tmp/payshap-mock.service

# Install service
sudo cp /tmp/payshap-mock.service /etc/systemd/system/payshap-mock.service
sudo systemctl daemon-reload
sudo systemctl enable payshap-mock

echo "✅ Service installed!"
echo ""
echo "Start service: sudo systemctl start payshap-mock"
echo "Stop service:  sudo systemctl stop payshap-mock"
echo "View status:   sudo systemctl status payshap-mock"
echo "View logs:     sudo journalctl -u payshap-mock -f"
