# Roboflow API 401 Error - Troubleshooting Guide

## Current Issue

You're getting: `401, this api has been removed or revoked error`

This means your Roboflow API key is either:
1. Invalid
2. Expired
3. Revoked
4. Incorrect format

## Quick Fix - Generate New API Key

### Step 1: Go to Roboflow API Settings
```
https://app.roboflow.com/settings/api
```

### Step 2: Generate New Private API Key

1. **Log in** to your Roboflow account
2. Click **"Create New Private API Key"** button
3. **Copy** the entire key (it starts with `rf_`)
4. **Delete** the old key if it shows as revoked

### Step 3: Set the New API Key

**On Mac/Linux:**
```bash
export ROBOFLOW_API_KEY='rf_YOUR_NEW_KEY_HERE'
```

**On Windows (CMD):**
```cmd
set ROBOFLOW_API_KEY=rf_YOUR_NEW_KEY_HERE
```

**On Windows (PowerShell):**
```powershell
$env:ROBOFLOW_API_KEY='rf_YOUR_NEW_KEY_HERE'
```

### Step 4: Test the New Key

```bash
python scripts/test_roboflow_auth.py
```

If you see ✅ **API KEY IS VALID**, proceed to download datasets!

---

## Alternative: Manual Dataset Download (No API Required)

If Roboflow API continues to fail, you can download datasets manually:

### Option 1: Download from Roboflow Website

1. **NEU Steel Defects** (~1,800 images)
   - Visit: https://universe.roboflow.com/brad-dwyer/neu-steel-defects
   - Click "Download Dataset"
   - Choose "YOLOv8" format
   - Download ZIP
   - Extract to: `data/universal_manufacturing/neu_steel/`

2. **PCB Defects** (~340 images)
   - Visit: https://universe.roboflow.com/university-xjcw5/pcb-defect-detection
   - Download as YOLOv8 format
   - Extract to: `data/universal_manufacturing/pcb_defects/`

3. **Welding Defects** (~80 images)
   - Visit: https://universe.roboflow.com/welding-defect-detection/welding-defect-detection
   - Download as YOLOv8 format
   - Extract to: `data/universal_manufacturing/welding_defects/`

### Option 2: Use MVTec AD Dataset (Larger, No API)

MVTec AD is a high-quality industrial dataset with 5,354 images:

1. **Visit MVTec Website:**
   ```
   https://www.mvtec.com/company/research/datasets/mvtec-ad
   ```

2. **Download Categories:**
   - metal_nut (~370 images)
   - screw (~320 images)
   - tile (~230 images)
   - carpet (~280 images)
   - metal (~300 images)

3. **Extract to:**
   ```
   data/universal_manufacturing/mvtec_ad/
   ```

4. **Convert to YOLO format:**
   ```bash
   python scripts/convert_mvtec_to_yolo.py
   ```

### Option 3: Use Pre-trained Universal Model (Skip Training)

If you want to skip the dataset download entirely:

1. Download our pre-trained universal model:
   ```bash
   # We can provide a pre-trained model weights file
   # Or use YOLOv8 pre-trained on COCO as starting point
   ```

2. This won't be specialized for manufacturing defects yet, but it's enough for initial demos

---

## Verify Your API Key Format

### ✅ Correct Private Key Format:
```
rf_abcdefgh123456ABCDEFGH123456abcdefgh
```
- Starts with `rf_`
- Followed by alphanumeric characters
- No spaces, no quotes in the actual key

### ❌ Incorrect Formats:
```
'rf_abc...'          ← Remove quotes when setting
rf_abc... (extra)    ← No extra characters
pk_abc...           ← This is publishable key (wrong type)
```

### Test in Terminal:

**Mac/Linux:**
```bash
echo $ROBOFLOW_API_KEY
```

**Windows:**
```cmd
echo %ROBOFLOW_API_KEY%
```

Should print: `rf_...` (your actual key)

---

## Common Mistakes

### 1. Using Publishable Key Instead of Private Key

**Publishable Key (❌ WRONG for downloads):**
- Format: `pk_...` or different format
- Used for: Public apps, client-side code
- Cannot download datasets

**Private Key (✅ CORRECT for downloads):**
- Format: `rf_...`
- Used for: Server-side, API access, dataset downloads
- This is what you need!

### 2. Extra Spaces or Quotes

```bash
# ❌ WRONG
export ROBOFLOW_API_KEY=' rf_abc123 '

# ✅ CORRECT
export ROBOFLOW_API_KEY='rf_abc123'
```

### 3. Environment Variable Not Set

After setting the key, verify it's actually set:
```bash
python -c "import os; print(os.getenv('ROBOFLOW_API_KEY'))"
```

Should print your key, not `None`

---

## Complete Reset Procedure

If nothing works, start fresh:

### 1. Generate Brand New API Key
```
https://app.roboflow.com/settings/api
→ Create New Private API Key
→ Copy the ENTIRE key
```

### 2. Clear Old Environment Variables
```bash
# Mac/Linux
unset ROBOFLOW_API_KEY

# Windows CMD
set ROBOFLOW_API_KEY=

# Windows PowerShell
Remove-Item Env:\ROBOFLOW_API_KEY
```

### 3. Set New Key
```bash
export ROBOFLOW_API_KEY='rf_YOUR_BRAND_NEW_KEY'
```

### 4. Test Immediately
```bash
python scripts/test_roboflow_auth.py
```

### 5. If Test Passes, Download Data
```bash
python scripts/universal_dataset.py --roboflow-api-key $ROBOFLOW_API_KEY
```

---

## Still Not Working?

### Check Roboflow Account Status

1. Log in to https://app.roboflow.com
2. Check if you're on a free tier with API limits
3. Verify account is in good standing
4. Check if you hit rate limits (wait 1 hour and retry)

### Contact Roboflow Support

- Email: support@roboflow.com
- Say: "My private API key is returning 401 errors when trying to download datasets via Python API"

### Use Alternative Approach

**Skip Roboflow entirely and use direct dataset links:**

We can modify `universal_dataset.py` to download from:
- Direct URLs
- Kaggle datasets
- Google Drive links
- GitHub releases

---

## Next Steps After Fix

Once API key works:

```bash
# 1. Test authentication
python scripts/test_roboflow_auth.py

# 2. Download datasets
python scripts/universal_dataset.py --roboflow-api-key $ROBOFLOW_API_KEY

# 3. Train universal model
python scripts/train_universal_model.py

# 4. Launch demo
python scripts/demo_ui.py
```

---

## Emergency Fallback

If you need to demo TODAY and can't fix the API:

1. **Use YOLOv8 pre-trained model:**
   ```bash
   python -c "from ultralytics import YOLO; model = YOLO('yolov8m.pt'); print('Downloaded')"
   ```

2. **Test on generic objects first:**
   - Pre-trained YOLO can detect 80 object classes
   - Not perfect for defects, but proves the technology works
   - Good enough for initial proof-of-concept

3. **Demo with webcam:**
   ```bash
   python scripts/demo_ui.py --use-pretrained
   ```

4. **Tell customers:**
   - "This is our base model trained on general objects"
   - "For YOUR defects, we'll train specifically on YOUR parts"
   - "Demo shows the technology, not final accuracy"

---

**Let's fix this API issue and get you training!** 🚀
