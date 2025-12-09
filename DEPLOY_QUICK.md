# 🚀 Quick Free Hosting Guide (5-10 minutes)

## ✅ Fastest Free Options (Ranked by Speed)

| Platform | Setup Time | Free Tier | Best For |
|----------|------------|-----------|----------|
| **Render.com** | 5-10 min | ✅ Yes | Easiest, already configured |
| **Railway** | 5-10 min | ✅ Yes | Simple, auto-deploy |
| **Fly.io** | 10-15 min | ✅ Yes | Good performance |
| **PythonAnywhere** | 10-15 min | ✅ Yes | Python-focused |

---

## 🥇 Option 1: Render.com (RECOMMENDED - Fastest!)

**Time: 5-10 minutes | Already configured!**

### Steps:

1. **Sign up at [render.com](https://render.com)** (free account)

2. **Connect your GitHub repository:**
   - Click "New +" → "Web Service"
   - Connect your GitHub account
   - Select your `MediGenius` repository

3. **Configure deployment:**
   - **Name:** `medigenius` (or any name)
   - **Environment:** `Python 3`
   - **Build Command:** (leave empty - auto-detects)
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Plan:** Free

4. **Add Environment Variables:**
   Click "Environment" tab and add:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   EMAIL_USERNAME=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   FLASK_ENV=production
   PYTHONUNBUFFERED=1
   ```

5. **Deploy:**
   - Click "Create Web Service"
   - Wait 5-10 minutes for first build
   - Your app will be live at: `https://medigenius.onrender.com`

### ✅ Already configured!
- `render.yaml` is already in your repo
- Just connect GitHub and deploy!

---

## 🥈 Option 2: Railway (Very Easy)

**Time: 5-10 minutes**

### Steps:

1. **Sign up at [railway.app](https://railway.app)** (free with GitHub)

2. **Deploy:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `MediGenius` repository

3. **Railway auto-detects:**
   - Detects Python automatically
   - Installs dependencies from `requirements.txt`
   - Runs the app

4. **Add Environment Variables:**
   Go to "Variables" tab:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   EMAIL_USERNAME=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   PORT=5000
   ```

5. **Done!** Your app is live at: `https://your-app.railway.app`

### Railway automatically:
- Detects Flask app
- Uses `Procfile` if present
- Or runs `python app.py` by default

---

## 🥉 Option 3: Fly.io (Good Performance)

**Time: 10-15 minutes**

### Steps:

1. **Install Fly CLI:**
   ```bash
   # Windows (PowerShell)
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   
   # Mac/Linux
   curl -L https://fly.io/install.sh | sh
   ```

2. **Sign up:**
   ```bash
   fly auth signup
   ```

3. **Create app:**
   ```bash
   fly launch
   ```
   - Follow prompts
   - Select region closest to you
   - Don't deploy yet (we'll configure first)

4. **Create `fly.toml`:**
   ```toml
   app = "medigenius"
   primary_region = "iad"
   
   [build]
   
   [http_service]
     internal_port = 5000
     force_https = true
     auto_stop_machines = true
     auto_start_machines = true
     min_machines_running = 0
     processes = ["app"]
   
   [[services]]
     protocol = "tcp"
     internal_port = 5000
   ```

5. **Set secrets:**
   ```bash
   fly secrets set GROQ_API_KEY=your_key_here
   fly secrets set EMAIL_USERNAME=your_email@gmail.com
   fly secrets set EMAIL_PASSWORD=your_app_password
   ```

6. **Deploy:**
   ```bash
   fly deploy
   ```

7. **Done!** Your app: `https://medigenius.fly.dev`

---

## 📝 Required Changes for Production

### 1. Add gunicorn to requirements.txt

Add this line to `requirements.txt`:
```
gunicorn
```

### 2. Update app.py (if needed)

Make sure the app can run with gunicorn. Your current setup should work, but ensure:

```python
# At the bottom of app.py
if __name__ == '__main__':
    initialize_system()
    # For production, gunicorn will handle this
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
```

### 3. Create Procfile (for Railway/Heroku)

Create a file named `Procfile` (no extension):
```
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

---

## ⚡ Quickest Setup Summary

**Fastest: Render.com (5 minutes)**
1. Sign up → Connect GitHub → Deploy
2. Add environment variables
3. Done!

**Why Render.com?**
- ✅ Already configured (`render.yaml` exists)
- ✅ Free tier with 750 hours/month
- ✅ Auto-deploy from GitHub
- ✅ Simple interface
- ✅ No credit card required

---

## 🔧 Environment Variables Needed

All platforms need these in their environment settings:

```
GROQ_API_KEY=your_groq_api_key_here
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
FLASK_ENV=production
PYTHONUNBUFFERED=1
```

**Note:** For Gmail, you need an [App Password](https://support.google.com/accounts/answer/185833), not your regular password.

---

## ⚠️ Important Notes

### Free Tier Limitations:

1. **Render.com:**
   - Spins down after 15 min of inactivity
   - First request after spin-down takes ~30 seconds
   - 750 hours/month free

2. **Railway:**
   - $5 credit/month (usually enough for small apps)
   - Auto-sleeps after inactivity

3. **Fly.io:**
   - 3 shared VMs free
   - Auto-stops when idle

### For Production Use:
- Consider paid plans for always-on service
- Or use a cron job to ping your app every 10 minutes (keeps it awake)

---

## 🎯 Recommended: Render.com

**Why?**
- Fastest setup (already configured)
- No credit card required
- Simple interface
- Good free tier

**Steps:**
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Select your repo
5. Use these settings:
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Plan:** Free
6. Add environment variables
7. Deploy!

**Time: 5-10 minutes total!**

---

## 🆘 Troubleshooting

### Build fails?
- Check that `gunicorn` is in `requirements.txt`
- Ensure all dependencies are listed
- Check build logs for errors

### App crashes on startup?
- Check environment variables are set
- Verify `GROQ_API_KEY` is correct
- Check logs for specific errors

### Slow first request?
- Normal on free tier (app spins down)
- Consider paid plan for always-on

---

## ✅ Checklist Before Deploying

- [ ] `gunicorn` added to `requirements.txt`
- [ ] `Procfile` created (for Railway)
- [ ] Environment variables ready
- [ ] Gmail App Password created (for email)
- [ ] Groq API key ready
- [ ] GitHub repo is public or connected

---

**Ready? Start with Render.com - it's the fastest!** 🚀

