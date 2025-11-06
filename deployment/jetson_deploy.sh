#!/bin/bash
# Deployment script for NVIDIA Jetson devices

set -e

echo "==== Manufacturing Quality Oracle - Jetson Deployment ===="

# Configuration
JETSON_IP=${1:-"192.168.1.100"}
JETSON_USER=${2:-"nvidia"}
APP_DIR="/home/${JETSON_USER}/quality-oracle"

echo "Deploying to Jetson at ${JETSON_IP}"

# Create directory on Jetson
ssh ${JETSON_USER}@${JETSON_IP} "mkdir -p ${APP_DIR}"

# Copy application files
echo "Copying application files..."
rsync -avz --exclude='data/' --exclude='logs/' --exclude='*.pyc' \
    . ${JETSON_USER}@${JETSON_IP}:${APP_DIR}/

# Install dependencies on Jetson
echo "Installing dependencies on Jetson..."
ssh ${JETSON_USER}@${JETSON_IP} << 'EOF'
cd ${APP_DIR}

# Update system
sudo apt-get update

# Install Python dependencies
pip3 install -r requirements.txt

# Install JetPack dependencies
# (These are typically pre-installed on Jetson)
sudo apt-get install -y \
    python3-opencv \
    python3-numpy \
    libopenblas-dev

# Create directories
mkdir -p data models logs reports

# Download YOLO model if not present
if [ ! -f "models/yolov8n.pt" ]; then
    echo "Downloading YOLOv8 model..."
    wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt \
        -O models/yolov8n.pt
fi

echo "Installation complete!"
EOF

# Copy environment file
echo "Copying environment configuration..."
scp .env.example ${JETSON_USER}@${JETSON_IP}:${APP_DIR}/.env

echo "Configuring .env file on Jetson..."
ssh ${JETSON_USER}@${JETSON_IP} << 'EOF'
cd ${APP_DIR}

# Update .env for Jetson
sed -i 's/EDGE_DEVICE_TYPE=.*/EDGE_DEVICE_TYPE=jetson/' .env
sed -i 's/GPU_ACCELERATION=.*/GPU_ACCELERATION=true/' .env
sed -i 's/TENSORRT_OPTIMIZATION=.*/TENSORRT_OPTIMIZATION=true/' .env
EOF

# Setup systemd service
echo "Setting up systemd service..."
ssh ${JETSON_USER}@${JETSON_IP} "sudo tee /etc/systemd/system/quality-oracle.service" << EOF
[Unit]
Description=Manufacturing Quality Oracle
After=network.target

[Service]
Type=simple
User=${JETSON_USER}
WorkingDirectory=${APP_DIR}
ExecStart=/usr/bin/python3 ${APP_DIR}/src/deployment/edge_inference.py --device jetson
Restart=always
RestartSec=10
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
ssh ${JETSON_USER}@${JETSON_IP} << 'EOF'
sudo systemctl daemon-reload
sudo systemctl enable quality-oracle
sudo systemctl start quality-oracle
sudo systemctl status quality-oracle
EOF

echo "==== Deployment Complete ===="
echo "Service is running on ${JETSON_IP}"
echo "View logs: ssh ${JETSON_USER}@${JETSON_IP} 'sudo journalctl -u quality-oracle -f'"
