# Instagram Comment Action API Documentation

## Overview
این document برای تیم Frontend است که نحوه ذخیره Instagram Action Node را توضیح می‌دهد.

## ⚠️ نکته مهم برای Frontend
**همیشه `instagram_public_reply_enabled: true` بفرستید!**

وقتی کاربر متن Reply را وارد کرده، باید این فیلد **حتماً** `true` باشد، وگرنه Reply ارسال نمی‌شود.

---

## API Endpoints

### Create/Update Action Node
```
POST   /api/workflow/action-nodes/
PUT    /api/workflow/action-nodes/{id}/
PATCH  /api/workflow/action-nodes/{id}/
```

یا از Unified endpoint:
```
POST   /api/workflow/nodes/
PUT    /api/workflow/nodes/{id}/
PATCH  /api/workflow/nodes/{id}/
```

---

## Request Body Structure

### برای Instagram Comment Action

```json
{
  "workflow": "workflow-uuid-here",
  "node_type": "action",
  "action_type": "instagram_comment_dm_reply",
  "title": "Send DM and Reply",
  "position": {
    "x": 400,
    "y": 200
  },
  
  // ✅ Instagram Action Fields
  "instagram_dm_mode": "STATIC",  // یا "PRODUCT"
  "instagram_dm_text_template": "سلام {{username}}! ممنون از کامنتت 😊",
  "instagram_product_id": null,  // اگر PRODUCT mode, UUID محصول
  
  // ⚠️ این دو فیلد مهم هستند!
  "instagram_public_reply_enabled": true,  // ✅ همیشه true بفرستید اگر reply می‌خواهید
  "instagram_public_reply_text": "ممنون از نظرت 🙏"
}
```

---

## Field Descriptions

### Required Fields
| Field | Type | Description |
|-------|------|-------------|
| `workflow` | UUID | شناسه workflow |
| `node_type` | string | باید `"action"` باشد |
| `action_type` | string | باید `"instagram_comment_dm_reply"` باشد |

### Instagram Action Fields
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `instagram_dm_mode` | string | Yes | `"STATIC"` | نوع DM: `"STATIC"` یا `"PRODUCT"` |
| `instagram_dm_text_template` | string | Yes (for STATIC) | `""` | متن DM (supports template variables) |
| `instagram_product_id` | UUID | Yes (for PRODUCT) | `null` | شناسه محصول برای حالت PRODUCT |
| `instagram_public_reply_enabled` | **boolean** | **No** | **`false`** | ⚠️ **فعال‌سازی Reply - باید `true` باشد!** |
| `instagram_public_reply_text` | string | No | `""` | متن Reply عمومی |

---

## ⚠️ مشکل رایج و راه‌حل

### مشکل:
کاربر متن Reply را وارد می‌کند ولی **Reply ارسال نمی‌شود**.

### علت:
```json
{
  "instagram_public_reply_enabled": false,  // ❌ این false است!
  "instagram_public_reply_text": "ممنون از نظرت"
}
```

### راه‌حل:
**Frontend باید همیشه این را `true` بفرستد:**

```json
{
  "instagram_public_reply_enabled": true,   // ✅ اینجا true کنید!
  "instagram_public_reply_text": "ممنون از نظرت"
}
```

---

## Template Variables

در `instagram_dm_text_template` و `instagram_public_reply_text` می‌توانید از این متغیرها استفاده کنید:

| Variable | Description | Example |
|----------|-------------|---------|
| `{{username}}` | نام کاربری Instagram کاربر | `ataei.ca` |
| `{{comment_text}}` | متن کامنت | `عالیه!` |
| `{{product_name}}` | نام محصول (فقط در PRODUCT mode) | `اشتراک ماهانه` |

### مثال:
```
متن DM: "سلام {{username}} عزیز! ممنون که «{{comment_text}}» گذاشتی 😊"

خروجی: "سلام ataei.ca عزیز! ممنون که «عالیه!» گذاشتی 😊"
```

---

## Response Structure

```json
{
  "id": "08d39508-efa7-4f69-bacc-bfbd177871a2",
  "workflow": "33d2eed6-c481-4b4e-8418-af322f6cdfbd",
  "node_type": "action",
  "action_type": "instagram_comment_dm_reply",
  "action_type_display": "Instagram Comment → DM + Reply",
  "title": "Send DM and Reply",
  "position": {"x": 400, "y": 200},
  
  "instagram_dm_mode": "STATIC",
  "instagram_dm_text_template": "سلام {{username}}!",
  "instagram_product_id": null,
  "instagram_public_reply_enabled": true,
  "instagram_public_reply_text": "ممنون از نظرت 🙏",
  
  // Legacy compatibility
  "config": {
    "dm_mode": "STATIC",
    "dm_text_template": "سلام {{username}}!",
    "product_id": null,
    "public_reply_enabled": true,
    "public_reply_template": "ممنون از نظرت 🙏"
  },
  
  "created_at": "2025-11-23T08:00:00Z",
  "updated_at": "2025-11-23T08:30:00Z"
}
```

---

## مثال‌های کامل

### مثال 1: Static DM + Reply
```json
{
  "workflow": "33d2eed6-c481-4b4e-8418-af322f6cdfbd",
  "node_type": "action",
  "action_type": "instagram_comment_dm_reply",
  "title": "Welcome Message",
  "position": {"x": 400, "y": 200},
  
  "instagram_dm_mode": "STATIC",
  "instagram_dm_text_template": "سلام {{username}} عزیز! 😊\n\nممنون از کامنتت. برای اطلاعات بیشتر به DM ما سر بزن.",
  "instagram_product_id": null,
  
  "instagram_public_reply_enabled": true,
  "instagram_public_reply_text": "ممنون {{username}} جان! 🙏 جواب کامل رو تو DM فرستادیم 💌"
}
```

### مثال 2: Product-based DM (با AI) + Reply
```json
{
  "workflow": "33d2eed6-c481-4b4e-8418-af322f6cdfbd",
  "node_type": "action",
  "action_type": "instagram_comment_dm_reply",
  "title": "Product Introduction",
  "position": {"x": 400, "y": 200},
  
  "instagram_dm_mode": "PRODUCT",
  "instagram_dm_text_template": "",  // در حالت PRODUCT، AI متن را می‌سازد
  "instagram_product_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  
  "instagram_public_reply_enabled": true,
  "instagram_public_reply_text": "سلام {{username}}! 🎉 اطلاعات {{product_name}} رو براتون تو DM فرستادیم 📦"
}
```

### مثال 3: فقط DM (بدون Reply)
```json
{
  "workflow": "33d2eed6-c481-4b4e-8418-af322f6cdfbd",
  "node_type": "action",
  "action_type": "instagram_comment_dm_reply",
  "title": "DM Only",
  "position": {"x": 400, "y": 200},
  
  "instagram_dm_mode": "STATIC",
  "instagram_dm_text_template": "سلام! این یک پیام خصوصی است.",
  "instagram_product_id": null,
  
  "instagram_public_reply_enabled": false,  // ✅ اینجا false باشد
  "instagram_public_reply_text": ""
}
```

---

## نکات مهم برای Frontend Developers

### 1. ✅ همیشه `instagram_public_reply_enabled` را چک کنید
```javascript
// ❌ اشتباه
const payload = {
  instagram_public_reply_text: replyText,
  // instagram_public_reply_enabled نداریم!
};

// ✅ درست
const payload = {
  instagram_public_reply_text: replyText,
  instagram_public_reply_enabled: !!replyText, // اگر متن داریم = true
};
```

### 2. ✅ Validation در Frontend
```javascript
if (formData.instagram_public_reply_text && !formData.instagram_public_reply_enabled) {
  console.warn('⚠️ Reply text exists but reply is not enabled!');
  formData.instagram_public_reply_enabled = true; // Auto-fix
}
```

### 3. ✅ UI Suggestion
به جای Checkbox جداگانه برای "Enable Reply"، می‌توانید:
- اگر textarea پر شد → خودکار `enabled: true`
- اگر textarea خالی شد → خودکار `enabled: false`

```javascript
const handleReplyTextChange = (text) => {
  setReplyText(text);
  setReplyEnabled(text.trim().length > 0); // Auto-enable
};
```

---

## حالت‌های مختلف DM Mode

### STATIC Mode
- متن DM را کاربر می‌نویسد
- از template variables استفاده می‌کند
- سریع‌تر و ساده‌تر

### PRODUCT Mode
- AI بر اساس محصول انتخابی، متن DM را می‌سازد
- باید `instagram_product_id` تنظیم شود
- کندتر (چون AI می‌سازد) ولی هوشمندتر

---

## Error Handling

### خطاهای رایج

| خطا | دلیل | راه‌حل |
|-----|------|--------|
| `dm_mode required` | فیلد `instagram_dm_mode` نفرستاده شده | مقدار `STATIC` یا `PRODUCT` بفرستید |
| `dm_text_template required for STATIC` | در حالت STATIC، متن DM خالی است | متن DM را بفرستید |
| `product_id required for PRODUCT` | در حالت PRODUCT، محصول انتخاب نشده | UUID محصول را بفرستید |
| Reply not sending | `instagram_public_reply_enabled` = `false` | به `true` تغییر دهید |

---

## Testing

### Test Case 1: ✅ DM + Reply کار کند
```bash
curl -X POST https://api.pilito.com/api/workflow/action-nodes/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow": "workflow-id",
    "node_type": "action",
    "action_type": "instagram_comment_dm_reply",
    "instagram_dm_mode": "STATIC",
    "instagram_dm_text_template": "Test DM",
    "instagram_public_reply_enabled": true,
    "instagram_public_reply_text": "Test Reply"
  }'
```

انتظار: در لاگ workflow execution باید ببینید:
```json
{
  "success": true,
  "dm_sent": true,
  "reply_sent": true
}
```

### Test Case 2: ❌ Reply کار نکند
```bash
# اگر instagram_public_reply_enabled = false
{
  "success": true,
  "dm_sent": true,
  "reply_sent": false  // ❌
}
```

---

## Monitoring & Debugging

### چک کردن Workflow Execution
```bash
GET /api/workflow/workflow-executions/?workflow=<workflow-id>&ordering=-created_at
```

### چک کردن لاگ‌ها
در celery worker logs:
```
[InstagramCommentAction] Completed: {'success': True, 'dm_sent': True, 'reply_sent': True}
```

اگر `reply_sent: False` بود، چک کنید:
1. `instagram_public_reply_enabled` چیست؟
2. `instagram_public_reply_text` پر است؟

---

## Summary برای Frontend

| موضوع | راه‌حل |
|-------|--------|
| **API Endpoint** | `POST /api/workflow/action-nodes/` |
| **Action Type** | `instagram_comment_dm_reply` |
| **فیلد مهم** | `instagram_public_reply_enabled: true` |
| **قاعده کلی** | اگر متن Reply داریم → `enabled: true` |
| **Validation** | `if (replyText) { enabled = true; }` |
| **UI Suggestion** | Checkbox را حذف کنید، خودکار enable کنید |

---

## Questions?

اگر سوالی داشتید، به Backend تیم مراجعه کنید یا این document را update کنید.

**نویسنده:** Backend Team  
**تاریخ:** 2025-11-23  
**نسخه:** 1.0

