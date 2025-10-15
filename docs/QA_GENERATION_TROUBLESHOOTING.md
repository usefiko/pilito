# Q&A Generation Troubleshooting Guide

## 🚨 **Issue: Q&A Pairs Not Being Created**

If you're seeing the message "Q&A pairs (minimum 3 per page) will be automatically generated for each crawled page" but no Q&A pairs are actually created, here's how to diagnose and fix the problem.

## 🔍 **Diagnosis Steps**

### Step 1: Check if Pages are Being Crawled Successfully

```bash
# Check if website crawling completed successfully
GET /api/v1/web-knowledge/websites/{website_id}/

# Response should show:
{
  "crawl_status": "completed",
  "pages_crawled": 15,  // Should be > 0
  "total_qa_pairs": 0   // This might be 0 if Q&A generation failed
}
```

### Step 2: Check if Pages Have Content

```bash
# Check pages for a website
GET /api/v1/web-knowledge/pages/?website={website_id}

# Look for:
{
  "processing_status": "completed",
  "word_count": 150,     // Should be >= 100
  "cleaned_content": "..." // Should have content
}
```

### Step 3: Check Current Q&A Pairs

```bash
# Check existing Q&A pairs
GET /api/v1/web-knowledge/qa-pairs/?website={website_id}

# Should return Q&A pairs if generation worked
```

## 🛠️ **Common Causes and Solutions**

### **Cause 1: AI Service Not Available**

**Problem**: The Gemini AI service isn't configured or isn't working.

**Solution**: The system should automatically use fallback generation, but this might not be working.

**Fix**: Use the manual Q&A generation API:

```bash
# Manual Q&A generation for entire website
POST /api/v1/web-knowledge/manual-qa-generation/
{
  "website_id": "your-website-uuid"
}

# Response:
{
  "success": true,
  "message": "Created 45 Q&A pairs for 15 pages",
  "total_qa_pairs_created": 45,
  "pages_processed": [...]
}
```

### **Cause 2: Celery Workers Not Running**

**Problem**: The background tasks (Celery) aren't running to process Q&A generation.

**Symptoms**:
- Website crawling completes
- Pages are created and processed
- But Q&A generation tasks never execute

**Fix**: Check if Celery workers are running:

```bash
# In Docker environment, check if celery service is running
docker-compose ps

# Should see celery worker running
```

### **Cause 3: Task Failures**

**Problem**: Q&A generation tasks are failing silently.

**Fix**: Check Celery logs or use manual generation to bypass async tasks:

```bash
# Generate Q&A for specific page
POST /api/v1/web-knowledge/manual-qa-generation/
{
  "page_id": "page-uuid-here"
}
```

## 🚀 **Quick Fix Solutions**

### **Solution 1: Manual Q&A Generation (Recommended)**

Use the manual Q&A generation API to immediately create Q&A pairs:

```bash
# For entire website
curl -X POST "http://localhost:8000/api/v1/web-knowledge/manual-qa-generation/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"website_id": "your-website-uuid"}'

# For specific page
curl -X POST "http://localhost:8000/api/v1/web-knowledge/manual-qa-generation/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"page_id": "your-page-uuid"}'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Created 15 Q&A pairs for 5 pages",
  "website_id": "123...",
  "website_name": "Your Website",
  "total_qa_pairs_created": 15,
  "pages_processed": [
    {
      "page_id": "456...",
      "page_title": "Home Page",
      "qa_pairs_created": 3
    }
  ]
}
```

### **Solution 2: Enhanced Q&A Generation**

If manual generation works, you can also use the enhanced generation:

```bash
curl -X POST "http://localhost:8000/api/v1/web-knowledge/generate-enhanced-qa/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": "your-website-uuid",
    "max_qa_per_page": 5,
    "categories": ["general", "contact", "services"],
    "question_types": ["factual", "procedural", "explanatory"]
  }'
```

### **Solution 3: Verify Q&A Creation**

After running manual generation, verify Q&A pairs were created:

```bash
# Check Q&A pairs for website
GET /api/v1/web-knowledge/qa-pairs/?website={website_id}

# Check Q&A statistics
GET /api/v1/web-knowledge/qa-pairs/statistics/
```

## 🔧 **System Improvements Applied**

I've made several improvements to ensure Q&A generation works reliably:

### **1. Fallback Q&A Generation**

The system now includes a fallback mechanism that creates basic Q&A pairs even if AI fails:

```python
# Automatically creates Q&A pairs like:
{
  "question": "What is [Page Title] about?",
  "answer": "This page provides information about [Page Title]. [Content preview...]",
  "category": "general",
  "question_type": "factual"
}
```

### **2. Guaranteed Minimum Q&A Pairs**

Every page now gets at least 3 Q&A pairs:

- If AI generates 0 pairs → Creates 3 fallback pairs
- If AI generates 1 pair → Adds 2 more fallback pairs
- If AI generates 3+ pairs → Uses AI pairs

### **3. Manual Generation API**

New endpoint for immediate Q&A generation without async tasks:

- `POST /api/v1/web-knowledge/manual-qa-generation/`
- Bypasses Celery and AI dependencies
- Creates Q&A pairs immediately
- Returns detailed results

## 📊 **Verification Checklist**

After applying fixes, verify Q&A generation works:

- [ ] ✅ Website crawling completes successfully
- [ ] ✅ Pages have `processing_status: "completed"`
- [ ] ✅ Pages have `word_count >= 100`
- [ ] ✅ Q&A pairs exist: `GET /api/v1/web-knowledge/qa-pairs/`
- [ ] ✅ Each page has at least 3 Q&A pairs
- [ ] ✅ Q&A pairs have proper categories and types

## 🎯 **Expected Results**

After fixing the Q&A generation:

1. **Automatic Generation**: Q&A pairs created during crawling
2. **Minimum Guarantee**: At least 3 Q&A pairs per page
3. **Fallback Support**: Works even without AI
4. **Manual Control**: Can trigger generation manually
5. **Rich Data**: Q&A pairs with categories, types, and keywords

## 📞 **If Issues Persist**

If Q&A generation still doesn't work:

1. **Check Database**: Ensure pages exist and have content
2. **Check Logs**: Look for error messages in Django/Celery logs
3. **Use Manual Generation**: Bypass async processing
4. **Verify Permissions**: Ensure user owns the website/pages
5. **Check Content**: Pages need at least 100 words for Q&A generation

The manual Q&A generation API should work in all cases and provides immediate results for testing and production use.
