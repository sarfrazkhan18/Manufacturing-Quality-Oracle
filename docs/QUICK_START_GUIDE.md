# Quick Start Guide: 8-Week Implementation

This guide will walk you through the practical execution of the 8-week implementation plan for metal surface defect detection.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Industrial camera (USB or CSI)
- [ ] Good lighting setup (diffused, angled)
- [ ] GPU-enabled workstation (for training) OR cloud GPU access
- [ ] Edge device (Jetson/Intel NUC) for deployment
- [ ] Roboflow account (free tier is fine to start)
- [ ] Python 3.9+ environment

## Week 1: Data Collection (Days 1-7)

### Setup
```bash
cd Manufacturing-Quality-Oracle
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Collect Images

**Interactive Capture:**
```bash
# Capture scratches
python scripts/week1_data_collection.py \
  --mode capture \
  --defect-type scratch \
  --camera 0

# Capture dents
python scripts/week1_data_collection.py \
  --mode capture \
  --defect-type dent \
  --camera 0

# Capture cracks
python scripts/week1_data_collection.py \
  --mode capture \
  --defect-type crack \
  --camera 0

# Capture good parts
python scripts/week1_data_collection.py \
  --mode capture \
  --defect-type good \
  --camera 0
```

**Controls during capture:**
- `SPACE` - Capture image
- `S` - Change severity (low/medium/high)
- `Q` - Quit session

**Import Existing Images:**
```bash
# If you already have images
python scripts/week1_data_collection.py \
  --mode import \
  --source-dir /path/to/existing/images \
  --defect-type scratch
```

### Check Quality
```bash
python scripts/week1_data_collection.py --mode check
```

### Generate Report
```bash
python scripts/week1_data_collection.py --mode report
```

**Target by end of Week 1:** 500-1000 quality images

---

## Week 2: Annotation with Roboflow (Days 8-14)

### 1. Create Roboflow Account
- Go to https://roboflow.com
- Sign up (free tier: 10,000 images)
- Create workspace

### 2. Create Project
- Click "Create Project"
- Name: "Automotive-Metal-Defects"
- Type: Object Detection
- Classes: scratch, dent, crack, rust, paint_defect

### 3. Upload Images
- Upload all images from `data/raw_images/`
- Organize by defect type

### 4. Annotate
**Best Practices:**
- Use tight bounding boxes
- Include defect margins
- Be consistent with boundaries
- Mark partially visible defects
- Add severity tags

**Annotation Shortcuts:**
- Draw box: Click and drag
- Delete box: Select + Delete key
- Copy to next: `Shift + →`
- Smart annotation: Enable in settings

### 5. Dataset Split
- Train: 70%
- Valid: 20%
- Test: 10%

### 6. Generate Dataset
- Go to "Generate" → "Create Version"
- Preprocessing: Auto-Orient
- Augmentation Settings:
  ```
  Rotation: ±15°
  Brightness: ±20%
  Exposure: ±10%
  Blur: 0-2px
  Noise: 0-5%
  Flip: Horizontal
  ```
- Click "Generate"
- Download in "YOLOv8" format
- Extract to `data/datasets/metal_defects/`

### 7. Create dataset.yaml
The download includes a `data.yaml` file. Copy it to your project:
```bash
cp data/datasets/metal_defects/data.yaml data/metal_defects.yaml
```

Edit to fix paths:
```yaml
path: ./data/datasets/metal_defects
train: train/images
val: valid/images
test: test/images

nc: 5  # Number of classes
names: ['scratch', 'dent', 'crack', 'rust', 'paint_defect']
```

**Target by end of Week 2:** Fully annotated dataset ready for training

---

## Week 3: Train Model (Days 15-21)

### 1. Setup Training Environment

**Option A: Local GPU**
```bash
# Verify CUDA
nvidia-smi

# Test PyTorch GPU
python -c "import torch; print(torch.cuda.is_available())"
```

**Option B: Google Colab**
- Upload dataset to Google Drive
- Use Colab notebook with GPU runtime

### 2. Start Training
```bash
python scripts/week3_train_model.py \
  --mode train \
  --dataset data/metal_defects.yaml \
  --model-size n \
  --epochs 100 \
  --batch 16
```

**Model Sizes:**
- `n` (nano): Fastest, 3.2M params, good for edge
- `s` (small): Balanced, 11.2M params
- `m` (medium): Better accuracy, 25.9M params

**Training takes:** 2-4 hours on GPU (depending on size)

### 3. Monitor Training
Watch the terminal output for:
- Loss decreasing
- mAP increasing
- Validation metrics

Checkpoints saved every 10 epochs in `models/training/`

### 4. Validate Model
```bash
python scripts/week3_train_model.py \
  --mode validate \
  --dataset data/metal_defects.yaml \
  --model-path models/training/train_*/weights/best.pt
```

**Target Metrics:**
- Precision: >90%
- Recall: >85%
- mAP@0.5: >90%

**Target by end of Week 3:** Trained baseline model

---

## Week 4: Optimize Model (Days 22-28)

### 1. Analyze Errors
Review validation results:
- Check confusion matrix
- Identify misclassified defects
- Note challenging cases

### 2. Collect More Data
Focus on:
- Underrepresented classes
- Difficult cases (small defects, poor lighting)
- Edge cases

### 3. Retrain with More Data
```bash
# After adding more data to Roboflow and re-generating
python scripts/week3_train_model.py \
  --mode train \
  --dataset data/metal_defects_v2.yaml \
  --model-size s \
  --epochs 150 \
  --batch 16
```

### 4. Try Different Model Sizes
```bash
# Train small model for comparison
python scripts/week3_train_model.py \
  --mode train \
  --dataset data/metal_defects.yaml \
  --model-size s \
  --epochs 100
```

### 5. Export Optimized Model
```bash
python scripts/week3_train_model.py \
  --mode export \
  --model-path models/training/train_*/weights/best.pt
```

This creates:
- `best.onnx` - For OpenVINO
- `best.torchscript` - For production

### 6. Benchmark Speed
```bash
python scripts/week3_train_model.py \
  --mode benchmark \
  --model-path models/training/train_*/weights/best.pt
```

**Target by end of Week 4:** Optimized model with >90% accuracy

---

## Week 5: Deploy to Edge (Days 29-35)

### For NVIDIA Jetson

```bash
# Copy model to Jetson
scp models/training/train_*/weights/best.pt nvidia@<JETSON_IP>:~/

# Deploy application
./deployment/jetson_deploy.sh <JETSON_IP> nvidia

# Verify deployment
ssh nvidia@<JETSON_IP>
sudo systemctl status quality-oracle
```

### For Intel NUC

```bash
# Deploy application
./deployment/intel_nuc_deploy.sh <NUC_IP> admin

# Verify deployment
ssh admin@<NUC_IP>
sudo systemctl status quality-oracle
```

### Test Edge Inference

```bash
# On edge device
python src/deployment/edge_inference.py --device jetson  # or intel_nuc

# Watch logs
sudo journalctl -u quality-oracle -f
```

**Target by end of Week 5:** Working edge inference system

---

## Week 6: Production Integration (Days 36-42)

### 1. Mount Camera
- Position at inspection point
- Ensure proper angle and distance
- Install lighting system

### 2. Configure System
Edit `.env` on edge device:
```bash
# Camera
CAMERA_IDS=0
CAMERA_RESOLUTION_WIDTH=1920
CAMERA_RESOLUTION_HEIGHT=1080

# Model
CONFIDENCE_THRESHOLD=0.5

# Alerts
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_TO=quality@company.com
```

### 3. Test Integration
```bash
# Run in test mode
sudo systemctl stop quality-oracle
python src/deployment/edge_inference.py --device jetson

# Watch for detections
# Place parts under camera
# Verify detections are accurate
```

### 4. Enable Alerts
- Test email alerts
- Configure MQTT (if using)
- Setup dashboard access

### 5. Shadow Mode
- Run parallel with human inspection
- Log both AI and human results
- Compare and analyze discrepancies

**Target by end of Week 6:** Integrated system in shadow mode

---

## Week 7: Pilot Testing (Days 43-49)

### Start Pilot
```bash
# On edge device - start service
sudo systemctl start quality-oracle

# On monitoring workstation - start tracking
python scripts/week7_pilot_monitoring.py
```

### Log Data Throughout Week

**For each inspection:**
```python
monitor.log_inspection(
    part_id="PART-001",
    defects_detected=1,
    detection_time_ms=45.2,
    ground_truth_defects=1,
    operator_agrees=True
)
```

**For each detection:**
```python
monitor.log_detection(
    part_id="PART-001",
    defect_type="scratch",
    confidence=0.95,
    severity="medium",
    is_correct=True
)
```

**Collect Operator Feedback:**
```python
monitor.log_operator_feedback(
    operator_id="OP-01",
    feedback_text="System is accurate but sometimes slow",
    rating=4,
    issues=["occasional_lag"]
)
```

### Daily Checks
- System uptime
- Detection accuracy
- False positive/negative rates
- Operator satisfaction

**Target by end of Week 7:** 1 week of pilot data (500+ inspections)

---

## Week 8: Analysis & ROI (Days 50-56)

### Generate Report
```python
from scripts.week7_pilot_monitoring import PilotMonitor

monitor = PilotMonitor()
# ... after loading data ...

report = monitor.generate_report()
monitor.export_to_csv()
```

### Calculate ROI
```python
roi_report = monitor.calculate_roi(
    labor_cost_per_hour=30,        # Your labor cost
    scrap_cost_per_defect=50,      # Cost per escaped defect
    implementation_cost=5000        # Total implementation cost
)
```

### Present Results

Create presentation with:
1. **Executive Summary**
   - 30% defect reduction achieved
   - ROI: X% in Y months
   - System accuracy: Z%

2. **Technical Metrics**
   - Precision/Recall/F1
   - Inference speed
   - System uptime

3. **Business Impact**
   - Labor savings
   - Scrap reduction
   - Quality improvement

4. **Operator Feedback**
   - Satisfaction ratings
   - Pain points addressed
   - Training needs

5. **Expansion Plan**
   - Deploy to 2nd facility
   - Timeline and budget
   - Lessons learned

**Target by end of Week 8:** Complete pilot report with positive ROI

---

## Troubleshooting

### Data Collection Issues

**Camera not detected:**
```bash
# List cameras
ls /dev/video*

# Test camera
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL')"
```

**Images too dark/bright:**
- Adjust lighting setup
- Add diffusers to reduce glare
- Increase camera exposure

### Training Issues

**CUDA out of memory:**
```bash
# Reduce batch size
python scripts/week3_train_model.py --batch 8

# Or use smaller model
python scripts/week3_train_model.py --model-size n
```

**Low accuracy:**
- Collect more diverse training data
- Check annotation quality
- Try longer training (more epochs)
- Adjust confidence threshold

### Deployment Issues

**Slow inference on edge:**
- Use TensorRT (Jetson) or OpenVINO (Intel)
- Reduce image resolution
- Use smaller model (nano)

**High false positive rate:**
- Increase confidence threshold
- Retrain with more negative examples
- Review training data quality

---

## Next Steps After Week 8

1. **Expand Deployment**
   - Facility 2: Weeks 9-10
   - Facility 3: Weeks 11-12

2. **Add Features**
   - More defect types
   - Reflection agent for self-improvement
   - Advanced analytics

3. **Continuous Improvement**
   - Collect edge cases
   - Retrain quarterly
   - Monitor drift

---

## Support Resources

- **Documentation:** `/docs` directory
- **Scripts:** `/scripts` directory
- **Issues:** GitHub Issues
- **Community:** Roboflow Community, Ultralytics Discord

**You're ready to start! Begin with Week 1 data collection.** 🚀
