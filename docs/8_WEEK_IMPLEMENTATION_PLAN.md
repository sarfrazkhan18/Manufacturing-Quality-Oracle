# 8-Week Implementation Plan: Metal Surface Defect Detection

## Use Case Selection: Metal Surface Defects (Automotive Parts)

**Target Defects:**
- Scratches (linear surface marks)
- Dents (deformations/indentations)
- Cracks (fractures in material)
- Rust/Corrosion
- Paint defects

**Success Criteria:**
- 95%+ detection accuracy
- <100ms inference time
- 30% reduction in escaped defects
- ROI demonstration within 8 weeks

---

## Week 1-2: Data Collection & Annotation

### Week 1: Data Collection

**Objectives:**
- Collect 500-1000 images of automotive metal parts
- Capture various lighting conditions and angles
- Document defect types and severity

**Tasks:**

#### Day 1-2: Setup Data Collection
- [ ] Setup industrial cameras at inspection stations
- [ ] Configure proper lighting (diffused, angled)
- [ ] Create data collection protocol document
- [ ] Train operators on image capture

#### Day 3-5: Collect Images
- [ ] Capture 200+ images with scratches
- [ ] Capture 200+ images with dents
- [ ] Capture 200+ images with cracks
- [ ] Capture 100+ images with multiple defects
- [ ] Capture 200+ images of good parts (no defects)

**Best Practices:**
```
Image Requirements:
- Resolution: 1920x1080 or higher
- Format: JPG/PNG
- Lighting: Consistent, diffused
- Angles: Multiple views per part
- Background: Neutral, consistent
- Focus: Sharp, clear defects
```

#### Day 6-7: Data Organization
- [ ] Organize images by defect type
- [ ] Remove blurry/unusable images
- [ ] Create metadata CSV (filename, defect_type, severity)
- [ ] Backup raw dataset

**Deliverable:** 500-1000 quality images organized by defect type

---

### Week 2: Data Annotation with Roboflow

**Objectives:**
- Annotate all collected images
- Setup Roboflow project
- Configure augmentation pipeline

**Tasks:**

#### Day 1: Roboflow Setup
- [ ] Create Roboflow account (free tier: 10k images)
- [ ] Create project: "Automotive-Metal-Defects"
- [ ] Define classes: scratch, dent, crack, rust, paint_defect
- [ ] Upload first batch (100 images)

#### Day 2-5: Annotation
- [ ] Annotate 150-200 images per day
- [ ] Use bounding boxes for defects
- [ ] Label defect severity (low/medium/high)
- [ ] Review and correct annotations
- [ ] Use smart annotation tools (if available)

**Annotation Guidelines:**
```
Bounding Box Rules:
1. Tight boxes around defects
2. Include defect margins
3. No overlapping boxes of same class
4. Label partially visible defects
5. Mark severity in notes
```

#### Day 6: Dataset Split
- [ ] Train: 70% (350-700 images)
- [ ] Validation: 20% (100-200 images)
- [ ] Test: 10% (50-100 images)
- [ ] Verify class distribution

#### Day 7: Augmentation Configuration
- [ ] Configure Roboflow augmentation:
  - Rotation: ±15°
  - Brightness: ±20%
  - Exposure: ±10%
  - Blur: 0-2px
  - Noise: 0-5%
  - Flip: Horizontal
- [ ] Generate dataset version 1
- [ ] Download in YOLOv8 format

**Deliverable:** Annotated dataset with augmentation, ready for training

---

## Week 3-4: Train YOLOv8 Model

### Week 3: Initial Training

**Objectives:**
- Train baseline YOLOv8 model
- Evaluate initial performance
- Identify problem areas

**Tasks:**

#### Day 1: Environment Setup
- [ ] Setup training environment (GPU recommended)
- [ ] Install Ultralytics YOLOv8
- [ ] Download pretrained weights (yolov8n.pt)
- [ ] Verify CUDA/GPU availability

#### Day 2-3: Initial Training
- [ ] Start training (100 epochs)
- [ ] Monitor training metrics
- [ ] Save checkpoints every 10 epochs
- [ ] Log training progress

**Training Configuration:**
```yaml
# config/training_config.yaml
task: detect
mode: train
model: yolov8n.pt
data: data/metal_defects.yaml
epochs: 100
batch: 16
imgsz: 640
patience: 50
save_period: 10
device: 0  # GPU
workers: 8
optimizer: AdamW
lr0: 0.001
```

#### Day 4-5: Evaluation & Analysis
- [ ] Run validation on test set
- [ ] Calculate precision, recall, mAP
- [ ] Generate confusion matrix
- [ ] Identify false positives/negatives
- [ ] Document problem patterns

#### Day 6-7: Error Analysis
- [ ] Review misclassified images
- [ ] Identify common failure modes
- [ ] Plan data collection for gaps
- [ ] Prepare iteration strategy

**Deliverable:** Baseline model with performance metrics

---

### Week 4: Model Optimization

**Objectives:**
- Improve model performance to >90% accuracy
- Optimize for target hardware
- Validate on real production samples

**Tasks:**

#### Day 1-2: Data Augmentation Iteration
- [ ] Collect additional hard examples
- [ ] Add more diverse lighting conditions
- [ ] Augment underrepresented classes
- [ ] Re-train with enhanced dataset

#### Day 3-4: Hyperparameter Tuning
- [ ] Test different model sizes (n, s, m)
- [ ] Adjust confidence threshold
- [ ] Tune IoU threshold
- [ ] Optimize batch size

#### Day 5: Model Optimization
- [ ] Export to ONNX format
- [ ] Convert to TensorRT (Jetson)
- [ ] Convert to OpenVINO (Intel)
- [ ] Benchmark inference speed

#### Day 6-7: Validation Testing
- [ ] Test on fresh production samples
- [ ] Calculate final metrics
- [ ] Document model performance
- [ ] Create model card

**Target Metrics:**
```
Precision: >95%
Recall: >90%
mAP@0.5: >92%
Inference time: <50ms
False positive rate: <2%
```

**Deliverable:** Optimized model ready for deployment

---

## Week 5-6: Deploy Edge Inference System

### Week 5: Edge Device Setup

**Objectives:**
- Setup edge device (Jetson/Intel NUC)
- Deploy inference system
- Integrate with camera

**Tasks:**

#### Day 1-2: Hardware Setup
- [ ] Unbox and setup edge device
- [ ] Install OS (JetPack for Jetson)
- [ ] Configure network connectivity
- [ ] Install system dependencies

#### Day 3-4: Software Deployment
- [ ] Deploy Quality Oracle codebase
- [ ] Install Python dependencies
- [ ] Copy trained model to device
- [ ] Configure environment variables

#### Day 5: Camera Integration
- [ ] Connect industrial camera
- [ ] Test camera feed
- [ ] Configure camera settings
- [ ] Verify frame rate and resolution

#### Day 6-7: Inference Testing
- [ ] Run edge inference script
- [ ] Test with sample parts
- [ ] Measure inference speed
- [ ] Optimize performance

**Deployment Checklist:**
```
✓ Edge device (Jetson/NUC)
✓ Industrial camera
✓ Lighting setup
✓ Network connectivity
✓ Trained model (.pt or .onnx)
✓ Configuration files
✓ Test dataset
```

**Deliverable:** Working edge inference system

---

### Week 6: Production Integration

**Objectives:**
- Integrate with production line
- Setup monitoring and alerts
- Begin shadow mode testing

**Tasks:**

#### Day 1-2: Production Line Integration
- [ ] Mount camera at inspection point
- [ ] Setup lighting system
- [ ] Configure trigger mechanism
- [ ] Test mechanical integration

#### Day 3-4: Software Integration
- [ ] Integrate with PLC (if needed)
- [ ] Setup MES/ERP connector
- [ ] Configure MQTT publishing
- [ ] Enable alert system

#### Day 5: Monitoring Setup
- [ ] Setup Grafana dashboard
- [ ] Configure Prometheus metrics
- [ ] Enable email alerts
- [ ] Test alert workflows

#### Day 6-7: Shadow Mode Testing
- [ ] Run parallel with human inspection
- [ ] Collect system performance data
- [ ] Compare AI vs human results
- [ ] Document discrepancies

**Deliverable:** Integrated system running in shadow mode

---

## Week 7-8: Pilot Testing & Validation

### Week 7: Live Pilot Testing

**Objectives:**
- Run live pilot on production line
- Collect performance data
- Gather operator feedback

**Tasks:**

#### Day 1-2: Pilot Launch
- [ ] Brief production team
- [ ] Start live defect detection
- [ ] Monitor system stability
- [ ] Log all detections

#### Day 3-5: Data Collection
- [ ] Track detection accuracy
- [ ] Monitor false positive rate
- [ ] Record operator interventions
- [ ] Collect production metrics

#### Day 6-7: Feedback & Adjustment
- [ ] Gather operator feedback
- [ ] Identify pain points
- [ ] Adjust thresholds if needed
- [ ] Document learnings

**Pilot Metrics to Track:**
```
- Total parts inspected
- Defects detected
- False positives
- False negatives
- System uptime
- Inference time
- Operator satisfaction
```

**Deliverable:** 1 week of pilot data

---

### Week 8: Analysis & Expansion Planning

**Objectives:**
- Analyze pilot results
- Calculate ROI
- Plan expansion to other facilities

**Tasks:**

#### Day 1-3: Results Analysis
- [ ] Calculate final accuracy metrics
- [ ] Measure defect reduction
- [ ] Calculate cost savings
- [ ] Document case studies

#### Day 4-5: ROI Calculation
- [ ] Labor cost savings
- [ ] Reduced scrap/rework
- [ ] Improved throughput
- [ ] Customer returns reduction
- [ ] Generate ROI report

#### Day 6-7: Expansion Planning
- [ ] Plan deployment to 2nd facility
- [ ] Document lessons learned
- [ ] Create training materials
- [ ] Present results to stakeholders

**ROI Template:**
```
Costs:
- Hardware: $X
- Software/Training: $X
- Implementation time: $X
Total Investment: $X

Benefits (Annual):
- Labor savings: $X
- Scrap reduction: $X
- Quality improvement: $X
- Throughput increase: $X
Total Annual Benefit: $X

ROI = (Benefit - Cost) / Cost × 100%
Payback Period = Cost / Monthly Benefit
```

**Deliverable:** Complete pilot report with ROI and expansion plan

---

## Success Criteria by End of Week 8

✅ **Technical:**
- Model accuracy >90%
- Inference time <100ms
- System uptime >95%

✅ **Business:**
- 20-30% defect reduction demonstrated
- Positive ROI projection
- Operator acceptance

✅ **Operational:**
- 1000+ parts inspected
- System integrated with production
- Documentation complete

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Insufficient training data | Collect 1000+ images before training |
| Poor lighting conditions | Install proper industrial lighting |
| Model not accurate enough | Iterate on data and hyperparameters |
| Edge device too slow | Use TensorRT/OpenVINO optimization |
| Operator resistance | Early involvement and training |
| Integration complexity | Start with standalone then integrate |

---

## Next Steps After Week 8

1. **Expand to 2nd facility** (Week 9-10)
2. **Deploy 3rd facility** (Week 11-12)
3. **Add more defect types** (Ongoing)
4. **Implement reflection agent** (Month 4)
5. **Full MES integration** (Month 5)
6. **Advanced analytics** (Month 6)

---

## Resources Needed

**Hardware:**
- Industrial camera: $300-1000
- Edge device: $200-1000
- Lighting: $100-500

**Software:**
- Roboflow: Free tier or $250/month
- Cloud GPU (training): $1-2/hour × 10 hours = $10-20

**Personnel:**
- AI/CV Engineer: 50% time
- Production Engineer: 25% time
- Operators: Training time

**Total 8-Week Budget: $3,000-5,000**

---

## Tools & Scripts Provided

All implementation tools are in the repository:
- `scripts/week1_data_collection.py`
- `scripts/week2_roboflow_setup.py`
- `scripts/week3_train_model.py`
- `scripts/week5_edge_deploy.py`
- `scripts/week7_pilot_monitoring.py`

**Let's execute this plan!** 🚀
