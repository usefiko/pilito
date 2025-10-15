# Web Knowledge - Website Content Analysis & Q&A Generation

A comprehensive Django app for crawling websites, extracting content, and generating AI-powered Q&A pairs for knowledge base creation.

## Features

### 🕷️ Website Crawling
- **Respectful Crawling**: Built-in delays and robots.txt compliance
- **Configurable Depth**: Control crawl depth and maximum pages
- **External Link Support**: Option to include external domains
- **Real-time Progress**: Live progress tracking with WebSocket updates
- **Error Handling**: Comprehensive error tracking and retry mechanisms

### 🧠 AI-Powered Content Processing
- **Content Extraction**: Clean text extraction from HTML
- **Content Summarization**: AI-generated page summaries
- **Q&A Generation**: Automatic question-answer pair creation using Gemini AI
- **Quality Scoring**: Confidence scores for generated content
- **Context Preservation**: Maintains source context for answers

### 📊 Analytics & Management
- **Progress Tracking**: Real-time crawl progress monitoring
- **Content Analytics**: Word counts, page statistics, and success rates
- **Search Functionality**: Full-text search across Q&A pairs
- **User Isolation**: Complete data separation between users
- **Admin Interface**: Comprehensive Django admin integration

## API Endpoints

### Website Management
```bash
# List user's websites
GET /api/v1/web-knowledge/websites/

# Create new website source
POST /api/v1/web-knowledge/websites/
{
    "name": "Company Website",
    "url": "https://example.com",
    "description": "Main company website",
    "max_pages": 50,
    "crawl_depth": 3,
    "include_external_links": false
}

# Start crawling a website
POST /api/v1/web-knowledge/websites/{id}/start_crawl/

# Get crawl status
GET /api/v1/web-knowledge/websites/{id}/crawl_status/

# Get website analytics
GET /api/v1/web-knowledge/websites/{id}/analytics/

# Recrawl website for updates
POST /api/v1/web-knowledge/websites/{id}/recrawl/
```

### Content & Pages
```bash
# List crawled pages
GET /api/v1/web-knowledge/pages/

# Get page details with Q&A pairs
GET /api/v1/web-knowledge/pages/{id}/

# Generate Q&A for specific page
POST /api/v1/web-knowledge/pages/{id}/generate_qa/
```

### Q&A Management
```bash
# List Q&A pairs
GET /api/v1/web-knowledge/qa-pairs/

# Search Q&A pairs
POST /api/v1/web-knowledge/search/
{
    "query": "business hours",
    "website_id": "uuid",
    "limit": 10,
    "include_context": true
}

# Toggle featured status
POST /api/v1/web-knowledge/qa-pairs/{id}/toggle_featured/
```

## Models

### WebsiteSource
- Main website configuration and crawl settings
- Tracks crawl progress and status
- Stores crawl statistics and error information

### WebsitePage
- Individual crawled pages with content
- Cleaned text and metadata extraction
- Processing status and error tracking

### QAPair
- AI-generated question-answer pairs
- Confidence scores and quality metrics
- View tracking and featured status

### CrawlJob
- Async crawl job tracking
- Progress monitoring and error handling
- Celery task integration

## Usage Examples

### Basic Website Setup
```python
from web_knowledge.models import WebsiteSource
from web_knowledge.tasks import crawl_website_task

# Create website source
website = WebsiteSource.objects.create(
    user=user,
    name="My Company Site",
    url="https://mycompany.com",
    max_pages=100,
    crawl_depth=3
)

# Start crawling
task = crawl_website_task.delay(str(website.id))
```

### Search Q&A Pairs
```python
from web_knowledge.models import QAPair
from django.db.models import Q

# Search for relevant Q&A pairs
qa_pairs = QAPair.objects.filter(
    page__website__user=user,
    generation_status='completed'
).filter(
    Q(question__icontains="hours") | 
    Q(answer__icontains="hours")
).order_by('-confidence_score')[:10]
```

### Generate Q&A for Content
```python
from web_knowledge.services.qa_generator import QAGenerator

generator = QAGenerator()
qa_pairs = generator.generate_qa_pairs(
    content="Your website content here...",
    page_title="About Us",
    max_pairs=5
)
```

## Configuration

### Required Settings
```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... other apps
    'web_knowledge',
]

# Add to Celery imports
CELERY_IMPORTS = [
    # ... other tasks
    'web_knowledge.tasks',
]

# Required packages
REQUIRED_PACKAGES = [
    'beautifulsoup4>=4.12.2',
    'lxml>=5.1.0',
    'aiohttp>=3.8.6',
    'google-generativeai>=0.3.2',
]
```

### URL Configuration
```python
# In main urls.py
path('api/v1/web-knowledge/', include('web_knowledge.urls')),
```

## Celery Tasks

### Async Processing
- `crawl_website_task`: Main website crawling
- `process_page_content_task`: Content extraction and cleaning
- `generate_qa_pairs_task`: AI-powered Q&A generation
- `cleanup_old_crawl_jobs`: Periodic cleanup maintenance

### Task Monitoring
All tasks provide progress callbacks and comprehensive error handling with automatic retries.

## Security & Performance

### Security Features
- User data isolation
- Input validation and sanitization
- Rate limiting for crawl requests
- Secure file handling

### Performance Optimizations
- Async task processing with Celery
- Database indexing for fast queries
- Connection pooling for HTTP requests
- Efficient content extraction algorithms

## Development

### Running Migrations
```bash
python manage.py makemigrations web_knowledge
python manage.py migrate
```

### Installing Dependencies
```bash
pip install -r requirements/base.txt
```

### Running Celery Workers
```bash
celery -A core worker --loglevel=info
celery -A core beat --loglevel=info
```

## Design Inspiration

This app implements the modern UI design patterns shown in the reference images:
- Clean, card-based layouts for website sources
- Progress indicators for crawl status
- Tabbed interfaces for knowledge sources, Q&A, and analytics
- Responsive design with proper spacing and typography
- Action buttons for crawl management and content generation

The API structure supports building frontend interfaces that match the provided design mockups, with proper data organization and real-time updates.
