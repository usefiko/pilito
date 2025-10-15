# Academy App


The Academy app is a Django application that provides a video library system with user progress tracking capabilities.

## Features

### Video Library
- Store course videos with metadata:
  - Title
  - Description
  - Tag/Category
  - Video file (upload actual video files)
  - Video duration (in hours)

### User Progress Tracking
- Track viewing status for each user and video:
  - **Not Started**: User hasn't begun watching the video (0% progress)
  - **In Progress**: User has started but not completed the video (1-99% progress)
  - **Complete**: User has finished watching the video (100% progress)

### Additional Features
- Progress percentage tracking (0-100%)
- Last watched timestamp
- User statistics and analytics
- Admin interface for managing videos and progress

## Models

### Video
- `title`: CharField - Title of the video
- `description`: TextField - Description of the video content
- `tag`: CharField - Tag or category for the video
- `video_file`: FileField - Uploaded video file (MP4, AVI, MOV, WMV, FLV, WebM, MKV)
- `video_minutes`: PositiveIntegerField - Duration in minutes
- `video_seconds`: PositiveIntegerField - Duration in seconds (0-59)
- `created_at`: DateTimeField - Creation timestamp
- `updated_at`: DateTimeField - Last update timestamp

### UserVideoProgress
- `user`: ForeignKey - Reference to User model
- `video`: ForeignKey - Reference to Video model
- `status`: CharField - Current viewing status (not_started, in_progress, complete)
- `progress_percentage`: DecimalField - Percentage watched (0-100)
- `last_watched_at`: DateTimeField - Last viewing timestamp
- `created_at`: DateTimeField - Creation timestamp
- `updated_at`: DateTimeField - Last update timestamp

## API Endpoints

### Video Endpoints
- `GET /api/v1/academy/videos/` - List all videos with user progress
- `GET /api/v1/academy/videos/{id}/` - Get specific video details with progress
- `GET /api/v1/academy/videos/?tag={tag}` - Filter videos by tag

### Video File Endpoints
- `GET /api/v1/academy/videos/{id}/stream/` - Stream video file for playback
- `GET /api/v1/academy/videos/{id}/download/` - Download video file

### Progress Endpoints
- `GET /api/v1/academy/progress/` - Get user's progress for all videos
- `GET /api/v1/academy/videos/{id}/progress/` - Get user's progress for specific video
- `POST /api/v1/academy/videos/{id}/update-progress/` - Update viewing progress

### Statistics
- `GET /api/v1/academy/statistics/` - Get user's learning statistics

## Usage

### Setup
1. Add 'academy' to INSTALLED_APPS in settings
2. Run migrations: `python manage.py migrate`
3. (Optional) Populate with sample data: `python manage.py populate_videos`

### Admin Interface
Access the Django admin to manage videos and view user progress:
- Videos: Add, edit, delete course videos
- User Video Progress: View and manage user viewing progress

### API Usage Examples

#### Get all videos with progress
```bash
GET /api/v1/academy/videos/
Authorization: Bearer <token>
```

#### Stream video file
```bash
GET /api/v1/academy/videos/1/stream/
Authorization: Bearer <token>
```

#### Download video file
```bash
GET /api/v1/academy/videos/1/download/
Authorization: Bearer <token>
```

#### Update video progress
```bash
POST /api/v1/academy/videos/1/update-progress/
Authorization: Bearer <token>
Content-Type: application/json

{
    "progress_percentage": 65.5
}
```

#### Get user statistics
```bash
GET /api/v1/academy/statistics/
Authorization: Bearer <token>
```

## Auto-Status Updates
The system automatically updates the viewing status based on progress percentage:
- 0% → "not_started"
- 1-99% → "in_progress"  
- 100% → "complete"

## File Storage
- Video files are stored in the `media/videos/` directory
- Unique filenames are generated to prevent conflicts
- Supported video formats: MP4, AVI, MOV, WMV, FLV, WebM, MKV
- File validation ensures only valid video files are uploaded

## Security
- All endpoints require authentication
- Users can only view/update their own progress
- Video streaming and downloads require authentication
- Admin interface provides oversight capabilities

## Response Format

### Video API Response
```json
{
    "id": 1,
    "title": "Basics of Angular",
    "description": "Introductory course for Angular and framework basics",
    "tag": "Programming",
    "video_file": "/media/videos/abc123def456.mp4",
    "video_file_url": "http://localhost:8000/media/videos/abc123def456.mp4",
    "video_minutes": 480,
    "video_seconds": 0,
    "duration_formatted": "480m 0s",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "user_progress": {
        "status": "in_progress",
        "progress_percentage": "45.50",
        "last_watched_at": "2024-01-01T12:30:00Z"
    }
}
```