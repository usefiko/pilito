# Enhanced Q&A Generation - Usage Examples

## 🎯 **Fixed Issues and Improvements**

### ✅ **Issue 1: Minimum 3 Q&A Pairs Guaranteed**
**Problem**: The enhanced Q&A generation API wasn't creating enough Q&A pairs.

**Solution**: Added fallback generation system that ensures minimum 3 Q&A pairs per page:
- If AI generation fails → automatically generates fallback Q&A pairs
- If AI generates less than 3 → adds additional fallback pairs to reach minimum
- Fallback pairs are created from page content (title, content, URL)

### ✅ **Issue 2: Automatic Q&A Generation in Create-and-Crawl**
**Problem**: Q&A generation wasn't automatically triggered when using create-and-crawl API.

**Solution**: Q&A generation is now automatically triggered:
- ✅ Every crawled page automatically gets Q&A pairs generated
- ✅ Minimum 3 Q&A pairs per page guaranteed
- ✅ Enhanced response messages inform users about automatic Q&A generation

## 🌐 **How the Automatic Q&A Generation Works**

### Flow Diagram:
```
1. Create Website → 2. Start Crawling → 3. Process Each Page → 4. Generate Q&A Pairs
                                     ↓
                              Content Processing → Q&A Generation (min 3 pairs)
```

### Automatic Trigger Points:

1. **During Crawling**: 
   - Each page is automatically processed after crawling
   - Q&A pairs are generated for pages with 100+ words
   - Minimum 3 Q&A pairs guaranteed per page

2. **Enhanced Generation**:
   - Use the enhanced Q&A API for more comprehensive pairs
   - Supports category and question type customization
   - Can generate 8-15 pairs per page

## 📋 **API Usage Examples**

### 1. **Create Website with Automatic Q&A Generation**

```bash
curl -X POST "http://localhost:8000/api/v1/web-knowledge/websites/create-and-crawl/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Business Website",
    "url": "https://example.com",
    "description": "Main business website",
    "max_pages": 20,
    "crawl_depth": 2
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Website created, crawling started, and Q&A generation will begin automatically",
  "website": {...},
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "task_id": "celery-task-id",
  "note": "Q&A pairs (minimum 3 per page) will be automatically generated for each crawled page",
  "auto_qa_generation": true,
  "urls": {
    "status": "/api/v1/web-knowledge/websites/123.../crawl_status/",
    "qa_pairs": "/api/v1/web-knowledge/qa-pairs/?website=123...",
    "enhanced_qa_generation": "/api/v1/web-knowledge/generate-enhanced-qa/"
  }
}
```

### 2. **Enhanced Q&A Generation (More Comprehensive)**

```bash
curl -X POST "http://localhost:8000/api/v1/web-knowledge/generate-enhanced-qa/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": "123e4567-e89b-12d3-a456-426614174000",
    "max_qa_per_page": 8,
    "categories": ["general", "contact", "services", "pricing", "support"],
    "question_types": ["factual", "procedural", "explanatory", "practical"]
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Enhanced Q&A generation started for 15 pages",
  "task_ids": ["task-1", "task-2", "task-3"],
  "pages_queued": 15,
  "categories": ["general", "contact", "services", "pricing", "support"],
  "question_types": ["factual", "procedural", "explanatory", "practical"],
  "max_qa_per_page": 8
}
```

### 3. **Get Q&A Pairs with Filtering**

```bash
# Get all Q&A pairs for a website
curl "http://localhost:8000/api/v1/web-knowledge/qa-pairs/?website=123e4567-e89b-12d3-a456-426614174000"

# Get contact-related Q&A pairs
curl "http://localhost:8000/api/v1/web-knowledge/qa-pairs/?category=contact"

# Get procedural questions
curl "http://localhost:8000/api/v1/web-knowledge/qa-pairs/?question_type=procedural"

# Get only approved Q&A pairs
curl "http://localhost:8000/api/v1/web-knowledge/qa-pairs/?approved_only=true"
```

### 4. **Create Q&A Pairs Manually**

```bash
curl -X POST "http://localhost:8000/api/v1/web-knowledge/qa-pairs/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "page": "page-uuid-here",
    "question": "What are your business hours?",
    "answer": "We are open Monday-Friday 9AM-5PM EST, and Saturday 10AM-2PM EST. We are closed on Sundays.",
    "category": "contact",
    "question_type": "factual",
    "keywords": ["hours", "business", "schedule", "contact"],
    "confidence_score": 0.95,
    "is_featured": true
  }'
```

### 5. **Get Q&A Statistics**

```bash
curl "http://localhost:8000/api/v1/web-knowledge/qa-pairs/statistics/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "total_qa_pairs": 142,
  "by_category": [
    {"category": "general", "count": 45, "avg_confidence": 0.89},
    {"category": "contact", "count": 32, "avg_confidence": 0.94},
    {"category": "services", "count": 28, "avg_confidence": 0.87}
  ],
  "by_question_type": [
    {"question_type": "factual", "count": 78, "avg_confidence": 0.91},
    {"question_type": "procedural", "count": 34, "avg_confidence": 0.86}
  ],
  "by_creation_method": {
    "ai_generated": 118,
    "manually_created": 24
  },
  "featured_count": 12,
  "average_confidence": 0.88
}
```

## 🧪 **Testing the Enhanced Q&A System**

### Test Command:
```bash
# Create test data and test the system
python manage.py test_enhanced_qa --create-test-data

# Test with existing website
python manage.py test_enhanced_qa --website-id "your-website-uuid"
```

### Example Output:
```
🚀 Testing Enhanced Q&A Generation System
📝 Creating test data...
✅ Test data created:
   Website ID: 123e4567-e89b-12d3-a456-426614174000
   Page ID: 456e7890-e89b-12d3-a456-426614174000

🧪 Testing enhanced Q&A generation for website: 123e4567...
📄 Found 1 pages to test

🔄 Testing page: Test Page for Q&A Generation (https://example.com/test-page)
✅ Generated 5 Q&A pairs
   1. Q: What are your business hours?
      A: Our business hours are Monday - Friday: 9:00 AM - 6:00 PM EST...
      Category: contact, Type: factual
      Confidence: 0.92

   2. Q: What services do you offer?
      A: We offer web development, digital marketing, business consulting...
      Category: services, Type: factual
      Confidence: 0.89

   3. Q: How can I contact you?
      A: You can contact us via email at support@example.com, phone at...
      Category: contact, Type: procedural
      Confidence: 0.95
```

## 🎯 **Key Benefits**

### ✅ **Guaranteed Minimum Q&A Pairs**
- Every page gets at least 3 Q&A pairs
- AI failure → automatic fallback generation
- No empty Q&A results

### ✅ **Automatic Generation**
- Q&A pairs created during crawling
- No manual intervention required
- Immediate availability after crawling

### ✅ **Enhanced Customization**
- Choose specific categories
- Select question types
- Control number of Q&A pairs per page

### ✅ **Quality Control**
- Manual approval system
- Edit and improve Q&A pairs
- Featured Q&A marking
- Confidence scoring

### ✅ **Comprehensive Coverage**
- 7 Categories: general, contact, services, pricing, support, policies, location
- 6 Question Types: factual, procedural, explanatory, comparison, practical, problem_solving
- Smart keyword extraction
- Customer-focused questions

## 🚀 **What's Next?**

The enhanced Q&A system now provides:
1. **Automatic generation** during website crawling
2. **Minimum 3 Q&A pairs** guaranteed per page
3. **Enhanced generation** with categories and types
4. **Full CRUD operations** for managing Q&A pairs
5. **Smart filtering** and search capabilities
6. **Quality control** with approval workflows

Your Q&A knowledge base is now comprehensive and fully automated! 🎉
