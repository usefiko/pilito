# API مستندات: کرال دستی صفحات و Bulk Delete

## 📋 خلاصه

این مستندات شامل دو بخش اصلی است:
1. **کرال دستی صفحات**: امکان کرال URLهای مشخص شده (بدون کرال صفحات داخلی)
2. **Bulk Delete**: امکان انتخاب و پاک کردن چندتایی برای Pages، Products و Q&A Pairs

### کرال دستی صفحات

این API امکان کرال دستی URLهای مشخص شده را فراهم می‌کند. برخلاف کرال عادی که تمام صفحات داخلی سایت را پیدا می‌کند، این API فقط URLهایی که کاربر مشخص کرده را کرال می‌کند.

**✅ وضعیت کرال دستی:** API آماده و تست شده است. تست‌ها نشان می‌دهند که کرال دستی به درستی کار می‌کند و فقط URLهای مشخص شده را کرال می‌کند.

### تفاوت با کرال عادی:

| ویژگی | کرال عادی | کرال دستی |
|-------|----------|-----------|
| **ورودی** | یک URL پایه | لیست URLها (هر URL در یک خط) |
| **رفتار** | صفحات داخلی را پیدا می‌کند | فقط URLهای مشخص شده |
| **استفاده** | کرال کامل سایت | کرال صفحات خاص |

---

## 🔌 API Endpoints

### 1. شروع کرال دستی

**Endpoint:** `POST /api/v1/web-knowledge/manual-crawl/`

**Authentication:** Required (Bearer Token)

**Request Body:**
```json
{
  "website_id": "uuid-of-website",
  "urls": "https://example.com/page1\nhttps://example.com/page2\nhttps://example.com/page3"
}
```

**Parameters:**
- `website_id` (string, required): UUID وب‌سایت که صفحات به آن اضافه می‌شوند
- `urls` (string, required): لیست URLها که با خط جدید (`\n`) از هم جدا شده‌اند

**Response (202 Accepted):**
```json
{
  "success": true,
  "task_id": "celery-task-id-12345",
  "message": "Crawl started for 3 URL(s)",
  "total_urls": 3,
  "status_url": "/api/v1/web-knowledge/manual-crawl/status/celery-task-id-12345/"
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "success": false,
  "message": "website_id is required"
}
```

```json
{
  "success": false,
  "message": "urls is required (one URL per line)"
}
```

**404 Not Found:**
```json
{
  "success": false,
  "message": "Website not found or access denied"
}
```

---

### 2. بررسی وضعیت کرال

**Endpoint:** `GET /api/v1/web-knowledge/manual-crawl/status/<task_id>/`

**Authentication:** Required (Bearer Token)

**Response (200 OK):**

**در حال پردازش:**
```json
{
  "success": true,
  "status": "processing",
  "progress": 66.7,
  "pages_crawled": 2,
  "total_urls": 3,
  "message": "Crawling... 2/3 pages"
}
```

**تکمیل شده:**
```json
{
  "success": true,
  "status": "completed",
  "progress": 100.0,
  "pages_crawled": 3,
  "total_urls": 3,
  "message": "Completed: 3 pages crawled"
}
```

**خطا:**
```json
{
  "success": true,
  "status": "failed",
  "progress": 0.0,
  "pages_crawled": 0,
  "total_urls": 3,
  "message": "Task failed"
}
```

**404 Not Found:**
```json
{
  "success": false,
  "message": "Task not found"
}
```

**Status Values:**
- `processing`: در حال کرال
- `completed`: تکمیل شده
- `failed`: خطا

---

## 💻 مثال استفاده در فرانت

### React/TypeScript Example

```typescript
interface ManualCrawlRequest {
  website_id: string;
  urls: string;
}

interface ManualCrawlResponse {
  success: boolean;
  task_id: string;
  message: string;
  total_urls: number;
  status_url: string;
}

interface CrawlStatus {
  success: boolean;
  status: 'processing' | 'completed' | 'failed';
  progress: number;
  pages_crawled: number;
  total_urls: number;
  message: string;
}

// شروع کرال
async function startManualCrawl(
  websiteId: string, 
  urls: string[]
): Promise<ManualCrawlResponse> {
  const response = await fetch('/api/v1/web-knowledge/manual-crawl/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      website_id: websiteId,
      urls: urls.join('\n') // تبدیل آرایه به string با \n
    })
  });
  
  if (!response.ok) {
    throw new Error('Failed to start crawl');
  }
  
  return response.json();
}

// بررسی وضعیت
async function getCrawlStatus(taskId: string): Promise<CrawlStatus> {
  const response = await fetch(
    `/api/v1/web-knowledge/manual-crawl/status/${taskId}/`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to get status');
  }
  
  return response.json();
}

// مثال استفاده در کامپوننت
function ManualCrawlComponent() {
  const [urls, setUrls] = useState('');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<CrawlStatus | null>(null);
  const [loading, setLoading] = useState(false);
  
  const handleStartCrawl = async () => {
    setLoading(true);
    try {
      const urlsArray = urls.split('\n').filter(url => url.trim());
      const response = await startManualCrawl(websiteId, urlsArray);
      setTaskId(response.task_id);
      
      // شروع polling برای بررسی وضعیت
      pollStatus(response.task_id);
    } catch (error) {
      console.error('Error starting crawl:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const pollStatus = async (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const status = await getCrawlStatus(taskId);
        setStatus(status);
        
        // اگر تکمیل شد یا خطا داشت، polling رو متوقف کن
        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(interval);
        }
      } catch (error) {
        console.error('Error getting status:', error);
        clearInterval(interval);
      }
    }, 2000); // هر 2 ثانیه یکبار بررسی کن
    
    // بعد از 5 دقیقه polling رو متوقف کن
    setTimeout(() => clearInterval(interval), 5 * 60 * 1000);
  };
  
  return (
    <div>
      <textarea
        value={urls}
        onChange={(e) => setUrls(e.target.value)}
        placeholder="Enter URLs, one per line:&#10;https://example.com/page1&#10;https://example.com/page2"
        rows={10}
        style={{ width: '100%' }}
      />
      
      <button 
        onClick={handleStartCrawl} 
        disabled={loading || !urls.trim()}
      >
        {loading ? 'Starting...' : 'Scan'}
      </button>
      
      {status && (
        <div>
          <div>Status: {status.status}</div>
          <div>Progress: {status.progress}%</div>
          <div>{status.pages_crawled} / {status.total_urls} pages</div>
          <progress value={status.progress} max={100} />
        </div>
      )}
    </div>
  );
}
```

---

### JavaScript/Vanilla Example

```javascript
// شروع کرال
async function startManualCrawl(websiteId, urls) {
  const response = await fetch('/api/v1/web-knowledge/manual-crawl/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`
    },
    body: JSON.stringify({
      website_id: websiteId,
      urls: urls.join('\n')
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to start crawl');
  }
  
  return response.json();
}

// بررسی وضعیت
async function getCrawlStatus(taskId) {
  const response = await fetch(
    `/api/v1/web-knowledge/manual-crawl/status/${taskId}/`,
    {
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to get status');
  }
  
  return response.json();
}

// مثال استفاده
const textarea = document.getElementById('urls-input');
const scanButton = document.getElementById('scan-button');
const progressBar = document.getElementById('progress-bar');
const statusText = document.getElementById('status-text');

scanButton.addEventListener('click', async () => {
  const urls = textarea.value.split('\n').filter(url => url.trim());
  
  try {
    // شروع کرال
    const response = await startManualCrawl(websiteId, urls);
    const taskId = response.task_id;
    
    // نمایش progress bar
    progressBar.style.display = 'block';
    
    // Polling برای بررسی وضعیت
    const interval = setInterval(async () => {
      try {
        const status = await getCrawlStatus(taskId);
        
        // آپدیت progress bar
        progressBar.value = status.progress;
        statusText.textContent = `${status.pages_crawled} / ${status.total_urls} pages`;
        
        // اگر تکمیل شد
        if (status.status === 'completed') {
          clearInterval(interval);
          statusText.textContent = `✅ Completed: ${status.pages_crawled} pages crawled`;
        }
        
        // اگر خطا داشت
        if (status.status === 'failed') {
          clearInterval(interval);
          statusText.textContent = `❌ Failed: ${status.message}`;
        }
      } catch (error) {
        console.error('Error getting status:', error);
        clearInterval(interval);
      }
    }, 2000); // هر 2 ثانیه
    
  } catch (error) {
    console.error('Error starting crawl:', error);
    alert('Failed to start crawl: ' + error.message);
  }
});
```

---

## 📝 نکات مهم

### 1. فرمت URLها

- هر URL باید در یک خط جداگانه باشد
- می‌تواند با `http://` یا `https://` شروع شود
- اگر scheme نداشته باشد، به صورت خودکار `https://` اضافه می‌شود

**مثال صحیح:**
```
https://example.com/page1
https://example.com/page2
example.com/page3
```

### 2. Progress Tracking

- بعد از شروع کرال، `task_id` برگردانده می‌شود
- از `status_url` برای بررسی وضعیت استفاده کنید
- پیشنهاد: هر 2-3 ثانیه یکبار وضعیت را بررسی کنید
- وقتی `status` برابر `completed` یا `failed` شد، polling را متوقف کنید

### 3. Error Handling

- همیشه خطاها را handle کنید
- اگر `status` برابر `failed` شد، پیام خطا را به کاربر نشان دهید
- اگر task پیدا نشد (404)، احتمالاً task_id اشتباه است

### 4. Performance

- برای تعداد زیاد URL (بیش از 50)، ممکن است زمان بیشتری طول بکشد
- Progress bar را به صورت real-time آپدیت کنید
- می‌توانید timeout برای polling تنظیم کنید (مثلاً 5 دقیقه)

---

## 🎨 UI/UX پیشنهادی

### 1. Text Area

```html
<textarea
  id="urls-input"
  placeholder="Enter URLs, one per line:&#10;https://example.com/page1&#10;https://example.com/page2"
  rows="10"
  style="width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 4px;"
></textarea>
```

### 2. Progress Bar

```html
<div style="margin-top: 16px;">
  <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
    <span id="status-text">Ready to scan</span>
    <span id="progress-percent">0%</span>
  </div>
  <progress 
    id="progress-bar" 
    value="0" 
    max="100" 
    style="width: 100%; height: 8px;"
  ></progress>
</div>
```

### 3. Button States

```css
/* Normal state */
.scan-button {
  background: #2271b1;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

/* Disabled state */
.scan-button:disabled {
  background: #ccc;
  cursor: not-allowed;
  opacity: 0.6;
}

/* Loading state */
.scan-button.loading {
  background: #999;
  cursor: wait;
}
```

---

## 🔄 Flow Diagram

```
User Input URLs
      ↓
POST /manual-crawl/
      ↓
Get task_id
      ↓
Start Polling (every 2s)
      ↓
GET /manual-crawl/status/<task_id>/
      ↓
Update Progress Bar
      ↓
Status = completed? → Stop Polling → Show Success
Status = failed? → Stop Polling → Show Error
Status = processing? → Continue Polling
```

---

## 📊 مثال کامل React Component

```tsx
import React, { useState, useEffect } from 'react';

interface ManualCrawlProps {
  websiteId: string;
  onComplete?: () => void;
}

export const ManualCrawl: React.FC<ManualCrawlProps> = ({ websiteId, onComplete }) => {
  const [urls, setUrls] = useState('');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startCrawl = async () => {
    if (!urls.trim()) {
      setError('Please enter at least one URL');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/web-knowledge/manual-crawl/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          website_id: websiteId,
          urls: urls.trim()
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Failed to start crawl');
      }

      setTaskId(data.task_id);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!taskId) return;

    const interval = setInterval(async () => {
      try {
        const response = await fetch(
          `/api/v1/web-knowledge/manual-crawl/status/${taskId}/`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          }
        );

        const data = await response.json();

        if (response.ok) {
          setStatus(data);

          if (data.status === 'completed' || data.status === 'failed') {
            clearInterval(interval);
            if (data.status === 'completed' && onComplete) {
              onComplete();
            }
          }
        }
      } catch (err) {
        console.error('Error getting status:', err);
        clearInterval(interval);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [taskId, onComplete]);

  return (
    <div style={{ padding: '20px' }}>
      <h2>Add Web Page Manually</h2>
      <p style={{ color: '#666', marginBottom: '16px' }}>
        Enter the URLs of your web pages one per line and press Enter after each. 
        Fiko will automatically crawl and save the content of all listed pages.
      </p>

      <div style={{ marginBottom: '16px' }}>
        <label htmlFor="urls-input" style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
          Add your website
        </label>
        <textarea
          id="urls-input"
          value={urls}
          onChange={(e) => setUrls(e.target.value)}
          placeholder="https://example.com/page1&#10;https://example.com/page2"
          rows={10}
          style={{
            width: '100%',
            padding: '12px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            fontFamily: 'monospace',
            fontSize: '14px'
          }}
          disabled={loading || !!taskId}
        />
      </div>

      {error && (
        <div style={{
          padding: '12px',
          background: '#fee',
          border: '1px solid #fcc',
          borderRadius: '4px',
          marginBottom: '16px',
          color: '#c33'
        }}>
          {error}
        </div>
      )}

      <button
        onClick={startCrawl}
        disabled={loading || !urls.trim() || !!taskId}
        style={{
          background: taskId ? '#999' : '#2271b1',
          color: 'white',
          padding: '10px 20px',
          border: 'none',
          borderRadius: '4px',
          cursor: taskId ? 'not-allowed' : 'pointer',
          opacity: (loading || !urls.trim() || !!taskId) ? 0.6 : 1
        }}
      >
        {loading ? 'Starting...' : taskId ? 'Scanning...' : 'Scan'}
      </button>

      {status && (
        <div style={{ marginTop: '24px' }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginBottom: '8px',
            fontSize: '14px',
            color: '#666'
          }}>
            <span>{status.message}</span>
            <span>{status.progress.toFixed(1)}%</span>
          </div>
          <progress
            value={status.progress}
            max={100}
            style={{
              width: '100%',
              height: '8px',
              borderRadius: '4px'
            }}
          />
          {status.status === 'completed' && (
            <div style={{
              marginTop: '12px',
              padding: '12px',
              background: '#dfd',
              border: '1px solid #9c9',
              borderRadius: '4px',
              color: '#363'
            }}>
              ✅ Successfully crawled {status.pages_crawled} page(s)
            </div>
          )}
          {status.status === 'failed' && (
            <div style={{
              marginTop: '12px',
              padding: '12px',
              background: '#fee',
              border: '1px solid #fcc',
              borderRadius: '4px',
              color: '#c33'
            }}>
              ❌ Failed: {status.message}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
```

---

## ✅ Checklist برای پیاده‌سازی

- [ ] Text area برای ورودی URLها
- [ ] دکمه "Scan" برای شروع کرال
- [ ] Progress bar برای نمایش پیشرفت
- [ ] نمایش درصد پیشرفت
- [ ] نمایش تعداد صفحات کرال شده
- [ ] Polling برای بررسی وضعیت (هر 2-3 ثانیه)
- [ ] Handle کردن خطاها
- [ ] نمایش پیام موفقیت/خطا
- [ ] Disable کردن دکمه در حین کرال
- [ ] نمایش وضعیت real-time

---

---

## 🗑️ Bulk Delete API

### 1. Bulk Delete Pages (Website Knowledge)

**Endpoint:** `POST /api/v1/web-knowledge/pages/bulk-delete/`

**Authentication:** Required (Bearer Token)

**Request Body:**
```json
{
  "page_ids": [
    "uuid-1",
    "uuid-2",
    "uuid-3"
  ]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "3 page(s) and 15 Q&A pair(s) deleted successfully",
  "deleted_count": 3,
  "qa_pairs_deleted": 15,
  "deleted_pages": [
    {
      "id": "uuid-1",
      "title": "Page Title 1",
      "url": "https://example.com/page1",
      "qa_pairs_count": 5
    },
    {
      "id": "uuid-2",
      "title": "Page Title 2",
      "url": "https://example.com/page2",
      "qa_pairs_count": 10
    }
  ]
}
```

**نکته مهم:** وقتی صفحات پاک می‌شن، chunks مربوطه هم به صورت خودکار از TenantKnowledge پاک می‌شن (via `pre_delete` signal).

---

### 2. Bulk Delete Products

**Endpoint:** `POST /api/v1/web-knowledge/products/bulk-delete/`

**Authentication:** Required (Bearer Token)

**Request Body:**
```json
{
  "product_ids": [
    "uuid-1",
    "uuid-2",
    "uuid-3"
  ]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "3 products deleted successfully",
  "deleted_count": 3,
  "deleted_products": [
    {
      "id": "uuid-1",
      "title": "Product 1",
      "product_type": "product"
    },
    {
      "id": "uuid-2",
      "title": "Product 2",
      "product_type": "service"
    }
  ]
}
```

**نکته مهم:** وقتی محصولات پاک می‌شن، chunks مربوطه هم به صورت خودکار از TenantKnowledge پاک می‌شن (via `pre_delete` signal).

---

### 3. Bulk Delete Q&A Pairs (FAQ)

**Endpoint:** `POST /api/v1/web-knowledge/qa-pairs/bulk_delete/`

**Authentication:** Required (Bearer Token)

**Request Body:**
```json
{
  "qa_pair_ids": [
    "uuid-1",
    "uuid-2",
    "uuid-3"
  ]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "3 Q&A pairs deleted successfully",
  "deleted_count": 3,
  "deleted_qa_pairs": [
    {
      "id": "uuid-1",
      "question": "Question 1?",
      "page_title": "Page Title",
      "website_name": "Website Name"
    },
    {
      "id": "uuid-2",
      "question": "Question 2?",
      "page_title": "Page Title 2",
      "website_name": "Website Name"
    }
  ]
}
```

**نکته مهم:** وقتی Q&A pairs پاک می‌شن، chunks مربوطه هم به صورت خودکار از TenantKnowledge پاک می‌شن (via `pre_delete` signal).

---

## 🔄 Automatic Chunk Cleanup

### نحوه کار:

وقتی یک آیتم (Product, Page, Q&A) پاک می‌شه:

1. **Signal Trigger:** `pre_delete` signal فعال می‌شه (قبل از پاک شدن از دیتابیس)
2. **Chunk Cleanup:** تمام chunks مربوطه از `TenantKnowledge` پاک می‌شن
3. **Database Delete:** آیتم از دیتابیس پاک می‌شه

### کد Signal:

```python
# در src/AI_model/signals.py

@receiver(pre_delete, sender='web_knowledge.Product')
def on_product_deleted_cleanup_chunks(sender, instance, **kwargs):
    """Delete chunks BEFORE Product is deleted"""
    TenantKnowledge.objects.filter(
        source_id=instance.id,
        chunk_type='product'
    ).delete()

@receiver(pre_delete, sender='web_knowledge.WebsitePage')
def on_webpage_deleted_cleanup_chunks(sender, instance, **kwargs):
    """Delete chunks BEFORE WebPage is deleted"""
    TenantKnowledge.objects.filter(
        source_id=instance.id,
        chunk_type='website'
    ).delete()

@receiver(pre_delete, sender='web_knowledge.QAPair')
def on_qapair_deleted_cleanup_chunks(sender, instance, **kwargs):
    """Delete chunks BEFORE QAPair is deleted"""
    TenantKnowledge.objects.filter(
        source_id=instance.id,
        chunk_type='faq'
    ).delete()
```

### اطمینان از Cleanup:

- ✅ **pre_delete signal:** استفاده از `pre_delete` به جای `post_delete` تا قبل از پاک شدن از دیتابیس، chunks پاک بشن
- ✅ **Bulk Delete:** در bulk delete هم signals برای هر آیتم فعال می‌شن
- ✅ **Automatic:** نیازی به کار دستی نیست - همه چیز خودکار انجام می‌شه

---

## 💻 مثال استفاده در فرانت

### React Component برای Bulk Delete

```tsx
import React, { useState } from 'react';

interface BulkDeleteProps {
  type: 'pages' | 'products' | 'qa-pairs';
  selectedIds: string[];
  onSuccess?: () => void;
}

export const BulkDeleteButton: React.FC<BulkDeleteProps> = ({ 
  type, 
  selectedIds, 
  onSuccess 
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) {
      setError('Please select at least one item');
      return;
    }

    if (!confirm(`Are you sure you want to delete ${selectedIds.length} item(s)?`)) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // تعیین endpoint بر اساس type
      const endpoint = {
        'pages': '/api/v1/web-knowledge/pages/bulk-delete/',
        'products': '/api/v1/web-knowledge/products/bulk-delete/',
        'qa-pairs': '/api/v1/web-knowledge/qa-pairs/bulk_delete/'
      }[type];

      const fieldName = {
        'pages': 'page_ids',
        'products': 'product_ids',
        'qa-pairs': 'qa_pair_ids'
      }[type];

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          [fieldName]: selectedIds
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || data.message || 'Failed to delete');
      }

      // Success
      alert(`✅ ${data.message}`);
      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button
        onClick={handleBulkDelete}
        disabled={loading || selectedIds.length === 0}
        style={{
          background: '#dc2626',
          color: 'white',
          padding: '8px 16px',
          border: 'none',
          borderRadius: '4px',
          cursor: loading ? 'not-allowed' : 'pointer',
          opacity: (loading || selectedIds.length === 0) ? 0.6 : 1
        }}
      >
        {loading ? 'Deleting...' : `Delete Selected (${selectedIds.length})`}
      </button>
      
      {error && (
        <div style={{
          marginTop: '8px',
          padding: '8px',
          background: '#fee',
          border: '1px solid #fcc',
          borderRadius: '4px',
          color: '#c33'
        }}>
          {error}
        </div>
      )}
    </div>
  );
};
```

### مثال استفاده در لیست:

```tsx
function PagesList() {
  const [pages, setPages] = useState([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(pages.map((p: any) => p.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectItem = (id: string, checked: boolean) => {
    if (checked) {
      setSelectedIds([...selectedIds, id]);
    } else {
      setSelectedIds(selectedIds.filter(i => i !== id));
    }
  };

  const handleBulkDeleteSuccess = () => {
    // Refresh list
    fetchPages();
    setSelectedIds([]);
  };

  return (
    <div>
      {/* Select All Checkbox */}
      <label>
        <input
          type="checkbox"
          checked={selectedIds.length === pages.length && pages.length > 0}
          onChange={(e) => handleSelectAll(e.target.checked)}
        />
        Select All
      </label>

      {/* Bulk Delete Button */}
      {selectedIds.length > 0 && (
        <BulkDeleteButton
          type="pages"
          selectedIds={selectedIds}
          onSuccess={handleBulkDeleteSuccess}
        />
      )}

      {/* List */}
      {pages.map((page: any) => (
        <div key={page.id}>
          <input
            type="checkbox"
            checked={selectedIds.includes(page.id)}
            onChange={(e) => handleSelectItem(page.id, e.target.checked)}
          />
          <span>{page.title}</span>
        </div>
      ))}
    </div>
  );
}
```

---

## 🎨 مثال کامل React/TypeScript برای Bulk Selection و Delete

### 1. Products Component با Bulk Delete

```tsx
import React, { useState, useEffect } from 'react';

interface Product {
  id: string;
  title: string;
  product_type: string;
  price: number;
  currency: string;
  description: string;
}

const ProductsPage: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [selectAll, setSelectAll] = useState(false);

  // بارگذاری محصولات
  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      const response = await fetch('/api/v1/web-knowledge/products/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setProducts(data.results || []);
    } catch (error) {
      console.error('Error loading products:', error);
    }
  };

  // انتخاب/لغو انتخاب یک آیتم
  const toggleSelect = (id: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
    setSelectAll(newSelected.size === products.length);
  };

  // انتخاب/لغو انتخاب همه
  const toggleSelectAll = () => {
    if (selectAll) {
      setSelectedIds(new Set());
      setSelectAll(false);
    } else {
      setSelectedIds(new Set(products.map(p => p.id)));
      setSelectAll(true);
    }
  };

  // Bulk Delete
  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) return;

    const confirmMessage = `آیا مطمئن هستید که می‌خواهید ${selectedIds.size} محصول را پاک کنید؟`;
    if (!window.confirm(confirmMessage)) return;

    setLoading(true);
    try {
      const response = await fetch('/api/v1/web-knowledge/products/bulk-delete/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          product_ids: Array.from(selectedIds)
        })
      });

      const data = await response.json();
      
      if (data.success) {
        alert(`✅ ${data.deleted_count} محصول با موفقیت پاک شد`);
        setSelectedIds(new Set());
        setSelectAll(false);
        loadProducts(); // Refresh لیست
      } else {
        alert(`❌ خطا: ${data.error || 'خطای نامشخص'}`);
      }
    } catch (error) {
      console.error('Error deleting products:', error);
      alert('❌ خطا در پاک کردن محصولات');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="products-page">
      {/* Header با Bulk Actions */}
      <div className="page-header">
        <h1>محصولات</h1>
        {selectedIds.size > 0 && (
          <div className="bulk-actions">
            <span className="selected-count">
              {selectedIds.size} مورد انتخاب شده
            </span>
            <button 
              onClick={handleBulkDelete}
              disabled={loading}
              className="btn btn-danger"
            >
              {loading ? 'در حال پاک کردن...' : `پاک کردن ${selectedIds.size} مورد`}
            </button>
          </div>
        )}
      </div>

      {/* لیست محصولات */}
      <div className="products-grid">
        {/* Select All Checkbox */}
        <div className="select-all-row">
          <label>
            <input
              type="checkbox"
              checked={selectAll}
              onChange={toggleSelectAll}
            />
            <span>انتخاب همه</span>
          </label>
        </div>

        {/* Product Cards */}
        {products.map(product => (
          <div key={product.id} className="product-card">
            <div className="product-checkbox">
              <input
                type="checkbox"
                checked={selectedIds.has(product.id)}
                onChange={() => toggleSelect(product.id)}
              />
            </div>
            <div className="product-content">
              <h3>{product.title}</h3>
              <p className="product-type">{product.product_type}</p>
              <p className="product-price">
                {product.price.toLocaleString('fa-IR')} {product.currency}
              </p>
              <p className="product-description">{product.description}</p>
            </div>
            <div className="product-actions">
              <button className="btn-icon" title="ویرایش">
                ✏️
              </button>
              <button 
                className="btn-icon btn-delete" 
                title="حذف"
                onClick={() => toggleSelect(product.id)}
              >
                🗑️
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProductsPage;
```

### 2. Q&A Pairs Component با Bulk Delete

```tsx
import React, { useState, useEffect } from 'react';

interface QAPair {
  id: string;
  question: string;
  answer: string;
  category: string;
  confidence_score: number;
}

const QAPairsPage: React.FC = () => {
  const [qaPairs, setQAPairs] = useState<QAPair[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadQAPairs();
  }, []);

  const loadQAPairs = async () => {
    try {
      const response = await fetch('/api/v1/web-knowledge/qa-pairs/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setQAPairs(data.results || []);
    } catch (error) {
      console.error('Error loading Q&A pairs:', error);
    }
  };

  const toggleSelect = (id: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) return;

    if (!window.confirm(`آیا مطمئن هستید که می‌خواهید ${selectedIds.size} سوال و جواب را پاک کنید؟`)) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/v1/web-knowledge/qa-pairs/bulk_delete/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          qa_pair_ids: Array.from(selectedIds)
        })
      });

      const data = await response.json();
      
      if (data.success) {
        alert(`✅ ${data.deleted_count} سوال و جواب با موفقیت پاک شد`);
        setSelectedIds(new Set());
        loadQAPairs();
      } else {
        alert(`❌ خطا: ${data.error || 'خطای نامشخص'}`);
      }
    } catch (error) {
      console.error('Error deleting Q&A pairs:', error);
      alert('❌ خطا در پاک کردن سوال و جواب‌ها');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="qa-pairs-page">
      <div className="page-header">
        <h1>سوال و جواب‌ها</h1>
        {selectedIds.size > 0 && (
          <button 
            onClick={handleBulkDelete}
            disabled={loading}
            className="btn btn-danger"
          >
            {loading ? 'در حال پاک کردن...' : `پاک کردن ${selectedIds.size} مورد`}
          </button>
        )}
      </div>

      <div className="qa-list">
        {qaPairs.map(qa => (
          <div key={qa.id} className="qa-item">
            <input
              type="checkbox"
              checked={selectedIds.has(qa.id)}
              onChange={() => toggleSelect(qa.id)}
              className="qa-checkbox"
            />
            <div className="qa-content">
              <h4>{qa.question}</h4>
              <p>{qa.answer}</p>
              <div className="qa-meta">
                <span className="badge">{qa.category}</span>
                <span>Confidence: {qa.confidence_score * 100}%</span>
              </div>
            </div>
            <div className="qa-actions">
              <button className="btn-icon">✏️</button>
              <button 
                className="btn-icon btn-delete"
                onClick={() => toggleSelect(qa.id)}
              >
                🗑️
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default QAPairsPage;
```

### 3. Pages Component با Bulk Delete

```tsx
const PagesPage: React.FC = () => {
  const [pages, setPages] = useState<Page[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);

  // ... مشابه Products

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) return;

    if (!window.confirm(`آیا مطمئن هستید که می‌خواهید ${selectedIds.size} صفحه را پاک کنید؟`)) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/v1/web-knowledge/pages/bulk-delete/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          page_ids: Array.from(selectedIds)
        })
      });

      const data = await response.json();
      
      if (data.success) {
        alert(`✅ ${data.deleted_count} صفحه با موفقیت پاک شد`);
        setSelectedIds(new Set());
        loadPages();
      }
    } catch (error) {
      console.error('Error deleting pages:', error);
      alert('❌ خطا در پاک کردن صفحات');
    } finally {
      setLoading(false);
    }
  };

  // ... بقیه کد
};
```

### 4. CSS برای Bulk Selection UI

```css
/* Bulk Actions */
.bulk-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #fef3c7;
  border-radius: 8px;
  margin-bottom: 16px;
}

.selected-count {
  font-weight: 600;
  color: #92400e;
}

/* Product Card با Checkbox */
.product-card {
  position: relative;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.product-card:hover {
  border-color: #e5e7eb;
}

.product-card.selected {
  border-color: #3b82f6;
  background: #eff6ff;
}

.product-checkbox {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 10;
}

.product-checkbox input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

/* Q&A Item با Checkbox */
.qa-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 12px;
  transition: all 0.2s;
}

.qa-item:hover {
  background: #f9fafb;
}

.qa-item.selected {
  background: #eff6ff;
  border-color: #3b82f6;
}

.qa-checkbox {
  margin-top: 4px;
  cursor: pointer;
}

/* Select All Row */
.select-all-row {
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  margin-bottom: 16px;
}

.select-all-row label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-weight: 600;
}
```

## ✅ Checklist برای پیاده‌سازی

- [x] API برای Bulk Delete آماده است
- [ ] Checkbox برای انتخاب آیتم‌ها در Frontend
- [ ] "Select All" checkbox
- [ ] دکمه "Delete Selected" (فقط وقتی آیتمی انتخاب شده)
- [ ] Confirmation dialog قبل از پاک کردن
- [ ] Loading state در حین پاک کردن
- [ ] نمایش پیام موفقیت/خطا
- [ ] Refresh لیست بعد از پاک کردن موفق
- [ ] Clear selection بعد از پاک کردن

---

## 🔗 لینک‌های مرتبط

- [Web Knowledge API Documentation](./WEB_KNOWLEDGE_API.md)
- [Website Crawling Guide](./WEBSITE_CRAWLING_GUIDE.md)

