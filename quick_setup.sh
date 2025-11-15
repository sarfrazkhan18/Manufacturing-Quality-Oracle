#!/bin/bash
# Quick Setup Script for Manufacturing Quality Oracle
# Run this after cloning the repository

echo "=========================================="
echo "Manufacturing Quality Oracle - Quick Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+')
echo "✅ Python $python_version detected"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
echo "✅ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel --quiet
echo "✅ Pip upgraded"
echo ""

# Install core dependencies
echo "Installing core dependencies (this takes 5-10 minutes)..."
echo "Installing: ultralytics, opencv-python, roboflow..."
pip install ultralytics opencv-python opencv-python-headless --quiet

echo "Installing: PyTorch (this is the big one)..."
pip install torch torchvision --quiet

echo "Installing: roboflow, loguru, pyyaml..."
pip install roboflow loguru pyyaml --quiet

echo "Installing: streamlit for demo UI..."
pip install streamlit plotly --quiet

echo "✅ Core dependencies installed"
echo ""

# Create necessary directories
echo "Creating project directories..."
mkdir -p data/universal_manufacturing
mkdir -p models/universal
mkdir -p models/customers
mkdir -p logs
mkdir -p reports
echo "✅ Directories created"
echo ""

# Verify installation
echo "Verifying installation..."
python -c "import ultralytics; print('✅ Ultralytics (YOLO) installed')" 2>/dev/null || echo "❌ Ultralytics installation failed"
python -c "import cv2; print('✅ OpenCV installed')" 2>/dev/null || echo "❌ OpenCV installation failed"
python -c "import roboflow; print('✅ Roboflow installed')" 2>/dev/null || echo "❌ Roboflow installation failed"
python -c "import torch; print(f'✅ PyTorch installed (CUDA: {torch.cuda.is_available()})')" 2>/dev/null || echo "❌ PyTorch installation failed"
python -c "import streamlit; print('✅ Streamlit installed')" 2>/dev/null || echo "❌ Streamlit installation failed"
echo ""

# Check GPU
echo "Checking GPU availability..."
python -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}'); print(f'GPU Name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None (CPU mode)\"}');" 2>/dev/null
echo ""

echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo ""
echo "1. Get Roboflow API key:"
echo "   https://app.roboflow.com/settings/api"
echo ""
echo "2. Set API key:"
echo "   export ROBOFLOW_API_KEY='your_key_here'"
echo ""
echo "3. Download datasets:"
echo "   python scripts/universal_dataset.py --roboflow-api-key \$ROBOFLOW_API_KEY"
echo ""
echo "4. Train universal model:"
echo "   python scripts/train_universal_model.py"
echo ""
echo "5. Launch demo UI:"
echo "   python scripts/demo_ui.py"
echo ""
echo "=========================================="
echo "Need help? Just ask!"
echo "=========================================="
