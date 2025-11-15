# Windows Setup Guide - Get Latest Files

## The Issue
The files I created (`test_roboflow_auth.py`, `claude.md`, etc.) are in the git repository but not yet on your local Windows machine. You need to pull them first!

## Quick Fix - Get the Files

### Step 1: Open Command Prompt and Navigate to Project

```cmd
cd Desktop\Manufacturing-Quality-Oracle
```

### Step 2: Pull Latest Changes from Repository

```cmd
git pull origin claude/quality-assurance-oracle-011CUrPQL4ZyeCpABwisPiMq
```

This downloads all the new files I just created.

### Step 3: Verify Files Exist

```cmd
dir scripts\test_roboflow_auth.py
```

Should show the file. If you see "File Not Found", continue reading below.

### Step 4: Run the Test Script

```cmd
python scripts\test_roboflow_auth.py
```

**Note:** Use backslash `\` on Windows, not forward slash `/`

---

## Full Windows Setup (If Git Pull Doesn't Work)

### If you haven't cloned the repository yet:

```cmd
:: Navigate to Desktop
cd Desktop

:: Clone the repository
git clone https://github.com/sarfrazkhan18/Manufacturing-Quality-Oracle.git

:: Enter the directory
cd Manufacturing-Quality-Oracle

:: Switch to the feature branch
git checkout claude/quality-assurance-oracle-011CUrPQL4ZyeCpABwisPiMq

:: Pull latest changes
git pull
```

### If you already have the folder but git isn't set up:

```cmd
:: Navigate to the folder
cd Desktop\Manufacturing-Quality-Oracle

:: Initialize git (if needed)
git init

:: Add remote
git remote add origin https://github.com/sarfrazkhan18/Manufacturing-Quality-Oracle.git

:: Fetch all branches
git fetch --all

:: Checkout the feature branch
git checkout claude/quality-assurance-oracle-011CUrPQL4ZyeCpABwisPiMq

:: Pull latest
git pull origin claude/quality-assurance-oracle-011CUrPQL4ZyeCpABwisPiMq
```

---

## Complete Windows Command Reference

### Setting Roboflow API Key (Windows CMD)

```cmd
:: Set the API key for current session
set ROBOFLOW_API_KEY=rf_YOUR_NEW_KEY_HERE

:: Verify it's set
echo %ROBOFLOW_API_KEY%
```

### Setting Roboflow API Key (Windows PowerShell)

```powershell
# Set the API key
$env:ROBOFLOW_API_KEY='rf_YOUR_NEW_KEY_HERE'

# Verify it's set
echo $env:ROBOFLOW_API_KEY
```

### Running Python Scripts on Windows

```cmd
:: Test authentication
python scripts\test_roboflow_auth.py

:: Download datasets (after API test passes)
python scripts\universal_dataset.py --roboflow-api-key %ROBOFLOW_API_KEY%

:: Train model (later)
python scripts\train_universal_model.py

:: Launch demo (later)
python scripts\demo_ui.py
```

---

## Troubleshooting Windows Issues

### Issue: "python is not recognized"

**Solution 1:** Use `py` instead of `python`
```cmd
py scripts\test_roboflow_auth.py
```

**Solution 2:** Install Python from python.org and add to PATH

### Issue: "git is not recognized"

**Solution:** Install Git for Windows from https://git-scm.com/download/win

### Issue: "No module named 'roboflow'"

**Solution:** Install dependencies
```cmd
:: Run the Windows setup script
quick_setup.bat

:: Or manually install
pip install roboflow ultralytics opencv-python torch loguru
```

### Issue: Files still not found after git pull

**Solution:** Check you're in the right directory
```cmd
:: Show current directory
cd

:: Should show: C:\Users\YourName\Desktop\Manufacturing-Quality-Oracle

:: List files
dir

:: Should see: scripts, docs, requirements.txt, etc.
```

---

## Step-by-Step: From Scratch on Windows

1. **Open Command Prompt (CMD)**
   - Press `Win + R`
   - Type `cmd`
   - Press Enter

2. **Navigate to Desktop**
   ```cmd
   cd Desktop
   ```

3. **Clone Repository (if not done)**
   ```cmd
   git clone https://github.com/sarfrazkhan18/Manufacturing-Quality-Oracle.git
   cd Manufacturing-Quality-Oracle
   ```

4. **Switch to Feature Branch**
   ```cmd
   git checkout claude/quality-assurance-oracle-011CUrPQL4ZyeCpABwisPiMq
   git pull
   ```

5. **Install Dependencies**
   ```cmd
   quick_setup.bat
   ```

6. **Set API Key**
   ```cmd
   set ROBOFLOW_API_KEY=rf_YOUR_NEW_KEY_HERE
   ```

7. **Test API**
   ```cmd
   python scripts\test_roboflow_auth.py
   ```

---

## Quick Check Commands

```cmd
:: Where am I?
cd

:: What's in this folder?
dir

:: Does the script exist?
dir scripts\test_roboflow_auth.py

:: Is Python installed?
python --version

:: Is git installed?
git --version

:: What branch am I on?
git branch

:: Do I have the latest files?
git status
```

---

## Expected Output After Setup

```cmd
C:\Users\YourName\Desktop\Manufacturing-Quality-Oracle>python scripts\test_roboflow_auth.py

======================================================================
🔍 Roboflow API Authentication Diagnostic
======================================================================

📋 Testing API Key: rf_abcdefg...xyz

Test 1: Initializing Roboflow client...
✅ Client initialized successfully

Test 2: Accessing your workspace...
✅ Workspace accessed: your-workspace

Test 3: Checking available projects...
✅ API key has workspace access

======================================================================
✅ API KEY IS VALID!
======================================================================

Your Roboflow API key is working correctly.
You can now proceed with downloading datasets.
```

---

## Still Having Issues?

### Option 1: Provide More Info
Tell me:
1. What directory are you in? (run `cd`)
2. What files do you see? (run `dir`)
3. Do you have git? (run `git --version`)
4. What's the exact error message?

### Option 2: Manual File Download
If git isn't working, I can provide the script content for you to copy manually.

---

**Next Step:** Run these commands and tell me what you see:

```cmd
cd Desktop\Manufacturing-Quality-Oracle
git status
dir scripts
```
