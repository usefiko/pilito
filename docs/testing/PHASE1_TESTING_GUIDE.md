# 🧪 Phase 1: Testing & Deployment Guide

## 📋 Overview

Phase 1 includes 3 **low-risk, high-impact** features:
1. ✅ **Knowledge Base Confidence Scoring** - AI admits when it doesn't know
2. ✅ **Response Quality Feedback Loop** - Customers rate AI responses (👍/👎)
3. ✅ **Conversation Intelligence** - Auto-summarize long conversations

**Total Risk: 🟢 5% (Very Low)**  
**No Breaking Changes**  
**Migration Required: Yes (1 simple migration for feedback fields)**

---

## 🔧 Files Changed

### Modified Files:
1. **`src/AI_model/services/gemini_service.py`**
   - Added `_get_confidence_instruction()` method
   - Modified `_rank_qa_with_embedding()` to return similarity score
   - Added `_get_conversation_summary()` method
   - Modified `_build_prompt()` to use confidence + summarization

2. **`src/message/models.py`**
   - Added `feedback`, `feedback_comment`, `feedback_at` fields to `Message` model

3. **`src/message/api/message.py`**
   - Added `submit_message_feedback()` API endpoint

4. **`src/message/urls.py`**
   - Added URL pattern for feedback API

### New Files:
- **`AI_INTELLIGENCE_ROADMAP.md`** - Full roadmap for Phase 1 & 2
- **`PHASE1_TESTING_GUIDE.md`** - This file

---

## 📦 Deployment Steps

### Step 1: Pull Latest Code
```bash
cd /home/ubuntu/fiko-backend
git pull origin main
```

### Step 2: Create Migration
```bash
# On server
docker compose exec web python manage.py makemigrations message

# Expected output:
# Migrations for 'message':
#   message/migrations/0008_add_feedback_fields.py
#     - Add field feedback to message
#     - Add field feedback_comment to message
#     - Add field feedback_at to message
```

### Step 3: Apply Migration
```bash
docker compose exec web python manage.py migrate

# Expected output:
# Operations to perform:
#   Apply all migrations: message, ...
# Running migrations:
#   Applying message.0008_add_feedback_fields... OK
```

### Step 4: Restart Services
```bash
# Rebuild containers to pick up code changes
docker compose down
docker compose build web celery_worker
docker compose up -d

# Check logs
docker logs -f web --tail 100
docker logs -f celery_worker --tail 100
```

---

## ✅ Testing Checklist

### Test 1: Knowledge Base Confidence Scoring

**Purpose:** Verify AI says "I don't know" when confidence is low

**Steps:**
1. Go to a conversation in your dashboard
2. Ask a question that's NOT in your knowledge base:
   ```
   "What is the capital of Mars?"
   ```
   or
   ```
   "Do you offer services in Antarctica?"
   ```

**Expected Result:**
- ❌ OLD: AI might hallucinate an answer
- ✅ NEW: AI should say something like:
  ```
  "I don't have specific information about this in our documentation. 
  Would you like me to connect you with our support team who can give 
  you accurate details? 😊"
  ```

**Check Logs:**
```bash
docker logs -f celery_worker | grep "Embedding ranking"
```

Look for:
```
✅ Embedding ranking: Selected 8 most relevant Q&A from 60 total (avg score: 0.45)
```

- If avg score < 0.65 → LOW confidence message
- If avg score 0.65-0.75 → MEDIUM confidence ("Based on our documentation, I believe...")
- If avg score > 0.75 → HIGH confidence (direct answer)

---

### Test 2: Response Quality Feedback

**Purpose:** Verify customers can rate AI responses

**Steps:**

#### A) Test via API (Postman/cURL):
```bash
# 1. Get your JWT token
curl -X POST https://api.pilito.com/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# 2. Get a message ID (from your conversations)
# 3. Submit positive feedback
curl -X POST https://api.pilito.com/api/message/MESSAGE_ID/feedback/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": "positive",
    "comment": "Very helpful!"
  }'

# Expected Response:
{
  "success": true,
  "message": "Feedback submitted successfully",
  "data": {
    "message_id": "abc123",
    "feedback": "positive",
    "comment": "Very helpful!",
    "feedback_at": "2025-10-05T10:30:00Z"
  }
}

# 4. Try negative feedback
curl -X POST https://api.pilito.com/api/message/MESSAGE_ID/feedback/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": "negative",
    "comment": "Not accurate"
  }'
```

#### B) Verify in Database:
```bash
docker compose exec web python manage.py shell
```

```python
from message.models import Message

# Check feedback stats
ai_messages = Message.objects.filter(type='AI')
total = ai_messages.count()
positive = ai_messages.filter(feedback='positive').count()
negative = ai_messages.filter(feedback='negative').count()
no_feedback = ai_messages.filter(feedback='none').count()

print(f"Total AI Messages: {total}")
print(f"Positive Feedback: {positive} ({positive/total*100:.1f}%)")
print(f"Negative Feedback: {negative} ({negative/total*100:.1f}%)")
print(f"No Feedback: {no_feedback} ({no_feedback/total*100:.1f}%)")

# Show recent feedback
recent_feedback = Message.objects.filter(
    type='AI', 
    feedback__in=['positive', 'negative']
).order_by('-feedback_at')[:10]

for msg in recent_feedback:
    print(f"\n{msg.feedback.upper()}: {msg.content[:80]}...")
    print(f"Comment: {msg.feedback_comment}")
    print(f"At: {msg.feedback_at}")
```

**Expected Result:**
- ✅ Feedback is saved correctly
- ✅ `feedback_at` timestamp is set
- ✅ Can update feedback multiple times

---

### Test 3: Conversation Intelligence (Summarization)

**Purpose:** Verify long conversations are summarized to save tokens

**Steps:**

1. **Create a long conversation** (>10 messages) with a test customer
   - Send 15-20 messages back and forth
   - Discuss various topics (pricing, features, etc.)

2. **Send a new message** and check logs:
```bash
docker logs -f celery_worker | grep "conversation summary"
```

**Expected Logs:**
```
✅ Generated conversation summary for abc123 (18 messages → 245 chars)
Using conversation summary + 5 recent messages
```

3. **Check Redis cache:**
```bash
docker exec -it redis redis-cli
```

```redis
# Check if summary is cached
KEYS conv_summary:*

# Example output:
1) "conv_summary:abc123"
2) "conv_summary:def456"

# Get summary content
GET conv_summary:abc123

# Example output:
"Customer is inquiring about Python course pricing and availability. They requested information about payment plans and asked if there's a student discount. We provided pricing details and confirmed a 20% student discount is available."

# Check TTL (should be ~3600 seconds = 1 hour)
TTL conv_summary:abc123
```

**Expected Results:**
- ✅ For conversations > 10 messages: Summary is generated
- ✅ Summary is cached for 1 hour
- ✅ Prompt uses summary + last 5 messages (instead of last 6)
- ✅ For conversations ≤ 10 messages: No summary (uses all messages)

4. **Compare Token Usage:**

Before (without summary):
```
Conversation with 20 messages × 100 tokens/message = 2000 tokens
```

After (with summary):
```
Summary: ~50 tokens
Last 5 messages: 5 × 100 = 500 tokens
Total: 550 tokens (72.5% reduction!)
```

**Check in logs:**
```bash
docker logs -f celery_worker | grep "Usage tracked"
```

Look for reduced token counts in long conversations.

---

## 📊 Success Criteria

### Feature 1: Confidence Scoring
- ✅ Low-confidence questions get "I don't know" response
- ✅ Medium-confidence gets disclaimer ("Based on our documentation...")
- ✅ High-confidence gets direct answer
- ✅ No hallucinations for unknown topics

### Feature 2: Feedback Loop
- ✅ API endpoint responds correctly (200 OK)
- ✅ Feedback is saved to database
- ✅ Can query feedback statistics
- ✅ Only works for AI messages (400 error for customer messages)
- ✅ Only works for own conversations (403/404 for others)

### Feature 3: Conversation Intelligence
- ✅ Summaries generated for conversations >10 messages
- ✅ Summaries cached in Redis (1 hour)
- ✅ Token usage reduced by 30-40% for long conversations
- ✅ No summaries for short conversations (≤10 messages)
- ✅ Graceful fallback if summarization fails

---

## 🚨 Troubleshooting

### Issue 1: Migration Fails
```
django.db.utils.ProgrammingError: column "feedback" already exists
```

**Solution:**
```bash
# Check existing migrations
docker compose exec web python manage.py showmigrations message

# If migration exists, just apply it
docker compose exec web python manage.py migrate

# If conflict, rollback and reapply
docker compose exec web python manage.py migrate message 0007  # Previous migration
docker compose exec web python manage.py migrate
```

---

### Issue 2: API Endpoint Not Found (404)
```
POST /api/message/abc123/feedback/ → 404 Not Found
```

**Solution:**
```bash
# Check if URL pattern is registered
docker compose exec web python manage.py show_urls | grep feedback

# Should show:
# /api/message/<str:message_id>/feedback/   message:submit-message-feedback

# If not showing, restart web container
docker compose restart web
```

---

### Issue 3: Summarization Not Working
```
Logs show: "Gemini model not initialized, cannot generate summary"
```

**Solution:**
```bash
# Check Gemini API key
docker compose exec web python manage.py shell
```

```python
from settings.models import GeneralSettings
settings = GeneralSettings.get_settings()
print(f"Gemini API key: {'✅ Set' if settings.gemini_api_key else '❌ Missing'}")
print(f"Key length: {len(settings.gemini_api_key) if settings.gemini_api_key else 0}")
```

If missing, set it in Django admin: `/admin/settings/generalsettings/`

---

### Issue 4: Redis Cache Not Working
```
Logs show: "ConnectionError: Error connecting to Redis"
```

**Solution:**
```bash
# Check Redis status
docker compose ps redis

# Should show: Up
# If not, restart Redis
docker compose restart redis

# Test Redis connection
docker exec -it redis redis-cli PING
# Should output: PONG
```

---

## 📈 Monitoring & Analytics

### Daily Monitoring Commands:

#### 1. Check Feedback Stats:
```bash
docker compose exec web python manage.py shell
```

```python
from message.models import Message
from django.db.models import Count

# Feedback summary
feedback_stats = Message.objects.filter(
    type='AI'
).values('feedback').annotate(count=Count('id'))

for stat in feedback_stats:
    print(f"{stat['feedback']}: {stat['count']}")

# Satisfaction rate (positive / total with feedback)
total_with_feedback = Message.objects.filter(
    type='AI', 
    feedback__in=['positive', 'negative']
).count()

positive_count = Message.objects.filter(
    type='AI', 
    feedback='positive'
).count()

satisfaction_rate = (positive_count / total_with_feedback * 100) if total_with_feedback > 0 else 0
print(f"\nSatisfaction Rate: {satisfaction_rate:.1f}%")
```

#### 2. Check Summarization Stats:
```bash
docker exec -it redis redis-cli
```

```redis
# Count cached summaries
KEYS conv_summary:* | wc -l

# Example: 45 conversations have summaries cached
```

#### 3. Check Logs for Issues:
```bash
# Check for errors in last hour
docker logs --since 1h celery_worker 2>&1 | grep -i error

# Check confidence levels
docker logs --since 1h celery_worker 2>&1 | grep "CONFIDENCE"

# Check summary generation
docker logs --since 1h celery_worker 2>&1 | grep "conversation summary"
```

---

## 🔄 Rollback Plan (If Needed)

If any issues arise, you can safely rollback:

### Option 1: Rollback Code Only
```bash
# Revert to previous commit
git log --oneline -10  # Find previous commit hash
git revert COMMIT_HASH
docker compose down
docker compose build web celery_worker
docker compose up -d
```

### Option 2: Rollback Code + Migration
```bash
# Rollback migration
docker compose exec web python manage.py migrate message 0007

# Revert code
git revert COMMIT_HASH
docker compose down
docker compose build web celery_worker
docker compose up -d
```

**Note:** Feedback fields will remain in database (no data loss), but won't be used.

---

## ✅ Phase 1 Complete Checklist

Before proceeding to Phase 2, verify:

- [ ] Migration applied successfully
- [ ] All 3 features tested and working
- [ ] No errors in logs (24 hours)
- [ ] Feedback API working correctly
- [ ] Confidence scoring prevents hallucinations
- [ ] Summarization reduces token usage
- [ ] Redis caching working
- [ ] Performance is stable (no slowdowns)
- [ ] Customer satisfaction rate is measurable

---

## 📞 Next Steps

Once Phase 1 is tested and stable (2-3 days), proceed to **Phase 2**:
- Sentiment Analysis + Intent Recognition
- Context-Aware Personality
- Smart Follow-ups & Proactive Messages

See `AI_INTELLIGENCE_ROADMAP.md` for Phase 2 details.

---

**Questions or Issues?**  
Check logs first, then review this guide's Troubleshooting section.

**Last Updated:** 2025-10-05
