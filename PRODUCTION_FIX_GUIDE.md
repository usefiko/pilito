# Production Server PostgreSQL Fix - Manual Commands

## Step 1: Connect to Server
```bash
ssh root@185.164.72.165
# Password: 9188945776poST?
```

## Step 2: Find your project directory
```bash
# Check current location
pwd

# Common locations:
cd /root/pilito  # or
cd /opt/pilito   # or
cd /app/pilito   # or wherever docker-compose.yml is located

# Verify you're in the right place
ls -la docker-compose.yml
```

## Step 3: Check current container status
```bash
docker ps -a
docker-compose ps
```

## Step 4: Stop all containers
```bash
docker-compose down
docker-compose down --remove-orphans
```

## Step 5: Start PostgreSQL first
```bash
# Start only the database
docker-compose up -d db

# Wait 15 seconds for it to initialize
sleep 15

# Check if it's running
docker ps | grep postgres
docker logs postgres_db --tail 50
```

## Step 6: Start Redis
```bash
docker-compose up -d redis
sleep 5
```

## Step 7: Start Django application
```bash
docker-compose up -d web

# Wait for it to start
sleep 10

# Check logs
docker logs django_app --tail 30
```

## Step 8: Run migrations
```bash
docker exec -it django_app python manage.py migrate
```

## Step 9: Start remaining services
```bash
# Start Celery workers
docker-compose up -d celery_worker celery_ai celery_beat

# Start monitoring
docker-compose up -d prometheus grafana redis_exporter postgres_exporter
```

## Step 10: Verify everything is running
```bash
docker-compose ps
docker ps

# Test the application
curl http://localhost:8000/health/
```

## Troubleshooting Commands

### If database still won't start:
```bash
# Check if there's a volume issue
docker volume ls | grep postgres

# Check database logs in detail
docker logs postgres_db --tail 100

# Try removing and recreating the database container
docker-compose stop db
docker-compose rm -f db
docker-compose up -d db
```

### If Django can't connect to DB:
```bash
# Check network connectivity
docker exec -it django_app ping -c 3 db
docker exec -it django_app nc -zv db 5432

# Check environment variables
docker exec -it django_app env | grep POSTGRES
```

### View real-time logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f db
```

## Quick Restart Script (One Command)
```bash
docker-compose down && \
docker-compose up -d db && sleep 15 && \
docker-compose up -d redis && sleep 5 && \
docker-compose up -d web && sleep 10 && \
docker exec django_app python manage.py migrate && \
docker-compose up -d celery_worker celery_ai celery_beat prometheus grafana redis_exporter postgres_exporter && \
docker-compose ps
```

## Emergency Full Reset
```bash
# WARNING: This will stop everything and remove volumes
docker-compose down -v
docker-compose up -d --build
docker exec -it django_app python manage.py migrate
```

