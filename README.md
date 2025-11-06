# Manufacturing Quality Oracle

**AI-Powered Quality Assurance Ecosystem for Automotive Manufacturing**

## Overview

The Manufacturing Quality Oracle is a comprehensive quality management system using advanced AI and reflection patterns to achieve 30%+ defect reduction in automotive parts manufacturing. The system leverages YOLOv8/v9 computer vision, Roboflow data pipeline, and self-improving AI agents.

## 🎯 Core Capabilities

- **Visual Inspection Agents**: Computer vision with self-correction using reflection patterns
- **Process Deviation Detection**: Automatic corrective actions and real-time monitoring
- **Supplier Quality Prediction**: ML-based predictions from historical performance data
- **Customer Feedback Integration**: Continuous improvement loop from customer insights
- **Real-time Defect Detection**: High-accuracy surface defect detection for automotive parts

## 🏗️ Architecture

```
Manufacturing Quality Oracle - YOLO + Roboflow Stack
├── Data Pipeline
│   ├── Roboflow (annotation, augmentation, dataset management)
│   ├── Industrial cameras (high-resolution capture)
│   └── Edge preprocessing (lighting normalization)
├── AI Models
│   ├── YOLOv8/v9 (real-time defect detection)
│   ├── Custom trained models per defect type
│   └── Reflection agents (self-improvement)
├── Deployment
│   ├── Edge devices (NVIDIA Jetson, Intel NUC)
│   ├── Cloud inference (scalability)
│   └── Real-time alerts and dashboards
└── Integration
    ├── MES/ERP systems
    ├── Production line controls
    └── Quality management systems
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- CUDA 11.8+ (for GPU acceleration)
- Docker (optional, for containerized deployment)
- Industrial cameras or video feed
- Edge device (NVIDIA Jetson/Intel NUC) or cloud server

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/Manufacturing-Quality-Oracle.git
cd Manufacturing-Quality-Oracle

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your configuration
```

### Configuration

1. **Roboflow Setup**:
   - Sign up at [Roboflow](https://roboflow.com)
   - Create a project for defect detection
   - Add your API key to `.env`

2. **Camera Configuration**:
   - Configure camera IDs in `.env`
   - Set resolution and FPS based on your hardware

3. **Database Setup**:
   ```bash
   # Run database migrations
   python scripts/setup_database.py
   ```

### Running the System

```bash
# Start the main quality inspection system
python src/main.py

# Start the API server
python src/api/server.py

# Start the dashboard
python src/dashboard/app.py

# Run inference on edge device
python src/deployment/edge_inference.py --device jetson
```

## 📊 Features

### 1. Computer Vision Defect Detection

- **YOLOv8/v9** real-time object detection
- Custom models for specific defect types:
  - Surface scratches
  - Dents and deformations
  - Color inconsistencies
  - Dimensional defects
  - Assembly errors

### 2. Reflection Pattern Self-Improvement

The system uses AI reflection agents to continuously improve:
- Analyzes misclassifications
- Identifies model weaknesses
- Suggests retraining strategies
- Adapts to new defect patterns

### 3. Supplier Quality Prediction

Machine learning models predict supplier quality based on:
- Historical defect rates
- Delivery consistency
- Material quality trends
- Compliance metrics

### 4. Process Deviation Detection

Real-time monitoring with automatic corrective actions:
- Statistical process control (SPC)
- Anomaly detection algorithms
- Automated alerts to operators
- Integration with production line controls

### 5. Customer Feedback Loop

Integrates customer feedback to improve production:
- Sentiment analysis on feedback
- Defect pattern correlation
- Predictive quality adjustments
- Closed-loop quality improvement

## 🖥️ Deployment Options

### Edge Deployment (NVIDIA Jetson)

```bash
# Build for Jetson
python scripts/build_jetson.py

# Deploy to device
python scripts/deploy_edge.py --device jetson --ip 192.168.1.100
```

### Edge Deployment (Intel NUC)

```bash
# Build with OpenVINO optimization
python scripts/build_openvino.py

# Deploy to device
python scripts/deploy_edge.py --device intel_nuc --ip 192.168.1.101
```

### Cloud Deployment

```bash
# Build Docker container
docker build -t quality-oracle:latest .

# Run container
docker run -d -p 8080:8080 \
  --env-file .env \
  --gpus all \
  quality-oracle:latest
```

## 📈 Dashboard & Monitoring

Access the real-time dashboard at `http://localhost:8080`

**Features**:
- Live camera feeds with defect overlays
- Real-time defect rate metrics
- Historical trend analysis
- Supplier quality scorecards
- Process deviation alerts
- Customer feedback dashboard

## 🔌 Integration

### MES/ERP Integration

```python
from src.integration.mes_connector import MESConnector

mes = MESConnector(api_url=os.getenv('MES_API_URL'))
mes.send_quality_data(inspection_results)
```

### OPC UA Industrial Protocol

```python
from src.integration.opcua_client import OPCUAClient

client = OPCUAClient(server_url=os.getenv('OPCUA_SERVER_URL'))
client.write_quality_status(station_id, status)
```

### PLC Communication

```python
from src.integration.plc_connector import PLCConnector

plc = PLCConnector(ip=os.getenv('PLC_IP_ADDRESS'))
plc.trigger_reject_mechanism(defective_part_id)
```

## 📊 Performance Metrics

Target KPIs:
- **Defect Detection Accuracy**: >95%
- **False Positive Rate**: <2%
- **Inference Time**: <50ms per image
- **Defect Reduction**: 30%+ within 3 months
- **System Uptime**: 99.5%

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test suites
pytest tests/test_vision_agent.py
pytest tests/test_reflection_pattern.py
pytest tests/test_integration.py

# Run with coverage
pytest --cov=src tests/
```

## 📚 Documentation

Detailed documentation is available in the `/docs` directory:

- [Computer Vision Agent Guide](docs/computer_vision_agent.md)
- [Reflection Pattern Implementation](docs/reflection_pattern.md)
- [Deployment Guide](docs/deployment.md)
- [API Reference](docs/api_reference.md)
- [Integration Guide](docs/integration.md)

## 🔧 Troubleshooting

### Common Issues

1. **Camera not detected**: Check camera ID in `.env` and permissions
2. **Low accuracy**: Retrain model with more annotated data in Roboflow
3. **Slow inference**: Enable GPU acceleration or reduce model size
4. **Integration errors**: Verify API keys and network connectivity

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md).

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 🏆 Pilot Facilities

Initial deployment at 3 automotive manufacturing facilities:
1. Facility A: Engine component manufacturing
2. Facility B: Transmission parts production
3. Facility C: Chassis assembly quality control

## 📞 Support

For support and questions:
- Email: support@manufacturing-oracle.com
- Documentation: https://docs.manufacturing-oracle.com
- Issues: GitHub Issues

## 🎯 Roadmap

- [x] Computer vision defect detection
- [x] Reflection pattern implementation
- [x] Supplier quality prediction
- [x] Customer feedback integration
- [ ] Advanced 3D defect detection
- [ ] Predictive maintenance integration
- [ ] Multi-site orchestration
- [ ] Industry 4.0 full integration

---

**Built with ❤️ for Manufacturing Excellence**
