# BusinessPromptData API Documentation

## Overview

The BusinessPromptData API allows frontend applications to retrieve BusinessPrompt configurations and their associated data (key-value pairs with optional file attachments). This data is managed by admins through the Django admin panel.

**Note:** These are **read-only** public APIs. All CRUD operations are performed through the Admin Panel.

## Base URL

```
/api/settings/
```

## Authentication

These endpoints are **publicly accessible** (no authentication required). They are designed for displaying configuration data to end users.

---

## Endpoints

### 1. List All BusinessPrompts

**GET** `/api/settings/business-prompts/`

Get all BusinessPrompts with a count of their associated data items.

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search by name |
| `ordering` | string | Order by: `name`, `-name`, `created_at`, `-created_at` |

#### Example Request

```javascript
const response = await fetch('/api/settings/business-prompts/');
const data = await response.json();
```

#### Example Response

```json
[
  {
    "id": 1,
    "name": "Sales Bot Prompt",
    "data_count": 3,
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
  },
  {
    "id": 2,
    "name": "Support Bot Prompt",
    "data_count": 5,
    "created_at": "2024-01-14T09:00:00Z",
    "updated_at": "2024-01-14T09:00:00Z"
  }
]
```

---

### 2. Get BusinessPrompt with All Data

**GET** `/api/settings/business-prompts/{id}/`

Get a single BusinessPrompt with all its associated data entries (full details including files).

#### Example Request

```javascript
const response = await fetch('/api/settings/business-prompts/1/');
const data = await response.json();
```

#### Example Response

```json
{
  "id": 1,
  "name": "Sales Bot Prompt",
  "prompt": "You are a helpful sales assistant...",
  "ai_answer_prompt": "When answering, always be friendly...",
  "prompt_data": [
    {
      "id": 1,
      "business": 1,
      "business_name": "Sales Bot Prompt",
      "key": "logo",
      "value": "Company logo for responses",
      "file": "/media/business_prompt_data/2024/01/15/logo.png",
      "file_url": "https://api.pilito.com/media/business_prompt_data/2024/01/15/logo.png",
      "file_name": "logo.png",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "business": 1,
      "business_name": "Sales Bot Prompt",
      "key": "pricing_doc",
      "value": "Official pricing document 2024",
      "file": "/media/business_prompt_data/2024/01/15/pricing.pdf",
      "file_url": "https://api.pilito.com/media/business_prompt_data/2024/01/15/pricing.pdf",
      "file_name": "pricing.pdf",
      "created_at": "2024-01-15T11:00:00Z",
      "updated_at": "2024-01-15T11:00:00Z"
    },
    {
      "id": 3,
      "business": 1,
      "business_name": "Sales Bot Prompt",
      "key": "contact_info",
      "value": "Phone: +98 21 1234 5678\nEmail: sales@company.com",
      "file": null,
      "file_url": null,
      "file_name": null,
      "created_at": "2024-01-15T12:00:00Z",
      "updated_at": "2024-01-15T12:00:00Z"
    }
  ],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

---

### 3. List All BusinessPromptData

**GET** `/api/settings/business-prompt-data/`

Get all data entries across all BusinessPrompts.

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `business` | integer | Filter by BusinessPrompt ID |
| `key` | string | Filter by exact key name |
| `search` | string | Search in key and value fields |
| `ordering` | string | Order by: `key`, `-key`, `created_at`, `-created_at` |

#### Example Request

```javascript
// Get all data for BusinessPrompt ID 1
const response = await fetch('/api/settings/business-prompt-data/?business=1');
const data = await response.json();
```

#### Example Response

```json
[
  {
    "id": 1,
    "business": 1,
    "business_name": "Sales Bot Prompt",
    "key": "logo",
    "value": "Company logo",
    "file": "/media/business_prompt_data/2024/01/15/logo.png",
    "file_url": "https://api.pilito.com/media/business_prompt_data/2024/01/15/logo.png",
    "file_name": "logo.png",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### 4. Get Single BusinessPromptData by ID

**GET** `/api/settings/business-prompt-data/{id}/`

Get a specific data entry by its ID.

#### Example Request

```javascript
const response = await fetch('/api/settings/business-prompt-data/1/');
const data = await response.json();
```

---

### 5. Get All Data for a Specific BusinessPrompt

**GET** `/api/settings/business-prompts/{business_id}/data/`

Get all data entries for a specific BusinessPrompt.

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search in key and value fields |
| `ordering` | string | Order by: `key`, `-key`, `created_at`, `-created_at` |

#### Example Request

```javascript
const response = await fetch('/api/settings/business-prompts/1/data/');
const data = await response.json();
```

---

### 6. Get Data Entry by BusinessPrompt and Key

**GET** `/api/settings/business-prompts/{business_id}/data/{key}/`

Get a specific data entry by BusinessPrompt ID and key name. Useful for fetching specific configuration values.

#### Example Request

```javascript
// Get the logo for BusinessPrompt ID 1
const response = await fetch('/api/settings/business-prompts/1/data/logo/');
const data = await response.json();
```

#### Example Response

```json
{
  "id": 1,
  "business": 1,
  "business_name": "Sales Bot Prompt",
  "key": "logo",
  "value": "Company logo",
  "file": "/media/business_prompt_data/2024/01/15/logo.png",
  "file_url": "https://api.pilito.com/media/business_prompt_data/2024/01/15/logo.png",
  "file_name": "logo.png",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique identifier |
| `business` | integer | BusinessPrompt ID |
| `business_name` | string | BusinessPrompt name |
| `key` | string | Data field name |
| `value` | string | Text value (may be empty if file-only) |
| `file` | string | Relative file path (null if no file) |
| `file_url` | string | Full URL to download file (null if no file) |
| `file_name` | string | Original file name (null if no file) |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |

---

## React/Next.js Examples

### Custom Hook for BusinessPromptData

```typescript
// hooks/useBusinessPromptData.ts
import { useState, useCallback, useEffect } from 'react';

interface BusinessPromptData {
  id: number;
  business: number;
  business_name: string;
  key: string;
  value: string;
  file_url: string | null;
  file_name: string | null;
  created_at: string;
  updated_at: string;
}

interface BusinessPrompt {
  id: number;
  name: string;
  prompt: string;
  ai_answer_prompt: string | null;
  prompt_data: BusinessPromptData[];
  created_at: string;
  updated_at: string;
}

export function useBusinessPrompt(businessId: number) {
  const [data, setData] = useState<BusinessPrompt | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/settings/business-prompts/${businessId}/`
      );
      if (!response.ok) {
        throw new Error('Failed to fetch');
      }
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [businessId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Helper to get data by key
  const getDataByKey = useCallback(
    (key: string): BusinessPromptData | undefined => {
      return data?.prompt_data.find((item) => item.key === key);
    },
    [data]
  );

  return {
    data,
    loading,
    error,
    refetch: fetchData,
    getDataByKey,
  };
}

// Hook for fetching a single key directly
export function useBusinessPromptDataByKey(businessId: number, key: string) {
  const [data, setData] = useState<BusinessPromptData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const response = await fetch(
          `/api/settings/business-prompts/${businessId}/data/${key}/`
        );
        if (!response.ok) {
          throw new Error('Not found');
        }
        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [businessId, key]);

  return { data, loading, error };
}
```

### Component Example: Display Business Configuration

```tsx
// components/BusinessConfig.tsx
import { useBusinessPrompt } from '@/hooks/useBusinessPromptData';

interface Props {
  businessId: number;
}

export function BusinessConfig({ businessId }: Props) {
  const { data, loading, error, getDataByKey } = useBusinessPrompt(businessId);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!data) return <div>No data found</div>;

  const logo = getDataByKey('logo');
  const contactInfo = getDataByKey('contact_info');
  const pricingDoc = getDataByKey('pricing_doc');

  return (
    <div className="business-config">
      <h2>{data.name}</h2>

      {/* Display Logo */}
      {logo?.file_url && (
        <div className="logo-section">
          <img src={logo.file_url} alt="Business Logo" />
        </div>
      )}

      {/* Display Contact Info */}
      {contactInfo && (
        <div className="contact-section">
          <h3>Contact Information</h3>
          <pre>{contactInfo.value}</pre>
        </div>
      )}

      {/* Download Pricing Document */}
      {pricingDoc?.file_url && (
        <div className="docs-section">
          <a
            href={pricingDoc.file_url}
            download={pricingDoc.file_name}
            className="download-btn"
          >
            📄 Download: {pricingDoc.file_name}
          </a>
        </div>
      )}

      {/* Display All Data */}
      <div className="all-data">
        <h3>All Configuration</h3>
        <table>
          <thead>
            <tr>
              <th>Key</th>
              <th>Value</th>
              <th>File</th>
            </tr>
          </thead>
          <tbody>
            {data.prompt_data.map((item) => (
              <tr key={item.id}>
                <td>{item.key}</td>
                <td>{item.value || '—'}</td>
                <td>
                  {item.file_url ? (
                    <a href={item.file_url} target="_blank" rel="noopener">
                      📎 {item.file_name}
                    </a>
                  ) : (
                    '—'
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

### Utility: Fetch Specific Key Value

```typescript
// utils/businessPromptUtils.ts

/**
 * Fetch a specific data value by business ID and key
 */
export async function getBusinessDataValue(
  businessId: number,
  key: string
): Promise<string | null> {
  try {
    const response = await fetch(
      `/api/settings/business-prompts/${businessId}/data/${key}/`
    );
    if (!response.ok) return null;
    const data = await response.json();
    return data.value || null;
  } catch {
    return null;
  }
}

/**
 * Fetch a specific file URL by business ID and key
 */
export async function getBusinessDataFileUrl(
  businessId: number,
  key: string
): Promise<string | null> {
  try {
    const response = await fetch(
      `/api/settings/business-prompts/${businessId}/data/${key}/`
    );
    if (!response.ok) return null;
    const data = await response.json();
    return data.file_url || null;
  } catch {
    return null;
  }
}
```

---

## Admin Panel Usage

All CRUD operations are performed through the Django Admin Panel:

### Creating BusinessPromptData

1. Go to **Admin Panel** → **💼 Business Prompts**
2. Click on a BusinessPrompt or create a new one
3. Scroll down to **Business Prompt Data** section
4. Click **Add another Business prompt data**
5. Fill in:
   - **Key**: A unique identifier (e.g., `logo`, `contact_info`, `pricing_doc`)
   - **Value**: Text content (optional if file is provided)
   - **File**: Upload a file (optional if value is provided)
6. Click **Save**

### Managing BusinessPromptData Separately

1. Go to **Admin Panel** → **📎 Business Prompt Data**
2. Here you can:
   - View all data entries across all BusinessPrompts
   - Filter by BusinessPrompt
   - Search by key or value
   - Edit or delete individual entries

---

## Error Codes

| Status | Description |
|--------|-------------|
| 200 | Success |
| 404 | BusinessPrompt or data not found |
| 400 | Bad request |

---

## Best Practices

1. **Use meaningful keys**: Use descriptive keys like `company_logo`, `pricing_2024`, `contact_email`
2. **Consistent naming**: Use snake_case for keys (e.g., `contact_info`, not `Contact Info`)
3. **File types**: Store logos as PNG/JPG, documents as PDF
4. **Caching**: Cache responses on the frontend for better performance
5. **Error handling**: Always handle 404 errors gracefully when fetching by key

