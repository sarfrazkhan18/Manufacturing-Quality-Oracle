@echo off
REM Quick Setup Script for Manufacturing Quality Oracle (Windows)
REM Run this after cloning the repository

echo ==========================================
echo Manufacturing Quality Oracle - Quick Setup
echo ==========================================
echo.

REM Check Python version
echo Checking Python version...
python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
echo Virtual environment created
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel
echo Pip upgraded
echo.

REM Install core dependencies
echo Installing core dependencies (this takes 5-10 minutes)...
echo Installing: ultralytics, opencv-python, roboflow...
pip install ultralytics opencv-python opencv-python-headless

echo Installing: PyTorch...
pip install torch torchvision

echo Installing: roboflow, loguru, pyyaml...
pip install roboflow loguru pyyaml

echo Installing: streamlit for demo UI...
pip install streamlit plotly

echo Core dependencies installed
echo.

REM Create necessary directories
echo Creating project directories...
mkdir data\universal_manufacturing 2>nul
mkdir models\universal 2>nul
mkdir models\customers 2>nul
mkdir logs 2>nul
mkdir reports 2>nul
echo Directories created
echo.

REM Verify installation
echo Verifying installation...
python -c "import ultralytics; print('✅ Ultralytics (YOLO) installed')" 2>nul || echo ❌ Ultralytics installation failed
python -c "import cv2; print('✅ OpenCV installed')" 2>nul || echo ❌ OpenCV installation failed
python -c "import roboflow; print('✅ Roboflow installed')" 2>nul || echo ❌ Roboflow installation failed
python -c "import torch; print(f'✅ PyTorch installed (CUDA: {torch.cuda.is_available()})')" 2>nul || echo ❌ PyTorch installation failed
python -c "import streamlit; print('✅ Streamlit installed')" 2>nul || echo ❌ Streamlit installation failed
echo.

REM Check GPU
echo Checking GPU availability...
python -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}'); print(f'GPU Name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None (CPU mode)\"}')" 2>nul
echo.

echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Next Steps:
echo.
echo 1. Get Roboflow API key:
echo    https://app.roboflow.com/settings/api
echo.
echo 2. Set API key:
echo    set ROBOFLOW_API_KEY=your_key_here
echo.
echo 3. Download datasets:
echo    python scripts\universal_dataset.py --roboflow-api-key %%ROBOFLOW_API_KEY%%
echo.
echo 4. Train universal model:
echo    python scripts\train_universal_model.py
echo.
echo 5. Launch demo UI:
echo    python scripts\demo_ui.py
echo.
echo ==========================================
echo Need help? Just ask!
echo ==========================================
pause
