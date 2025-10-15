# AI Prompts API Enhancement

## Overview

Created a comprehensive API system for managing AI prompts with OneToOneField relationship to User model, automatic creation, and full CRUD operations.

## Changes Made

### 1. Model Changes

**File:** `src/settings/models.py`

```python
class AIPrompts(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ai_prompts')
    manual_prompt = models.TextField(max_length=5000, null=True, blank=True)
    auto_prompt = models.TextField(max_length=5000, null=True, blank=True)  # Added
    knowledge_source = models.JSONField(null=True, blank=True)
    product_service = models.JSONField(null=True, blank=True)
    question_answer = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @classmethod
    def get_or_create_for_user(cls, user):
        """Get or create AIPrompts for a user with default prompts"""
        # Returns (prompts, created) tuple
```

**Key Changes:**
- ✅ Changed from `ForeignKey` to `OneToOneField` 
- ✅ Added `related_name='ai_prompts'` 
- ✅ Added `auto_prompt` field
- ✅ Added convenience method `get_or_create_for_user()`

### 2. Auto-Creation via Signals

**File:** `src/settings/signals.py` (New)

```python
@receiver(post_save, sender=User)
def create_ai_prompts_for_user(sender, instance, created, **kwargs):
    """Automatically create AIPrompts when a new User is created"""
    if created:
        prompts, prompts_created = AIPrompts.get_or_create_for_user(instance)
```

**Connected in:** `src/settings/apps.py`

### 3. Serializers

**File:** `src/settings/serializers.py`

Created three serializers:

```python
# Full serializer with all fields
class AIPromptsSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField(read_only=True)

# Simple serializer for manual_prompt only  
class AIPromptsManualPromptSerializer(serializers.ModelSerializer):
    fields = ['manual_prompt']

# Create/update serializer (without user field)
class AIPromptsCreateUpdateSerializer(serializers.ModelSerializer):
    fields = ['manual_prompt', 'auto_prompt', 'knowledge_source', ...]
```

### 4. API Views

**File:** `src/settings/views.py`

#### `AIPromptsAPIView`
- **GET** `/api/v1/settings/ai-prompts/` - Get all user's AI prompts
- **PATCH** `/api/v1/settings/ai-prompts/` - Update user's AI prompts

#### `AIPromptsManualPromptAPIView`
- **GET** `/api/v1/settings/ai-prompts/manual-prompt/` - Get only manual_prompt
- **PATCH** `/api/v1/settings/ai-prompts/manual-prompt/` - Update only manual_prompt

**Features:**
- ✅ Auto-creates AIPrompts if user doesn't have them
- ✅ Returns default prompts for new users
- ✅ Full error handling and logging
- ✅ Swagger documentation
- ✅ Authentication required

### 5. URL Configuration

**File:** `src/settings/urls.py`

```python
urlpatterns = [
    # AI & Prompts
    path("ai-prompts/", AIPromptsAPIView.as_view(), name="ai-prompts"),
    path("ai-prompts/manual-prompt/", AIPromptsManualPromptAPIView.as_view(), name="ai-prompts-manual"),
]
```

## API Endpoints

### Get User's AI Prompts

```http
GET /api/v1/settings/ai-prompts/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "user": 1,
    "user_name": "John Doe",
    "manual_prompt": "You are a helpful customer service assistant...",
    "auto_prompt": "You are an AI customer service representative...",
    "knowledge_source": null,
    "product_service": null,
    "question_answer": null,
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  },
  "created": false
}
```

### Get Manual Prompt Only

```http
GET /api/v1/settings/ai-prompts/manual-prompt/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "manual_prompt": "You are a helpful customer service assistant. Answer customer questions professionally and helpfully in the same language they write. Keep responses concise but informative.",
  "created": false
}
```

### Update Manual Prompt

```http
PATCH /api/v1/settings/ai-prompts/manual-prompt/
Authorization: Bearer <token>
Content-Type: application/json

{
  "manual_prompt": "Updated prompt text here..."
}
```

**Response:**
```json
{
  "success": true,
  "manual_prompt": "Updated prompt text here...",
  "message": "Manual prompt updated successfully"
}
```

### Update All AI Prompts

```http
PATCH /api/v1/settings/ai-prompts/
Authorization: Bearer <token>
Content-Type: application/json

{
  "manual_prompt": "Updated manual prompt...",
  "auto_prompt": "Updated auto prompt...",
  "knowledge_source": {"key": "value"},
  "product_service": {"key": "value"}
}
```

## Default Prompts

When AIPrompts is auto-created for a new user, it includes default prompts:

```python
defaults = {
    'manual_prompt': '''You are a helpful customer service assistant. 
Answer customer questions professionally and helpfully in the same language they write. 
Keep responses concise but informative.''',
    
    'auto_prompt': '''You are an AI customer service representative.
Respond to customer inquiries professionally and helpfully.
Always respond in the same language the customer uses.
Keep your responses clear and concise.'''
}
```

## Database Migration

You'll need to run a migration to change from ForeignKey to OneToOneField:

```bash
# Generate migration
python manage.py makemigrations settings

# Apply migration  
python manage.py migrate settings
```

**Note:** This migration may require data cleanup if users have multiple AIPrompts records.

## Testing

### Test Command

```bash
python manage.py test_ai_prompts_api
```

### Manual Testing

```bash
# Test API with curl
curl -X GET "http://localhost:8000/api/v1/settings/ai-prompts/" \
  -H "Authorization: Bearer YOUR_TOKEN"

curl -X PATCH "http://localhost:8000/api/v1/settings/ai-prompts/manual-prompt/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"manual_prompt": "Test prompt"}'
```

### Python Testing

```python
# In Django shell
from accounts.models import User
from settings.models import AIPrompts

user = User.objects.first()

# Test OneToOneField access
prompts = user.ai_prompts  # Should work with related_name

# Test get_or_create
prompts, created = AIPrompts.get_or_create_for_user(user)
print(f"Created: {created}")
print(f"Manual prompt: {prompts.manual_prompt}")
```

## Benefits

### 1. **OneToOneField Relationship**
- ✅ Each user has exactly one AIPrompts record
- ✅ Prevents duplicate prompts 
- ✅ Clean related access: `user.ai_prompts`

### 2. **Automatic Creation**
- ✅ New users automatically get default AI prompts
- ✅ No manual setup required
- ✅ Signal-based creation on user registration

### 3. **API Flexibility**
- ✅ Get all prompts or just manual_prompt
- ✅ Update specific fields or all at once
- ✅ Auto-creation if prompts don't exist

### 4. **Default Prompts**
- ✅ Sensible defaults for new users
- ✅ Multilingual support instructions
- ✅ Professional customer service tone

## Error Handling

All API endpoints include comprehensive error handling:

```json
// Success response
{
  "success": true,
  "data": {...},
  "message": "Operation completed"
}

// Error response  
{
  "success": false,
  "error": "Error description",
  "errors": {...}  // Field validation errors
}
```

## Frontend Integration

```javascript
// Get user's AI prompts
const response = await fetch('/api/v1/settings/ai-prompts/', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

const data = await response.json();
if (data.success) {
  console.log('Manual prompt:', data.data.manual_prompt);
  console.log('Auto-created:', data.created);
}

// Update manual prompt
const updateResponse = await fetch('/api/v1/settings/ai-prompts/manual-prompt/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    manual_prompt: 'New prompt text'
  })
});
```

## Files Created/Modified

### New Files:
- `src/settings/signals.py` - User creation signals
- `src/settings/management/commands/test_ai_prompts_api.py` - Test command
- `AI_PROMPTS_API_ENHANCEMENT.md` - Documentation

### Modified Files:
- `src/settings/models.py` - OneToOneField, auto_prompt, helper method
- `src/settings/serializers.py` - Added AIPrompts serializers  
- `src/settings/views.py` - Added API views
- `src/settings/urls.py` - Added URL patterns
- `src/settings/apps.py` - Connected signals

## Migration Notes

When running the migration from ForeignKey to OneToOneField:

1. **Check for duplicates** first:
```sql
SELECT user_id, COUNT(*) 
FROM settings_aiprompts 
GROUP BY user_id 
HAVING COUNT(*) > 1;
```

2. **Clean up duplicates** if any exist
3. **Run migration**
4. **Test API endpoints**

The OneToOneField ensures data integrity and prevents future duplicates.