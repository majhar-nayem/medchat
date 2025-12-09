# Docker Guide for MediGenius

## Quick Start

### Using Docker Compose (Recommended)

1. **Build and start the container:**
   ```bash
   docker-compose up -d
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f
   ```

3. **Stop the container:**
   ```bash
   docker-compose down
   ```

4. **Restart the container:**
   ```bash
   docker-compose restart
   ```

### Using Docker directly

1. **Build the image:**
   ```bash
   docker build -t medigenius .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name medigenius-app \
     -p 5000:5000 \
     -v $(pwd)/chat_db:/app/chat_db \
     -v $(pwd)/medical_db:/app/medical_db \
     -v $(pwd)/data:/app/data \
     --env-file .env \
     medigenius
   ```

3. **View logs:**
   ```bash
   docker logs -f medigenius-app
   ```

4. **Stop the container:**
   ```bash
   docker stop medigenius-app
   docker rm medigenius-app
   ```

## Environment Variables

Make sure your `.env` file contains:

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here  # Optional
```

The `.env` file is automatically loaded by docker-compose.

## Volumes

The following directories are mounted as volumes to persist data:

- `./chat_db` → `/app/chat_db` - Chat history database
- `./medical_db` → `/app/medical_db` - Vector database
- `./data` → `/app/data` - Medical PDF files

## Accessing the Application

Once running, access the application at:
- **Web Interface:** http://localhost:5000
- **Health Check:** http://localhost:5000/api/health

## Useful Commands

### View running containers
```bash
docker ps | grep medigenius
```

### View container logs
```bash
docker-compose logs -f medigenius
# or
docker logs -f medigenius-app
```

### Execute commands in container
```bash
docker exec -it medigenius-app bash
```

### Rebuild after code changes
```bash
docker-compose build --no-cache
docker-compose up -d
```

### View container resource usage
```bash
docker stats medigenius-app
```

### Stop and remove everything
```bash
docker-compose down
docker-compose down -v  # Also removes volumes
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs medigenius-app

# Check if port is already in use
lsof -i :5000
```

### Database issues
```bash
# Access the database inside container
docker exec -it medigenius-app sqlite3 /app/chat_db/medigenius_chats.db
```

### Permission issues
```bash
# Fix permissions on mounted volumes
sudo chown -R $USER:$USER chat_db medical_db data
```

### Rebuild from scratch
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Production Considerations

For production deployment, consider:

1. **Use environment variables instead of .env file:**
   ```yaml
   environment:
     - GROQ_API_KEY=${GROQ_API_KEY}
     - TAVILY_API_KEY=${TAVILY_API_KEY}
   ```

2. **Add resource limits:**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 4G
   ```

3. **Use a reverse proxy (nginx) for SSL/HTTPS**

4. **Set up proper logging and monitoring**

5. **Use Docker secrets for sensitive data**

## Health Check

The container includes a health check that monitors the application:
```bash
docker inspect medigenius-app | grep -A 10 Health
```

## Network

The application is accessible on:
- **Host:** localhost:5000
- **Container:** 0.0.0.0:5000

To access from other machines, use your host IP address instead of localhost.



