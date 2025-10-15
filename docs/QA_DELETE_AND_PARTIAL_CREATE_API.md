# Q&A Delete and Partial Create API Documentation

## 🎯 **Overview**

This documentation covers the new Q&A management features:
1. **Delete API for Q&A pairs** - Single and bulk deletion
2. **Partial Q&A Create API** - Create Q&A without requiring page/context

---

## 🗑️ **Q&A Delete APIs**

### **1. Delete Single Q&A Pair**
```http
DELETE /api/v1/web-knowledge/qa-pairs/{qa_pair_id}/
```

**Response:**
```json
{
  "success": true,
  "message": "Q&A pair deleted successfully",
  "deleted_qa": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "question": "What are your business hours?",
    "page_title": "Contact Us",
    "website_name": "My Business Website"
  }
}
```

### **2. Bulk Delete Q&A Pairs**
```http
POST /api/v1/web-knowledge/qa-pairs/bulk_delete/
```

**Request Body:**
```json
{
  "qa_pair_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "456e7890-e89b-12d3-a456-426614174001",
    "789e0123-e89b-12d3-a456-426614174002"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "3 Q&A pairs deleted successfully",
  "deleted_count": 3,
  "deleted_qa_pairs": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "question": "What are your business hours?",
      "page_title": "Contact Us",
      "website_name": "My Business Website"
    },
    {
      "id": "456e7890-e89b-12d3-a456-426614174001",
      "question": "How can I contact support?",
      "page_title": "Support",
      "website_name": "My Business Website"
    },
    {
      "id": "789e0123-e89b-12d3-a456-426614174002",
      "question": "What payment methods do you accept?",
      "page_title": "Billing",
      "website_name": "My Business Website"
    }
  ]
}
```

---

## ➕ **Partial Q&A Create API**

### **Create Q&A Without Page/Context Requirements**
```http
POST /api/v1/web-knowledge/qa-pairs/create/
```

**Key Features:**
- ✅ **No page requirement** - Automatically creates or uses a general page
- ✅ **No context required** - Context is optional and defaults to empty string
- ✅ **Simplified fields** - Only essential fields needed
- ✅ **Website-based** - Link Q&A to a website instead of specific page

**Request Body:**
```json
{
  "website_id": "123e4567-e89b-12d3-a456-426614174000",
  "question": "What are your business hours?",
  "answer": "We are open Monday through Friday from 9 AM to 6 PM, and Saturday from 10 AM to 4 PM. We are closed on Sundays.",
  "question_type": "factual",
  "category": "contact",
  "keywords": ["hours", "schedule", "contact"],
  "confidence_score": 0.95,
  "is_featured": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Q&A pair created successfully",
  "id": "987e6543-e89b-12d3-a456-426614174003",
  "qa_pair": {
    "id": "987e6543-e89b-12d3-a456-426614174003",
    "page": {
      "id": "abc123de-e89b-12d3-a456-426614174004",
      "title": "General Information",
      "url": "https://example.com/general"
    },
    "question": "What are your business hours?",
    "answer": "We are open Monday through Friday from 9 AM to 6 PM, and Saturday from 10 AM to 4 PM. We are closed on Sundays.",
    "context": "",
    "confidence_score": 0.95,
    "question_type": "factual",
    "question_type_display": "Factual",
    "category": "contact",
    "category_display": "Contact",
    "keywords": ["hours", "schedule", "contact"],
    "view_count": 0,
    "is_featured": false,
    "is_approved": true,
    "created_by_ai": false,
    "generation_status": "completed",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

### **Field Descriptions**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `website_id` | UUID | ✅ Yes | Website to associate the Q&A with |
| `question` | String | ✅ Yes | The question text |
| `answer` | String | ✅ Yes | The answer text |
| `question_type` | Choice | ❌ Optional | Type: `factual`, `procedural`, `explanatory`, `comparison`, `practical`, `problem_solving` |
| `category` | Choice | ❌ Optional | Category: `general`, `contact`, `services`, `pricing`, `support`, `policies`, `location` |
| `keywords` | Array | ❌ Optional | Keywords for search and categorization |
| `confidence_score` | Float | ❌ Optional | Confidence score (0.0-1.0), defaults to 0.8 |
| `is_featured` | Boolean | ❌ Optional | Mark as featured Q&A, defaults to false |

### **How It Works**

1. **Website Association**: When you provide a `website_id`, the system:
   - Validates that the website belongs to you
   - Looks for an existing "General Information" page
   - Creates one if it doesn't exist
   - Associates the Q&A with this page

2. **Automatic Page Creation**: The system automatically creates:
   ```json
   {
     "title": "General Information",
     "url": "{website_url}/general",
     "content": "General Q&A content",
     "processing_status": "completed"
   }
   ```

3. **Default Values**: The system sets:
   - `created_by_ai`: `false` (manually created)
   - `is_approved`: `true` (automatically approved)
   - `generation_status`: `completed`
   - `context`: `""` (empty string)

---

## 💻 **Frontend Integration Examples**

### **1. Delete Single Q&A**
```javascript
const deleteQA = async (qaId) => {
  const response = await fetch(`/api/v1/web-knowledge/qa-pairs/${qaId}/`, {
    method: 'DELETE',
    headers: {
      'Authorization': 'Bearer ' + token
    }
  });
  
  const result = await response.json();
  if (result.success) {
    console.log('Q&A deleted:', result.message);
    // Refresh Q&A list
    loadQAPairs();
  }
};
```

### **2. Bulk Delete Q&As**
```javascript
const bulkDeleteQA = async (qaIds) => {
  const response = await fetch('/api/v1/web-knowledge/qa-pairs/bulk_delete/', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + token,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      qa_pair_ids: qaIds
    })
  });
  
  const result = await response.json();
  if (result.success) {
    console.log(`${result.deleted_count} Q&A pairs deleted`);
    // Refresh Q&A list
    loadQAPairs();
  }
};

// Usage with selected checkboxes
const selectedQAIds = document.querySelectorAll('.qa-checkbox:checked')
  .map(checkbox => checkbox.value);
bulkDeleteQA(selectedQAIds);
```

### **3. Create Partial Q&A**
```javascript
const createPartialQA = async (websiteId, question, answer) => {
  const response = await fetch('/api/v1/web-knowledge/qa-pairs/create/', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + token,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      website_id: websiteId,
      question: question,
      answer: answer,
      question_type: 'factual',
      category: 'general',
      keywords: extractKeywords(question + ' ' + answer),
      confidence_score: 0.9,
      is_featured: false
    })
  });
  
  const result = await response.json();
  if (result.success) {
    console.log('Q&A created:', result.qa_pair);
    // Add to Q&A list
    addQAToList(result.qa_pair);
    // Clear form
    clearQAForm();
  }
};

// Helper function to extract keywords
const extractKeywords = (text) => {
  return text.toLowerCase()
    .split(/\s+/)
    .filter(word => word.length > 3)
    .slice(0, 5); // Take first 5 meaningful words
};
```

### **4. Q&A Management Interface**
```javascript
// Complete Q&A management component
class QAManager {
  constructor(websiteId) {
    this.websiteId = websiteId;
    this.selectedQAs = new Set();
  }
  
  async loadQAPairs() {
    const response = await fetch(`/api/v1/web-knowledge/qa-pairs/?website=${this.websiteId}`, {
      headers: { 'Authorization': 'Bearer ' + token }
    });
    const data = await response.json();
    this.renderQAPairs(data.results);
  }
  
  renderQAPairs(qaPairs) {
    const container = document.getElementById('qa-list');
    container.innerHTML = qaPairs.map(qa => `
      <div class="qa-item">
        <input type="checkbox" class="qa-checkbox" value="${qa.id}" 
               onchange="qaManager.toggleSelection('${qa.id}')">
        <div class="qa-content">
          <h4>${qa.question}</h4>
          <p>${qa.answer}</p>
          <span class="badge">${qa.category_display}</span>
          <span class="badge">${qa.question_type_display}</span>
        </div>
        <div class="qa-actions">
          <button onclick="qaManager.editQA('${qa.id}')">Edit</button>
          <button onclick="qaManager.deleteQA('${qa.id}')" class="btn-danger">Delete</button>
        </div>
      </div>
    `).join('');
  }
  
  toggleSelection(qaId) {
    if (this.selectedQAs.has(qaId)) {
      this.selectedQAs.delete(qaId);
    } else {
      this.selectedQAs.add(qaId);
    }
    this.updateBulkActions();
  }
  
  updateBulkActions() {
    const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
    bulkDeleteBtn.style.display = this.selectedQAs.size > 0 ? 'block' : 'none';
    bulkDeleteBtn.textContent = `Delete ${this.selectedQAs.size} Selected`;
  }
  
  async bulkDeleteSelected() {
    if (this.selectedQAs.size === 0) return;
    
    if (!confirm(`Delete ${this.selectedQAs.size} Q&A pairs?`)) return;
    
    await bulkDeleteQA(Array.from(this.selectedQAs));
    this.selectedQAs.clear();
    this.loadQAPairs();
  }
  
  async deleteQA(qaId) {
    if (!confirm('Delete this Q&A pair?')) return;
    await deleteQA(qaId);
    this.loadQAPairs();
  }
}

// Initialize
const qaManager = new QAManager('your-website-id');
qaManager.loadQAPairs();
```

---

## 🔒 **Security & Validation**

### **Security Features:**
- ✅ **User Isolation**: Users can only delete/create Q&A for their own websites
- ✅ **Authentication Required**: All endpoints require valid token
- ✅ **Ownership Validation**: Website ownership verified before operations
- ✅ **Bulk Delete Protection**: Only processes Q&A pairs user owns

### **Validation Rules:**
- **Question**: Required, minimum 10 characters
- **Answer**: Required, minimum 20 characters  
- **Website ID**: Must be valid UUID and belong to user
- **Keywords**: Optional array, max 10 keywords
- **Confidence Score**: Optional float between 0.0 and 1.0

### **Error Responses:**
```json
{
  "success": false,
  "errors": {
    "question": ["This field is required."],
    "website_id": ["Website not found or access denied"],
    "confidence_score": ["Ensure this value is between 0.0 and 1.0"]
  }
}
```

---

## 🎯 **Use Cases**

### **Q&A Delete APIs:**
- ✅ Remove outdated or incorrect Q&A pairs
- ✅ Bulk cleanup of auto-generated Q&A
- ✅ Content moderation and quality control
- ✅ Manage storage and database size

### **Partial Q&A Create API:**
- ✅ Quick manual Q&A addition without complex setup
- ✅ Add frequently asked questions easily
- ✅ Create Q&A for general business information
- ✅ Supplement auto-generated content with manual entries
- ✅ Customer service team can add common questions

The new APIs provide complete Q&A management capabilities with simplified creation and comprehensive deletion options! 🚀
