# Enhanced Q&A System - Complete Documentation

## 🚀 **New Enhanced Q&A Features**

I've completely upgraded the Q&A system based on your request to generate many more comprehensive Q&A pairs with better categorization and management capabilities.

## 🎯 **Key Enhancements**

### 1. **Enhanced AI Prompt System**
- **More Comprehensive Prompts**: AI now generates diverse question types
- **Category-Specific Questions**: Questions focused on specific business areas
- **Customer-Focused**: Questions real customers would ask
- **Multiple Question Types**: Factual, procedural, explanatory, comparison, practical, problem-solving

### 2. **Advanced Categorization**
- **7 Categories**: General, Contact, Services, Pricing, Support, Policies, Location
- **6 Question Types**: Factual, Procedural, Explanatory, Comparison, Practical, Problem-solving
- **Keyword Tagging**: Automatic keyword extraction for search optimization
- **Quality Scoring**: Enhanced confidence scoring and approval system

### 3. **Full CRUD Operations**
- **Create**: Add Q&A pairs manually or via AI
- **Read**: Advanced filtering and search capabilities
- **Update**: Edit existing Q&A pairs
- **Delete**: Remove unwanted Q&A pairs
- **Bulk Operations**: Generate many Q&A pairs at once

## 📊 **Enhanced Model Structure**

### Updated QAPair Model Fields:
```python
class QAPair(models.Model):
    # Original fields
    question = models.TextField()
    answer = models.TextField()
    context = models.TextField()
    confidence_score = models.FloatField()
    
    # NEW ENHANCEMENT FIELDS
    question_type = models.CharField(choices=[
        ('factual', 'Factual'),
        ('procedural', 'Procedural'),
        ('explanatory', 'Explanatory'),
        ('comparison', 'Comparison'),
        ('practical', 'Practical'),
        ('problem_solving', 'Problem Solving'),
    ])
    category = models.CharField(choices=[
        ('general', 'General'),
        ('contact', 'Contact'),
        ('services', 'Services'),
        ('pricing', 'Pricing'),
        ('support', 'Support'),
        ('policies', 'Policies'),
        ('location', 'Location'),
    ])
    keywords = models.JSONField(default=list)
    is_approved = models.BooleanField(default=True)
    created_by_ai = models.BooleanField(default=True)
```

## 🌐 **New API Endpoints**

### 1. **Enhanced Q&A Generation**
```http
POST /api/v1/web-knowledge/generate-enhanced-qa/
```

**Request:**
```json
{
    "website_id": "123e4567-e89b-12d3-a456-426614174000",
    "max_qa_per_page": 8,
    "categories": ["general", "contact", "services", "pricing"],
    "question_types": ["factual", "procedural", "explanatory", "practical"]
}
```

**Response:**
```json
{
    "success": true,
    "message": "Enhanced Q&A generation started for 25 pages",
    "task_ids": ["task-1", "task-2", "task-3"],
    "pages_queued": 25,
    "categories": ["general", "contact", "services", "pricing"],
    "question_types": ["factual", "procedural", "explanatory", "practical"],
    "max_qa_per_page": 8
}
```

### 2. **Create Q&A Pairs Manually**
```http
POST /api/v1/web-knowledge/qa-pairs/
```

**Request:**
```json
{
    "page": "page-uuid-123",
    "question": "What are your business hours?",
    "answer": "We're open Monday-Friday 9AM-5PM EST. Weekend hours vary by location.",
    "context": "Business hours information from contact page",
    "question_type": "factual",
    "category": "contact",
    "keywords": ["hours", "business", "schedule", "contact"],
    "confidence_score": 0.95,
    "is_featured": false
}
```

### 3. **Advanced Q&A Filtering**
```http
GET /api/v1/web-knowledge/qa-pairs/?category=contact&question_type=factual&website=123-uuid
```

**Query Parameters:**
- `category` - Filter by category (contact, services, pricing, etc.)
- `question_type` - Filter by type (factual, procedural, etc.)
- `website` - Filter by website ID
- `approved_only=true` - Only approved Q&A pairs
- `created_by=ai` or `created_by=manual` - Filter by creation method

### 4. **Q&A by Category**
```http
GET /api/v1/web-knowledge/qa-pairs/by_category/
```

**Response:**
```json
{
    "contact": [
        {
            "id": "qa-uuid-1",
            "question": "What are your business hours?",
            "answer": "We're open Monday-Friday 9AM-5PM EST",
            "category": "contact",
            "question_type": "factual",
            "confidence_score": 0.95
        }
    ],
    "services": [
        {
            "id": "qa-uuid-2", 
            "question": "What services do you offer?",
            "answer": "We provide web development, consulting, and support services",
            "category": "services",
            "question_type": "factual",
            "confidence_score": 0.92
        }
    ]
}
```

### 5. **Q&A Statistics**
```http
GET /api/v1/web-knowledge/qa-pairs/statistics/
```

**Response:**
```json
{
    "total_qa_pairs": 342,
    "by_category": [
        {"category": "general", "count": 89, "avg_confidence": 0.91},
        {"category": "contact", "count": 76, "avg_confidence": 0.94},
        {"category": "services", "count": 68, "avg_confidence": 0.88}
    ],
    "by_question_type": [
        {"question_type": "factual", "count": 156, "avg_confidence": 0.92},
        {"question_type": "procedural", "count": 89, "avg_confidence": 0.87}
    ],
    "by_creation_method": {
        "ai_generated": 298,
        "manually_created": 44
    },
    "approval_status": {
        "approved": 325,
        "pending_approval": 17
    },
    "featured_count": 23,
    "average_confidence": 0.89,
    "most_viewed": [
        {"id": "qa-1", "question": "How to contact support?", "view_count": 45, "category": "support"}
    ]
}
```

### 6. **Toggle Approval Status**
```http
POST /api/v1/web-knowledge/qa-pairs/{id}/toggle_approval/
```

## 💡 **Example Usage Scenarios**

### 1. **Generate Comprehensive Q&A for New Website**
```javascript
// Step 1: Create and crawl website
const website = await createWebsite({
    name: "Company Website",
    url: "https://example.com",
    max_pages: 50
});

// Step 2: Generate enhanced Q&A with multiple categories
const qaGeneration = await fetch('/api/v1/web-knowledge/generate-enhanced-qa/', {
    method: 'POST',
    body: JSON.stringify({
        website_id: website.id,
        max_qa_per_page: 10,
        categories: ['general', 'contact', 'services', 'pricing', 'support'],
        question_types: ['factual', 'procedural', 'explanatory', 'practical']
    })
});

// Step 3: Monitor progress
// This will generate 10 Q&A pairs per page with diverse categories and types
```

### 2. **Add Manual Q&A Pairs**
```javascript
// Add specific Q&A pairs manually
const manualQA = await fetch('/api/v1/web-knowledge/qa-pairs/', {
    method: 'POST',
    body: JSON.stringify({
        page: pageId,
        question: "Do you offer 24/7 customer support?",
        answer: "Yes, we provide 24/7 customer support via chat, email, and phone for all our premium customers.",
        category: "support",
        question_type: "factual",
        keywords: ["support", "24/7", "customer", "chat", "email", "phone"],
        is_featured: true
    })
});
```

### 3. **Get Customer Service Q&A by Category**
```javascript
// Get all contact-related Q&A pairs
const contactQAs = await fetch('/api/v1/web-knowledge/qa-pairs/?category=contact&approved_only=true');

// Get procedural questions for customer support
const howToQuestions = await fetch('/api/v1/web-knowledge/qa-pairs/?question_type=procedural');

// Get Q&A pairs organized by category
const organizedQAs = await fetch('/api/v1/web-knowledge/qa-pairs/by_category/');
```

## 📊 **Enhanced AI Generation Process**

The new system generates Q&A pairs in multiple phases:

### Phase 1: General Questions
- Generates broad questions about the page content
- Covers main topics and key information
- Creates 2-4 foundational Q&A pairs

### Phase 2: Category-Specific Questions  
- Focuses on specific business categories
- Generates questions customers would actually ask
- Creates targeted Q&A pairs for each category

### Phase 3: Question Type Diversification
- Ensures variety in question types
- Balances factual vs procedural vs explanatory questions
- Creates comprehensive coverage

## 🎯 **Quality Improvements**

### 1. **Better Question Quality**
- More natural, conversational questions
- Questions customers actually ask
- Context-aware question generation
- Diverse question complexity levels

### 2. **Enhanced Answers**
- More comprehensive and helpful answers
- Actionable information included
- Customer-focused language
- Specific details from website content

### 3. **Smart Categorization**
- Automatic category assignment
- Keyword extraction for search
- Quality scoring and confidence metrics
- Manual approval workflow

## 🚀 **Benefits for Your Business**

1. **Comprehensive Coverage**: Generate 8-15 Q&A pairs per page instead of 3-5
2. **Better Customer Service**: Organized by categories customers care about
3. **Easy Management**: Full CRUD operations with approval workflow
4. **Smart Search**: Filter by category, type, keywords, or website
5. **Quality Control**: Manual approval and editing capabilities
6. **Analytics**: Detailed statistics and performance tracking

The enhanced Q&A system now provides a complete knowledge base solution that can automatically generate hundreds of high-quality, categorized Q&A pairs from your website content!
