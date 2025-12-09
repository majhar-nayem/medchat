# 🪟 Windows Docker Build Optimization Guide

## Why Docker Builds Are Slow on Windows

Docker builds on Windows can take **hours** due to several factors:

1. **WSL2 Filesystem Performance** - Very slow I/O when accessing Windows files from WSL2
2. **Large Dependencies** - `torch` (~800MB), `transformers` (~500MB), `chromadb` (~200MB)
3. **Network Issues** - Downloading large packages over slow connections
4. **Docker Desktop Settings** - Resource limits (CPU, RAM, disk)
5. **Antivirus Interference** - Scanning files during build

## ⚡ Quick Fixes (Try These First)

### 1. **Optimize Docker Desktop Settings**

Open Docker Desktop → Settings → Resources:

- **CPU**: Set to maximum (e.g., 8 cores)
- **Memory**: Set to at least 8GB (16GB recommended)
- **Disk Image Size**: Increase to 100GB+ if needed
- **WSL Integration**: Enable WSL 2 backend

### 2. **Move Project to WSL2 Filesystem**

**CRITICAL**: Don't build from Windows filesystem! Move project to WSL2:

```bash
# In WSL2 terminal
cd ~
mkdir projects
cd projects
# Copy your project here or clone it
git clone <your-repo>
cd MediGenius
```

**Why?** Building from `/mnt/c/Users/...` is **10-100x slower** than WSL2 native filesystem.

### 3. **Exclude Project from Antivirus**

Add these paths to Windows Defender/Antivirus exclusions:
- `\\wsl$\Ubuntu\home\<user>\projects\MediGenius`
- `C:\Users\<user>\AppData\Local\Docker\`

### 4. **Use Optimized Dockerfile**

Use `Dockerfile.windows` instead of `Dockerfile`:

```bash
docker build -f Dockerfile.windows -t medigenius .
```

Or update `docker-compose.yml`:

```yaml
services:
  medigenius:
    build:
      context: .
      dockerfile: Dockerfile.windows
```

### 5. **Use Pre-built PyTorch Wheels**

The optimized Dockerfile uses CPU-only PyTorch wheels which are faster to install:

```dockerfile
RUN pip install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cpu
```

## 🚀 Advanced Optimizations

### Option 1: Multi-Stage Build (Already in Dockerfile.windows)

Reduces final image size and improves caching.

### Option 2: Build Cache

Use Docker BuildKit for better caching:

```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1

# Build with cache
docker build --cache-from medigenius:latest -t medigenius .
```

### Option 3: Use Docker Buildx

```bash
# Install buildx
docker buildx create --use

# Build with cache mount
docker buildx build --cache-from type=local,src=/tmp/.buildx-cache \
  --cache-to type=local,dest=/tmp/.buildx-cache \
  -t medigenius .
```

### Option 4: Pre-download Dependencies

Create a base image with dependencies pre-installed:

```dockerfile
# Dockerfile.base
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

Build base image once:
```bash
docker build -f Dockerfile.base -t medigenius-base .
```

Then use it in your main Dockerfile:
```dockerfile
FROM medigenius-base
COPY . /app
```

## 📊 Expected Build Times

| Setup | Time |
|-------|------|
| Windows filesystem (`/mnt/c/...`) | **2-4 hours** ❌ |
| WSL2 filesystem (`~/projects/...`) | **30-60 minutes** ⚠️ |
| WSL2 + Optimized Dockerfile | **15-30 minutes** ✅ |
| WSL2 + Optimized + Pre-built base | **5-10 minutes** ✅✅ |

## 🔧 Troubleshooting

### Build Hangs on "Installing torch"

**Solution**: Use CPU-only PyTorch (already in Dockerfile.windows):
```dockerfile
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### "Out of memory" errors

**Solution**: Increase Docker Desktop memory to 16GB+ and reduce parallel builds.

### Network timeouts

**Solution**: Use pip mirror or proxy:
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt \
    --index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### Still too slow?

**Alternative**: Build on Linux VM or use GitHub Actions for builds.

## ✅ Checklist

- [ ] Project is in WSL2 filesystem (`~/projects/...`)
- [ ] Docker Desktop has 8GB+ RAM allocated
- [ ] Using `Dockerfile.windows`
- [ ] Antivirus excludes project directory
- [ ] BuildKit enabled (`DOCKER_BUILDKIT=1`)
- [ ] Using `.dockerignore` to exclude unnecessary files

## 🎯 Quick Start (Recommended)

```bash
# 1. Move to WSL2 filesystem
cd ~/projects/MediGenius

# 2. Enable BuildKit
export DOCKER_BUILDKIT=1

# 3. Build with optimized Dockerfile
docker-compose build --file docker-compose.yml

# Or if using Dockerfile.windows:
docker build -f Dockerfile.windows -t medigenius .
```

## 📝 Notes

- First build will always be slowest (downloading dependencies)
- Subsequent builds are faster due to Docker layer caching
- Consider using a CI/CD service (GitHub Actions) for production builds
- For development, consider running locally without Docker

