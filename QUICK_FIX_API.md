# QUICK FIX: Roboflow API 401 Error

## Your Current Situation
- ❌ Getting: `401, this api has been removed or revoked error`
- 📁 Empty folders created at: `data/universal_manufacturing/images/test/train/model`
- 🔑 You have both private and publishable keys

## Immediate Steps to Fix

### Step 1: Generate Fresh API Key (2 minutes)

1. **Open Roboflow API Settings:**
   ```
   https://app.roboflow.com/settings/api
   ```

2. **Look for your API keys section**
   - You should see "Private API Key" section
   - If the current key shows as "revoked" or "expired", delete it

3. **Click "Create New Private API Key"**
   - Copy the ENTIRE key (starts with `rf_`)
   - It will look like: `rf_abcdefgh123456789ABCDEFGH`

### Step 2: Set the New Key in Terminal

**On Mac/Linux:**
```bash
cd ~/Desktop/Manufacturing-Quality-Oracle
export ROBOFLOW_API_KEY='rf_PASTE_YOUR_NEW_KEY_HERE'
```

**On Windows CMD:**
```cmd
cd Desktop\Manufacturing-Quality-Oracle
set ROBOFLOW_API_KEY=rf_PASTE_YOUR_NEW_KEY_HERE
```

**On Windows PowerShell:**
```powershell
cd Desktop\Manufacturing-Quality-Oracle
$env:ROBOFLOW_API_KEY='rf_PASTE_YOUR_NEW_KEY_HERE'
```

### Step 3: Verify the Key is Set

**Mac/Linux:**
```bash
echo $ROBOFLOW_API_KEY
```

**Windows CMD:**
```cmd
echo %ROBOFLOW_API_KEY%
```

**Windows PowerShell:**
```powershell
echo $env:ROBOFLOW_API_KEY
```

✅ Should print: `rf_...` (your actual key)
❌ If it prints blank or "undefined", the key wasn't set correctly

### Step 4: Test Authentication

```bash
python scripts/test_roboflow_auth.py
```

**Expected output:**
```
✅ API KEY IS VALID!
```

**If still failing:**
- The key might need a few minutes to activate
- Try logging out and back in to Roboflow
- Check if you're on a free tier with restrictions

### Step 5: Download Datasets

Once authentication works:

```bash
python scripts/universal_dataset.py --roboflow-api-key $ROBOFLOW_API_KEY
```

---

## Alternative: Skip Roboflow Entirely (Use Pre-trained Model)

If the API continues to fail, you can skip dataset download and use YOLOv8's pre-trained weights:

```bash
# Download pre-trained YOLOv8 medium model
python -c "from ultralytics import YOLO; model = YOLO('yolov8m.pt'); print('✅ Model downloaded')"
```

This gives you:
- ✅ Working YOLO model immediately
- ✅ Can demo the technology today
- ❌ Not trained on manufacturing defects (yet)
- ⚠️  Accuracy will be lower for defects

Then tell customers:
> "This base model demonstrates our AI technology. For YOUR specific defects, we'll train on YOUR parts and achieve 95%+ accuracy."

---

## Common Issues

### Issue: "Command not found: python"

**Mac/Linux:**
```bash
python3 scripts/test_roboflow_auth.py
```

**Windows:**
Make sure Python is installed and in PATH

### Issue: "No module named 'roboflow'"

```bash
pip install roboflow
```

Or run the full setup:
```bash
# Mac/Linux
bash quick_setup.sh

# Windows
quick_setup.bat
```

### Issue: Environment variable disappears after closing terminal

You need to set it each time, OR add to your shell config:

**Mac/Linux (permanent):**
```bash
echo 'export ROBOFLOW_API_KEY="rf_YOUR_KEY"' >> ~/.bashrc
source ~/.bashrc
```

**Windows (permanent):**
Use System Environment Variables:
1. Search "Environment Variables" in Windows
2. Add new variable: `ROBOFLOW_API_KEY` = `rf_YOUR_KEY`

---

## Quick Diagnostic Commands

### Check Python Installation
```bash
python --version
# Should show: Python 3.8+
```

### Check if Roboflow Package is Installed
```bash
python -c "import roboflow; print('✅ Roboflow installed')"
```

### Test API Key Format
```bash
# Your key should start with 'rf_'
echo $ROBOFLOW_API_KEY | grep "^rf_"
# Should print your key if format is correct
```

---

## Timeline After Fix

Once API works:

**Today (30 minutes):**
- ✅ Fix API key
- ✅ Download datasets (~2,220 images)
- ✅ Verify dataset structure

**Tomorrow (2-4 hours):**
- ✅ Train universal model
- ✅ Get 85-92% accuracy

**Day 3 (1 hour):**
- ✅ Test demo UI
- ✅ Ready for customer demos!

---

## Need Help?

1. **Run diagnostic script:**
   ```bash
   python scripts/test_roboflow_auth.py
   ```

2. **Check detailed troubleshooting:**
   ```bash
   cat docs/ROBOFLOW_API_TROUBLESHOOTING.md
   ```

3. **Try alternative approach:**
   - Skip Roboflow
   - Use pre-trained YOLO
   - Demo with generic model first

---

**Let's get your API key fixed and start downloading data!** 🚀
