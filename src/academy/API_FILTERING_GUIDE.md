# Academy API Filtering and Search Guide

This guide explains all the filtering and search capabilities available in the Academy APIs, including thumbnail support for all video content.

## Available APIs with Filtering

### 1. Video List API (`/api/v1/academy/videos/`)

**Endpoint:** `GET /api/v1/academy/videos/`

**Supported Query Parameters:**

- `lang` or `language`: Filter by language (`persian`, `arabic`, `english`, `turkish`)
- `status`: Filter by progress status (`not_started`, `in_progress`, `complete`)
- `tag`: Filter by video tag (case-insensitive)
- `search`: Search in titles and descriptions across all languages
- `ordering`: Sort by fields (`created_at`, `-created_at`, `video_minutes`, `-video_minutes`, `updated_at`, `-updated_at`)
- `page`: Page number for pagination
- `page_size`: Number of items per page (max 500)

**Example Requests:**

```bash
# Get all videos
GET /api/v1/academy/videos/

# Get videos in Persian language
GET /api/v1/academy/videos/?lang=persian

# Get completed videos
GET /api/v1/academy/videos/?status=complete

# Get videos with specific tag
GET /api/v1/academy/videos/?tag=programming

# Search in video titles and descriptions
GET /api/v1/academy/videos/?search=python

# Combined filtering
GET /api/v1/academy/videos/?lang=english&status=in_progress&search=javascript&ordering=-created_at

# Get not started videos with pagination
GET /api/v1/academy/videos/?status=not_started&page=2&page_size=20
```

### 2. Videos by Status API (`/api/v1/academy/videos/by-status/`)

**Endpoint:** `GET /api/v1/academy/videos/by-status/`

**Required Parameters:**
- `status`: Progress status (`not_started`, `in_progress`, `complete`)

**Optional Parameters:**
- `lang` or `language`: Language filter (defaults to `persian`)
- `search`: Search in titles and descriptions
- `tag`: Filter by video tag
- `page`: Page number for pagination

**Example Requests:**

```bash
# Get all not started videos
GET /api/v1/academy/videos/by-status/?status=not_started

# Get completed videos in English
GET /api/v1/academy/videos/by-status/?status=complete&lang=english

# Search for in-progress videos containing "react"
GET /api/v1/academy/videos/by-status/?status=in_progress&search=react

# Get not started programming videos
GET /api/v1/academy/videos/by-status/?status=not_started&tag=programming&page=1
```

### 3. User Progress List API (`/api/v1/academy/progress/`)

**Endpoint:** `GET /api/v1/academy/progress/`

**Supported Query Parameters:**

- `lang` or `language`: Filter by language (`persian`, `arabic`, `english`, `turkish`)
- `status`: Filter by progress status (`not_started`, `in_progress`, `complete`)
- `tag`: Filter by video tag (case-insensitive)
- `search`: Search in video titles, descriptions, and tags
- `ordering`: Sort by fields (`updated_at`, `-updated_at`, `progress_percentage`, `-progress_percentage`, `last_watched_at`, `-last_watched_at`, `created_at`, `-created_at`)
- `page`: Page number for pagination
- `page_size`: Number of items per page

**Example Requests:**

```bash
# Get all user progress
GET /api/v1/academy/progress/

# Get progress for Persian videos
GET /api/v1/academy/progress/?lang=persian

# Get completed video progress
GET /api/v1/academy/progress/?status=complete

# Search in video information
GET /api/v1/academy/progress/?search=python

# Get progress for specific tag
GET /api/v1/academy/progress/?tag=frontend

# Combined filtering with ordering
GET /api/v1/academy/progress/?status=in_progress&lang=english&ordering=-progress_percentage

# Recently updated progress
GET /api/v1/academy/progress/?ordering=-updated_at&page_size=5
```

### 4. User Statistics API (`/api/v1/academy/statistics/`)

**Endpoint:** `GET /api/v1/academy/statistics/`

**Supported Query Parameters:**

- `lang` or `language`: Filter statistics by language
- `tag`: Filter statistics by video tag

**Example Requests:**

```bash
# Get overall statistics
GET /api/v1/academy/statistics/

# Get statistics for Persian videos
GET /api/v1/academy/statistics/?lang=persian

# Get statistics for programming videos
GET /api/v1/academy/statistics/?tag=programming

# Get statistics for English programming videos
GET /api/v1/academy/statistics/?lang=english&tag=programming
```

**Response includes:**
- `total_videos`: Total number of videos
- `completed_videos`: Number of completed videos
- `in_progress_videos`: Number of videos in progress
- `not_started_videos`: Number of not started videos
- `total_hours_completed`: Total hours of completed videos
- `total_hours_available`: Total hours of all videos
- `completion_percentage`: Percentage of videos completed
- `hours_completion_percentage`: Percentage of hours completed

## Search Functionality

The search functionality works across all language fields:

- Default title and description
- Persian title and description (`title_persian`, `description_persian`)
- Arabic title and description (`title_arabic`, `description_arabic`)
- English title and description (`title_english`, `description_english`)
- Turkish title and description (`title_turkish`, `description_turkish`)
- Video tags

### Search Examples:

```bash
# Search for "Python" in any language
GET /api/v1/academy/videos/?search=Python

# Search in progress list
GET /api/v1/academy/progress/?search=JavaScript

# Combined search and filter
GET /api/v1/academy/videos/?search=programming&status=not_started&lang=english
```

## Ordering/Sorting

### Video List Ordering Options:
- `created_at`: Oldest first
- `-created_at`: Newest first (default)
- `video_minutes`: Shortest first
- `-video_minutes`: Longest first
- `updated_at`: Least recently updated first
- `-updated_at`: Most recently updated first

### Progress List Ordering Options:
- `updated_at`: Least recently updated first
- `-updated_at`: Most recently updated first (default)
- `progress_percentage`: Lowest progress first
- `-progress_percentage`: Highest progress first
- `last_watched_at`: Least recently watched first
- `-last_watched_at`: Most recently watched first
- `created_at`: Oldest first
- `-created_at`: Newest first

## Pagination

All list endpoints support pagination:

- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 10, max: 500)

**Pagination Response Format:**
```json
{
  "count": 150,
  "next": "http://api.example.com/academy/videos/?page=3",
  "previous": "http://api.example.com/academy/videos/?page=1",
  "results": [...]
}
```

## Status Values

The following status values are available for filtering:

- `not_started`: User hasn't started watching the video (progress = 0%)
- `in_progress`: User has started but not completed the video (0% < progress < 100%)
- `complete`: User has completed the video (progress = 100%)

## Language Codes

The following language codes are supported:

- `persian`: Persian (فارسی)
- `arabic`: Arabic (العربية)
- `english`: English
- `turkish`: Turkish (Türkçe)

## Example Use Cases

### 1. Dashboard - Recent Activity
```bash
GET /api/v1/academy/progress/?ordering=-updated_at&page_size=10
```

### 2. Continue Learning Section
```bash
GET /api/v1/academy/videos/by-status/?status=in_progress&lang=persian
```

### 3. Recommended Videos
```bash
GET /api/v1/academy/videos/by-status/?status=not_started&tag=beginner&lang=english
```

### 4. Search Learning Materials
```bash
GET /api/v1/academy/videos/?search=react hooks&lang=english&ordering=-created_at
```

### 5. Progress Analytics
```bash
GET /api/v1/academy/statistics/?lang=persian
GET /api/v1/academy/progress/?status=complete&lang=persian&ordering=-progress_percentage
```

### 6. Course Completion Tracking
```bash
GET /api/v1/academy/videos/by-status/?status=complete&tag=javascript&lang=english
GET /api/v1/academy/statistics/?tag=javascript&lang=english
```

## Thumbnail Support

All Academy APIs now include thumbnail support with multi-language capabilities:

### **Thumbnail Fields in API Responses:**

- `localized_thumbnail_url`: Returns the thumbnail URL for the requested language
- Supports the same language codes as video content: `persian`, `arabic`, `english`, `turkish`
- Falls back to default thumbnail if language-specific thumbnail is not available
- Returns `null` if no thumbnail is available

### **Example API Responses with Thumbnails:**

**Video List Response:**
```json
{
  "count": 25,
  "results": [
    {
      "id": 1,
      "localized_title": "Introduction to Python Programming",
      "localized_description": "Learn the basics of Python programming...",
      "localized_video_file_url": "https://your-storage.com/videos/python-intro.mp4",
      "localized_thumbnail_url": "https://your-storage.com/thumbnails/python-intro.jpg",
      "tag": "programming",
      "video_minutes": 150,
      "video_seconds": 0,
      "duration_formatted": "150m 0s",
      "available_languages": ["english", "persian"],
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-01-15T10:00:00Z",
      "user_progress": {
        "language": "english",
        "status": "in_progress",
        "progress_percentage": "45.50",
        "last_watched_at": "2025-01-15T15:30:00Z"
      }
    }
  ]
}
```

**User Progress Response:**
```json
{
  "results": [
    {
      "id": 1,
      "user": 123,
      "video": 1,
      "language": "persian",
      "video_title": "مقدمه‌ای بر برنامه‌نویسی پایتون",
      "video_thumbnail_url": "https://your-storage.com/thumbnails/persian/python-intro.jpg",
      "video_tag": "programming",
      "video_minutes": 150,
      "video_seconds": 0,
      "duration_formatted": "150m 0s",
      "status": "complete",
      "progress_percentage": "100.00",
      "last_watched_at": "2025-01-15T16:00:00Z"
    }
  ]
}
```

### **Thumbnail Management:**

**Admin Panel Features:**
- Upload separate thumbnails for each language
- Default thumbnail as fallback
- Automatic language detection for thumbnail selection
- Support for JPG, PNG, and WEBP formats

**Storage Paths:**
- Default: `thumbnails/`
- Persian: `thumbnails/persian/`
- Arabic: `thumbnails/arabic/`
- English: `thumbnails/english/`
- Turkish: `thumbnails/turkish/`

## Notes

1. **Language Filtering**: When filtering by language, only videos that have content (title, video file, or thumbnail) in that language are returned.

2. **Progress Status**: The system automatically calculates status based on progress percentage:
   - 0% = `not_started`
   - 1-99% = `in_progress`
   - 100% = `complete`

3. **Case-Insensitive**: All text searches and tag filters are case-insensitive.

4. **Performance**: The APIs use `select_related` for optimal database queries and support pagination for large datasets.

5. **Authentication**: All endpoints require authentication using JWT tokens.

6. **Thumbnails**: All video APIs automatically include appropriate thumbnails based on the requested language. Thumbnails are stored using the same cloud storage system as videos (S3-compatible).