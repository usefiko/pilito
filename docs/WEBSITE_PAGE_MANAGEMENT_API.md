# Website and Page Management APIs

## 🗑️ **Delete Website API**

### **Delete a Website and All Related Data**

```http
DELETE /api/v1/web-knowledge/websites/{website_id}/
```

**Description**: Deletes a website source and ALL related data including:
- All pages from the website
- All Q&A pairs from all pages
- All crawl jobs for the website

**Request Headers**:
```
Authorization: Bearer YOUR_TOKEN
```

**Response Example**:
```json
{
  "success": true,
  "message": "Website \"My Business Website\" and all related data deleted successfully",
  "deleted_data": {
    "website": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "My Business Website",
      "url": "https://example.com",
      "pages_count": 15,
      "qa_pairs_count": 67,
      "crawl_jobs_count": 3
    },
    "summary": {
      "pages_deleted": 15,
      "qa_pairs_deleted": 67,
      "crawl_jobs_deleted": 3,
      "total_items_deleted": 86
    }
  }
}
```

**Security**: 
- ✅ Only the website owner can delete their websites
- ✅ Cascading delete ensures no orphaned data
- ✅ Returns detailed summary of what was deleted

---

## ✏️ **Edit Website Page APIs**

### **1. Update Page Content**

```http
PUT /api/v1/web-knowledge/pages/{page_id}/
PATCH /api/v1/web-knowledge/pages/{page_id}/
```

**Description**: Edit page title, content, meta tags, and other fields.

**Request Body**:
```json
{
  "title": "Updated Page Title",
  "summary": "Updated page summary describing the content",
  "meta_description": "Updated meta description for SEO",
  "meta_keywords": ["keyword1", "keyword2", "keyword3"],
  "h1_tags": ["Main Heading", "Secondary Heading"],
  "h2_tags": ["Subheading 1", "Subheading 2"],
  "cleaned_content": "Updated clean text content of the page..."
}
```

**Editable Fields**:
- `title` - Page title (min 3 characters)
- `summary` - Page summary
- `meta_description` - Meta description for SEO
- `meta_keywords` - Array of keywords
- `h1_tags` - Array of H1 headings
- `h2_tags` - Array of H2 headings  
- `cleaned_content` - Main text content (min 50 characters)

**Response Example**:
```json
{
  "success": true,
  "message": "Page updated successfully",
  "content_changed": true,
  "note": "Content was changed. You may want to regenerate Q&A pairs for this page.",
  "regenerate_qa_url": "/api/v1/web-knowledge/manual-qa-generation/",
  "page": {
    "id": "456e7890-e89b-12d3-a456-426614174000",
    "title": "Updated Page Title",
    "url": "https://example.com/page",
    "summary": "Updated page summary",
    "word_count": 347,
    "processing_status": "completed",
    "qa_pairs_count": 5,
    "qa_pairs": [...]
  }
}
```

### **2. Delete a Page**

```http
DELETE /api/v1/web-knowledge/pages/{page_id}/
```

**Description**: Delete a page and all its Q&A pairs.

**Response Example**:
```json
{
  "success": true,
  "message": "Page \"Updated Page Title\" and 5 Q&A pairs deleted successfully",
  "deleted_data": {
    "page": {
      "id": "456e7890-e89b-12d3-a456-426614174000",
      "title": "Updated Page Title",
      "url": "https://example.com/page",
      "qa_pairs_count": 5
    },
    "qa_pairs_deleted": 5
  }
}
```

### **3. Regenerate Q&A Pairs for Page**

```http
POST /api/v1/web-knowledge/pages/{page_id}/regenerate_qa/
```

**Description**: Delete all existing Q&A pairs for the page and generate new ones based on current content.

**Response Example**:
```json
{
  "success": true,
  "message": "Q&A pairs regenerated for page \"Updated Page Title\"",
  "page_id": "456e7890-e89b-12d3-a456-426614174000",
  "page_title": "Updated Page Title",
  "old_qa_pairs_deleted": 5,
  "new_qa_pairs_created": 5
}
```

---

## 📊 **Usage Examples**

### **Example 1: Delete a Website Completely**

```bash
curl -X DELETE "http://localhost:8000/api/v1/web-knowledge/websites/123e4567-e89b-12d3-a456-426614174000/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Use Case**: Remove a website that's no longer needed, including all crawled data.

### **Example 2: Edit Page Title and Content**

```bash
curl -X PATCH "http://localhost:8000/api/v1/web-knowledge/pages/456e7890-e89b-12d3-a456-426614174000/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Services Page",
    "cleaned_content": "We offer comprehensive web development services including custom websites, e-commerce solutions, and mobile applications. Our team specializes in modern technologies and delivers high-quality results."
  }'
```

**Use Case**: Fix typos, update information, or improve content quality.

### **Example 3: Update Page Meta Tags for SEO**

```bash
curl -X PATCH "http://localhost:8000/api/v1/web-knowledge/pages/456e7890-e89b-12d3-a456-426614174000/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "meta_description": "Professional web development services including custom websites and mobile apps",
    "meta_keywords": ["web development", "custom websites", "mobile apps", "professional services"],
    "h1_tags": ["Professional Web Development Services"],
    "h2_tags": ["Custom Websites", "Mobile Applications", "E-commerce Solutions"]
  }'
```

**Use Case**: Improve SEO by updating meta tags and headings.

### **Example 4: Delete Specific Page**

```bash
curl -X DELETE "http://localhost:8000/api/v1/web-knowledge/pages/456e7890-e89b-12d3-a456-426614174000/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Use Case**: Remove outdated or irrelevant pages.

### **Example 5: Regenerate Q&A After Content Changes**

```bash
curl -X POST "http://localhost:8000/api/v1/web-knowledge/pages/456e7890-e89b-12d3-a456-426614174000/regenerate_qa/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Use Case**: Update Q&A pairs after significantly changing page content.

---

## 🔒 **Security and Permissions**

### **Access Control**:
- ✅ Users can only edit/delete their own websites and pages
- ✅ All operations require authentication
- ✅ Foreign key relationships ensure data integrity

### **Validation**:
- ✅ Title must be at least 3 characters
- ✅ Content must be at least 50 characters
- ✅ All fields are validated for format and length

### **Data Integrity**:
- ✅ Cascading deletes ensure no orphaned data
- ✅ Word count automatically recalculated when content changes
- ✅ Q&A pairs maintain relationships to pages

---

## 📋 **Available Endpoints Summary**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `DELETE` | `/api/v1/web-knowledge/websites/{id}/` | Delete website and all data |
| `GET` | `/api/v1/web-knowledge/pages/` | List all pages |
| `GET` | `/api/v1/web-knowledge/pages/{id}/` | Get page details |
| `PUT` | `/api/v1/web-knowledge/pages/{id}/` | Update page (full) |
| `PATCH` | `/api/v1/web-knowledge/pages/{id}/` | Update page (partial) |
| `DELETE` | `/api/v1/web-knowledge/pages/{id}/` | Delete page and Q&A pairs |
| `POST` | `/api/v1/web-knowledge/pages/{id}/regenerate_qa/` | Regenerate Q&A pairs |

---

## 💡 **Best Practices**

### **When to Use Each API**:

1. **Delete Website**: When removing a business or project completely
2. **Edit Page Content**: When fixing errors or updating information
3. **Update Meta Tags**: When improving SEO optimization
4. **Delete Page**: When removing outdated or irrelevant content
5. **Regenerate Q&A**: After significant content changes to keep Q&A relevant

### **Content Change Workflow**:
1. Edit page content using PATCH/PUT
2. Check if `content_changed: true` in response
3. If content changed significantly, use regenerate Q&A endpoint
4. Verify new Q&A pairs are relevant and accurate

The management APIs provide complete control over your website knowledge base with proper security and data integrity! 🚀
