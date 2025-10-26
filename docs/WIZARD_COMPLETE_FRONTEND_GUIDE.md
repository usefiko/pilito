# Wizard Complete API - Frontend Integration Guide

## 📋 Overview

این API به شما کمک می‌کنه تا وضعیت تکمیل ویزارد کاربر رو بررسی کنید و فقط وقتی همه شرایط لازم کامل شده باشه، ویزارد رو به عنوان "تکمیل شده" علامت بزنید.

## 🎯 Prerequisites (شرایط لازم)

برای تکمیل ویزارد، کاربر باید موارد زیر را کامل کرده باشه:

1. ✅ **نام** (`first_name`)
2. ✅ **نام خانوادگی** (`last_name`)
3. ✅ **شماره تماس** (`phone_number`)
4. ✅ **نوع بیزنس** (`business_type`) - اینداستری یا دسته‌بندی کسب‌وکار
5. ✅ **منوال پرامپت** (`manual_prompt`) - پرامپت دستی AI
6. ✅ **کانال متصل** - حداقل یکی از Instagram یا Telegram باید connect شده باشه

---

## 🔌 API Endpoints

### Base URL
```
/api/v1/accounts/wizard-complete
```

### Authentication
تمام درخواست‌ها نیاز به Bearer Token دارند:
```javascript
headers: {
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json'
}
```

---

## 📖 API Methods

### 1️⃣ GET - دریافت وضعیت ویزارد

بررسی می‌کنه که آیا کاربر همه شرایط رو کامل کرده یا نه و جزئیات کامل رو برمی‌گردونه.

**Request:**
```javascript
GET /api/v1/accounts/wizard-complete
```

**Response (موفق):**
```json
{
  "wizard_complete": false,
  "can_complete": true,
  "missing_fields": [],
  "details": {
    "first_name": true,
    "last_name": true,
    "phone_number": true,
    "business_type": true,
    "manual_prompt": true,
    "channel_connected": true,
    "instagram_connected": true,
    "telegram_connected": false
  }
}
```

**Response (ناقص):**
```json
{
  "wizard_complete": false,
  "can_complete": false,
  "missing_fields": ["manual_prompt", "business_type"],
  "details": {
    "first_name": true,
    "last_name": true,
    "phone_number": true,
    "business_type": false,
    "manual_prompt": false,
    "channel_connected": true,
    "instagram_connected": false,
    "telegram_connected": true
  }
}
```

**Response Fields:**
- `wizard_complete` (boolean): آیا کاربر قبلاً ویزارد رو تکمیل کرده
- `can_complete` (boolean): آیا همه شرایط کامل شده و می‌تونه الان تکمیل کنه
- `missing_fields` (array): لیست فیلدهایی که هنوز کامل نشده
- `details` (object): جزئیات وضعیت هر فیلد

---

### 2️⃣ PATCH - تکمیل ویزارد

وقتی کاربر روی دکمه "Complete Wizard" کلیک می‌کنه، این endpoint فراخوانی می‌شه.

**⚠️ مهم:** این endpoint فقط وقتی موفق می‌شه که **همه شرایط** کامل باشه.

**Request:**
```javascript
PATCH /api/v1/accounts/wizard-complete
```

**Response (موفق - همه شرایط کامل):**
```json
{
  "success": true,
  "message": "Wizard completed successfully",
  "wizard_complete": true,
  "details": {
    "first_name": true,
    "last_name": true,
    "phone_number": true,
    "business_type": true,
    "manual_prompt": true,
    "channel_connected": true,
    "instagram_connected": true,
    "telegram_connected": false
  }
}
```

**Response (ناموفق - شرایط ناقص):**
```json
{
  "success": false,
  "message": "Cannot complete wizard. Missing required fields.",
  "missing_fields": ["manual_prompt", "business_type"],
  "wizard_complete": false,
  "details": {
    "first_name": true,
    "last_name": true,
    "phone_number": true,
    "business_type": false,
    "manual_prompt": false,
    "channel_connected": true,
    "instagram_connected": false,
    "telegram_connected": true
  }
}
```

---

## 💻 Frontend Implementation Examples

### React/TypeScript Example

```typescript
import { useState, useEffect } from 'react';
import axios from 'axios';

interface WizardStatus {
  wizard_complete: boolean;
  can_complete: boolean;
  missing_fields: string[];
  details: {
    first_name: boolean;
    last_name: boolean;
    phone_number: boolean;
    business_type: boolean;
    manual_prompt: boolean;
    channel_connected: boolean;
    instagram_connected?: boolean;
    telegram_connected?: boolean;
  };
}

const WizardCompletePage = () => {
  const [wizardStatus, setWizardStatus] = useState<WizardStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // دریافت وضعیت ویزارد
  const fetchWizardStatus = async () => {
    try {
      const response = await axios.get('/api/v1/accounts/wizard-complete', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      setWizardStatus(response.data);
    } catch (err) {
      console.error('Failed to fetch wizard status:', err);
      setError('خطا در دریافت وضعیت');
    }
  };

  // تکمیل ویزارد
  const completeWizard = async () => {
    if (!wizardStatus?.can_complete) {
      alert('لطفاً ابتدا همه مراحل را تکمیل کنید');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.patch(
        '/api/v1/accounts/wizard-complete',
        {},
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      if (response.data.success) {
        alert('ویزارد با موفقیت تکمیل شد! ✅');
        // Redirect to dashboard
        window.location.href = '/dashboard';
      }
    } catch (err: any) {
      if (err.response?.data?.missing_fields) {
        setError(
          `موارد زیر را تکمیل کنید: ${err.response.data.missing_fields.join(', ')}`
        );
      } else {
        setError('خطا در تکمیل ویزارد');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWizardStatus();
  }, []);

  if (!wizardStatus) return <div>در حال بارگذاری...</div>;

  return (
    <div className="wizard-page">
      <h1>تکمیل ویزارد</h1>

      {/* نمایش وضعیت هر بخش */}
      <div className="wizard-checklist">
        <ChecklistItem
          label="نام"
          completed={wizardStatus.details.first_name}
          link="/settings/account"
        />
        <ChecklistItem
          label="نام خانوادگی"
          completed={wizardStatus.details.last_name}
          link="/settings/account"
        />
        <ChecklistItem
          label="شماره تماس"
          completed={wizardStatus.details.phone_number}
          link="/settings/account"
        />
        <ChecklistItem
          label="نوع بیزنس"
          completed={wizardStatus.details.business_type}
          link="/settings/account"
        />
        <ChecklistItem
          label="منوال پرامپت"
          completed={wizardStatus.details.manual_prompt}
          link="/settings/ai-prompts"
        />
        <ChecklistItem
          label="اتصال کانال (Instagram/Telegram)"
          completed={wizardStatus.details.channel_connected}
          link="/settings/channels"
        />
      </div>

      {/* دکمه تکمیل */}
      <button
        onClick={completeWizard}
        disabled={!wizardStatus.can_complete || loading}
        className={wizardStatus.can_complete ? 'btn-primary' : 'btn-disabled'}
      >
        {loading ? 'در حال پردازش...' : 'تکمیل ویزارد'}
      </button>

      {/* نمایش خطا */}
      {error && <div className="error-message">{error}</div>}

      {/* نمایش موارد کم شده */}
      {wizardStatus.missing_fields.length > 0 && (
        <div className="missing-fields-warning">
          ⚠️ موارد زیر را تکمیل کنید:
          <ul>
            {wizardStatus.missing_fields.map(field => (
              <li key={field}>{getFieldLabel(field)}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

// کامپوننت برای نمایش هر آیتم
const ChecklistItem = ({ label, completed, link }: any) => (
  <div className="checklist-item">
    <span className={completed ? 'check-icon completed' : 'check-icon'}>
      {completed ? '✅' : '❌'}
    </span>
    <span>{label}</span>
    {!completed && (
      <a href={link} className="complete-link">
        تکمیل کنید →
      </a>
    )}
  </div>
);

// تبدیل نام فیلد به فارسی
const getFieldLabel = (field: string): string => {
  const labels: Record<string, string> = {
    first_name: 'نام',
    last_name: 'نام خانوادگی',
    phone_number: 'شماره تماس',
    business_type: 'نوع بیزنس',
    manual_prompt: 'منوال پرامپت',
    channel_connected: 'اتصال کانال (Instagram/Telegram)'
  };
  return labels[field] || field;
};

export default WizardCompletePage;
```

---

### Vue.js Example

```vue
<template>
  <div class="wizard-page">
    <h1>تکمیل ویزارد</h1>

    <!-- Loading State -->
    <div v-if="loading" class="loading">در حال بارگذاری...</div>

    <!-- Wizard Status -->
    <div v-else-if="wizardStatus" class="wizard-content">
      <!-- Progress Bar -->
      <div class="progress-bar">
        <div 
          class="progress-fill" 
          :style="{ width: progressPercentage + '%' }"
        ></div>
        <span>{{ progressPercentage }}% تکمیل شده</span>
      </div>

      <!-- Checklist -->
      <div class="wizard-checklist">
        <div 
          v-for="(item, key) in checklistItems" 
          :key="key"
          class="checklist-item"
        >
          <span :class="['check-icon', item.completed ? 'completed' : '']">
            {{ item.completed ? '✅' : '❌' }}
          </span>
          <span>{{ item.label }}</span>
          <a v-if="!item.completed" :href="item.link" class="complete-link">
            تکمیل کنید →
          </a>
        </div>
      </div>

      <!-- Complete Button -->
      <button
        @click="completeWizard"
        :disabled="!wizardStatus.can_complete || isSubmitting"
        :class="wizardStatus.can_complete ? 'btn-primary' : 'btn-disabled'"
      >
        {{ isSubmitting ? 'در حال پردازش...' : 'تکمیل ویزارد' }}
      </button>

      <!-- Error Message -->
      <div v-if="error" class="error-message">{{ error }}</div>

      <!-- Missing Fields Warning -->
      <div v-if="wizardStatus.missing_fields.length > 0" class="warning">
        ⚠️ موارد زیر را تکمیل کنید:
        <ul>
          <li v-for="field in wizardStatus.missing_fields" :key="field">
            {{ getFieldLabel(field) }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

interface WizardStatus {
  wizard_complete: boolean;
  can_complete: boolean;
  missing_fields: string[];
  details: {
    first_name: boolean;
    last_name: boolean;
    phone_number: boolean;
    business_type: boolean;
    manual_prompt: boolean;
    channel_connected: boolean;
    instagram_connected?: boolean;
    telegram_connected?: boolean;
  };
}

const wizardStatus = ref<WizardStatus | null>(null);
const loading = ref(true);
const isSubmitting = ref(false);
const error = ref('');

// محاسبه درصد پیشرفت
const progressPercentage = computed(() => {
  if (!wizardStatus.value) return 0;
  const details = wizardStatus.value.details;
  const total = 6; // تعداد کل موارد
  const completed = Object.values(details).filter(v => v === true).length;
  return Math.round((completed / total) * 100);
});

// لیست آیتم‌های checklist
const checklistItems = computed(() => {
  if (!wizardStatus.value) return {};
  
  return {
    first_name: {
      label: 'نام',
      completed: wizardStatus.value.details.first_name,
      link: '/settings/account'
    },
    last_name: {
      label: 'نام خانوادگی',
      completed: wizardStatus.value.details.last_name,
      link: '/settings/account'
    },
    phone_number: {
      label: 'شماره تماس',
      completed: wizardStatus.value.details.phone_number,
      link: '/settings/account'
    },
    business_type: {
      label: 'نوع بیزنس',
      completed: wizardStatus.value.details.business_type,
      link: '/settings/account'
    },
    manual_prompt: {
      label: 'منوال پرامپت',
      completed: wizardStatus.value.details.manual_prompt,
      link: '/settings/ai-prompts'
    },
    channel_connected: {
      label: 'اتصال کانال (Instagram/Telegram)',
      completed: wizardStatus.value.details.channel_connected,
      link: '/settings/channels'
    }
  };
});

// دریافت وضعیت ویزارد
const fetchWizardStatus = async () => {
  try {
    loading.value = true;
    const response = await axios.get('/api/v1/accounts/wizard-complete', {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    wizardStatus.value = response.data;
  } catch (err) {
    console.error('Failed to fetch wizard status:', err);
    error.value = 'خطا در دریافت وضعیت';
  } finally {
    loading.value = false;
  }
};

// تکمیل ویزارد
const completeWizard = async () => {
  if (!wizardStatus.value?.can_complete) {
    alert('لطفاً ابتدا همه مراحل را تکمیل کنید');
    return;
  }

  isSubmitting.value = true;
  error.value = '';

  try {
    const response = await axios.patch(
      '/api/v1/accounts/wizard-complete',
      {},
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
      }
    );

    if (response.data.success) {
      alert('ویزارد با موفقیت تکمیل شد! ✅');
      // Redirect to dashboard
      window.location.href = '/dashboard';
    }
  } catch (err: any) {
    if (err.response?.data?.missing_fields) {
      error.value = `موارد زیر را تکمیل کنید: ${err.response.data.missing_fields.join(', ')}`;
    } else {
      error.value = 'خطا در تکمیل ویزارد';
    }
  } finally {
    isSubmitting.value = false;
  }
};

// تبدیل نام فیلد به فارسی
const getFieldLabel = (field: string): string => {
  const labels: Record<string, string> = {
    first_name: 'نام',
    last_name: 'نام خانوادگی',
    phone_number: 'شماره تماس',
    business_type: 'نوع بیزنس',
    manual_prompt: 'منوال پرامپت',
    channel_connected: 'اتصال کانال (Instagram/Telegram)'
  };
  return labels[field] || field;
};

onMounted(() => {
  fetchWizardStatus();
});
</script>

<style scoped>
.wizard-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

.progress-bar {
  background: #f0f0f0;
  border-radius: 10px;
  height: 30px;
  position: relative;
  margin-bottom: 2rem;
  overflow: hidden;
}

.progress-fill {
  background: linear-gradient(90deg, #4caf50, #8bc34a);
  height: 100%;
  transition: width 0.3s ease;
}

.progress-bar span {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-weight: bold;
  color: #333;
}

.wizard-checklist {
  margin-bottom: 2rem;
}

.checklist-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-bottom: 1px solid #eee;
}

.check-icon {
  font-size: 1.5rem;
}

.check-icon.completed {
  color: #4caf50;
}

.complete-link {
  margin-left: auto;
  color: #6366f1;
  text-decoration: none;
}

.complete-link:hover {
  text-decoration: underline;
}

.btn-primary {
  background: #6366f1;
  color: white;
  padding: 1rem 2rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  width: 100%;
}

.btn-primary:hover {
  background: #4f46e5;
}

.btn-disabled {
  background: #ccc;
  color: #666;
  padding: 1rem 2rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: not-allowed;
  width: 100%;
}

.error-message {
  color: #f44336;
  padding: 1rem;
  background: #ffebee;
  border-radius: 8px;
  margin-top: 1rem;
}

.warning {
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
}

.warning ul {
  margin-top: 0.5rem;
  padding-left: 1.5rem;
}
</style>
```

---

## 🔄 Workflow (گردش کار)

### مرحله 1: بررسی وضعیت اولیه
```javascript
// هنگام بارگذاری صفحه ویزارد
GET /api/v1/accounts/wizard-complete

// پاسخ:
{
  "can_complete": false,
  "missing_fields": ["manual_prompt", "business_type"],
  ...
}
```

### مرحله 2: نمایش موارد ناقص به کاربر
```
❌ نام - تکمیل شده ✅
❌ نام خانوادگی - تکمیل شده ✅
❌ شماره تماس - تکمیل شده ✅
❌ نوع بیزنس - تکمیل کنید →
❌ منوال پرامپت - تکمیل کنید →
❌ اتصال کانال - تکمیل شده ✅
```

### مرحله 3: کاربر موارد ناقص را تکمیل می‌کنه
```javascript
// بعد از هر تغییر، وضعیت رو دوباره بگیر
GET /api/v1/accounts/wizard-complete
```

### مرحله 4: تکمیل نهایی
```javascript
// وقتی همه چیز کامل شد
PATCH /api/v1/accounts/wizard-complete

// پاسخ موفق:
{
  "success": true,
  "wizard_complete": true
}

// بعد از موفقیت → Redirect به Dashboard
window.location.href = '/dashboard';
```

---

## ⚠️ نکات مهم

### 1. چک کردن مجدد وضعیت
بعد از هر تغییر در فیلدها (مثلاً save کردن profile)، حتماً وضعیت رو دوباره بگیرید:

```javascript
// بعد از save کردن profile
await saveProfile();
// بررسی مجدد وضعیت
await fetchWizardStatus();
```

### 2. نمایش دکمه Complete
دکمه "Complete Wizard" باید فقط وقتی active باشه که `can_complete === true`:

```javascript
<button 
  disabled={!wizardStatus.can_complete}
  onClick={completeWizard}
>
  تکمیل ویزارد
</button>
```

### 3. Handling Errors
همیشه برای خطاها آماده باشید:

```javascript
try {
  await completeWizard();
} catch (error) {
  if (error.response?.data?.missing_fields) {
    // نمایش موارد کم شده
    showMissingFieldsAlert(error.response.data.missing_fields);
  }
}
```

### 4. Real-time Updates
اگه چند تب باز باشه، می‌تونید از polling یا WebSocket استفاده کنید:

```javascript
// هر 30 ثانیه یکبار چک کن
setInterval(() => {
  fetchWizardStatus();
}, 30000);
```

---

## 🎨 UI/UX Recommendations

### Progress Bar
```
[████████████░░░░░░░░] 67% Complete
```

### Checklist با لینک به صفحات مربوطه
```
✅ نام و نام خانوادگی
✅ شماره تماس  
❌ نوع بیزنس          → [تکمیل کنید]
❌ منوال پرامپت       → [تکمیل کنید]
✅ کانال متصل
```

### دکمه‌های Smart
- **Active**: همه چیز کامل شده → دکمه سبز و فعال
- **Disabled**: چیزی کم هست → دکمه خاکستری و غیرفعال + نمایش لیست موارد کم شده

---

## 🐛 Troubleshooting

### مشکل: همه چیز کامل شده ولی `can_complete` هنوز `false` است

**راه‌حل:**
1. چک کنید manual_prompt خالی نباشه (فقط فاصله)
2. چک کنید business_type null نباشه
3. چک کنید حداقل یک کانال `is_connect=True` باشه

```javascript
// دیباگ کردن
const response = await axios.get('/api/v1/accounts/wizard-complete');
console.log('Details:', response.data.details);
console.log('Missing:', response.data.missing_fields);
```

### مشکل: بعد از PATCH هنوز wizard_complete سبز نمی‌شه

**راه‌حل:**
صفحه رو refresh کنید یا user info رو دوباره بگیرید:

```javascript
// بعد از موفقیت
await fetchUserProfile(); // برای گرفتن wizard_complete جدید
```

---

## 📞 Support

اگر مشکلی داشتید:
1. لاگ‌های مرورگر رو چک کنید (Console)
2. Network tab رو بررسی کنید
3. Response های API رو بررسی کنید
4. با تیم بک‌اند تماس بگیرید

---

## ✅ Summary

این API یک راه **ساده و قدرتمند** برای مدیریت ویزارد شماست:
- ✅ GET: بررسی وضعیت + جزئیات کامل
- ✅ PATCH: تکمیل فقط با شرایط کامل
- ✅ خطاهای واضح و قابل فهم
- ✅ جزئیات کامل برای نمایش به کاربر

**Good luck! 🚀**

