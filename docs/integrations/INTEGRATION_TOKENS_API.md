# API مستندات: Integration Tokens (برای فرانت)

## 📋 خلاصه

این API امکان نمایش Integration Tokens کاربر را در فرانت فراهم می‌کند. این tokens برای اتصال پلاگین WordPress به سیستم استفاده می‌شوند.

**⚠️ توجه:** این API فقط برای **نمایش** tokens است. ساخت و حذف token از طریق Admin Panel انجام می‌شود.

---

## 🔌 API Endpoints

### 1. لیست همه Tokens کاربر

**Endpoint:** `GET /api/v1/integrations/tokens/`

**Authentication:** Required (Bearer Token)

**دستور curl:**
```bash
curl -X GET "https://api.pilito.com/api/v1/integrations/tokens/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

**Response (200 OK):**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "1616a793-eb91-416b-ada7-11c87cf237cd",
      "user_id": 13,
      "user_email": "iamyaserm@gmail.com",
      "integration_type": "woocommerce",
      "integration_type_display": "WooCommerce",
      "name": "faracoach (woocommerce)",
      "token_preview": "wc_sk...qmy0lk",
      "is_active": true,
      "is_valid_status": true,
      "last_used_at": "2025-11-11T21:30:00Z",
      "usage_count": 45,
      "allowed_ips": [],
      "created_at": "2025-10-15T10:20:00Z",
      "expires_at": null
    },
    {
      "id": "another-uuid-here",
      "user_id": 13,
      "user_email": "iamyaserm@gmail.com",
      "integration_type": "woocommerce",
      "integration_type_display": "WooCommerce",
      "name": "Store 2",
      "token_preview": "wc_sk...xyz123",
      "is_active": true,
      "is_valid_status": true,
      "last_used_at": null,
      "usage_count": 0,
      "allowed_ips": [],
      "created_at": "2025-11-01T08:00:00Z",
      "expires_at": null
    }
  ]
}
```

**Query Parameters (اختیاری):**
- `page`: شماره صفحه (برای pagination)
- `page_size`: تعداد آیتم در هر صفحه (پیش‌فرض: 20)

**مثال با Pagination:**
```bash
curl -X GET "https://api.pilito.com/api/v1/integrations/tokens/?page=2&page_size=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### 2. دریافت یک Token خاص

**Endpoint:** `GET /api/v1/integrations/tokens/{token_id}/`

**Authentication:** Required (Bearer Token)

**دستور curl:**
```bash
curl -X GET "https://api.pilito.com/api/v1/integrations/tokens/1616a793-eb91-416b-ada7-11c87cf237cd/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

**Response (200 OK):**
```json
{
  "id": "1616a793-eb91-416b-ada7-11c87cf237cd",
  "user_id": 13,
  "user_email": "iamyaserm@gmail.com",
  "integration_type": "woocommerce",
  "integration_type_display": "WooCommerce",
  "name": "faracoach (woocommerce)",
  "token_preview": "wc_sk...qmy0lk",
  "is_active": true,
  "is_valid_status": true,
  "last_used_at": "2025-11-11T21:30:00Z",
  "usage_count": 45,
  "allowed_ips": [],
  "created_at": "2025-10-15T10:20:00Z",
  "expires_at": null
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Not found."
}
```

---

## 📊 فیلدهای Response

| فیلد | نوع | توضیح |
|------|-----|-------|
| `id` | UUID | شناسه یکتای token |
| `user_id` | Integer | شناسه کاربر |
| `user_email` | String | ایمیل کاربر |
| `integration_type` | String | نوع integration (`woocommerce`, `shopify`, `custom`) |
| `integration_type_display` | String | نام نمایشی نوع integration |
| `name` | String | نام دلخواه token (مثلاً "faracoach (woocommerce)") |
| `token_preview` | String | پیش‌نمایش امن token (مثلاً `wc_sk...qmy0lk`) |
| `is_active` | Boolean | آیا token فعال است |
| `is_valid_status` | Boolean | آیا token معتبر است (فعال + منقضی نشده) |
| `last_used_at` | DateTime/null | آخرین زمان استفاده (null = هرگز استفاده نشده) |
| `usage_count` | Integer | تعداد دفعات استفاده از token |
| `allowed_ips` | Array | لیست IPهای مجاز (خالی = همه IPها مجاز) |
| `created_at` | DateTime | تاریخ و زمان ساخت token |
| `expires_at` | DateTime/null | تاریخ انقضا (null = بدون انقضا) |

---

## 🎨 مثال React/TypeScript

### 1. Component کامل برای نمایش Tokens

```tsx
import React, { useState, useEffect } from 'react';

interface IntegrationToken {
  id: string;
  user_id: number;
  user_email: string;
  integration_type: 'woocommerce' | 'shopify' | 'custom';
  integration_type_display: string;
  name: string;
  token_preview: string;
  is_active: boolean;
  is_valid_status: boolean;
  last_used_at: string | null;
  usage_count: number;
  allowed_ips: string[];
  created_at: string;
  expires_at: string | null;
}

interface TokensResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: IntegrationToken[];
}

const IntegrationTokensPage: React.FC = () => {
  const [tokens, setTokens] = useState<IntegrationToken[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTokens();
  }, []);

  const loadTokens = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/integrations/tokens/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: TokensResponse = await response.json();
      setTokens(data.results || []);
    } catch (err) {
      console.error('Error loading tokens:', err);
      setError('خطا در بارگذاری tokens');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('fa-IR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="loading-container">
        <p>در حال بارگذاری...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <p className="error-message">{error}</p>
        <button onClick={loadTokens}>تلاش مجدد</button>
      </div>
    );
  }

  return (
    <div className="integration-tokens-page">
      <div className="page-header">
        <h1>Integration Tokens</h1>
        <p className="page-description">
          Tokens برای اتصال پلاگین WordPress به سیستم
        </p>
      </div>

      {tokens.length === 0 ? (
        <div className="empty-state">
          <p>هیچ tokenی یافت نشد</p>
          <p className="empty-hint">
            برای ساخت token جدید، لطفاً با ادمین تماس بگیرید
          </p>
        </div>
      ) : (
        <div className="tokens-grid">
          {tokens.map(token => (
            <div 
              key={token.id} 
              className={`token-card ${token.is_valid_status ? 'active' : 'inactive'}`}
            >
              {/* Header */}
              <div className="token-header">
                <div className="token-title-section">
                  <h3>{token.name}</h3>
                  <span className="integration-badge">
                    {token.integration_type_display}
                  </span>
                </div>
                <div className={`status-badge ${token.is_valid_status ? 'valid' : 'invalid'}`}>
                  {token.is_valid_status ? '✅ فعال' : '❌ غیرفعال'}
                </div>
              </div>

              {/* Token Preview */}
              <div className="token-preview-section">
                <label>Token Preview:</label>
                <div className="token-preview-box">
                  <code>{token.token_preview}</code>
                  <button 
                    className="copy-btn"
                    onClick={() => {
                      navigator.clipboard.writeText(token.token_preview);
                      alert('Token preview کپی شد');
                    }}
                    title="کپی"
                  >
                    📋
                  </button>
                </div>
              </div>

              {/* Stats */}
              <div className="token-stats">
                <div className="stat-item">
                  <span className="stat-label">استفاده شده:</span>
                  <span className="stat-value">{token.usage_count} بار</span>
                </div>
                
                {token.last_used_at && (
                  <div className="stat-item">
                    <span className="stat-label">آخرین استفاده:</span>
                    <span className="stat-value">
                      {formatDate(token.last_used_at)}
                    </span>
                  </div>
                )}
                
                <div className="stat-item">
                  <span className="stat-label">ساخته شده:</span>
                  <span className="stat-value">
                    {formatDate(token.created_at)}
                  </span>
                </div>

                {token.expires_at && (
                  <div className="stat-item">
                    <span className="stat-label">انقضا:</span>
                    <span className="stat-value">
                      {formatDate(token.expires_at)}
                    </span>
                  </div>
                )}
              </div>

              {/* IP Whitelist */}
              {token.allowed_ips && token.allowed_ips.length > 0 && (
                <div className="ip-whitelist">
                  <label>IPهای مجاز:</label>
                  <div className="ip-list">
                    {token.allowed_ips.map((ip, index) => (
                      <span key={index} className="ip-badge">{ip}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Warning for inactive tokens */}
              {!token.is_valid_status && (
                <div className="warning-box">
                  ⚠️ این token غیرفعال است یا منقضی شده است
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default IntegrationTokensPage;
```

### 2. CSS برای Styling

```css
.integration-tokens-page {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 8px;
}

.page-description {
  color: #6b7280;
  font-size: 14px;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 64px 24px;
  background: #f9fafb;
  border-radius: 12px;
}

.empty-state p {
  font-size: 16px;
  color: #374151;
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 14px;
  color: #6b7280;
}

/* Tokens Grid */
.tokens-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 24px;
}

/* Token Card */
.token-card {
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  transition: all 0.2s;
}

.token-card:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.token-card.active {
  border-color: #10b981;
}

.token-card.inactive {
  border-color: #ef4444;
  opacity: 0.8;
}

/* Token Header */
.token-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.token-title-section {
  flex: 1;
}

.token-title-section h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #111827;
}

.integration-badge {
  display: inline-block;
  padding: 4px 12px;
  background: #eff6ff;
  color: #1e40af;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.status-badge.valid {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.invalid {
  background: #fee2e2;
  color: #991b1b;
}

/* Token Preview */
.token-preview-section {
  margin-bottom: 20px;
}

.token-preview-section label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.token-preview-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.token-preview-box code {
  flex: 1;
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  color: #111827;
  background: transparent;
}

.copy-btn {
  padding: 6px 10px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.2s;
}

.copy-btn:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

/* Token Stats */
.token-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 20px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.stat-value {
  font-size: 14px;
  color: #111827;
  font-weight: 600;
}

/* IP Whitelist */
.ip-whitelist {
  margin-bottom: 16px;
}

.ip-whitelist label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 8px;
}

.ip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.ip-badge {
  padding: 4px 10px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 12px;
  font-family: monospace;
  color: #374151;
}

/* Warning Box */
.warning-box {
  padding: 12px;
  background: #fef3c7;
  border: 1px solid #fbbf24;
  border-radius: 8px;
  color: #92400e;
  font-size: 14px;
  margin-top: 16px;
}

/* Loading & Error States */
.loading-container,
.error-container {
  text-align: center;
  padding: 64px 24px;
}

.error-message {
  color: #dc2626;
  font-size: 16px;
  margin-bottom: 16px;
}

/* Responsive */
@media (max-width: 768px) {
  .tokens-grid {
    grid-template-columns: 1fr;
  }
  
  .token-stats {
    grid-template-columns: 1fr;
  }
}
```

### 3. Hook برای استفاده مجدد

```tsx
import { useState, useEffect } from 'react';

interface IntegrationToken {
  id: string;
  user_id: number;
  user_email: string;
  integration_type: 'woocommerce' | 'shopify' | 'custom';
  integration_type_display: string;
  name: string;
  token_preview: string;
  is_active: boolean;
  is_valid_status: boolean;
  last_used_at: string | null;
  usage_count: number;
  allowed_ips: string[];
  created_at: string;
  expires_at: string | null;
}

export const useIntegrationTokens = () => {
  const [tokens, setTokens] = useState<IntegrationToken[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTokens = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/integrations/tokens/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setTokens(data.results || []);
    } catch (err) {
      console.error('Error loading tokens:', err);
      setError('خطا در بارگذاری tokens');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTokens();
  }, []);

  return {
    tokens,
    loading,
    error,
    refetch: loadTokens
  };
};
```

**استفاده از Hook:**
```tsx
const MyComponent = () => {
  const { tokens, loading, error, refetch } = useIntegrationTokens();

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      {tokens.map(token => (
        <div key={token.id}>{token.name}</div>
      ))}
    </div>
  );
};
```

---

## 🔒 نکات امنیتی

1. **Token کامل نمایش داده نمی‌شود:** API فقط `token_preview` را برمی‌گرداند (مثلاً `wc_sk...qmy0lk`)
2. **فقط tokens کاربر:** هر کاربر فقط tokens خودش را می‌بیند
3. **Authentication ضروری:** همه endpoints نیاز به Bearer Token دارند
4. **HTTPS:** همیشه از HTTPS استفاده کنید

---

## ⚠️ محدودیت‌ها

- **ساخت Token:** از طریق Admin Panel انجام می‌شود (API در دسترس نیست)
- **حذف Token:** از طریق Admin Panel انجام می‌شود (API در دسترس نیست)
- **Token کامل:** فقط در زمان ساخت نمایش داده می‌شود (در API موجود نیست)

---

## 📝 مثال استفاده در TypeScript

```typescript
// types.ts
export interface IntegrationToken {
  id: string;
  user_id: number;
  user_email: string;
  integration_type: 'woocommerce' | 'shopify' | 'custom';
  integration_type_display: string;
  name: string;
  token_preview: string;
  is_active: boolean;
  is_valid_status: boolean;
  last_used_at: string | null;
  usage_count: number;
  allowed_ips: string[];
  created_at: string;
  expires_at: string | null;
}

// api.ts
export const fetchIntegrationTokens = async (): Promise<IntegrationToken[]> => {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/v1/integrations/tokens/', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    throw new Error('Failed to fetch tokens');
  }

  const data = await response.json();
  return data.results;
};

export const fetchIntegrationToken = async (tokenId: string): Promise<IntegrationToken> => {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`/api/v1/integrations/tokens/${tokenId}/`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    throw new Error('Failed to fetch token');
  }

  return await response.json();
};
```

---

## ✅ Checklist برای پیاده‌سازی

- [x] API برای لیست tokens آماده است
- [x] API برای دریافت یک token خاص آماده است
- [ ] Component React برای نمایش tokens
- [ ] Styling برای token cards
- [ ] نمایش وضعیت token (فعال/غیرفعال)
- [ ] نمایش آمار استفاده
- [ ] نمایش تاریخ ساخت و آخرین استفاده
- [ ] Responsive design برای موبایل

---

## 🔗 لینک‌های مرتبط

- [WooCommerce Sync API](./../wordpress/WOOCOMMERCE_FRONTEND_API.md)
- [WordPress Plugin Documentation](./../wordpress/)

