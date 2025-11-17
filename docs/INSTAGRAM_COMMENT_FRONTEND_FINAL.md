# 📱 راهنمای فرانت - پاسخ به کامنت اینستاگرام (نسخه نهایی)

---

## 🎯 خلاصه برای شروع سریع

شما باید در **Visual Workflow Builder** (Node-Based) این کار را انجام دهید:

### 1️⃣ در بخش When Nodes:
یک نوع جدید اضافه کنید:
```typescript
when_type: 'instagram_comment'  // حروف کوچک
label: 'کامنت اینستاگرام'
```

### 2️⃣ در بخش Action Nodes:
یک نوع جدید اضافه کنید:
```typescript
action_type: 'instagram_comment_dm_reply'
label: 'پاسخ به کامنت (DM + Reply)'
```

---

## 📋 API Endpoints صحیح

### محصولات:
```http
GET /api/v1/web-knowledge/products/
GET /api/v1/web-knowledge/products/?search=query
```

### Workflows (Node-Based):
```http
GET  /api/v1/workflow/api/node-workflows/
POST /api/v1/workflow/api/node-workflows/
GET  /api/v1/workflow/api/node-workflows/{id}/
PUT  /api/v1/workflow/api/node-workflows/{id}/
```

### When Nodes:
```http
GET  /api/v1/workflow/api/when-nodes/
POST /api/v1/workflow/api/when-nodes/
```

### Action Nodes:
```http
GET  /api/v1/workflow/api/action-nodes/
POST /api/v1/workflow/api/action-nodes/
```

---

## 🎨 UI Components

### الف) When Node Selector

در فایل مربوط به When Node selection (مثلاً `WhenNodeSelector.tsx`):

```typescript
const whenTypes = [
  { 
    value: 'receive_message', 
    label: 'دریافت پیام',
    icon: '💬'
  },
  { 
    value: 'add_tag', 
    label: 'افزودن تگ',
    icon: '🏷️'
  },
  { 
    value: 'new_customer', 
    label: 'مشتری جدید',
    icon: '👤'
  },
  { 
    value: 'scheduled', 
    label: 'زمان‌بندی شده',
    icon: '⏰'
  },
  // ✅ این را اضافه کنید:
  { 
    value: 'instagram_comment', 
    label: 'کامنت اینستاگرام',
    icon: '💬',
    badge: 'جدید',
    platforms: ['instagram']  // فقط برای کانال‌های اینستاگرام
  },
];
```

---

### ب) Action Node Selector

در فایل مربوط به Action Node selection:

```typescript
const actionTypes = [
  { 
    value: 'send_message', 
    label: 'ارسال پیام',
    icon: '✉️'
  },
  { 
    value: 'delay', 
    label: 'تأخیر',
    icon: '⏱️'
  },
  // ✅ این را اضافه کنید:
  { 
    value: 'instagram_comment_dm_reply', 
    label: 'پاسخ به کامنت اینستاگرام',
    description: 'ارسال DM + پاسخ عمومی',
    icon: '📱',
    badge: 'جدید',
    platforms: ['instagram']
  },
];
```

---

### ج) Config Form برای Action

وقتی `action_type === 'instagram_comment_dm_reply'`:

```tsx
{actionType === 'instagram_comment_dm_reply' && (
  <div className="config-form">
    
    {/* 1. نوع DM */}
    <FormGroup>
      <Label>نوع پیام دایرکت *</Label>
      <ButtonGroup>
        <Button
          active={config.dm_mode === 'STATIC'}
          onClick={() => setConfig({...config, dm_mode: 'STATIC'})}
        >
          📝 متن ثابت
        </Button>
        <Button
          active={config.dm_mode === 'PRODUCT'}
          onClick={() => setConfig({...config, dm_mode: 'PRODUCT'})}
        >
          🛍️ معرفی محصول (AI)
        </Button>
      </ButtonGroup>
    </FormGroup>
    
    {/* 2. متن ثابت */}
    {config.dm_mode === 'STATIC' && (
      <FormGroup>
        <Label>متن دایرکت *</Label>
        <Textarea
          value={config.dm_text_template}
          onChange={(e) => setConfig({...config, dm_text_template: e.target.value})}
          placeholder="سلام {{username}}! 👋&#10;&#10;[[CTA:سایت ما|https://example.com]]"
          maxLength={1000}
        />
        <FormText>
          متغیرها: <code>{'{{username}}'}</code>, <code>{'{{comment_text}}'}</code>, <code>{'{{post_url}}'}</code>
          <br/>
          دکمه CTA: <code>[[CTA:عنوان|URL]]</code> (حداکثر 3)
        </FormText>
      </FormGroup>
    )}
    
    {/* 3. انتخاب محصول */}
    {config.dm_mode === 'PRODUCT' && (
      <FormGroup>
        <Label>انتخاب محصول *</Label>
        <AsyncSelect
          loadOptions={loadProducts}
          value={config.product}
          onChange={(p) => setConfig({...config, product_id: p.value})}
        />
        <FormText>
          🤖 AI بر اساس کامنت و اطلاعات محصول، متن را خودکار می‌سازد
        </FormText>
      </FormGroup>
    )}
    
    {/* 4. پاسخ عمومی */}
    <FormGroup>
      <div className="d-flex justify-content-between">
        <Label>پاسخ عمومی (اختیاری)</Label>
        <Switch
          checked={config.public_reply_enabled}
          onChange={(v) => setConfig({...config, public_reply_enabled: v})}
        />
      </div>
      {config.public_reply_enabled && (
        <Textarea
          value={config.public_reply_template}
          onChange={(e) => setConfig({...config, public_reply_template: e.target.value})}
          placeholder="{{username}} عزیز، پیام دادیم! 💌"
          maxLength={300}
        />
      )}
    </FormGroup>
    
  </div>
)}
```

---

## 📦 Data Structure

### ساخت Workflow جدید:

```typescript
const workflowPayload = {
  name: "پاسخ به کامنت‌های محصول",
  description: "ارسال خودکار دایرکت",
  workflow_type: "node_based",  // مهم!
  nodes: [
    {
      node_type: "when",
      when_type: "instagram_comment",  // ✅ حروف کوچک
      title: "کامنت اینستاگرام",
      position_x: 100,
      position_y: 100,
      configuration: {}
    },
    {
      node_type: "action",
      action_type: "instagram_comment_dm_reply",  // ✅
      title: "ارسال DM و Reply",
      position_x: 300,
      position_y: 100,
      configuration: {
        dm_mode: "PRODUCT",
        product_id: "uuid-here",
        public_reply_enabled: true,
        public_reply_template: "پیام دادیم! 💌"
      }
    }
  ],
  connections: [
    {
      from_node: "when_node_uuid",
      to_node: "action_node_uuid"
    }
  ]
};

// ارسال به API
await axios.post('/api/v1/workflow/api/node-workflows/', workflowPayload);
```

---

## ✅ Validation Rules

```typescript
const validateConfig = (config) => {
  const errors = {};
  
  if (!config.dm_mode) {
    errors.dm_mode = 'نوع DM اجباری است';
  }
  
  if (config.dm_mode === 'STATIC') {
    if (!config.dm_text_template?.trim()) {
      errors.dm_text_template = 'متن دایرکت اجباری است';
    }
    if (config.dm_text_template?.length > 1000) {
      errors.dm_text_template = 'حداکثر 1000 کاراکتر';
    }
    // بررسی تعداد CTA
    const ctaCount = (config.dm_text_template?.match(/\[\[CTA:/g) || []).length;
    if (ctaCount > 3) {
      errors.dm_text_template = 'حداکثر 3 دکمه CTA';
    }
  }
  
  if (config.dm_mode === 'PRODUCT') {
    if (!config.product_id) {
      errors.product_id = 'محصول را انتخاب کنید';
    }
  }
  
  if (config.public_reply_enabled) {
    if (!config.public_reply_template?.trim()) {
      errors.public_reply_template = 'متن پاسخ عمومی اجباری است';
    }
    if (config.public_reply_template?.length > 300) {
      errors.public_reply_template = 'حداکثر 300 کاراکتر';
    }
  }
  
  return errors;
};
```

---

## 🔌 Product Selector Implementation

```typescript
const loadProducts = async (inputValue: string) => {
  try {
    const response = await axios.get('/api/v1/web-knowledge/products/', {
      params: { 
        search: inputValue || '',
        is_active: true,
        page_size: 20
      }
    });
    
    return response.data.results.map(product => ({
      value: product.id,
      label: product.title,
      price: product.price_display,
      image: product.image_url,
      data: product
    }));
  } catch (error) {
    console.error('Error loading products:', error);
    return [];
  }
};
```

---

## 🎯 Translation Keys

اضافه کنید به فایل locale:

```json
{
  "workflow.when.instagram_comment": "کامنت اینستاگرام",
  "workflow.when.instagram_comment.desc": "وقتی کسی زیر پست کامنت می‌گذارد",
  
  "workflow.action.instagram_comment_dm_reply": "پاسخ به کامنت",
  "workflow.action.instagram_comment_dm_reply.desc": "ارسال دایرکت و پاسخ عمومی",
  
  "workflow.config.dm_mode": "نوع پیام",
  "workflow.config.dm_mode.static": "متن ثابت",
  "workflow.config.dm_mode.product": "معرفی محصول",
  "workflow.config.dm_text": "متن دایرکت",
  "workflow.config.product": "انتخاب محصول",
  "workflow.config.public_reply": "پاسخ عمومی",
  "workflow.config.public_reply_text": "متن پاسخ",
  
  "workflow.validation.dm_mode_required": "نوع DM اجباری است",
  "workflow.validation.dm_text_required": "متن دایرکت اجباری است",
  "workflow.validation.product_required": "محصول را انتخاب کنید",
  "workflow.validation.max_1000_chars": "حداکثر 1000 کاراکتر",
  "workflow.validation.max_300_chars": "حداکثر 300 کاراکتر",
  "workflow.validation.max_3_cta": "حداکثر 3 دکمه CTA",
  
  "workflow.help.cta_format": "فرمت: [[CTA:عنوان|URL]]",
  "workflow.help.variables": "{{username}}, {{comment_text}}, {{post_url}}"
}
```

---

## 🚀 چک‌لیست پیاده‌سازی

### Phase 1: UI (1 روز)
- [ ] اضافه کردن `instagram_comment` به When Node selector
- [ ] اضافه کردن `instagram_comment_dm_reply` به Action Node selector
- [ ] ساخت config form برای action

### Phase 2: Integration (1 روز)
- [ ] اتصال به Products API
- [ ] پیاده‌سازی ProductSelector
- [ ] Validation logic

### Phase 3: Testing (1 روز)
- [ ] تست ساخت workflow
- [ ] تست validation
- [ ] تست با API واقعی

**جمع**: 3 روز کاری

---

## ⚠️ نکات مهم

1. **حتماً Node-Based** استفاده کنید (سیستم جدید)
2. **when_type با حروف کوچک**: `'instagram_comment'`
3. **API Base URL**: `/api/v1/workflow/api/`
4. **Products API**: `/api/v1/web-knowledge/products/`

---

**تاریخ**: 2025-11-17  
**نسخه**: 2.0 (نهایی)  
**سیستم**: Node-Based Workflows

