# 🪟 Windows Local Setup Guide (No Docker - Much Faster!)

## ✅ Why Install Locally on Windows?

**Yes, installing without Docker is MUCH faster on Windows!**

| Method               | Setup Time    | Performance          | Complexity |
| -------------------- | ------------- | -------------------- | ---------- |
| **Docker (Windows)** | 2-4 hours     | Slow (WSL2 overhead) | High       |
| **Local (Windows)**  | 15-30 minutes | Fast (native)        | Low        |

### Benefits:

- ⚡ **10-20x faster setup** (15-30 min vs 2-4 hours)
- 🚀 **Better performance** (no virtualization overhead)
- 🔧 **Easier debugging** (direct access to files/logs)
- 💾 **Less disk space** (no Docker images)
- 🔄 **Faster development** (instant code changes)

---

## 📋 Prerequisites

1. **Python 3.11+** - Download from [python.org](https://www.python.org/downloads/)

   - ✅ Check "Add Python to PATH" during installation
   - Verify: `python --version` in Command Prompt

2. **Git** (optional) - For cloning repository

   - Download from [git-scm.com](https://git-scm.com/download/win)

3. **Visual C++ Build Tools** (for some packages)
   - Download from [Microsoft](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - Or install Visual Studio with C++ workload

---

## 🚀 Quick Setup (15-30 minutes)

### Step 1: Open Command Prompt or PowerShell

Press `Win + R`, type `cmd`, press Enter

### Step 2: Navigate to Project Directory

```cmd
cd C:\Users\YourName\MediGenius
```

Or if you need to clone:

```cmd
git clone <your-repo-url>
cd MediGenius
```

### Step 3: Create Virtual Environment

```cmd
python -m venv venv
```

### Step 4: Activate Virtual Environment

```cmd
venv\Scripts\activate
```

You should see `(venv)` in your prompt.

### Step 5: Upgrade pip

```cmd
python -m pip install --upgrade pip setuptools wheel
```

### Step 6: Install Dependencies (This takes 15-30 minutes)

**Option A: Install all at once (recommended)**

```cmd
pip install -r requirements.txt
```

**Option B: Install in stages (if you encounter errors)**

```cmd
REM Install core dependencies first
pip install flask python-dotenv passlib bcrypt reportlab apscheduler scikit-learn

REM Install LangChain packages
pip install langchain-core langchain-community langchain-groq langchain_huggingface langgraph langchain-chroma

REM Install ML dependencies (these are large)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers sentence-transformers

REM Install remaining packages
pip install huggingface-hub pypdf wikipedia duckduckgo-search chromadb
```

### Step 7: Create `.env` File

Create a file named `.env` in the project root:

```env
# Groq API Key (Required)
# Get your API key from: https://console.groq.com/
GROQ_API_KEY=your_groq_api_key_here

# Email Configuration (for medication reminders)
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Tavily API Key (Optional - for web search fallback)
TAVILY_API_KEY=your_tavily_api_key_here
```

**Important:**

- Get Groq API key from https://console.groq.com/
- For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833)

### Step 8: Create Required Directories

```cmd
mkdir chat_db
mkdir medical_db
mkdir data
```

### Step 9: Run the Application

```cmd
python app.py
```

You should see:

```
 * Running on http://127.0.0.1:5000
```

Open your browser and go to: **http://localhost:5000**

---

## 🔧 Troubleshooting

### Issue: "python is not recognized"

**Solution:**

1. Reinstall Python and check "Add Python to PATH"
2. Or use full path: `C:\Python311\python.exe -m venv venv`

### Issue: "Microsoft Visual C++ 14.0 is required"

**Solution:**

1. Install [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Or install [Visual Studio](https://visualstudio.microsoft.com/) with C++ workload

### Issue: "Failed building wheel for bcrypt"

**Solution:**

```cmd
pip install --upgrade pip setuptools wheel
pip install bcrypt --no-cache-dir
```

### Issue: "torch installation is very slow"

**Solution:** Use CPU-only version (faster install):

```cmd
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Issue: "Out of memory" during installation

**Solution:**

1. Close other applications
2. Install packages one by one instead of all at once
3. Use `--no-cache-dir` flag: `pip install --no-cache-dir -r requirements.txt`

### Issue: "Permission denied" errors

**Solution:**

1. Run Command Prompt as Administrator
2. Or install to user directory: `pip install --user -r requirements.txt`

### Issue: "SSL certificate verification failed"

**Solution:**

```cmd
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
```

---

## ⚡ Performance Tips

### 1. Use CPU-only PyTorch (Faster Install)

If you don't need GPU acceleration, use CPU-only PyTorch:

```cmd
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### 2. Install in Stages

If installation fails, install in smaller groups:

```cmd
REM Stage 1: Core
pip install flask python-dotenv

REM Stage 2: LangChain
pip install langchain-core langchain-community langchain-groq

REM Stage 3: ML (large packages)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers sentence-transformers

REM Stage 4: Rest
pip install -r requirements.txt
```

### 3. Use pip Cache (Faster Reinstalls)

```cmd
REM Clear cache if corrupted
pip cache purge

REM Or use cache for faster reinstalls
pip install -r requirements.txt
```

---

## 🎯 Daily Usage

### Starting the Application

```cmd
cd C:\Users\YourName\MediGenius
venv\Scripts\activate
python app.py
```

### Stopping the Application

Press `Ctrl + C` in the terminal

### Updating Dependencies

```cmd
venv\Scripts\activate
pip install --upgrade -r requirements.txt
```

---

## 📊 Expected Installation Times

| Package Group      | Size     | Time          |
| ------------------ | -------- | ------------- |
| Core (flask, etc.) | ~50MB    | 2-3 min       |
| LangChain packages | ~100MB   | 3-5 min       |
| PyTorch (CPU)      | ~150MB   | 5-10 min      |
| Transformers       | ~500MB   | 5-10 min      |
| ChromaDB           | ~200MB   | 3-5 min       |
| **Total**          | **~1GB** | **15-30 min** |

**Note:** Times depend on your internet speed and CPU.

---

## ✅ Verification

After installation, verify everything works:

```cmd
python -c "import flask; import torch; import transformers; print('✅ All packages installed successfully!')"
```

---

## 🆚 Docker vs Local Comparison

| Aspect             | Docker (Windows)   | Local (Windows) |
| ------------------ | ------------------ | --------------- |
| **Setup Time**     | 2-4 hours          | 15-30 minutes   |
| **Disk Space**     | ~10GB+             | ~2-3GB          |
| **Performance**    | Slow (WSL2)        | Fast (native)   |
| **Debugging**      | Harder             | Easier          |
| **Code Changes**   | Requires rebuild   | Instant         |
| **Resource Usage** | High (VM overhead) | Low (native)    |

**Recommendation:** Use local installation for development, Docker for production deployment.

---

## 🎉 You're Done!

Your application should now be running at **http://localhost:5000**

If you encounter any issues, check the troubleshooting section above or refer to `SETUP_LOCAL.md` for more details.
