# Raspberry Pi 3B Deployment Guide

## Overview
Deploy the Rubik's Cube Alarm Clock system on a Raspberry Pi 3B for headless operation with local audio output and WiFi-based mobile control.

## Architecture
- **Raspberry Pi 3B**: Backend server + BLE worker + local audio output
- **Phone/Browser**: Frontend control via WiFi
- **GAN Cube**: BLE connection for solved state detection

## Prerequisites
- Raspberry Pi 3B with Raspberry Pi OS (Bullseye or newer)
- MicroSD card (16GB+)
- WiFi network access
- Speaker connected to Pi (3.5mm jack or USB)
- GAN356 i Carry 2 cube

## Installation Steps

### 1. Raspberry Pi OS Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3 python3-pip python3-venv git bluetooth bluez libbluetooth-dev alsa-utils

# Enable Bluetooth
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```

### 2. Audio Configuration
```bash
# Test audio output
speaker-test -t sine -f 1000 -l 1

# Configure default audio output (if needed)
sudo raspi-config
# Navigate to: Advanced Options > Audio > Force 3.5mm jack

# Install audio dependencies
sudo apt install -y pulseaudio pulseaudio-utils
```

### 3. Project Setup
```bash
# Clone the repository
cd /home/pi
git clone https://github.com/pshapiro/cube-alarm.git
cd cube-alarm

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install additional Pi-specific dependencies
pip install pygame  # For better audio control on Pi
```

### 4. BLE Permissions
```bash
# Add pi user to bluetooth group
sudo usermod -a -G bluetooth pi

# Configure BLE permissions
sudo setcap cap_net_raw+eip $(readlink -f $(which python3))

# Or run with sudo (less secure but simpler)
```

### 5. Environment Configuration
```bash
# Create environment file
cp .env.example .env

# Edit environment variables
nano .env
```

Add to `.env`:
```
CUBE_MAC=CF:AA:79:C9:96:9C
FLASK_ENV=production
ALARM_SOUND_FILE=/home/pi/cube-alarm/sounds/alarm.wav
```

### 6. Custom Alarm Sound (Optional)
```bash
# Create sounds directory
mkdir -p sounds

# Download or copy your custom alarm sound
# Example: wget https://example.com/alarm.wav -O sounds/alarm.wav
```

### 7. Systemd Service Setup
Create service file:
```bash
sudo nano /etc/systemd/system/cube-alarm.service
```

Service file content:
```ini
[Unit]
Description=Rubik's Cube Alarm Clock
After=network.target bluetooth.target
Wants=bluetooth.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/cube-alarm
Environment=PATH=/home/pi/cube-alarm/venv/bin
ExecStart=/home/pi/cube-alarm/venv/bin/python backend/alarm_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable cube-alarm.service
sudo systemctl start cube-alarm.service

# Check status
sudo systemctl status cube-alarm.service
```

### 8. Frontend Setup (Optional - serve from Pi)
```bash
# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Build frontend
cd frontend
npm install
npm run build

# Serve frontend from Pi (optional)
sudo apt install -y nginx
sudo cp -r build/* /var/www/html/
```

### 9. Network Configuration
```bash
# Find Pi's IP address
hostname -I

# Configure firewall (if needed)
sudo ufw allow 5001  # Backend API
sudo ufw allow 3000  # Frontend (if serving from Pi)
```

## Usage

### Access from Phone/Browser
1. Connect phone to same WiFi network as Pi
2. Open browser and navigate to: `http://[PI_IP_ADDRESS]:5001`
3. Create and manage alarms via web interface

### Manual Control
```bash
# Check service status
sudo systemctl status cube-alarm.service

# View logs
sudo journalctl -u cube-alarm.service -f

# Restart service
sudo systemctl restart cube-alarm.service

# Stop service
sudo systemctl stop cube-alarm.service
```

## Testing

### 1. Test Audio Output
```bash
# Test system audio
speaker-test -t sine -f 800 -l 1

# Test Python audio (if using pygame)
python3 -c "import pygame; pygame.mixer.init(); pygame.mixer.Sound('sounds/alarm.wav').play(); import time; time.sleep(3)"
```

### 2. Test BLE Connection
```bash
# Scan for BLE devices
sudo bluetoothctl scan on

# Test Python BLE
python3 -c "import asyncio; from bleak import BleakScanner; print(asyncio.run(BleakScanner.discover()))"
```

### 3. Test API
```bash
# Test backend API
curl http://localhost:5001/api/status

# Create test alarm
curl -X POST http://localhost:5001/api/alarms -H "Content-Type: application/json" -d '{"time": "10:30", "days": ["monday"], "label": "test", "enabled": true, "requires_cube_solve": true}'
```

## Troubleshooting

### BLE Issues
```bash
# Reset Bluetooth
sudo systemctl restart bluetooth
sudo hciconfig hci0 down
sudo hciconfig hci0 up
```

### Audio Issues
```bash
# Check audio devices
aplay -l

# Test audio output
speaker-test -c 2 -t wav
```

### Service Issues
```bash
# Check service logs
sudo journalctl -u cube-alarm.service --no-pager

# Check Python errors
sudo journalctl -u cube-alarm.service -f
```

## Performance Optimization

### 1. Reduce CPU Usage
- Use smart BLE connection strategy (already implemented)
- Limit log verbosity in production
- Use efficient audio playback

### 2. Memory Optimization
```bash
# Increase swap if needed
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### 3. Power Management
- Smart BLE strategy saves cube battery
- Pi can run 24/7 with minimal power consumption
- Consider UPS for reliability

## Security Considerations

### 1. Network Security
```bash
# Change default Pi password
passwd

# Configure SSH (if needed)
sudo systemctl enable ssh
sudo nano /etc/ssh/sshd_config  # Disable root login, use key auth
```

### 2. Firewall
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 5001  # Backend API
sudo ufw allow from 192.168.1.0/24 to any port 5001  # Restrict to local network
```

## Monitoring

### 1. System Health
```bash
# CPU temperature
vcgencmd measure_temp

# Memory usage
free -h

# Disk usage
df -h
```

### 2. Service Monitoring
```bash
# Service status
systemctl is-active cube-alarm.service

# Recent logs
sudo journalctl -u cube-alarm.service --since "1 hour ago"
```

## Updates

### 1. Code Updates
```bash
cd /home/pi/cube-alarm
git pull origin main
sudo systemctl restart cube-alarm.service
```

### 2. System Updates
```bash
sudo apt update && sudo apt upgrade -y
sudo reboot  # If kernel updated
```

## Mobile App (Future Enhancement)
Consider creating a dedicated mobile app using:
- React Native
- Flutter
- Progressive Web App (PWA)

This would provide a better mobile experience than the web interface.
