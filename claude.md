# Claude Code - Manufacturing Quality Oracle Project Guidelines

## Critical Project Management

1. **NEVER let AI modify requirements.txt without review**
   - Review all package additions/updates before accepting
   - One incompatible dependency = broken Python environment
   - Pin critical versions (PyTorch, CUDA, Ultralytics)
   - Document why each dependency is needed

2. **Git commit discipline**
   - Don't use "Claude fix" when pushing commits/PRs
   - All commits must come from your personal account
   - Use conventional commits: feat/fix/docs/refactor/perf
   - Review every change before committing
   - ALWAYS commit to branch: `claude/quality-assurance-oracle-011CUrPQL4ZyeCpABwisPiMq`

3. **API Key Security**
   - NEVER commit API keys to git
   - Always use environment variables
   - Keep `.env` in `.gitignore`
   - Use `.env.example` for templates only
   - Roboflow private keys start with `rf_`

## ML/Computer Vision Specific Gotchas

4. **Dataset Management**
   - ALWAYS verify dataset structure before training
   - Required structure:
     ```
     data/
     ├── images/
     │   ├── train/
     │   ├── valid/
     │   └── test/
     └── labels/
         ├── train/
         ├── valid/
         └── test/
     ```
   - Check `dataset.yaml` exists and paths are correct
   - Verify class count matches actual classes
   - Document data sources and licenses

5. **Training Best Practices**
   - ALWAYS check GPU availability before training: `torch.cuda.is_available()`
   - Start with small epochs (10-20) to test pipeline
   - Save checkpoints frequently (every 10-20 epochs)
   - Monitor for overfitting: train vs validation loss
   - Document training hyperparameters in commit messages
   - Expected training times:
     - YOLOv8n: 1-2 hours on GPU
     - YOLOv8m: 2-4 hours on GPU
     - YOLOv8l: 4-8 hours on GPU

6. **Model Versioning**
   - Save models with descriptive names: `universal_v1_mAP85.pt`
   - Track model performance metrics
   - Keep training logs: `runs/detect/train/`
   - Document model improvements in `models/CHANGELOG.md`
   - Never overwrite working models

## Roboflow API Issues

7. **Authentication Troubleshooting**
   - Use PRIVATE key (starts with `rf_`), not publishable key
   - Test API before downloading: `python scripts/test_roboflow_auth.py`
   - 401 errors = invalid/expired key → generate new one
   - 429 errors = rate limit → wait 1 hour
   - Keys can take 5-10 minutes to activate after creation
   - Free tier limits: Check Roboflow dashboard

8. **Dataset Download Fallbacks**
   - If Roboflow fails, use manual download
   - Alternative: Pre-trained YOLOv8 weights as starting point
   - Alternative: Kaggle datasets (NEU Steel, MVTec AD)
   - Document data provenance for compliance

## Development Workflow

9. **Test after EVERY change**
   - Verify imports: `python -c "import ultralytics, cv2, torch"`
   - Check Python version: `python --version` (need 3.8+)
   - Test CUDA: `python -c "import torch; print(torch.cuda.is_available())"`
   - Lint Python code: `pylint src/` or `flake8 src/`
   - Run quick inference test before full training

10. **Always request debug logging**
    - Use `loguru` for all logging (already in dependencies)
    - Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    - Log these events:
      - Dataset loading progress
      - Model training metrics (loss, mAP, precision, recall)
      - API calls (requests/responses)
      - File I/O operations
      - Inference times
    - Example:
      ```python
      from loguru import logger
      logger.info(f"Training started: {epochs} epochs")
      logger.debug(f"Batch size: {batch_size}")
      ```

11. **Performance Benchmarking**
    - ALWAYS measure inference time
    - Target: <50ms for edge devices (Jetson)
    - Target: <30ms for desktop (GPU)
    - Use TensorRT for production (10x speedup)
    - Document FPS and latency in model README

## Conversation Management

12. **Keep conversations focused on single features**
    - Don't ask to "rewrite the entire pipeline"
    - One script, one model, one bug at a time
    - Smaller changes = easier debugging
    - ML experiments should be isolated

13. **Document what changed in each session**
    - End major changes with markdown explaining:
      - What was added/modified
      - Why (dataset change, model improvement, bug fix)
      - Performance metrics (before/after)
      - How to test it
      - Rollback procedure
    - Keep in `docs/session-notes/YYYY-MM-DD.md`

## Known Issues & Solutions

### Roboflow API Issues
- **401 Unauthorized**: API key expired/revoked → Generate new private key
- **429 Rate Limit**: Too many requests → Wait 1 hour or use manual download
- **Workspace not found**: Wrong workspace name → Check Roboflow dashboard
- **Solution**: `python scripts/test_roboflow_auth.py` to diagnose

### PyTorch/CUDA Issues
- **CUDA out of memory**: Reduce batch size (16 → 8 → 4)
- **No CUDA detected**: Check `nvidia-smi` and reinstall torch with CUDA
- **Version mismatch**: PyTorch CUDA version must match system CUDA
- **Mac M1/M2**: Use `device='mps'` instead of `cuda`
- **CPU fallback**: Training will be 10-100x slower

### YOLOv8/Ultralytics Issues
- **Low mAP (<60%)**: Need more training data or longer training
- **Overfitting**: Reduce model size or increase augmentation
- **Slow inference**: Use smaller model (yolov8n) or TensorRT
- **Class imbalance**: Use class weights in training
- **Solution**: Check `runs/detect/train/` for training curves

### Dataset Issues
- **Empty folders**: Roboflow download failed → Check API key
- **Mismatched labels**: Class IDs don't match `dataset.yaml`
- **Missing images**: Check file extensions (.jpg, .jpeg, .png)
- **Corrupt images**: Use `cv2.imread()` to validate all images
- **Wrong format**: YOLO needs: `class_id x_center y_center width height`

### Streamlit Demo Issues
- **Port already in use**: Use `--server.port 8502`
- **Model not found**: Check model path in `demo_ui.py`
- **Slow predictions**: Use smaller model or GPU
- **CORS errors**: Set `--server.enableCORS false`

## Project-Specific Conventions

### File Naming
- **Scripts**: `verb_noun.py` (e.g., `train_universal_model.py`)
- **Models**: `{type}_v{version}_mAP{score}.pt` (e.g., `universal_v1_mAP87.pt`)
- **Datasets**: `{source}_{date}.zip` (e.g., `roboflow_20251115.zip`)
- **Logs**: `{script}_{timestamp}.log`

### Directory Structure (Never modify without discussion)
```
Manufacturing-Quality-Oracle/
├── data/                      # Datasets (gitignored)
│   ├── universal_manufacturing/
│   └── customers/{customer_name}/
├── models/                    # Trained models (gitignored)
│   ├── universal/
│   └── customers/{customer_name}/
├── scripts/                   # Executable Python scripts
├── src/                       # Core library code
├── docs/                      # Documentation
├── deployment/                # Docker, Kubernetes configs
└── tests/                     # Unit and integration tests
```

### Model Performance Expectations
- **Universal Model (Week 1)**: 85-92% mAP@0.5
- **Customer Fine-tuned (Week 5+)**: 95%+ mAP@0.5
- **Inference Speed**: <50ms on Jetson Xavier, <30ms on desktop GPU
- **Classes**: 7 unified classes (scratch, dent, crack, contamination, color_defect, missing, surface_defect)

## Python Best Practices

14. **Type Hints**
    - Always use type hints for function signatures
    - Use `from typing import List, Dict, Optional, Union`
    - Example:
      ```python
      def train_model(dataset_path: Path, epochs: int = 100) -> YOLO:
          ...
      ```

15. **Error Handling**
    - Catch specific exceptions, not bare `except:`
    - Log errors with context
    - Provide actionable error messages
    - Example:
      ```python
      try:
          rf = Roboflow(api_key=api_key)
      except Exception as e:
          logger.error(f"Roboflow auth failed: {e}")
          logger.info("Generate new key: https://app.roboflow.com/settings/api")
          raise
      ```

16. **Resource Management**
    - Use context managers for file I/O
    - Clear CUDA cache after training: `torch.cuda.empty_cache()`
    - Delete large variables when done
    - Monitor RAM/VRAM usage during training

## Rollback Procedures

If Claude Code breaks something:
1. `git status` to see what changed
2. `git diff` to review exact changes
3. `git checkout -- <file>` to restore individual files
4. Or `git reset --hard HEAD` to reset everything (DESTRUCTIVE)
5. Test with: `python scripts/test_roboflow_auth.py`
6. Document the issue in this file to prevent recurrence

## Environment Setup

### Required Versions
- **Python**: 3.8+ (tested on 3.10)
- **PyTorch**: 2.0+ with CUDA 11.8+ (or CPU version)
- **Ultralytics**: Latest (updates frequently)
- **CUDA**: 11.8 or 12.1 (for GPU training)

### Package Manager
- **Primary**: `pip` (standard Python)
- **Virtual env**: `venv` or `conda`
- **Setup script**: `quick_setup.sh` (Mac/Linux) or `quick_setup.bat` (Windows)

### Key Dependencies (Locked Versions)
```
ultralytics>=8.0.0      # YOLOv8 framework
torch>=2.0.0            # Deep learning
opencv-python>=4.8.0    # Computer vision
roboflow>=1.1.0         # Dataset management
loguru>=0.7.0           # Logging
streamlit>=1.28.0       # Demo UI
Pillow>=10.0.0          # Image processing
pyyaml>=6.0             # Config files
tqdm>=4.66.0            # Progress bars
```

### GPU Setup
```bash
# Check CUDA version
nvidia-smi

# Install PyTorch with CUDA
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Verify GPU
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

## Week 1 Critical Path (DO NOT DEVIATE)

**Day 1-2: Data Collection**
- Fix Roboflow API authentication
- Download 2,220-7,200 images (NEU Steel, PCB, Welding, MVTec)
- Verify dataset structure

**Day 3-4: Training**
- Train universal model (85-92% target)
- Benchmark inference speed (<50ms)
- Save best model

**Day 5-7: Demo Preparation**
- Build Streamlit demo UI
- Test with sample images
- Prepare sales materials

## Common Questions

**Q: Training is slow (>1 hour/epoch)**
- A: Reduce batch size, use smaller model (yolov8n), or switch to Google Colab GPU

**Q: Getting CUDA out of memory**
- A: Reduce batch size: `--batch 4` or use CPU: `--device cpu`

**Q: Model accuracy is low (<70%)**
- A: Need more data, longer training, or better augmentation

**Q: Roboflow API keeps failing**
- A: Use manual download from Roboflow website or skip to pre-trained model

**Q: Can't find dataset.yaml**
- A: Run `python scripts/universal_dataset.py --roboflow-api-key $KEY` first

**Q: Demo UI won't start**
- A: Check `pip install streamlit` and use `streamlit run scripts/demo_ui.py`

## Emergency Contacts & Resources

- **Roboflow Support**: support@roboflow.com
- **Ultralytics Docs**: https://docs.ultralytics.com
- **PyTorch Docs**: https://pytorch.org/docs
- **Project Issues**: https://github.com/sarfrazkhan18/Manufacturing-Quality-Oracle/issues
- **Claude Code Docs**: https://docs.claude.com/en/docs/claude-code

## Project Timeline (Reference)

- **Week 1**: Universal model (85-92% accuracy) ← YOU ARE HERE
- **Week 2-4**: Customer demos & pilot signups
- **Week 5+**: Fine-tuning per customer (95%+ accuracy)
- **Month 3+**: Production deployments

## Success Metrics

**Technical:**
- ✅ Universal model: 85-92% mAP@0.5
- ✅ Inference: <50ms on edge devices
- ✅ Demo: Works on customer images
- ✅ Deployable: Docker + TensorRT ready

**Business:**
- ✅ Week 4: 3-5 pilot customers signed
- ✅ Month 3: 2-3 production deployments
- ✅ Year 1: 20-50 customers, $400k-$2.5M revenue

---

**Last Updated**: 2025-11-15
**Current Phase**: Week 1 - Universal Model Setup
**Current Branch**: `claude/quality-assurance-oracle-011CUrPQL4ZyeCpABwisPiMq`
**Next Milestone**: Fix Roboflow API → Download datasets → Train universal model
