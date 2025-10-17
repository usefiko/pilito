# مستندات Smart PATCH API
## سیستم هوشمند به‌روزرسانی نودها

### 📋 معرفی کلی
Smart PATCH API روشی هوشمند و انعطاف‌پذیر برای به‌روزرسانی نودهای workflow فراهم می‌کند. این API هر فیلدی را می‌پذیرد و تغییرات را به صورت هوشمندانه اعمال می‌کند، از merge operations، مدیریت موقعیت، و به‌روزرسانی محتوا در یک request پشتیبانی می‌کند.

---

## 🚀 ویژگی‌های کلیدی

### ✅ **هوش مصنوعی**
- **هر فیلدی را می‌پذیرد** و تغییرات را به درستی اعمال می‌کند
- **merge خودکار** برای arrays (keywords, tags, channels, conditions)
- **مدیریت هوشمند JSON** برای objects (webhook headers/payload)
- **مدیریت موقعیت** با قابلیت‌های پیشرفته
- **validation مخصوص نوع** بر اساس نوع نود
- **گزینه‌های انعطاف‌پذیر جایگزینی** با special flags

### ✅ **انواع نودهای پشتیبانی شده**
- **When Nodes** - شرایط راه‌انداز
- **Condition Nodes** - شرایط منطقی
- **Action Nodes** - عملیات قابل اجرا
- **Waiting Nodes** - مدیریت پاسخ کاربر

---

## 🌐 API Endpoint

```http
PATCH /api/v1/workflow/api/nodes/{node_id}/
```

### احراز هویت
```http
Authorization: Bearer {your-jwt-token}
Content-Type: application/json
```

---

## 📍 مدیریت موقعیت

### به‌روزرسانی مستقیم موقعیت
```json
{
  "position_x": 450,
  "position_y": 350
}
```

### فرمت Position Object
```json
{
  "position": {
    "x": 500,
    "y": 300
  }
}
```

### حرکت نسبی
```json
{
  "move_by": {
    "x": 50,
    "y": -30
  }
}
```
**نتیجه:** نود 50 پیکسل به راست، 30 پیکسل به بالا حرکت می‌کند

### تراز کردن موقعیت
```json
{
  "align_to": {
    "x": 600
  }
}
```
**نتیجه:** نود به x=600 تراز می‌شود، مختصات Y تغییر نمی‌کند

### چسبیدن به Grid
```json
{
  "position_x": 347,
  "position_y": 183,
  "snap_to_grid": true,
  "grid_size": 25
}
```
**نتیجه:** موقعیت به grid چسبیده می‌شود: (350, 175) با grid 25 پیکسلی

### اعمال محدودیت مکانی
```json
{
  "position_x": 2500,
  "position_y": -50,
  "enforce_bounds": {
    "min_x": 0,
    "max_x": 2000,
    "min_y": 0,
    "max_y": 1500
  }
}
```
**نتیجه:** موقعیت در محدوده تنظیم می‌شود: (2000, 0)

### به‌روزرسانی پیچیده موقعیت
```json
{
  "move_by": {"x": 100, "y": 75},
  "snap_to_grid": true,
  "grid_size": 20,
  "enforce_bounds": {
    "min_x": 0,
    "max_x": 1800,
    "min_y": 0,
    "max_y": 1200
  }
}
```
**ترتیب پردازش:** حرکت → چسبیدن به Grid → اعمال محدودیت

---

## 🔥 مثال‌های When Node

### اضافه کردن Keywords (Merge)
```json
{
  "keywords": ["کمک", "پشتیبانی", "راهنمایی"]
}
```
**نتیجه:** keywords جدید با موجودی merge می‌شوند (بدون تکرار)

### اضافه کردن Channels
```json
{
  "channels": ["whatsapp", "email"]
}
```
**نتیجه:** کانال‌ها merge می‌شوند: telegram, instagram, whatsapp, email

### به‌روزرسانی‌های متعدد
```json
{
  "title": "راه‌انداز به‌روزرسانی شده",
  "position_x": 350,
  "keywords": ["به‌روزرسانی"],
  "channels": ["telegram"],
  "customer_tags": ["ویژه", "پریمیوم"]
}
```

### جایگزینی Keywords (جایگزینی کامل)
```json
{
  "keywords": ["کاملاً", "جدید", "کلمات"],
  "replace_keywords": true
}
```
**نتیجه:** تمام keywords قدیمی با جدید جایگزین می‌شوند

### به‌روزرسانی زمان‌بندی
```json
{
  "when_type": "scheduled",
  "schedule_frequency": "weekly",
  "schedule_time": "10:00:00",
  "schedule_date": "2024-01-15"
}
```

---

## ❓ مثال‌های Condition Node

### اضافه کردن Condition (Merge)
```json
{
  "conditions": [
    {
      "type": "message",
      "operator": "contains",
      "value": "فوری"
    }
  ]
}
```
**نتیجه:** condition جدید به conditions موجود اضافه می‌شود

### تغییر Operator + اضافه کردن Condition
```json
{
  "combination_operator": "or",
  "conditions": [
    {
      "type": "ai",
      "prompt": "آیا این اورژانسی است؟"
    }
  ]
}
```

### جایگزینی تمام Conditions
```json
{
  "conditions": [
    {
      "type": "message",
      "operator": "equals",
      "value": "کمک"
    }
  ],
  "replace_conditions": true
}
```
**نتیجه:** تمام conditions قبلی با جدید جایگزین می‌شوند

---

## ⚡ مثال‌های Action Node

### به‌روزرسانی محتوای پیام
```json
{
  "message_content": "پیام خوشامدگویی به‌روزرسانی شده! 🎉"
}
```

### اضافه کردن Webhook Headers (Merge)
```json
{
  "webhook_headers": {
    "X-Custom-Header": "value",
    "Authorization": "Bearer new-token"
  }
}
```
**نتیجه:** headers جدید با موجودی merge می‌شوند

### به‌روزرسانی Webhook + Payload
```json
{
  "webhook_url": "https://new-webhook.com/endpoint",
  "webhook_payload": {
    "new_field": "new_value",
    "timestamp": "{{now}}"
  }
}
```
**نتیجه:** URL به‌روزرسانی شده، payload با موجودی merge شده

### جایگزینی Webhook Headers
```json
{
  "webhook_headers": {
    "Content-Type": "application/json"
  },
  "replace_webhook_headers": true
}
```
**نتیجه:** تمام headers قدیمی با جدید جایگزین می‌شوند

### تغییر نوع Action
```json
{
  "action_type": "send_email",
  "email_to": "admin@company.com",
  "email_subject": "هشدار جدید",
  "email_body": "متن پیام هشدار"
}
```

---

## ⏳ مثال‌های Waiting Node

### اضافه کردن Choice Options (Merge)
```json
{
  "choice_options": ["گزینه جدید", "انتخاب دیگر"]
}
```
**نتیجه:** گزینه‌های جدید به لیست موجود اضافه می‌شوند

### به‌روزرسانی پیام + اضافه کردن Skip Keywords
```json
{
  "customer_message": "به‌روزرسانی: لطفاً گزینه‌ای انتخاب کنید:",
  "skip_keywords": ["رد", "لغو", "بعداً"]
}
```

### فعال کردن محدودیت زمانی
```json
{
  "response_time_limit_enabled": true,
  "response_timeout_amount": 10,
  "response_timeout_unit": "minutes"
}
```

### جایگزینی تمام Choice Options
```json
{
  "choice_options": ["بله", "خیر", "شاید"],
  "replace_choice_options": true
}
```

### تنظیمات ذخیره‌سازی
```json
{
  "storage_type": "database",
  "storage_field": "user_preference",
  "allowed_errors": 2
}
```

---

## 🏷️ Special Replacement Flags

### When Node Flags
```json
{
  "keywords": ["کلمات", "جدید"],
  "replace_keywords": true,     // جایگزینی تمام keywords
  "replace_channels": true,     // جایگزینی تمام channels
  "replace_customer_tags": true // جایگزینی تمام customer tags
}
```

### Condition Node Flags
```json
{
  "conditions": [...],
  "replace_conditions": true    // جایگزینی تمام conditions
}
```

### Action Node Flags
```json
{
  "webhook_headers": {...},
  "replace_webhook_headers": true,  // جایگزینی تمام headers
  "replace_webhook_payload": true   // جایگزینی payload
}
```

### Waiting Node Flags
```json
{
  "choice_options": [...],
  "replace_choice_options": true,   // جایگزینی تمام options
  "replace_skip_keywords": true     // جایگزینی skip keywords
}
```

---

## 💻 پیاده‌سازی JavaScript

### استفاده پایه
```javascript
class SmartNodeUpdater {
  constructor(token, baseUrl = '/api/v1/workflow/api') {
    this.token = token;
    this.baseUrl = baseUrl;
  }

  async smartPatch(nodeId, updates) {
    const response = await fetch(`${this.baseUrl}/nodes/${nodeId}/`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates)
    });

    if (response.ok) {
      return await response.json();
    } else {
      throw new Error(await response.text());
    }
  }

  // متدهای کمکی
  async addKeywords(nodeId, keywords) {
    return this.smartPatch(nodeId, { keywords });
  }

  async replaceKeywords(nodeId, keywords) {
    return this.smartPatch(nodeId, { 
      keywords, 
      replace_keywords: true 
    });
  }

  async updatePosition(nodeId, x, y) {
    return this.smartPatch(nodeId, { position_x: x, position_y: y });
  }

  async moveBy(nodeId, deltaX, deltaY) {
    return this.smartPatch(nodeId, { 
      move_by: { x: deltaX, y: deltaY } 
    });
  }

  async snapToGrid(nodeId, gridSize = 20) {
    return this.smartPatch(nodeId, { 
      snap_to_grid: true, 
      grid_size: gridSize 
    });
  }
}

// مثال‌های استفاده
const updater = new SmartNodeUpdater('your-jwt-token');

// به‌روزرسانی موقعیت
await updater.updatePosition('node-id', 400, 300);
await updater.moveBy('node-id', 50, -30);
await updater.snapToGrid('node-id', 25);

// به‌روزرسانی محتوا
await updater.addKeywords('node-id', ['کمک', 'پشتیبانی']);
await updater.replaceKeywords('node-id', ['کلمات', 'جدید']);

// به‌روزرسانی پیچیده
await updater.smartPatch('node-id', {
  title: 'نود به‌روزرسانی شده',
  position: { x: 500, y: 300 },
  keywords: ['به‌روزرسانی'],
  snap_to_grid: true,
  grid_size: 25
});
```

### کلاس مدیریت موقعیت
```javascript
class NodePositionManager {
  constructor(token, baseUrl = '/api/v1/workflow/api') {
    this.token = token;
    this.baseUrl = baseUrl;
  }

  async setPosition(nodeId, x, y) {
    return this.updatePosition(nodeId, { position_x: x, position_y: y });
  }

  async setPositionObject(nodeId, position) {
    return this.updatePosition(nodeId, { position });
  }

  async moveBy(nodeId, deltaX, deltaY) {
    return this.updatePosition(nodeId, { 
      move_by: { x: deltaX, y: deltaY } 
    });
  }

  async alignTo(nodeId, x = null, y = null) {
    const align_to = {};
    if (x !== null) align_to.x = x;
    if (y !== null) align_to.y = y;
    return this.updatePosition(nodeId, { align_to });
  }

  async snapToGrid(nodeId, gridSize = 20, newPosition = null) {
    const updates = { snap_to_grid: true, grid_size: gridSize };
    if (newPosition) updates.position = newPosition;
    return this.updatePosition(nodeId, updates);
  }

  async constrainToBounds(nodeId, bounds, newPosition = null) {
    const updates = { enforce_bounds: bounds };
    if (newPosition) updates.position = newPosition;
    return this.updatePosition(nodeId, updates);
  }

  // کمک‌کنندگان layout
  async arrangeHorizontally(nodes, startX = 100, y = 200, spacing = 200) {
    const promises = nodes.map((nodeId, index) => 
      this.setPosition(nodeId, startX + (index * spacing), y)
    );
    return Promise.all(promises);
  }

  async arrangeVertically(nodes, x = 300, startY = 100, spacing = 150) {
    const promises = nodes.map((nodeId, index) => 
      this.setPosition(nodeId, x, startY + (index * spacing))
    );
    return Promise.all(promises);
  }

  async createGridLayout(nodes, cols = 3, startX = 100, startY = 100, 
                         spacingX = 250, spacingY = 200) {
    const promises = nodes.map((nodeId, index) => {
      const row = Math.floor(index / cols);
      const col = index % cols;
      const x = startX + (col * spacingX);
      const y = startY + (row * spacingY);
      return this.setPosition(nodeId, x, y);
    });
    return Promise.all(promises);
  }

  async updatePosition(nodeId, updates) {
    const response = await fetch(`${this.baseUrl}/nodes/${nodeId}/`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates)
    });
    return response.json();
  }
}
```

---

## 🌐 مثال‌های cURL

### به‌روزرسانی پایه موقعیت
```bash
curl -X PATCH \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "position_x": 450,
    "position_y": 350
  }' \
  "https://api.pilito.com/api/v1/workflow/api/nodes/{node-id}/"
```

### به‌روزرسانی پیچیده با موقعیت + محتوا
```bash
curl -X PATCH \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "نود به‌روزرسانی شده",
    "position": {"x": 500, "y": 300},
    "keywords": ["به‌روزرسانی", "جابجایی"],
    "snap_to_grid": true,
    "grid_size": 25,
    "enforce_bounds": {
      "min_x": 0, "max_x": 2000,
      "min_y": 0, "max_y": 1500
    }
  }' \
  "https://api.pilito.com/api/v1/workflow/api/nodes/{node-id}/"
```

### به‌روزرسانی When Node
```bash
curl -X PATCH \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["کمک", "پشتیبانی"],
    "channels": ["whatsapp"],
    "customer_tags": ["ویژه"]
  }' \
  "https://api.pilito.com/api/v1/workflow/api/nodes/{node-id}/"
```

### به‌روزرسانی Condition Node
```bash
curl -X PATCH \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "combination_operator": "or",
    "conditions": [{
      "type": "message",
      "operator": "contains",
      "value": "فوری"
    }]
  }' \
  "https://api.pilito.com/api/v1/workflow/api/nodes/{node-id}/"
```

### به‌روزرسانی Action Node
```bash
curl -X PATCH \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message_content": "پیام به‌روزرسانی شده!",
    "webhook_headers": {
      "X-Custom": "value"
    }
  }' \
  "https://api.pilito.com/api/v1/workflow/api/nodes/{node-id}/"
```

### به‌روزرسانی Waiting Node
```bash
curl -X PATCH \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_message": "لطفاً انتخاب کنید:",
    "choice_options": ["گزینه الف", "گزینه ب"],
    "response_time_limit_enabled": true,
    "response_timeout_amount": 10,
    "response_timeout_unit": "minutes"
  }' \
  "https://api.pilito.com/api/v1/workflow/api/nodes/{node-id}/"
```

---

## ✅ فرمت پاسخ

### پاسخ موفقیت‌آمیز
```json
{
  "id": "uuid",
  "node_type": "when",
  "title": "نود به‌روزرسانی شده",
  "position_x": 450,
  "position_y": 350,
  "keywords": ["کمک", "پشتیبانی", "موجود"],
  "channels": ["telegram", "whatsapp"],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### پاسخ خطا
```json
{
  "error": "اعتبارسنجی ناموفق",
  "details": {
    "keywords": ["این فیلد برای when nodes الزامی است"],
    "position_x": ["موقعیت باید عدد مثبت باشد"]
  }
}
```

---

## 🎯 بهترین روش‌ها

### 1. **به‌روزرسانی‌های تدریجی**
```json
// خوب: فقط فیلدهایی که می‌خواهید تغییر دهید بفرستید
{
  "title": "عنوان جدید",
  "position_x": 400
}

// اجتناب: ارسال کل object بدون نیاز
```

### 2. **استفاده از Merge به صورت پیش‌فرض**
```json
// merge keywords جدید با موجود
{
  "keywords": ["جدید", "کلمه"]
}

// فقط در صورت نیاز از replace استفاده کنید
{
  "keywords": ["کاملاً", "جدید"],
  "replace_keywords": true
}
```

### 3. **ترکیب به‌روزرسانی‌های مرتبط**
```json
// خوب: موقعیت و محتوا را با هم به‌روزرسانی کنید
{
  "title": "نود جابجا شده",
  "position": {"x": 500, "y": 300},
  "snap_to_grid": true
}
```

### 4. **مدیریت موقعیت**
```json
// از متد مناسب موقعیت استفاده کنید
{
  "position": {"x": 400, "y": 300}        // موقعیت‌یابی مستقیم
}
{
  "move_by": {"x": 50, "y": -30}          // حرکت نسبی
}
{
  "align_to": {"x": 500}                  // تراز کردن
}
```

### 5. **Grid و Bounds**
```json
// همیشه grid_size را با snap_to_grid مشخص کنید
{
  "position": {"x": 347, "y": 183},
  "snap_to_grid": true,
  "grid_size": 25
}

// از bounds برای محدودیت canvas استفاده کنید
{
  "enforce_bounds": {
    "min_x": 0, "max_x": 2000,
    "min_y": 0, "max_y": 1500
  }
}
```

---

## 🔍 قوانین اعتبارسنجی

### اعتبارسنجی موقعیت
- `position_x`, `position_y`: باید عدد باشند
- `grid_size`: باید عدد صحیح مثبت باشد (پیش‌فرض: 20)
- `enforce_bounds`: تمام مقادیر باید عدد باشند
- `move_by`: مقادیر می‌توانند مثبت یا منفی باشند

### اعتبارسنجی محتوا
- Arrays به صورت خودکار merge می‌شوند (مگر replace flag استفاده شود)
- JSON objects بر اساس key merge می‌شوند
- فیلدهای الزامی بر اساس نوع نود اعتبارسنجی می‌شوند

### اعتبارسنجی مخصوص نود
- **When Nodes**: حداقل یک شرط راه‌انداز نیاز دارند
- **Condition Nodes**: operator و conditions معتبر نیاز دارند
- **Action Nodes**: action_type معتبر نیاز دارند
- **Waiting Nodes**: اعتبارسنجی شرطی بر اساس تنظیمات

---

## 🚀 نکات عملکرد

### 1. **به‌روزرسانی‌های دسته‌ای**
```javascript
// خوب: یک request با چندین تغییر
await updater.smartPatch('node-id', {
  title: 'به‌روزرسانی',
  position: {x: 400, y: 300},
  keywords: ['جدید'],
  snap_to_grid: true
});

// اجتناب: چندین request جداگانه
await updater.updateTitle('node-id', 'به‌روزرسانی');
await updater.updatePosition('node-id', 400, 300);
await updater.addKeywords('node-id', ['جدید']);
```

### 2. **به‌روزرسانی‌های کارآمد موقعیت**
```javascript
// خوب: از حرکت نسبی برای تغییرات کوچک استفاده کنید
await updater.moveBy('node-id', 25, 0);

// اجتناب: محاسبه غیرضروری موقعیت‌های مطلق
const current = await getNodePosition('node-id');
await updater.setPosition('node-id', current.x + 25, current.y);
```

### 3. **به‌روزرسانی‌های هوشمند Array**
```javascript
// خوب: بگذارید API arrays را merge کند
await updater.smartPatch('node-id', {
  keywords: ['جدید', 'کلمه']
});

// اجتناب: fetch و merge دستی
const node = await getNode('node-id');
const mergedKeywords = [...node.keywords, 'جدید', 'کلمه'];
await updater.replaceKeywords('node-id', mergedKeywords);
```

---

## 📚 موارد استفاده رایج

### 1. **ادغام طراح Workflow**
```javascript
// به‌روزرسانی موقعیت drag and drop
async function onNodeDrag(nodeId, newPosition) {
  await updater.smartPatch(nodeId, {
    position: newPosition,
    snap_to_grid: true,
    grid_size: 25,
    enforce_bounds: CANVAS_BOUNDS
  });
}

// به‌روزرسانی‌های پنل خصوصیات
async function onPropertyChange(nodeId, property, value) {
  await updater.smartPatch(nodeId, {
    [property]: value
  });
}
```

### 2. **به‌روزرسانی‌های Layout دسته‌ای**
```javascript
// تنظیم workflow در layout افقی
async function arrangeWorkflow(nodeIds) {
  const positionManager = new NodePositionManager(token);
  await positionManager.arrangeHorizontally(nodeIds, 100, 200, 250);
}

// سازمان‌دهی خودکار نودهای همپوشان
async function autoOrganize(nodes) {
  for (let i = 0; i < nodes.length; i++) {
    await updater.smartPatch(nodes[i].id, {
      position: { x: 100 + (i % 4) * 300, y: 100 + Math.floor(i / 4) * 200 },
      snap_to_grid: true,
      grid_size: 50
    });
  }
}
```

### 3. **مدیریت محتوا**
```javascript
// اضافه کردن keywords از ورودی کاربر
async function addKeywords(nodeId, newKeywords) {
  await updater.addKeywords(nodeId, newKeywords);
}

// به‌روزرسانی condition با اعتبارسنجی
async function addCondition(nodeId, condition) {
  await updater.smartPatch(nodeId, {
    conditions: [condition]
  });
}
```

---

## 🎉 خلاصه

Smart PATCH API ارائه می‌دهد:

✅ **مدیریت هوشمند فیلدها** - هر فیلدی را می‌پذیرد و به درستی اعمال می‌کند  
✅ **Merge کردن Array** - خودکار merge keywords, tags, channels, conditions  
✅ **مدیریت موقعیت** - موقعیت‌یابی پیشرفته با grid snap و bounds  
✅ **گزینه‌های جایگزینی** - special flags برای جایگزینی کامل  
✅ **اعتبارسنجی مخصوص نوع** - اعتبارسنجی هوشمند بر اساس نوع نود  
✅ **بهینه‌سازی عملکرد** - یک request برای چندین به‌روزرسانی  
✅ **دوستدار توسعه‌دهنده** - طراحی API بدیهی با کتابخانه‌های کمکی JavaScript  

**نودهای workflow شما حالا با حداکثر انعطاف‌پذیری و هوش قابل به‌روزرسانی هستند!** 🚀
