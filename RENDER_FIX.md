# 🔧 Fix Render.com Deployment Error

## Error: "destination path '/opt/render/project/src' already exists"

This error occurs when Render's build cache has leftover files from a previous deployment.

## ✅ Quick Fixes (Try in Order)

### Solution 1: Clear Build Cache (Easiest)

1. Go to your Render dashboard
2. Click on your service
3. Go to **Settings** tab
4. Scroll down to **Build & Deploy**
5. Click **Clear build cache**
6. Click **Manual Deploy** → **Deploy latest commit**

### Solution 2: Update render.yaml

Update your `render.yaml` to explicitly clean the directory:

```yaml
services:
  - type: web
    name: medi-genius
    env: python
    buildCommand: |
      rm -rf /opt/render/project/src/* || true
      pip install -r requirements.txt
    startCommand: gunicorn app:app --bind 0.0.0.0:$PORT
    plan: free
```

### Solution 3: Add Clean Build Command

In Render dashboard:
1. Go to your service → **Settings**
2. Under **Build Command**, add:
   ```bash
   rm -rf /opt/render/project/src/* 2>/dev/null || true && pip install -r requirements.txt
   ```
3. Under **Start Command**, use:
   ```bash
   gunicorn app:app --bind 0.0.0.0:$PORT
   ```

### Solution 4: Delete and Recreate Service

If above don't work:
1. Delete the current service in Render
2. Create a new web service
3. Connect your GitHub repo again
4. Use these settings:
   - **Build Command:** (leave empty or use `pip install -r requirements.txt`)
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`

## 🔍 Alternative: Use Manual Build Command

In Render dashboard, set **Build Command** to:

```bash
cd /opt/render/project/src && rm -rf * .* 2>/dev/null || true && git clone $RENDER_GIT_REPO . && pip install -r requirements.txt
```

## 📝 Recommended render.yaml (Updated)

```yaml
services:
  - type: web
    name: medi-genius
    env: python
    buildCommand: |
      if [ -d "/opt/render/project/src" ]; then
        rm -rf /opt/render/project/src/*
      fi
      pip install --upgrade pip
      pip install -r requirements.txt
    startCommand: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
    plan: free
    envVars:
      - key: PYTHONUNBUFFERED
        value: 1
      - key: FLASK_ENV
        value: production
```

## ⚡ Quick Steps (Most Likely to Work)

1. **In Render Dashboard:**
   - Go to your service
   - Click **Settings**
   - Scroll to **Build & Deploy**
   - Click **Clear build cache**
   - Click **Save Changes**

2. **Manual Deploy:**
   - Click **Manual Deploy** button
   - Select **Deploy latest commit**
   - Wait for build to complete

3. **If still fails:**
   - Delete the service
   - Create new web service
   - Connect repo
   - Use start command: `gunicorn app:app --bind 0.0.0.0:$PORT`

## 🎯 Most Common Fix

**Just clear the build cache and redeploy!**

1. Render Dashboard → Your Service → Settings
2. **Clear build cache** button
3. **Manual Deploy** → **Deploy latest commit**

This fixes 90% of these errors!

