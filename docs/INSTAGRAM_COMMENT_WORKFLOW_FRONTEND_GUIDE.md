# 📱 Instagram Comment → DM + Reply Workflow
## راهنمای کامل پیاده‌سازی فرانت‌اند

---

## 📋 فهرست مطالب
1. [نمای کلی](#نمای-کلی)
2. [UI Components مورد نیاز](#ui-components-مورد-نیاز)
3. [API Endpoints](#api-endpoints)
4. [Data Models](#data-models)
5. [گام‌های پیاده‌سازی](#گامهای-پیادهسازی)
6. [Validation Rules](#validation-rules)
7. [نمونه‌های کد](#نمونههای-کد)

---

## 🎯 نمای کلی

### قابلیت جدید:
وقتی کاربری زیر پست اینستاگرام شما کامنت می‌گذارد، workflow خودکار:
1. یک **دایرکت (DM)** به کاربر می‌فرستد (با یا بدون دکمه CTA)
2. (اختیاری) یک **پاسخ عمومی** زیر کامنت می‌گذارد

### کاربرد:
- پاسخ خودکار به سوالات قیمت
- معرفی محصول به کاربران علاقه‌مند
- هدایت ترافیک از کامنت به دایرکت

---

## 🎨 UI Components مورد نیاز

### 1️⃣ صفحه Workflow Builder

#### الف) Trigger Section - اضافه کردن Trigger جدید

**مکان**: `src/pages/Workflows/WorkflowBuilder.jsx` (یا مشابه)

```jsx
// در بخش Trigger Type Selector
const triggerTypes = [
  { value: 'MESSAGE_RECEIVED', label: 'دریافت پیام', icon: '💬' },
  { value: 'USER_CREATED', label: 'مشتری جدید', icon: '👤' },
  // ✅ اضافه کردن این:
  { 
    value: 'INSTAGRAM_COMMENT', 
    label: 'کامنت اینستاگرام', 
    icon: '💬',
    badge: 'جدید',
    requiresInstagram: true, // فقط برای کانال‌های اینستاگرام
  },
  // ... بقیه
];
```

**Conditions برای INSTAGRAM_COMMENT** (اختیاری):
```jsx
{
  triggerType === 'INSTAGRAM_COMMENT' && (
    <div className="conditions">
      <h4>شرط‌های تریگر (اختیاری)</h4>
      
      {/* فیلتر کلمات کلیدی */}
      <FormGroup>
        <Label>کامنت شامل این کلمات باشد:</Label>
        <TagInput
          placeholder="مثال: قیمت، خرید، سفارش"
          value={trigger.keywords}
          onChange={handleKeywordsChange}
        />
        <small>اگر خالی باشد، همه کامنت‌ها تریگر می‌شوند</small>
      </FormGroup>
      
      {/* فیلتر پست خاص */}
      <FormGroup>
        <Label>فقط برای این پست‌ها:</Label>
        <Input 
          placeholder="لینک پست (اختیاری)"
          value={trigger.postUrl}
          onChange={handlePostUrlChange}
        />
      </FormGroup>
    </div>
  )
}
```

---

#### ب) Action Section - اضافه کردن Action جدید

**مکان**: `src/pages/Workflows/ActionBuilder.jsx`

```jsx
// در بخش Action Type Selector
const actionTypes = [
  { value: 'send_message', label: 'ارسال پیام', icon: '✉️' },
  { value: 'add_tag', label: 'افزودن تگ', icon: '🏷️' },
  // ✅ اضافه کردن این:
  { 
    value: 'instagram_comment_dm_reply', 
    label: 'پاسخ به کامنت اینستاگرام', 
    icon: '📱',
    badge: 'جدید',
    description: 'ارسال DM + پاسخ عمومی',
    requiresInstagram: true,
  },
  // ... بقیه
];
```

**Configuration Form برای این Action**:

```jsx
{actionType === 'instagram_comment_dm_reply' && (
  <div className="instagram-comment-action-config">
    
    {/* ─────────────────────────────────────────────────── */}
    {/* بخش 1: انتخاب نوع DM */}
    {/* ─────────────────────────────────────────────────── */}
    <Card className="mb-4">
      <CardHeader>
        <h5>📩 تنظیمات دایرکت (DM)</h5>
      </CardHeader>
      <CardBody>
        
        {/* نوع DM */}
        <FormGroup>
          <Label>نوع پیام دایرکت *</Label>
          <div className="btn-group-toggle">
            <Button
              color={config.dm_mode === 'STATIC' ? 'primary' : 'outline-secondary'}
              onClick={() => setConfig({...config, dm_mode: 'STATIC'})}
            >
              📝 متن ثابت
            </Button>
            <Button
              color={config.dm_mode === 'PRODUCT' ? 'primary' : 'outline-secondary'}
              onClick={() => setConfig({...config, dm_mode: 'PRODUCT'})}
            >
              🛍️ معرفی محصول (AI)
            </Button>
          </div>
        </FormGroup>
        
        {/* ─────────────────────────────────────────────────── */}
        {/* حالت STATIC */}
        {/* ─────────────────────────────────────────────────── */}
        {config.dm_mode === 'STATIC' && (
          <FormGroup>
            <Label>متن دایرکت *</Label>
            <Textarea
              rows={5}
              placeholder="سلام {{username}}! 👋
به صفحه ما خوش اومدی.

برای اطلاعات بیشتر می‌تونی از این لینک استفاده کنی:
[[CTA:مشاهده سایت|https://example.com]]"
              value={config.dm_text_template}
              onChange={(e) => setConfig({...config, dm_text_template: e.target.value})}
              maxLength={1000}
            />
            <FormText>
              متغیرهای قابل استفاده:
              <ul className="mb-0">
                <li><code>{'{{username}}'}</code> - نام کاربری</li>
                <li><code>{'{{comment_text}}'}</code> - متن کامنت</li>
                <li><code>{'{{post_url}}'}</code> - لینک پست</li>
              </ul>
              
              <strong className="text-primary d-block mt-2">
                برای افزودن دکمه CTA:
              </strong>
              <code>[[CTA:عنوان دکمه|https://لینک]]</code>
              <br />
              <small className="text-muted">حداکثر 3 دکمه</small>
            </FormText>
          </FormGroup>
        )}
        
        {/* ─────────────────────────────────────────────────── */}
        {/* حالت PRODUCT (AI) */}
        {/* ─────────────────────────────────────────────────── */}
        {config.dm_mode === 'PRODUCT' && (
          <FormGroup>
            <Label>انتخاب محصول *</Label>
            <AsyncSelect
              placeholder="جستجوی محصول..."
              loadOptions={loadProducts}
              value={config.product}
              onChange={(product) => setConfig({...config, product_id: product.value})}
              getOptionLabel={(option) => (
                <div className="d-flex align-items-center">
                  {option.image && <img src={option.image} width="30" className="me-2" />}
                  <div>
                    <strong>{option.label}</strong>
                    {option.price && <small className="text-muted d-block">{option.price}</small>}
                  </div>
                </div>
              )}
            />
            <FormText>
              <span className="text-info">🤖 هوش مصنوعی:</span> بر اساس کامنت کاربر و اطلاعات محصول، 
              متن دایرکت را به صورت خودکار می‌سازد (شامل قیمت، توضیحات، و لینک محصول)
            </FormText>
            
            {/* نمایش پیش‌نمایش محصول انتخاب شده */}
            {config.product_id && (
              <Alert color="success" className="mt-2">
                <strong>محصول انتخاب شده:</strong> {selectedProduct.title}
                <br />
                <small>قیمت: {selectedProduct.price_display || 'تماس بگیرید'}</small>
              </Alert>
            )}
          </FormGroup>
        )}
        
      </CardBody>
    </Card>
    
    {/* ─────────────────────────────────────────────────── */}
    {/* بخش 2: پاسخ عمومی (اختیاری) */}
    {/* ─────────────────────────────────────────────────── */}
    <Card>
      <CardHeader>
        <div className="d-flex justify-content-between align-items-center">
          <h5>💬 پاسخ عمومی زیر کامنت (اختیاری)</h5>
          <Switch
            checked={config.public_reply_enabled}
            onChange={(checked) => setConfig({...config, public_reply_enabled: checked})}
          />
        </div>
      </CardHeader>
      
      {config.public_reply_enabled && (
        <CardBody>
          <FormGroup>
            <Label>متن پاسخ عمومی</Label>
            <Textarea
              rows={3}
              placeholder="{{username}} عزیز، ممنون از علاقه‌تون! 🙏
پیام دادیم، لطفاً دایرکت چک کنید 💌"
              value={config.public_reply_template}
              onChange={(e) => setConfig({...config, public_reply_template: e.target.value})}
              maxLength={300}
            />
            <FormText>
              <ul className="mb-0">
                <li>این پیام به صورت عمومی زیر کامنت نمایش داده می‌شود</li>
                <li>حداکثر 300 کاراکتر</li>
                <li>متغیرها: <code>{'{{username}}'}</code>, <code>{'{{product_name}}'}</code> (فقط در حالت PRODUCT)</li>
              </ul>
            </FormText>
          </FormGroup>
        </CardBody>
      )}
    </Card>
    
    {/* ─────────────────────────────────────────────────── */}
    {/* هشدارها */}
    {/* ─────────────────────────────────────────────────── */}
    <Alert color="warning" className="mt-3">
      <strong>⚠️ نکات مهم:</strong>
      <ul className="mb-0">
        <li>این قابلیت فقط برای <strong>حساب‌های Business و Creator</strong> اینستاگرام کار می‌کند</li>
        <li>باید Webhook را در Meta App Dashboard تنظیم کرده باشید</li>
        <li>دایرکت فقط به کاربرانی فرستاده می‌شود که حساب‌شان عمومی است</li>
      </ul>
    </Alert>
    
  </div>
)}
```

---

### 2️⃣ صفحه Instagram Channel Settings

**مکان**: `src/pages/Settings/InstagramChannels.jsx`

```jsx
// اضافه کردن بخش جدید در کارت هر کانال اینستاگرام

<Card>
  <CardBody>
    {/* اطلاعات فعلی کانال */}
    <div className="channel-info">
      <h5>{channel.username}</h5>
      <Badge color={channel.is_connect ? 'success' : 'secondary'}>
        {channel.is_connect ? 'متصل' : 'قطع'}
      </Badge>
      
      {/* ✅ اضافه کردن این بخش */}
      <Badge 
        color={channel.account_type === 'business' || channel.account_type === 'creator' ? 'info' : 'warning'}
        className="ms-2"
      >
        {channel.account_type === 'business' ? '💼 Business' : 
         channel.account_type === 'creator' ? '⭐ Creator' : 
         '👤 Personal'}
      </Badge>
    </div>
    
    {/* ✅ هشدار برای حساب‌های Personal */}
    {channel.account_type === 'personal' && (
      <Alert color="warning" className="mt-2">
        <strong>محدودیت:</strong> برای استفاده از قابلیت «پاسخ به کامنت»، 
        حساب شما باید Business یا Creator باشد.
        <br />
        <a href="https://help.instagram.com/502981923235522" target="_blank">
          راهنمای تبدیل به Business Account
        </a>
      </Alert>
    )}
    
    {/* دکمه‌های عملیات */}
    <div className="mt-3">
      <Button color="primary" onClick={() => handleTestConnection(channel.id)}>
        تست اتصال
      </Button>
      
      {/* ✅ دکمه جدید برای تست Webhook */}
      {(channel.account_type === 'business' || channel.account_type === 'creator') && (
        <Button 
          color="info" 
          outline 
          className="ms-2"
          onClick={() => handleTestWebhook(channel.id)}
        >
          🔔 تست Webhook
        </Button>
      )}
    </div>
  </CardBody>
</Card>
```

---

### 3️⃣ صفحه Products (محصولات)

اگر صفحه محصولات ندارید، باید اضافه کنید:

**مکان جدید**: `src/pages/Products/ProductsList.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Badge } from 'reactstrap';
import { getProducts, deleteProduct } from '../../api/products';

const ProductsList = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadProducts();
  }, []);
  
  const loadProducts = async () => {
    try {
      const response = await getProducts();
      setProducts(response.data.results);
    } catch (error) {
      toast.error('خطا در بارگذاری محصولات');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="products-page">
      <div className="d-flex justify-content-between mb-4">
        <h2>محصولات و خدمات</h2>
        <Button color="primary" onClick={() => navigate('/products/new')}>
          ➕ افزودن محصول
        </Button>
      </div>
      
      <Card>
        <Table>
          <thead>
            <tr>
              <th>عکس</th>
              <th>نام محصول</th>
              <th>قیمت</th>
              <th>لینک</th>
              <th>وضعیت</th>
              <th>عملیات</th>
            </tr>
          </thead>
          <tbody>
            {products.map(product => (
              <tr key={product.id}>
                <td>
                  {product.image_url && (
                    <img src={product.image_url} width="50" alt={product.title} />
                  )}
                </td>
                <td>{product.title}</td>
                <td>{product.price_display || '-'}</td>
                <td>
                  {product.product_url && (
                    <a href={product.product_url} target="_blank">
                      لینک
                    </a>
                  )}
                </td>
                <td>
                  <Badge color={product.is_active ? 'success' : 'secondary'}>
                    {product.is_active ? 'فعال' : 'غیرفعال'}
                  </Badge>
                </td>
                <td>
                  <Button size="sm" color="info" onClick={() => navigate(`/products/${product.id}/edit`)}>
                    ویرایش
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Card>
    </div>
  );
};
```

---

## 🔌 API Endpoints

### 1. Products API

#### `GET /api/knowledge/products/`
دریافت لیست محصولات

**Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "title": "محصول نمونه",
      "description": "توضیحات محصول",
      "price": 1500000,
      "currency": "IRT",
      "price_display": "1,500,000 تومان",
      "billing_period": "one_time",
      "product_url": "https://example.com/product",
      "buy_url": "https://example.com/buy",
      "image_url": "https://...",
      "is_active": true,
      "created_at": "2025-11-17T10:00:00Z"
    }
  ]
}
```

#### `POST /api/knowledge/products/`
ساخت محصول جدید

**Request Body:**
```json
{
  "title": "نام محصول",
  "description": "توضیحات",
  "price": 1500000,
  "currency": "IRT",
  "billing_period": "one_time",
  "product_url": "https://...",
  "image_url": "https://...",
  "is_active": true
}
```

#### `GET /api/knowledge/products/?search=query`
جستجوی محصولات (برای AsyncSelect)

**Response:** همان فرمت بالا

---

### 2. Workflow API (تغییرات)

#### `GET /api/workflow/triggers/`
لیست انواع Trigger

**Response شامل مورد جدید:**
```json
{
  "trigger_types": [
    {"value": "MESSAGE_RECEIVED", "label": "Receive Message"},
    {"value": "INSTAGRAM_COMMENT", "label": "Instagram Comment"},  // ✅ جدید
    // ...
  ]
}
```

#### `GET /api/workflow/actions/`
لیست انواع Action

**Response شامل مورد جدید:**
```json
{
  "action_types": [
    {"value": "send_message", "label": "Send Message"},
    {"value": "instagram_comment_dm_reply", "label": "Instagram Comment → DM + Reply"},  // ✅ جدید
    // ...
  ]
}
```

#### `POST /api/workflow/workflows/`
ساخت Workflow جدید

**Request Body برای Instagram Comment Workflow:**
```json
{
  "name": "پاسخ به کامنت‌های محصول",
  "description": "ارسال دایرکت و پاسخ عمومی",
  "status": "ACTIVE",
  "triggers": [
    {
      "trigger_type": "INSTAGRAM_COMMENT",
      "filters": {
        "operator": "AND",
        "conditions": [
          {
            "field": "comment_text",
            "operator": "contains",
            "value": "قیمت"
          }
        ]
      }
    }
  ],
  "actions": [
    {
      "action_type": "instagram_comment_dm_reply",
      "order": 1,
      "config": {
        "dm_mode": "PRODUCT",
        "product_id": "uuid-here",
        "public_reply_enabled": true,
        "public_reply_template": "{{username}} عزیز، پیام دادیم! 💌"
      }
    }
  ]
}
```

**مثال دیگر با STATIC mode:**
```json
{
  "actions": [
    {
      "action_type": "instagram_comment_dm_reply",
      "config": {
        "dm_mode": "STATIC",
        "dm_text_template": "سلام {{username}}! 👋\n\nممنون از کامنتت.\n\n[[CTA:سایت ما|https://example.com]]",
        "public_reply_enabled": true,
        "public_reply_template": "{{username}} عزیز، پیام خصوصی فرستادیم ✅"
      }
    }
  ]
}
```

---

### 3. Instagram Channel API

#### `GET /api/settings/instagram-channels/`
لیست کانال‌های اینستاگرام

**Response:**
```json
{
  "results": [
    {
      "id": "uuid",
      "username": "my_page",
      "instagram_user_id": "123456",
      "account_type": "business",  // "business" | "creator" | "personal"
      "is_connect": true,
      "access_token_valid": true,
      "created_at": "2025-11-17T10:00:00Z"
    }
  ]
}
```

#### `POST /api/settings/instagram-channels/{id}/test-webhook/`
تست Webhook برای کامنت‌ها

**Response:**
```json
{
  "success": true,
  "message": "Webhook configuration is correct",
  "subscriptions": [
    "messages",
    "messaging_postbacks",
    "comments"  // ✅ باید این وجود داشته باشد
  ]
}
```

---

## 📊 Data Models

### Trigger Model
```typescript
interface Trigger {
  id: string;
  trigger_type: 'MESSAGE_RECEIVED' | 'USER_CREATED' | 'INSTAGRAM_COMMENT' | ...;
  filters?: {
    operator: 'AND' | 'OR';
    conditions: Array<{
      field: string;
      operator: 'equals' | 'contains' | 'starts_with' | ...;
      value: any;
    }>;
  };
}
```

### Action Model
```typescript
interface Action {
  id: string;
  action_type: 'send_message' | 'instagram_comment_dm_reply' | ...;
  order: number;
  config: InstagramCommentActionConfig | SendMessageConfig | ...;
  is_required: boolean;
}

interface InstagramCommentActionConfig {
  dm_mode: 'STATIC' | 'PRODUCT';
  dm_text_template?: string;  // Required if dm_mode === 'STATIC'
  product_id?: string;         // Required if dm_mode === 'PRODUCT'
  public_reply_enabled: boolean;
  public_reply_template?: string;
}
```

### Product Model
```typescript
interface Product {
  id: string;
  title: string;
  description?: string;
  price?: number;
  currency: 'IRT' | 'USD' | 'EUR';
  price_display?: string;
  billing_period: 'one_time' | 'monthly' | 'yearly';
  product_url?: string;
  buy_url?: string;
  image_url?: string;
  is_active: boolean;
  created_at: string;
}
```

---

## ✅ Validation Rules

### 1. در زمان ساخت Workflow:

```javascript
const validateInstagramCommentAction = (action) => {
  const errors = {};
  
  // dm_mode اجباری است
  if (!action.config.dm_mode) {
    errors.dm_mode = 'نوع DM را انتخاب کنید';
  }
  
  // اگر STATIC: متن اجباری
  if (action.config.dm_mode === 'STATIC') {
    if (!action.config.dm_text_template || action.config.dm_text_template.trim() === '') {
      errors.dm_text_template = 'متن دایرکت اجباری است';
    }
    if (action.config.dm_text_template.length > 1000) {
      errors.dm_text_template = 'حداکثر 1000 کاراکتر';
    }
  }
  
  // اگر PRODUCT: محصول اجباری
  if (action.config.dm_mode === 'PRODUCT') {
    if (!action.config.product_id) {
      errors.product_id = 'محصول را انتخاب کنید';
    }
  }
  
  // اگر public reply فعال: متن اجباری
  if (action.config.public_reply_enabled) {
    if (!action.config.public_reply_template || action.config.public_reply_template.trim() === '') {
      errors.public_reply_template = 'متن پاسخ عمومی اجباری است';
    }
    if (action.config.public_reply_template.length > 300) {
      errors.public_reply_template = 'حداکثر 300 کاراکتر';
    }
  }
  
  // بررسی تعداد دکمه‌های CTA
  if (action.config.dm_mode === 'STATIC' && action.config.dm_text_template) {
    const ctaCount = (action.config.dm_text_template.match(/\[\[CTA:/g) || []).length;
    if (ctaCount > 3) {
      errors.dm_text_template = 'حداکثر 3 دکمه CTA مجاز است';
    }
  }
  
  return errors;
};
```

### 2. بررسی Account Type:

```javascript
const canUseCommentAction = (channel) => {
  return channel.account_type === 'business' || channel.account_type === 'creator';
};

// در UI:
if (!canUseCommentAction(selectedChannel)) {
  showError('این قابلیت فقط برای حساب‌های Business و Creator قابل استفاده است');
  return;
}
```

---

## 💻 نمونه‌های کد کامل

### نمونه 1: Component برای انتخاب Product

```jsx
import React, { useState } from 'react';
import AsyncSelect from 'react-select/async';
import axios from 'axios';

const ProductSelector = ({ value, onChange }) => {
  const loadProducts = async (inputValue) => {
    try {
      const response = await axios.get('/api/knowledge/products/', {
        params: { search: inputValue, is_active: true }
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
  
  return (
    <AsyncSelect
      cacheOptions
      defaultOptions
      loadOptions={loadProducts}
      value={value}
      onChange={onChange}
      placeholder="جستجوی محصول..."
      noOptionsMessage={() => 'محصولی یافت نشد'}
      loadingMessage={() => 'در حال جستجو...'}
      formatOptionLabel={(option) => (
        <div className="d-flex align-items-center">
          {option.image && (
            <img 
              src={option.image} 
              alt={option.label}
              width="40" 
              height="40" 
              className="rounded me-2"
              style={{ objectFit: 'cover' }}
            />
          )}
          <div>
            <div className="fw-bold">{option.label}</div>
            {option.price && (
              <small className="text-muted">{option.price}</small>
            )}
          </div>
        </div>
      )}
    />
  );
};

export default ProductSelector;
```

---

### نمونه 2: Form Component کامل برای Action Config

```jsx
import React, { useState, useEffect } from 'react';
import { 
  Card, CardHeader, CardBody, 
  FormGroup, Label, Input, Button,
  Alert, FormText, Badge
} from 'reactstrap';
import ProductSelector from './ProductSelector';

const InstagramCommentActionForm = ({ value, onChange }) => {
  const [config, setConfig] = useState(value || {
    dm_mode: 'STATIC',
    dm_text_template: '',
    product_id: null,
    public_reply_enabled: false,
    public_reply_template: ''
  });
  
  const [errors, setErrors] = useState({});
  
  useEffect(() => {
    onChange(config);
  }, [config]);
  
  const validate = () => {
    const newErrors = {};
    
    if (config.dm_mode === 'STATIC' && !config.dm_text_template.trim()) {
      newErrors.dm_text_template = 'متن دایرکت اجباری است';
    }
    
    if (config.dm_mode === 'PRODUCT' && !config.product_id) {
      newErrors.product_id = 'محصول را انتخاب کنید';
    }
    
    if (config.public_reply_enabled && !config.public_reply_template.trim()) {
      newErrors.public_reply_template = 'متن پاسخ عمومی اجباری است';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleModeChange = (mode) => {
    setConfig(prev => ({
      ...prev,
      dm_mode: mode,
      // Reset fields based on mode
      dm_text_template: mode === 'STATIC' ? prev.dm_text_template : '',
      product_id: mode === 'PRODUCT' ? prev.product_id : null
    }));
  };
  
  const insertVariable = (variable) => {
    const textarea = document.querySelector('textarea[name="dm_text_template"]');
    const cursorPos = textarea.selectionStart;
    const textBefore = config.dm_text_template.substring(0, cursorPos);
    const textAfter = config.dm_text_template.substring(cursorPos);
    
    setConfig(prev => ({
      ...prev,
      dm_text_template: textBefore + variable + textAfter
    }));
  };
  
  return (
    <div className="instagram-comment-action-form">
      
      {/* DM Settings */}
      <Card className="mb-3">
        <CardHeader>
          <h5>📩 تنظیمات دایرکت</h5>
        </CardHeader>
        <CardBody>
          
          {/* Mode Selection */}
          <FormGroup>
            <Label>نوع پیام *</Label>
            <div className="d-flex gap-2">
              <Button
                color={config.dm_mode === 'STATIC' ? 'primary' : 'outline-secondary'}
                onClick={() => handleModeChange('STATIC')}
                block
              >
                📝 متن ثابت
              </Button>
              <Button
                color={config.dm_mode === 'PRODUCT' ? 'primary' : 'outline-secondary'}
                onClick={() => handleModeChange('PRODUCT')}
                block
              >
                🛍️ معرفی محصول (AI)
              </Button>
            </div>
          </FormGroup>
          
          {/* STATIC Mode */}
          {config.dm_mode === 'STATIC' && (
            <>
              <FormGroup>
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <Label>متن دایرکت *</Label>
                  <div className="btn-group btn-group-sm">
                    <Button 
                      size="sm" 
                      outline 
                      onClick={() => insertVariable('{{username}}')}
                    >
                      نام کاربری
                    </Button>
                    <Button 
                      size="sm" 
                      outline 
                      onClick={() => insertVariable('{{comment_text}}')}
                    >
                      متن کامنت
                    </Button>
                  </div>
                </div>
                
                <Input
                  type="textarea"
                  name="dm_text_template"
                  rows={6}
                  value={config.dm_text_template}
                  onChange={(e) => setConfig({...config, dm_text_template: e.target.value})}
                  invalid={!!errors.dm_text_template}
                  placeholder="سلام {{username}}! 👋&#10;ممنون از کامنتت.&#10;&#10;[[CTA:سایت ما|https://example.com]]"
                />
                
                {errors.dm_text_template && (
                  <div className="invalid-feedback d-block">
                    {errors.dm_text_template}
                  </div>
                )}
                
                <FormText>
                  <strong>افزودن دکمه CTA:</strong>
                  <br />
                  <code>[[CTA:عنوان دکمه|https://لینک]]</code>
                  <Badge color="info" className="ms-2">حداکثر 3 دکمه</Badge>
                </FormText>
                
                <div className="text-end text-muted small mt-1">
                  {config.dm_text_template.length}/1000
                </div>
              </FormGroup>
            </>
          )}
          
          {/* PRODUCT Mode */}
          {config.dm_mode === 'PRODUCT' && (
            <FormGroup>
              <Label>انتخاب محصول *</Label>
              <ProductSelector
                value={config.product}
                onChange={(product) => setConfig({
                  ...config, 
                  product_id: product?.value,
                  product: product
                })}
              />
              {errors.product_id && (
                <div className="text-danger small mt-1">
                  {errors.product_id}
                </div>
              )}
              <FormText>
                <span className="text-info">🤖 هوش مصنوعی</span> بر اساس کامنت کاربر 
                و اطلاعات محصول، متن را خودکار می‌سازد
              </FormText>
            </FormGroup>
          )}
          
        </CardBody>
      </Card>
      
      {/* Public Reply Settings */}
      <Card>
        <CardHeader>
          <div className="d-flex justify-content-between align-items-center">
            <h5>💬 پاسخ عمومی (اختیاری)</h5>
            <div className="form-check form-switch">
              <input
                className="form-check-input"
                type="checkbox"
                checked={config.public_reply_enabled}
                onChange={(e) => setConfig({
                  ...config, 
                  public_reply_enabled: e.target.checked
                })}
              />
            </div>
          </div>
        </CardHeader>
        
        {config.public_reply_enabled && (
          <CardBody>
            <FormGroup>
              <Label>متن پاسخ عمومی</Label>
              <Input
                type="textarea"
                rows={3}
                value={config.public_reply_template}
                onChange={(e) => setConfig({
                  ...config, 
                  public_reply_template: e.target.value
                })}
                invalid={!!errors.public_reply_template}
                placeholder="{{username}} عزیز، ممنون! پیام دادیم 💌"
                maxLength={300}
              />
              {errors.public_reply_template && (
                <div className="invalid-feedback d-block">
                  {errors.public_reply_template}
                </div>
              )}
              <div className="text-end text-muted small mt-1">
                {config.public_reply_template.length}/300
              </div>
            </FormGroup>
          </CardBody>
        )}
      </Card>
      
      {/* Warnings */}
      <Alert color="warning" className="mt-3">
        <strong>⚠️ نکات مهم:</strong>
        <ul className="mb-0 mt-2">
          <li>فقط برای حساب‌های <strong>Business و Creator</strong></li>
          <li>Webhook باید در Meta App تنظیم شده باشد</li>
          <li>دایرکت فقط به حساب‌های عمومی ارسال می‌شود</li>
        </ul>
      </Alert>
      
    </div>
  );
};

export default InstagramCommentActionForm;
```

---

### نمونه 3: API Service Layer

```javascript
// src/services/api/workflows.js

import axios from 'axios';

const API_BASE = '/api/workflow';

export const workflowService = {
  // Get available trigger types
  getTriggerTypes: async () => {
    const response = await axios.get(`${API_BASE}/triggers/types/`);
    return response.data;
  },
  
  // Get available action types
  getActionTypes: async () => {
    const response = await axios.get(`${API_BASE}/actions/types/`);
    return response.data;
  },
  
  // Create workflow with Instagram comment action
  createWorkflow: async (workflowData) => {
    const response = await axios.post(`${API_BASE}/workflows/`, workflowData);
    return response.data;
  },
  
  // Validate action config before save
  validateActionConfig: (actionType, config) => {
    if (actionType === 'instagram_comment_dm_reply') {
      const errors = {};
      
      if (!config.dm_mode) {
        errors.dm_mode = 'نوع DM اجباری است';
      }
      
      if (config.dm_mode === 'STATIC' && !config.dm_text_template?.trim()) {
        errors.dm_text_template = 'متن دایرکت اجباری است';
      }
      
      if (config.dm_mode === 'PRODUCT' && !config.product_id) {
        errors.product_id = 'محصول اجباری است';
      }
      
      if (config.public_reply_enabled && !config.public_reply_template?.trim()) {
        errors.public_reply_template = 'متن پاسخ عمومی اجباری است';
      }
      
      return {
        isValid: Object.keys(errors).length === 0,
        errors
      };
    }
    
    return { isValid: true, errors: {} };
  }
};

// src/services/api/products.js

export const productService = {
  getAll: async (params = {}) => {
    const response = await axios.get('/api/knowledge/products/', { params });
    return response.data;
  },
  
  search: async (query) => {
    const response = await axios.get('/api/knowledge/products/', {
      params: { search: query, is_active: true }
    });
    return response.data.results;
  },
  
  getById: async (id) => {
    const response = await axios.get(`/api/knowledge/products/${id}/`);
    return response.data;
  }
};
```

---

## 🚀 چک‌لیست پیاده‌سازی

### Phase 1: UI Components ✅
- [ ] اضافه کردن `INSTAGRAM_COMMENT` به Trigger selector
- [ ] اضافه کردن `instagram_comment_dm_reply` به Action selector
- [ ] ساخت form component برای config این action
- [x] اضافه کردن بخش Products (اگر وجود ندارد)اینو انجام نده اصلا
- [x] نمایش account type در Instagram channels اینو انجام نده اصلا
- [x] اضافه کردن هشدارها برای حساب‌های Personal اینو انجام نده اصلا

### Phase 2: API Integration ✅
- [ ] ساخت service برای Products API
- [ ] آپدیت workflow service برای پشتیبانی از action جدید
- [ ] پیاده‌سازی validation logic
- [ ] تست connection با backend

### Phase 3: UX Enhancement ✅
- [ ] پیاده‌سازی ProductSelector با AsyncSelect
- [ ] افزودن helper buttons برای درج متغیرها
- [ ] نمایش character count برای textarea
- [ ] پیش‌نمایش CTA buttons
- [ ] نمایش توضیحات و راهنما

### Phase 4: Testing ✅
- [ ] تست ساخت workflow با STATIC mode
- [ ] تست ساخت workflow با PRODUCT mode
- [ ] تست validation errors
- [x ] تست با حساب Businessاینو انجام نده اصلا
- [ x] تست با حساب Personal (باید error بدهد)اینو انجام نده اصلا

---

## 🎨 استایل‌های پیشنهادی (CSS)

```css
/* Instagram Comment Action Specific Styles */

.instagram-comment-action-form .mode-selector {
  display: flex;
  gap: 0.5rem;
}

.instagram-comment-action-form .mode-selector .btn {
  flex: 1;
  padding: 1rem;
  font-size: 0.9rem;
}

.instagram-comment-action-form .variable-buttons {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
}

.instagram-comment-action-form .cta-helper {
  background: #f8f9fa;
  padding: 0.75rem;
  border-radius: 0.25rem;
  border-left: 3px solid #007bff;
  margin-top: 0.5rem;
}

.instagram-comment-action-form .cta-helper code {
  background: #fff;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.85rem;
}

.product-selector-option {
  display: flex;
  align-items: center;
  padding: 0.5rem;
}

.product-selector-option img {
  border-radius: 0.25rem;
  object-fit: cover;
}

.account-type-badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
}

/* Character counter */
.char-counter {
  text-align: right;
  font-size: 0.75rem;
  color: #6c757d;
  margin-top: 0.25rem;
}

.char-counter.warning {
  color: #ffc107;
}

.char-counter.danger {
  color: #dc3545;
}
```

---

## ❓ سوالات متداول (FAQ)

### Q1: چرا action من کار نمی‌کند؟
**A:** بررسی کنید:
1. حساب اینستاگرام Business یا Creator است؟
2. Webhook در Meta App تنظیم شده؟
3. Product انتخاب شده فعال (is_active=true) است؟
4. Config به درستی validation می‌شود؟

### Q2: چگونه بفهمم Webhook درست کار می‌کند؟
**A:** از endpoint تست webhook استفاده کنید:
```javascript
POST /api/settings/instagram-channels/{id}/test-webhook/
```

### Q3: آیا می‌توانم بیش از 3 دکمه CTA داشته باشم؟
**A:** خیر، Instagram حداکثر 3 دکمه را پشتیبانی می‌کند.

### Q4: چرا بعضی محصولات در selector نمایش داده نمی‌شوند؟
**A:** فقط محصولات با `is_active=true` نمایش داده می‌شوند.

---

## 📞 پشتیبانی

در صورت بروز مشکل:
1. Log های browser console را چک کنید
2. Network tab را برای خطاهای API بررسی کنید
3. با تیم بک‌اند تماس بگیرید و خطا را گزارش دهید

---

**آخرین بروزرسانی**: 2025-11-17  
**نسخه مستند**: 1.0  
**نویسنده**: Backend Team

