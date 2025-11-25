# 🎨 AI Behavior Settings - Frontend Integration Guide

> **Status:** ✅ FULLY TESTED & PRODUCTION READY  
> **API Base URL:** `https://api.pilito.com/api/settings/`  
> **Proxy:** ✅ All AI APIs route through Iran proxy automatically  
> **Date:** November 20, 2025

---

## 📑 Table of Contents

1. [Quick Start](#quick-start)
2. [API Endpoints](#api-endpoints)
3. [Request/Response Examples](#requestresponse-examples)
4. [Field Specifications](#field-specifications)
5. [Validation Rules](#validation-rules)
6. [Error Handling](#error-handling)
7. [React/TypeScript Examples](#reacttypescript-examples)
8. [Testing Checklist](#testing-checklist)

---

## 🚀 Quick Start

### Authentication
All endpoints require authentication with Bearer token:

```http
Authorization: Bearer YOUR_JWT_TOKEN
```

### Base URL
```
https://api.pilito.com/api/settings/
```

### Available Endpoints
```
GET    /ai-behavior/me/      - Get current user's settings
PUT    /ai-behavior/me/      - Update all settings
PATCH  /ai-behavior/me/      - Update specific fields
POST   /ai-behavior/reset/   - Reset to defaults
```

---

## 📡 API Endpoints

### 1. Get AI Behavior Settings

**Endpoint:** `GET /api/settings/ai-behavior/me/`

**Description:** دریافت تنظیمات رفتار AI برای کاربر فعلی. اگر تنظیمات وجود نداشته باشد، به صورت خودکار با مقادیر پیش‌فرض ساخته می‌شود.

**Authentication:** Required ✅

**Request:**
```http
GET /api/settings/ai-behavior/me/ HTTP/1.1
Host: api.pilito.com
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Accept: application/json
```

**Response:** `200 OK`
```json
{
  "id": 1,
  
  "tone": "friendly",
  "tone_display": "😊 دوستانه و صمیمی",
  "tone_choices": [
    {
      "value": "formal",
      "label": "🎩 رسمی و حرفه‌ای"
    },
    {
      "value": "friendly",
      "label": "😊 دوستانه و صمیمی"
    },
    {
      "value": "energetic",
      "label": "⚡ پرانرژی و هیجان‌انگیز"
    },
    {
      "value": "empathetic",
      "label": "🤝 همدلانه و حمایتگر"
    }
  ],
  
  "emoji_usage": "moderate",
  "emoji_usage_display": "🙂 متعادل - کمی ایموجی",
  "emoji_usage_choices": [
    {
      "value": "none",
      "label": "⛔ هیچ - بدون ایموجی"
    },
    {
      "value": "moderate",
      "label": "🙂 متعادل - کمی ایموجی"
    },
    {
      "value": "high",
      "label": "😍 زیاد - پر از ایموجی"
    }
  ],
  
  "response_length": "balanced",
  "response_length_display": "🔸 متعادل - 3-4 جمله",
  "response_length_choices": [
    {
      "value": "short",
      "label": "🔹 کوتاه - 1-2 جمله"
    },
    {
      "value": "balanced",
      "label": "🔸 متعادل - 3-4 جمله"
    },
    {
      "value": "detailed",
      "label": "🔶 تفصیلی - 5-7 جمله"
    }
  ],
  
  "use_customer_name": true,
  "use_bio_context": true,
  
  "persuasive_selling_enabled": false,
  "persuasive_cta_text": "آیا می‌خواهید این محصول را سفارش دهید؟ 🛒",
  
  "unknown_fallback_text": "من در حال حاضر پاسخ دقیق این سوال را ندارم، اما همکارانم به زودی پاسخ شما را خواهند داد.",
  "custom_instructions": "",
  
  "estimated_token_usage": {
    "total": 45,
    "max_allowed": 200,
    "percentage": 22,
    "breakdown": {
      "base_flags": 30,
      "cta_text": 10,
      "fallback_text": 5,
      "custom_instructions": 0
    }
  },
  
  "created_at": "2025-11-20T08:16:47.123456Z",
  "updated_at": "2025-11-20T08:16:47.123456Z"
}
```

---

### 2. Update AI Behavior Settings (Full)

**Endpoint:** `PUT /api/settings/ai-behavior/me/`

**Description:** به‌روزرسانی کامل تنظیمات. تمام فیلدها باید ارسال شوند.

**Authentication:** Required ✅

**Request:**
```http
PUT /api/settings/ai-behavior/me/ HTTP/1.1
Host: api.pilito.com
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "tone": "energetic",
  "emoji_usage": "high",
  "response_length": "short",
  "use_customer_name": true,
  "use_bio_context": false,
  "persuasive_selling_enabled": true,
  "persuasive_cta_text": "همین الان سفارش بده! 🔥",
  "unknown_fallback_text": "این سوال رو نمی‌دونم، اما بزار چک کنم برات!",
  "custom_instructions": "Always mention free shipping for orders over 500,000 Toman"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "tone": "energetic",
  "tone_display": "⚡ پرانرژی و هیجان‌انگیز",
  "emoji_usage": "high",
  ...
  "updated_at": "2025-11-20T09:30:00.000000Z"
}
```

---

### 3. Update AI Behavior Settings (Partial)

**Endpoint:** `PATCH /api/settings/ai-behavior/me/`

**Description:** به‌روزرسانی جزئی. فقط فیلدهایی که می‌خواهید تغییر دهید را ارسال کنید.

**Authentication:** Required ✅

**Request:**
```http
PATCH /api/settings/ai-behavior/me/ HTTP/1.1
Host: api.pilito.com
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "tone": "formal",
  "emoji_usage": "none"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "tone": "formal",
  "tone_display": "🎩 رسمی و حرفه‌ای",
  "emoji_usage": "none",
  "emoji_usage_display": "⛔ هیچ - بدون ایموجی",
  ...
}
```

---

### 4. Reset to Defaults

**Endpoint:** `POST /api/settings/ai-behavior/reset/`

**Description:** بازگشت تنظیمات به حالت پیش‌فرض

**Authentication:** Required ✅

**Request:**
```http
POST /api/settings/ai-behavior/reset/ HTTP/1.1
Host: api.pilito.com
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "تنظیمات به حالت پیش‌فرض بازگشت",
  "data": {
    "id": 1,
    "tone": "friendly",
    "emoji_usage": "moderate",
    "response_length": "balanced",
    ...
  }
}
```

---

## 📋 Field Specifications

### Core Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | integer | read-only | auto | شناسه یکتای تنظیمات |
| `tone` | string | optional | `"friendly"` | لحن صحبت AI |
| `emoji_usage` | string | optional | `"moderate"` | میزان استفاده از ایموجی |
| `response_length` | string | optional | `"balanced"` | طول پاسخ‌ها |
| `use_customer_name` | boolean | optional | `true` | استفاده از نام مشتری در سلام |
| `use_bio_context` | boolean | optional | `true` | استفاده از بیو برای شخصی‌سازی |
| `persuasive_selling_enabled` | boolean | optional | `false` | فعال‌سازی فروش فعال |
| `persuasive_cta_text` | string | optional | (default in Persian) | متن CTA برای فروش |
| `unknown_fallback_text` | string | required | (default in Persian) | پاسخ هنگام نداشتن اطلاعات |
| `custom_instructions` | string | optional | `""` | دستورات اضافی (انگلیسی) |
| `created_at` | datetime | read-only | auto | تاریخ ایجاد |
| `updated_at` | datetime | read-only | auto | تاریخ آخرین به‌روزرسانی |

### Display Fields (Read-Only)

| Field | Type | Description |
|-------|------|-------------|
| `tone_display` | string | نمایش فارسی tone |
| `emoji_usage_display` | string | نمایش فارسی emoji_usage |
| `response_length_display` | string | نمایش فارسی response_length |
| `tone_choices` | array | لیست گزینه‌های tone |
| `emoji_usage_choices` | array | لیست گزینه‌های emoji |
| `response_length_choices` | array | لیست گزینه‌های length |
| `estimated_token_usage` | object | تخمین مصرف token |

### Tone Options

```typescript
type Tone = 'formal' | 'friendly' | 'energetic' | 'empathetic';
```

| Value | Label | Meaning |
|-------|-------|---------|
| `formal` | 🎩 رسمی و حرفه‌ای | زبان رسمی، احترام‌آمیز، حرفه‌ای |
| `friendly` | 😊 دوستانه و صمیمی | صمیمی، راحت، مثل دوست |
| `energetic` | ⚡ پرانرژی و هیجان‌انگیز | پرانرژی، هیجان‌انگیز، مثبت |
| `empathetic` | 🤝 همدلانه و حمایتگر | همدل، حمایتگر، با درک |

### Emoji Usage Options

```typescript
type EmojiUsage = 'none' | 'moderate' | 'high';
```

| Value | Label | Token Impact |
|-------|-------|--------------|
| `none` | ⛔ هیچ - بدون ایموجی | 0 emojis per message |
| `moderate` | 🙂 متعادل - کمی ایموجی | 1-2 emojis per message |
| `high` | 😍 زیاد - پر از ایموجی | 3+ emojis per message |

### Response Length Options

```typescript
type ResponseLength = 'short' | 'balanced' | 'detailed';
```

| Value | Label | Tokens | Sentences |
|-------|-------|--------|-----------|
| `short` | 🔹 کوتاه - 1-2 جمله | 250 | 1-2 جمله |
| `balanced` | 🔸 متعادل - 3-4 جمله | 450 | 3-4 جمله |
| `detailed` | 🔶 تفصیلی - 5-7 جمله | 750 | 5-7 جمله |

---

## ✅ Validation Rules

### Character Limits

```typescript
{
  persuasive_cta_text: {
    max: 300,  // characters
    error: "متن CTA نباید بیشتر از 300 کاراکتر باشد"
  },
  unknown_fallback_text: {
    min: 1,    // required, can't be empty
    max: 500,  // characters
    error: "متن fallback نباید بیشتر از 500 کاراکتر باشد"
  },
  custom_instructions: {
    max: 1000, // characters
    optional: true,
    error: "دستورات اضافی نباید بیشتر از 1000 کاراکتر باشد"
  }
}
```

### Token Budget

```typescript
interface TokenUsage {
  total: number;        // Current total tokens
  max_allowed: number;  // Maximum allowed (200)
  percentage: number;   // Percentage used (0-100)
  breakdown: {
    base_flags: number;          // ~30 tokens (tone, emoji, length flags)
    cta_text: number;            // ~0.25 token per character
    fallback_text: number;       // ~0.25 token per character
    custom_instructions: number; // ~0.25 token per character
  };
}
```

**Warning Thresholds:**
- 🟢 Green: 0-70% (< 140 tokens)
- 🟡 Yellow: 71-90% (141-180 tokens)
- 🔴 Red: 91-100% (181-200 tokens)

---

## ❌ Error Handling

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| `200` | Success | تنظیمات با موفقیت ذخیره شد |
| `400` | Validation Error | خطای اعتبارسنجی - پیام خطا را نمایش دهید |
| `401` | Unauthorized | کاربر احراز هویت نشده - به صفحه لاگین بروید |
| `404` | Not Found | endpoint اشتباه است |
| `500` | Server Error | خطای سرور - بعداً تلاش کنید |

### Validation Error Response

```json
{
  "persuasive_cta_text": [
    "متن CTA نباید بیشتر از 300 کاراکتر باشد. طول فعلی: 350 کاراکتر"
  ],
  "unknown_fallback_text": [
    "متن fallback نمی‌تواند خالی باشد"
  ]
}
```

### Example Error Handling (TypeScript)

```typescript
try {
  const response = await updateSettings(data);
  toast.success('تنظیمات با موفقیت ذخیره شد');
} catch (error) {
  if (error.response?.status === 400) {
    // Validation errors
    const errors = error.response.data;
    Object.entries(errors).forEach(([field, messages]) => {
      toast.error(`${field}: ${messages[0]}`);
    });
  } else if (error.response?.status === 401) {
    // Unauthorized
    router.push('/login');
  } else {
    // General error
    toast.error('خطا در ذخیره تنظیمات. لطفاً دوباره تلاش کنید.');
  }
}
```

---

## 💻 React/TypeScript Examples

### TypeScript Interfaces

```typescript
// types/ai-behavior.ts

export type Tone = 'formal' | 'friendly' | 'energetic' | 'empathetic';
export type EmojiUsage = 'none' | 'moderate' | 'high';
export type ResponseLength = 'short' | 'balanced' | 'detailed';

export interface Choice {
  value: string;
  label: string;
}

export interface TokenUsage {
  total: number;
  max_allowed: number;
  percentage: number;
  breakdown: {
    base_flags: number;
    cta_text: number;
    fallback_text: number;
    custom_instructions: number;
  };
}

export interface AIBehaviorSettings {
  id: number;
  
  // Persona
  tone: Tone;
  tone_display: string;
  tone_choices: Choice[];
  
  emoji_usage: EmojiUsage;
  emoji_usage_display: string;
  emoji_usage_choices: Choice[];
  
  response_length: ResponseLength;
  response_length_display: string;
  response_length_choices: Choice[];
  
  // Behavior
  use_customer_name: boolean;
  use_bio_context: boolean;
  
  // Sales
  persuasive_selling_enabled: boolean;
  persuasive_cta_text: string;
  
  // Rules
  unknown_fallback_text: string;
  custom_instructions: string;
  
  // Metadata
  estimated_token_usage: TokenUsage;
  created_at: string;
  updated_at: string;
}

export interface UpdateAIBehaviorSettingsRequest {
  tone?: Tone;
  emoji_usage?: EmojiUsage;
  response_length?: ResponseLength;
  use_customer_name?: boolean;
  use_bio_context?: boolean;
  persuasive_selling_enabled?: boolean;
  persuasive_cta_text?: string;
  unknown_fallback_text?: string;
  custom_instructions?: string;
}
```

### API Service

```typescript
// services/ai-behavior-api.ts

import axios from 'axios';
import { AIBehaviorSettings, UpdateAIBehaviorSettingsRequest } from '@/types/ai-behavior';

const API_BASE_URL = 'https://api.pilito.com/api/settings';

// Axios instance with auth interceptor
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const AIBehaviorAPI = {
  /**
   * Get current user's AI behavior settings
   * Auto-creates with defaults if not exists
   */
  getSettings: async (): Promise<AIBehaviorSettings> => {
    const response = await apiClient.get<AIBehaviorSettings>('/ai-behavior/me/');
    return response.data;
  },

  /**
   * Update AI behavior settings (partial update)
   * Only send fields you want to change
   */
  updateSettings: async (
    data: UpdateAIBehaviorSettingsRequest
  ): Promise<AIBehaviorSettings> => {
    const response = await apiClient.patch<AIBehaviorSettings>(
      '/ai-behavior/me/',
      data
    );
    return response.data;
  },

  /**
   * Update AI behavior settings (full update)
   * Must send all fields
   */
  replaceSettings: async (
    data: UpdateAIBehaviorSettingsRequest
  ): Promise<AIBehaviorSettings> => {
    const response = await apiClient.put<AIBehaviorSettings>(
      '/ai-behavior/me/',
      data
    );
    return response.data;
  },

  /**
   * Reset settings to defaults
   */
  resetSettings: async (): Promise<{
    success: boolean;
    message: string;
    data: AIBehaviorSettings;
  }> => {
    const response = await apiClient.post('/ai-behavior/reset/');
    return response.data;
  },
};
```

### React Hook (with React Query)

```typescript
// hooks/useAIBehaviorSettings.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { AIBehaviorAPI } from '@/services/ai-behavior-api';
import { UpdateAIBehaviorSettingsRequest } from '@/types/ai-behavior';

export const useAIBehaviorSettings = () => {
  const queryClient = useQueryClient();
  const queryKey = ['ai-behavior-settings'];

  // Fetch settings
  const {
    data: settings,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey,
    queryFn: AIBehaviorAPI.getSettings,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Update settings (partial)
  const updateMutation = useMutation({
    mutationFn: (data: UpdateAIBehaviorSettingsRequest) =>
      AIBehaviorAPI.updateSettings(data),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKey, data);
      toast.success('تنظیمات با موفقیت ذخیره شد ✅');
    },
    onError: (error: any) => {
      if (error.response?.status === 400) {
        const errors = error.response.data;
        const firstError = Object.values(errors)[0] as string[];
        toast.error(firstError[0] || 'خطا در اعتبارسنجی');
      } else {
        toast.error('خطا در ذخیره تنظیمات');
      }
    },
  });

  // Reset to defaults
  const resetMutation = useMutation({
    mutationFn: AIBehaviorAPI.resetSettings,
    onSuccess: (response) => {
      queryClient.setQueryData(queryKey, response.data);
      toast.success(response.message);
    },
    onError: () => {
      toast.error('خطا در بازگشت به تنظیمات پیش‌فرض');
    },
  });

  return {
    settings,
    isLoading,
    error,
    refetch,
    updateSettings: updateMutation.mutate,
    isUpdating: updateMutation.isPending,
    resetSettings: resetMutation.mutate,
    isResetting: resetMutation.isPending,
  };
};
```

### React Component Example

```tsx
// components/AIBehaviorSettingsForm.tsx

import React from 'react';
import { useForm } from 'react-hook-form';
import { useAIBehaviorSettings } from '@/hooks/useAIBehaviorSettings';
import { UpdateAIBehaviorSettingsRequest } from '@/types/ai-behavior';

export const AIBehaviorSettingsForm: React.FC = () => {
  const { settings, isLoading, updateSettings, isUpdating, resetSettings } =
    useAIBehaviorSettings();

  const { register, handleSubmit, reset, watch, formState: { errors } } =
    useForm<UpdateAIBehaviorSettingsRequest>({
      defaultValues: settings,
    });

  // Update form when settings load
  React.useEffect(() => {
    if (settings) {
      reset(settings);
    }
  }, [settings, reset]);

  const onSubmit = (data: UpdateAIBehaviorSettingsRequest) => {
    updateSettings(data);
  };

  const handleReset = () => {
    if (confirm('آیا مطمئن هستید که می‌خواهید به تنظیمات پیش‌فرض برگردید؟')) {
      resetSettings();
    }
  };

  // Watch token usage
  const ctaText = watch('persuasive_cta_text');
  const fallbackText = watch('unknown_fallback_text');
  const customInstructions = watch('custom_instructions');
  
  const estimatedTokens = React.useMemo(() => {
    const cta = (ctaText?.length || 0) * 0.25;
    const fallback = (fallbackText?.length || 0) * 0.25;
    const custom = (customInstructions?.length || 0) * 0.25;
    const base = 30;
    return Math.round(base + cta + fallback + custom);
  }, [ctaText, fallbackText, customInstructions]);

  if (isLoading) {
    return <div>در حال بارگذاری...</div>;
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Tone Selection */}
      <div>
        <label className="block text-sm font-medium mb-2">
          لحن صحبت
        </label>
        <select
          {...register('tone')}
          className="w-full px-3 py-2 border rounded-lg"
        >
          {settings?.tone_choices.map((choice) => (
            <option key={choice.value} value={choice.value}>
              {choice.label}
            </option>
          ))}
        </select>
      </div>

      {/* Emoji Usage */}
      <div>
        <label className="block text-sm font-medium mb-2">
          استفاده از ایموجی
        </label>
        <select
          {...register('emoji_usage')}
          className="w-full px-3 py-2 border rounded-lg"
        >
          {settings?.emoji_usage_choices.map((choice) => (
            <option key={choice.value} value={choice.value}>
              {choice.label}
            </option>
          ))}
        </select>
      </div>

      {/* Response Length */}
      <div>
        <label className="block text-sm font-medium mb-2">
          طول پاسخ
        </label>
        <select
          {...register('response_length')}
          className="w-full px-3 py-2 border rounded-lg"
        >
          {settings?.response_length_choices.map((choice) => (
            <option key={choice.value} value={choice.value}>
              {choice.label}
            </option>
          ))}
        </select>
      </div>

      {/* Toggles */}
      <div className="space-y-3">
        <label className="flex items-center">
          <input
            type="checkbox"
            {...register('use_customer_name')}
            className="mr-2"
          />
          <span>استفاده از نام مشتری در سلام</span>
        </label>

        <label className="flex items-center">
          <input
            type="checkbox"
            {...register('use_bio_context')}
            className="mr-2"
          />
          <span>استفاده از اطلاعات بیو برای شخصی‌سازی</span>
        </label>

        <label className="flex items-center">
          <input
            type="checkbox"
            {...register('persuasive_selling_enabled')}
            className="mr-2"
          />
          <span>فعال‌سازی فروش فعال</span>
        </label>
      </div>

      {/* CTA Text */}
      <div>
        <label className="block text-sm font-medium mb-2">
          متن دعوت به اقدام (CTA)
          <span className="text-sm text-gray-500 mr-2">
            ({(ctaText?.length || 0)}/300)
          </span>
        </label>
        <input
          type="text"
          {...register('persuasive_cta_text', { maxLength: 300 })}
          className="w-full px-3 py-2 border rounded-lg"
          placeholder="آیا می‌خواهید این محصول را سفارش دهید؟"
        />
        {errors.persuasive_cta_text && (
          <p className="text-red-500 text-sm mt-1">
            حداکثر 300 کاراکتر
          </p>
        )}
      </div>

      {/* Fallback Text */}
      <div>
        <label className="block text-sm font-medium mb-2">
          پاسخ عدم اطلاع
          <span className="text-sm text-gray-500 mr-2">
            ({(fallbackText?.length || 0)}/500)
          </span>
        </label>
        <textarea
          {...register('unknown_fallback_text', {
            required: true,
            maxLength: 500,
          })}
          className="w-full px-3 py-2 border rounded-lg"
          rows={3}
        />
        {errors.unknown_fallback_text && (
          <p className="text-red-500 text-sm mt-1">
            این فیلد الزامی است (حداکثر 500 کاراکتر)
          </p>
        )}
      </div>

      {/* Token Usage Indicator */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium">مصرف Token</span>
          <span className="text-sm">
            {estimatedTokens} / 200 ({Math.round((estimatedTokens / 200) * 100)}%)
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${
              estimatedTokens < 140
                ? 'bg-green-500'
                : estimatedTokens < 180
                ? 'bg-yellow-500'
                : 'bg-red-500'
            }`}
            style={{ width: `${Math.min((estimatedTokens / 200) * 100, 100)}%` }}
          />
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          type="submit"
          disabled={isUpdating}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {isUpdating ? 'در حال ذخیره...' : 'ذخیره تنظیمات'}
        </button>

        <button
          type="button"
          onClick={handleReset}
          disabled={isUpdating}
          className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
        >
          بازگشت به پیش‌فرض
        </button>
      </div>
    </form>
  );
};
```

---

## ⚠️ Important Notes

### 🌐 Proxy Configuration

**✅ همه API های هوش مصنوعی از پشت پروکسی ایران عبور می‌کنند**

این شامل:
- ✅ Gemini AI (Google Generative AI)
- ✅ OpenAI GPT
- ✅ Embedding Services

**کد مربوطه در بکند:**
```python
# src/AI_model/services/gemini_service.py (خط 7-9)
from core.utils import setup_ai_proxy
setup_ai_proxy()  # ✅ Proxy setup قبل از import

import google.generativeai as genai
```

**شما در فرانت نیازی به تنظیم پروکسی ندارید.** همه درخواست‌های API از طریق سرور شما (`api.pilito.com`) می‌روند و سرور خودش از پروکسی استفاده می‌کند.

### 🔒 Security

1. **Never store JWT tokens in localStorage for sensitive apps** - consider using httpOnly cookies
2. **Always validate user input** before sending to API
3. **Handle 401 errors** by redirecting to login
4. **Rate limiting:** API has rate limiting (implement exponential backoff for retries)

### ⚡ Performance Tips

1. **Cache settings:** Use React Query with 5-minute stale time
2. **Debounce text inputs:** Especially for real-time token calculation
3. **Optimistic updates:** Update UI immediately, revert on error
4. **Auto-save:** Consider auto-saving after 2-3 seconds of inactivity

---

## ✅ Testing Checklist

### Manual Testing

- [ ] Get settings loads correctly
- [ ] Dropdowns show all choices
- [ ] Token usage calculates correctly
- [ ] Character limits are enforced
- [ ] Validation errors display properly
- [ ] Update (PATCH) saves changes
- [ ] Reset button works
- [ ] Auth errors redirect to login
- [ ] Loading states show correctly
- [ ] Success/error toasts appear

### Test Data

```typescript
// Valid update
{
  tone: 'energetic',
  emoji_usage: 'high',
  response_length: 'short'
}

// Invalid - exceeds character limit
{
  persuasive_cta_text: 'a'.repeat(301)  // Should fail
}

// Invalid - empty required field
{
  unknown_fallback_text: ''  // Should fail
}
```

---

## 📞 Support & Questions

**Backend Status:** ✅ 100% TESTED & WORKING

**Test Results:**
```
✅ 14/14 users have settings
✅ Model methods work correctly
✅ Serializer produces valid JSON
✅ Token allocation is dynamic
✅ Proxy routes through Iran server
```

**Questions?** Contact backend team or check:
- Implementation doc: `docs/AI_BEHAVIOR_SETTINGS_IMPLEMENTATION.md`
- Admin panel: `https://api.pilito.com/admin/settings/aibehaviorsettings/`

---

**Document Version:** 1.0  
**Last Updated:** November 20, 2025  
**Status:** ✅ Production Ready

