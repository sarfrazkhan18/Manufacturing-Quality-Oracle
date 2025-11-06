#!/bin/bash
# Deployment script for Intel NUC devices with OpenVINO

set -e

echo "==== Manufacturing Quality Oracle - Intel NUC Deployment ===="

# Configuration
NUC_IP=${1:-"192.168.1.101"}
NUC_USER=${2:-"admin"}
APP_DIR="/home/${NUC_USER}/quality-oracle"

echo "Deploying to Intel NUC at ${NUC_IP}"

# Create directory on NUC
ssh ${NUC_USER}@${NUC_IP} "mkdir -p ${APP_DIR}"

# Copy application files
echo "Copying application files..."
rsync -avz --exclude='data/' --exclude='logs/' --exclude='*.pyc' \
    . ${NUC_USER}@${NUC_IP}:${APP_DIR}/

# Install dependencies on NUC
echo "Installing dependencies on Intel NUC..."
ssh ${NUC_USER}@${NUC_IP} << 'EOF'
cd ${APP_DIR}

# Update system
sudo apt-get update

# Install OpenVINO (if not already installed)
if ! command -v setupvars.sh &> /dev/null; then
    echo "Installing OpenVINO..."
    wget https://storage.openvinotoolkit.org/repositories/openvino/packages/2023.0/linux/l_openvino_toolkit_ubuntu22_2023.0.0.10926.b4452d56304_x86_64.tgz
    tar -xf l_openvino_toolkit_ubuntu22_2023.0.0.10926.b4452d56304_x86_64.tgz
    cd l_openvino_toolkit_ubuntu22_2023.0.0.10926.b4452d56304_x86_64
    sudo ./install.sh
    source /opt/intel/openvino_2023/setupvars.sh
    cd ..
fi

# Install Python dependencies
pip3 install -r requirements.txt

# Install additional OpenVINO Python tools
pip3 install openvino-dev[onnx,pytorch]

# Create directories
mkdir -p data models logs reports

# Download and convert YOLO model to OpenVINO format
if [ ! -f "models/yolov8n.xml" ]; then
    echo "Converting YOLOv8 to OpenVINO format..."
    python3 << PYTHON
from ultralytics import YOLO
import openvino as ov

# Load YOLO model
model = YOLO('yolov8n.pt')

# Export to ONNX first
model.export(format='onnx')

# Convert ONNX to OpenVINO
!mo --input_model yolov8n.onnx --output_dir models/
PYTHON
fi

echo "Installation complete!"
EOF

# Copy environment file
echo "Copying environment configuration..."
scp .env.example ${NUC_USER}@${NUC_IP}:${APP_DIR}/.env

echo "Configuring .env file on Intel NUC..."
ssh ${NUC_USER}@${NUC_IP} << 'EOF'
cd ${APP_DIR}

# Update .env for Intel NUC with OpenVINO
sed -i 's/EDGE_DEVICE_TYPE=.*/EDGE_DEVICE_TYPE=intel_nuc/' .env
sed -i 's/GPU_ACCELERATION=.*/GPU_ACCELERATION=false/' .env
sed -i 's/TENSORRT_OPTIMIZATION=.*/TENSORRT_OPTIMIZATION=false/' .env
EOF

# Setup systemd service
echo "Setting up systemd service..."
ssh ${NUC_USER}@${NUC_IP} "sudo tee /etc/systemd/system/quality-oracle.service" << EOF
[Unit]
Description=Manufacturing Quality Oracle
After=network.target

[Service]
Type=simple
User=${NUC_USER}
WorkingDirectory=${APP_DIR}
ExecStartPre=/bin/bash -c 'source /opt/intel/openvino_2023/setupvars.sh'
ExecStart=/usr/bin/python3 ${APP_DIR}/src/deployment/edge_inference.py --device intel_nuc
Restart=always
RestartSec=10
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
ssh ${NUC_USER}@${NUC_IP} << 'EOF'
sudo systemctl daemon-reload
sudo systemctl enable quality-oracle
sudo systemctl start quality-oracle
sudo systemctl status quality-oracle
EOF

echo "==== Deployment Complete ===="
echo "Service is running on ${NUC_IP}"
echo "View logs: ssh ${NUC_USER}@${NUC_IP} 'sudo journalctl -u quality-oracle -f'"
