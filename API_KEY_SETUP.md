# API Key Setup Required

## The Issue
You're getting a 500 error because the `GROQ_API_KEY` is not set in your `.env` file.

## Solution

1. **Get a Groq API Key:**
   - Visit: https://console.groq.com/
   - Sign up or log in
   - Create a new API key

2. **Update your `.env` file:**
   ```bash
   cd /Users/majhar/medChat/MediGenius
   nano .env
   ```
   
   Replace `your_groq_api_key_here` with your actual API key:
   ```
   GROQ_API_KEY=gsk_your_actual_api_key_here
   ```

3. **Restart the application:**
   ```bash
   # Kill the current process
   lsof -ti:5000 | xargs kill
   
   # Restart
   source venv/bin/activate
   python app.py
   ```

## Optional: Tavily API Key
For web search fallback features, you can also add:
```
TAVILY_API_KEY=your_tavily_api_key_here
```
Get it from: https://tavily.com/

## After Setup
Once the API key is set, the `/api/chat` endpoint should work correctly!

