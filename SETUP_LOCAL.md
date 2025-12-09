# Local Setup Guide (Without Docker)

> **💡 For Windows users:** See `SETUP_WINDOWS.md` for Windows-specific instructions (much faster than Docker on Windows!)

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

## Setup Steps

### 1. Create Virtual Environment

**Linux/Mac:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**

```cmd
python -m venv venv
venv\Scripts\activate
```

### 2. Upgrade pip

```bash
python -m pip install --upgrade pip setuptools wheel
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** This may take 15-30 minutes depending on your internet speed. The large packages (torch, transformers) are ~1GB total.

### 4. Create .env File

Create a `.env` file in the project root with the following content:

```env
# Groq API Key (Required)
# Get your API key from: https://console.groq.com/
GROQ_API_KEY=your_groq_api_key_here

# Email Configuration (for medication reminders)
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Tavily API Key (Optional - for web search fallback)
# Get your API key from: https://tavily.com/
TAVILY_API_KEY=your_tavily_api_key_here
```

**Important:**

- Replace `your_groq_api_key_here` with your actual Groq API key from https://console.groq.com/
- For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833) for EMAIL_PASSWORD

### 5. Create Required Directories

**Linux/Mac:**

```bash
mkdir -p chat_db medical_db data
```

**Windows:**

```cmd
mkdir chat_db
mkdir medical_db
mkdir data
```

### 6. Run the Application

#### Option A: Web Interface (Flask)

```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Run the app
python app.py
```

The application will be available at: **http://localhost:5000**

#### Option B: Command Line Interface

```bash
source venv/bin/activate
python main.py
```

## Notes

- The vector database will be automatically created from `data/medical_book.pdf` on first run
- Chat history is stored in `chat_db/medigenius_chats.db`
- The medical vector database is stored in `medical_db/`

## Troubleshooting

### Installation Issues

**If pip install fails:**

- Try installing packages in smaller groups
- Use `--no-cache-dir` flag: `pip install --no-cache-dir -r requirements.txt`
- On Windows, you may need Visual C++ Build Tools for some packages

**If torch installation is slow:**

- Use CPU-only version: `pip install torch --index-url https://download.pytorch.org/whl/cpu`

**For Windows-specific issues:** See `SETUP_WINDOWS.md`
