#!/bin/bash
# SPDX-License-Identifier: LicenseRef-CubeAlarm-Custom-Attribution
# Copyright (c) 2025 Paul Shapiro

# Raspberry Pi 3B Setup Script for Rubik's Cube Alarm Clock
# Run this script on a fresh Raspberry Pi OS installation

set -e  # Exit on any error

echo "🍓 Starting Raspberry Pi 3B setup for Rubik's Cube Alarm Clock..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    print_warning "This script is designed for Raspberry Pi. Continuing anyway..."
fi

# Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y
print_success "System updated"

# Install system dependencies
print_status "Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    bluetooth \
    bluez \
    libbluetooth-dev \
    alsa-utils \
    pulseaudio \
    pulseaudio-utils \
    curl \
    wget \
    nginx \
    ufw
print_success "System dependencies installed"

# Enable and start Bluetooth
print_status "Configuring Bluetooth..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
print_success "Bluetooth configured"

# Configure audio
print_status "Testing audio configuration..."
if speaker-test -t sine -f 1000 -l 1 -s 1 >/dev/null 2>&1; then
    print_success "Audio test passed"
else
    print_warning "Audio test failed - you may need to configure audio manually"
    print_status "Run 'sudo raspi-config' and go to Advanced Options > Audio"
fi

# Create project directory
PROJECT_DIR="/home/pi/cube-alarm"
if [ ! -d "$PROJECT_DIR" ]; then
    print_status "Cloning project repository..."
    cd /home/pi
    git clone https://github.com/pshapiro/cube-alarm.git
    cd cube-alarm
    print_success "Project cloned"
else
    print_status "Project directory already exists, updating..."
    cd "$PROJECT_DIR"
    git pull origin main
    print_success "Project updated"
fi

# Create Python virtual environment
print_status "Setting up Python virtual environment..."
cd "$PROJECT_DIR"
python3 -m venv venv
source venv/bin/activate
print_success "Virtual environment created"

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pygame  # For better audio control on Pi
print_success "Python dependencies installed"

# Configure BLE permissions
print_status "Configuring BLE permissions..."
sudo usermod -a -G bluetooth pi
# Set capabilities for Python BLE access
PYTHON_PATH=$(which python3)
sudo setcap cap_net_raw+eip "$PYTHON_PATH"
print_success "BLE permissions configured"

# Create environment file
print_status "Creating environment configuration..."
if [ ! -f .env ]; then
    cat > .env << EOF
# Raspberry Pi Environment Configuration
CUBE_MAC=CF:AA:79:C9:96:9C
FLASK_ENV=production
ALARM_SOUND_FILE=/home/pi/cube-alarm/sounds/alarm.wav
PI_DEPLOYMENT=true
EOF
    print_success "Environment file created"
else
    print_status "Environment file already exists"
fi

# Create sounds directory and default alarm sound
print_status "Setting up alarm sounds..."
mkdir -p sounds
if [ ! -f sounds/alarm.wav ]; then
    # Create a simple beep sound using sox (if available) or download a default
    if command -v sox >/dev/null 2>&1; then
        sudo apt install -y sox
        sox -n sounds/alarm.wav synth 3 sine 800 vol 0.7
        print_success "Default alarm sound created"
    else
        print_warning "Sox not available - using system beep for alarm sound"
    fi
fi

# Create systemd service
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/cube-alarm.service > /dev/null << EOF
[Unit]
Description=Rubik's Cube Alarm Clock
After=network.target bluetooth.target
Wants=bluetooth.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python backend/alarm_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable cube-alarm.service
print_success "Systemd service created and enabled"

# Configure firewall
print_status "Configuring firewall..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 5001  # Backend API
sudo ufw allow from 192.168.0.0/16 to any port 5001  # Restrict to local networks
print_success "Firewall configured"

# Setup frontend (optional)
read -p "Do you want to serve the frontend from this Pi? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Setting up frontend..."
    
    # Install Node.js
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
    
    # Build frontend
    cd frontend
    npm install
    npm run build
    
    # Configure nginx
    sudo cp -r build/* /var/www/html/
    sudo systemctl enable nginx
    sudo systemctl start nginx
    sudo ufw allow 80  # HTTP
    
    print_success "Frontend setup complete"
    print_status "Frontend will be available at http://[PI_IP]/index.html"
else
    print_status "Skipping frontend setup"
fi

# Start the service
print_status "Starting cube alarm service..."
sudo systemctl start cube-alarm.service

# Wait a moment for service to start
sleep 3

# Check service status
if sudo systemctl is-active --quiet cube-alarm.service; then
    print_success "Cube alarm service is running!"
else
    print_error "Service failed to start. Check logs with: sudo journalctl -u cube-alarm.service"
fi

# Get Pi IP address
PI_IP=$(hostname -I | awk '{print $1}')

# Final instructions
echo
echo "🎉 Raspberry Pi setup complete!"
echo
print_success "Service Status:"
sudo systemctl status cube-alarm.service --no-pager -l
echo
print_success "Access Information:"
echo "  • Backend API: http://$PI_IP:5001"
echo "  • API Status: http://$PI_IP:5001/api/status"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "  • Frontend: http://$PI_IP"
fi
echo
print_success "Useful Commands:"
echo "  • Check service: sudo systemctl status cube-alarm.service"
echo "  • View logs: sudo journalctl -u cube-alarm.service -f"
echo "  • Restart service: sudo systemctl restart cube-alarm.service"
echo "  • Update code: cd $PROJECT_DIR && git pull && sudo systemctl restart cube-alarm.service"
echo
print_success "Mobile Access:"
echo "  1. Connect your phone to the same WiFi network"
echo "  2. Open browser and go to: http://$PI_IP:5001"
echo "  3. Create and manage alarms via the web interface"
echo
print_warning "Next Steps:"
echo "  1. Test the API: curl http://$PI_IP:5001/api/status"
echo "  2. Test audio: speaker-test -t sine -f 800 -l 1"
echo "  3. Pair your GAN cube and test alarm functionality"
echo "  4. Consider setting up a static IP for the Pi"
echo
print_status "Setup complete! Your Rubik's Cube Alarm Clock is ready to use."
