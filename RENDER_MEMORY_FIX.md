# 🔧 Fix Render.com Memory Error (512MB Limit)

## Error: "Out of memory (used over 512Mi)"

Your app is too memory-intensive for Render's **free tier (512MB)**. The ML models (torch, transformers, chromadb) require 1-2GB+ RAM.

## ✅ Solutions (Ranked by Ease)

### Solution 1: Upgrade to Paid Tier (Easiest)

**Render Starter Plan ($7/month):**
- 512MB → **2GB RAM**
- Enough for your ML app
- Always-on (no spin-down)

**Steps:**
1. Render Dashboard → Your Service → Settings
2. Change plan from **Free** to **Starter ($7/month)**
3. Redeploy

### Solution 2: Use Railway Instead (Free Tier with More Memory)

**Railway free tier:**
- $5 credit/month (usually enough)
- More flexible memory limits
- Better for ML apps

**Steps:**
1. Go to [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Select your repo
4. Railway auto-detects and deploys
5. Add environment variables

### Solution 3: Lazy Load Models (Code Changes)

Make models load only when needed, not at startup.

**Update `app.py`:**

```python
# Change from loading at startup to lazy loading
workflow_app = None

def get_workflow():
    """Lazy load workflow only when needed"""
    global workflow_app
    if workflow_app is None:
        print("Loading workflow (first request)...")
        workflow_app = create_workflow()
    return workflow_app

# In your chat route, use:
workflow = get_workflow()  # Instead of workflow_app
```

### Solution 4: Use CPU-Only PyTorch (Smaller Memory)

Already in requirements.txt, but ensure it's used:

```python
# In tools/vector_store.py or wherever models load
import os
os.environ['TORCH_DEVICE'] = 'cpu'  # Force CPU
```

### Solution 5: Disable RAG on Free Tier (Lightweight Mode)

Skip ChromaDB initialization on free tier:

```python
def initialize_system():
    # Skip heavy initialization on free tier
    if os.environ.get('RENDER', '').lower() == 'true':
        print("Running in lightweight mode (free tier)")
        init_db()
        init_auth_db()
        # Skip vector store initialization
        return
    
    # Full initialization for paid tiers
    # ... rest of code
```

## 🎯 Recommended: Upgrade to Starter Plan

**Why?**
- ✅ Easiest solution (no code changes)
- ✅ Only $7/month
- ✅ 2GB RAM (enough for your app)
- ✅ Always-on service
- ✅ Better performance

**Cost comparison:**
- Free tier: $0 but crashes
- Starter plan: $7/month, works perfectly
- Your time debugging: Worth more than $7

## 🔧 Quick Code Fix (If You Want to Stay Free)

I'll create a memory-optimized version that lazy loads everything.

## 📊 Memory Usage Breakdown

| Component | Memory |
|-----------|--------|
| Python + Flask | ~100MB |
| torch (CPU) | ~200-300MB |
| transformers | ~200-300MB |
| chromadb | ~100-200MB |
| sentence-transformers | ~100MB |
| **Total** | **~700-1000MB** |

**Free tier:** 512MB ❌  
**Starter plan:** 2048MB ✅

## ⚡ Immediate Action

**Option A (Recommended):**
1. Render Dashboard → Settings
2. Upgrade to **Starter Plan ($7/month)**
3. Redeploy

**Option B (Free Alternative):**
1. Switch to Railway (better free tier)
2. Or use the lazy loading code I'll provide

---

**I'll create an optimized version with lazy loading next!**

