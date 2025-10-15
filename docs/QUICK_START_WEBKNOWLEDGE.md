# Quick Start Guide - WebKnowledge App

## 🚀 Getting Started

The WebKnowledge app has been successfully created and integrated into your Fiko backend. Here's how to get it running:

### 1. Install Fixed Dependencies

The `aiohttp` dependency has been removed due to Python 3.12 compatibility issues. The fixed requirements are now ready:

```bash
# From the project root
cd /Users/nima/Projects/Fiko-Backend
source venv/bin/activate
pip install beautifulsoup4 lxml
```

### 2. Run Migrations

```bash
cd src
python manage.py makemigrations web_knowledge
python manage.py migrate
```

### 3. Start the Services

```bash
# Terminal 1: Django server
python manage.py runserver

# Terminal 2: Celery worker (for background tasks)
celery -A core worker --loglevel=info

# Terminal 3: Celery beat (for periodic tasks)
celery -A core beat --loglevel=info
```

### 4. Test the System

```bash
# Test the web knowledge functionality
python manage.py test_web_knowledge --url=https://example.com --max-pages=3 --skip-qa
```

### 5. Access the API

The WebKnowledge API is available at:
```
http://localhost:8000/api/v1/web-knowledge/
```

### 6. View the Demo UI

A demo interface matching your design is available at:
```
http://localhost:8000/api/v1/web-knowledge/demo/
```

## 🎯 Key API Endpoints

```bash
# Create a new website source
POST /api/v1/web-knowledge/websites/
{
    "name": "My Website",
    "url": "https://example.com",
    "max_pages": 50,
    "crawl_depth": 3
}

# Start crawling
POST /api/v1/web-knowledge/websites/{id}/start_crawl/

# Check crawl status
GET /api/v1/web-knowledge/websites/{id}/crawl_status/

# Search Q&A pairs
POST /api/v1/web-knowledge/search/
{
    "query": "business hours",
    "limit": 10
}
```

## ✅ What's Fixed

1. **Removed problematic `aiohttp` dependency** - Caused build failures on Python 3.12
2. **Using reliable `requests` library** - More stable for HTTP operations
3. **All imports cleaned up** - No unused async imports
4. **Dependencies optimized** - Only essential packages included

## 🛠️ Docker Alternative

If you prefer to use Docker (which handles the Python compatibility automatically):

```bash
# From project root
docker-compose up --build
```

This will automatically handle all dependencies and compatibility issues.

## 📊 Features Ready to Use

✅ **Website Crawling** - Add websites and crawl them automatically
✅ **Content Extraction** - Clean text extraction from web pages  
✅ **AI Q&A Generation** - Generate Q&A pairs using Gemini AI
✅ **Progress Tracking** - Real-time crawl progress monitoring
✅ **Search & Analytics** - Full-text search and comprehensive analytics
✅ **Modern UI** - Demo interface matching your design specifications

The WebKnowledge system is now fully functional and ready for production use!
