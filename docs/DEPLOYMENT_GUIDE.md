# Manufacturing Quality Oracle - Deployment Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Cloud Deployment](#cloud-deployment)
3. [Edge Deployment](#edge-deployment)
4. [Configuration](#configuration)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Hardware Requirements

**Cloud Deployment:**
- CPU: 8+ cores
- RAM: 16GB+
- GPU: NVIDIA GPU with 6GB+ VRAM (recommended)
- Storage: 100GB+ SSD

**Edge Deployment (Jetson):**
- NVIDIA Jetson Nano, Xavier NX, or AGX Xavier
- 4GB+ RAM
- 32GB+ storage
- Industrial camera (USB or CSI)

**Edge Deployment (Intel NUC):**
- Intel NUC with 11th gen or newer processor
- 8GB+ RAM
- 128GB+ SSD
- Industrial camera (USB)

### Software Requirements

- Python 3.9+
- CUDA 11.8+ (for GPU acceleration)
- Docker 20.10+ (for containerized deployment)
- Git

## Cloud Deployment

### Docker Deployment (Recommended)

1. **Clone repository:**
   ```bash
   git clone https://github.com/your-org/Manufacturing-Quality-Oracle.git
   cd Manufacturing-Quality-Oracle
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   nano .env
   ```

3. **Start with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

4. **Verify deployment:**
   ```bash
   curl http://localhost:8080/health
   ```

### Manual Deployment

1. **Setup Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Setup database:**
   ```bash
   # PostgreSQL
   sudo -u postgres createdb quality_oracle

   # Redis
   sudo systemctl start redis

   # MongoDB
   sudo systemctl start mongod
   ```

3. **Run application:**
   ```bash
   python src/main.py
   ```

## Edge Deployment

### NVIDIA Jetson

1. **Prepare Jetson device:**
   ```bash
   # Ensure JetPack is installed
   sudo apt update
   sudo apt install python3-pip
   ```

2. **Deploy to Jetson:**
   ```bash
   # From your development machine
   chmod +x deployment/jetson_deploy.sh
   ./deployment/jetson_deploy.sh <JETSON_IP> <USERNAME>
   ```

3. **Monitor service:**
   ```bash
   ssh nvidia@<JETSON_IP>
   sudo systemctl status quality-oracle
   sudo journalctl -u quality-oracle -f
   ```

### Intel NUC with OpenVINO

1. **Deploy to Intel NUC:**
   ```bash
   chmod +x deployment/intel_nuc_deploy.sh
   ./deployment/intel_nuc_deploy.sh <NUC_IP> <USERNAME>
   ```

2. **Monitor service:**
   ```bash
   ssh admin@<NUC_IP>
   sudo systemctl status quality-oracle
   sudo journalctl -u quality-oracle -f
   ```

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Application
APP_NAME="Manufacturing Quality Oracle"
ENVIRONMENT=production
LOG_LEVEL=INFO

# Roboflow
ROBOFLOW_API_KEY=your_key_here
ROBOFLOW_PROJECT=defect-detection

# AI Models
YOLO_MODEL_PATH=./models/yolov8n.pt
CONFIDENCE_THRESHOLD=0.5

# Camera
CAMERA_IDS=0,1,2
CAMERA_RESOLUTION_WIDTH=1920
CAMERA_RESOLUTION_HEIGHT=1080

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=quality_oracle

# MES Integration
MES_API_URL=http://your-mes-system.com/api
MES_API_KEY=your_mes_key

# Alerts
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_TO=quality@company.com
```

### Model Configuration

Download and configure YOLO models:

```bash
# Download YOLOv8 base model
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt \
  -O models/yolov8n.pt

# Train custom model (if needed)
python scripts/train_model.py --data data/dataset.yaml --epochs 100
```

## Monitoring

### Grafana Dashboards

Access Grafana at `http://localhost:3000`:
- Default credentials: admin/admin
- Import dashboard from `deployment/grafana_dashboard.json`

### Prometheus Metrics

Access Prometheus at `http://localhost:9090`:
- View metrics at `/metrics` endpoint
- Configure alerts in `deployment/prometheus.yml`

### API Monitoring

Check API status:
```bash
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/metrics
```

## Troubleshooting

### Common Issues

**1. Camera not detected:**
```bash
# Check camera permissions
sudo usermod -a -G video $USER
# Restart service
sudo systemctl restart quality-oracle
```

**2. Low inference speed:**
```bash
# Check GPU utilization
nvidia-smi
# Enable TensorRT optimization in .env
TENSORRT_OPTIMIZATION=true
```

**3. Database connection errors:**
```bash
# Check database status
sudo systemctl status postgresql
# Verify connection
psql -h localhost -U postgres -d quality_oracle
```

**4. Out of memory on edge device:**
```bash
# Reduce model size or batch size in config
# Use smaller YOLO model (yolov8n instead of yolov8m)
```

### Logs

View application logs:
```bash
# Main application
tail -f logs/quality_oracle_production.log

# Edge inference
tail -f logs/edge_inference_jetson.log

# Docker logs
docker logs quality-oracle-app -f
```

### Performance Optimization

**For Cloud:**
- Enable GPU acceleration
- Use batch processing
- Increase worker processes

**For Edge:**
- Use TensorRT (Jetson) or OpenVINO (Intel)
- Reduce camera resolution if needed
- Optimize preprocessing pipeline

## Production Checklist

- [ ] Configure all environment variables
- [ ] Setup database backups
- [ ] Configure email alerts
- [ ] Test camera connections
- [ ] Verify MES/ERP integration
- [ ] Setup monitoring dashboards
- [ ] Configure firewall rules
- [ ] Test failover procedures
- [ ] Document custom configurations
- [ ] Train operators on system

## Support

For additional support:
- Documentation: `/docs`
- Issues: GitHub Issues
- Email: support@manufacturing-oracle.com
