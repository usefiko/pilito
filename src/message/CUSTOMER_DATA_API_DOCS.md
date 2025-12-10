# CustomerData API Documentation

## Overview

The CustomerData API allows users to store custom key-value data (with optional file attachments) for their customers. Each user can create multiple data entries per customer, but each key must be unique per customer-user combination.

## Base URL

```
/api/message/
```

## Authentication

All endpoints require authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

---

## Endpoints

### 1. List All Customer Data

**GET** `/api/message/customer-data/`

Get all customer data created by the authenticated user.

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `customer` | integer | Filter by customer ID |
| `key` | string | Filter by exact key name |
| `search` | string | Search in key and value fields |
| `ordering` | string | Order by: `key`, `-key`, `created_at`, `-created_at` |

#### Example Request

```javascript
// JavaScript/Fetch
const response = await fetch('/api/message/customer-data/?customer=1&search=email', {
  headers: {
    'Authorization': 'Bearer <token>'
  }
});
const data = await response.json();
```

#### Example Response

```json
[
  {
    "id": 1,
    "customer": 1,
    "user": 5,
    "key": "company_email",
    "value": "contact@company.com",
    "file": null,
    "file_url": null,
    "file_name": null,
    "customer_name": "John Doe (@johndoe) | instagram",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  {
    "id": 2,
    "customer": 1,
    "user": 5,
    "key": "contract",
    "value": "Signed contract for 2024",
    "file": "/media/customer_data/2024/01/15/contract.pdf",
    "file_url": "https://api.pilito.com/media/customer_data/2024/01/15/contract.pdf",
    "file_name": "contract.pdf",
    "customer_name": "John Doe (@johndoe) | instagram",
    "created_at": "2024-01-15T11:00:00Z",
    "updated_at": "2024-01-15T11:00:00Z"
  }
]
```

---

### 2. Create Customer Data

**POST** `/api/message/customer-data/`

Create a new customer data entry. Supports both text values and file uploads.

#### Content Types

- **JSON** (`application/json`): For text-only data
- **Form Data** (`multipart/form-data`): For file uploads (with or without text)

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `customer` | integer | ✅ | Customer ID |
| `key` | string | ✅ | Data field name (unique per customer) |
| `value` | string | ❌* | Text value |
| `file` | file | ❌* | File attachment |

*At least one of `value` or `file` must be provided.

#### Example: Create Text Data (JSON)

```javascript
const response = await fetch('/api/message/customer-data/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    customer: 1,
    key: 'birthday',
    value: '1990-05-15'
  })
});
```

#### Example: Create with File Upload (FormData)

```javascript
const formData = new FormData();
formData.append('customer', 1);
formData.append('key', 'id_card');
formData.append('value', 'National ID Card');
formData.append('file', fileInput.files[0]);  // From <input type="file">

const response = await fetch('/api/message/customer-data/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <token>'
    // Don't set Content-Type - browser will set it with boundary
  },
  body: formData
});
```

#### Example Response (201 Created)

```json
{
  "id": 3,
  "customer": 1,
  "user": 5,
  "key": "id_card",
  "value": "National ID Card",
  "file": "/media/customer_data/2024/01/15/id_card.jpg",
  "file_url": "https://api.pilito.com/media/customer_data/2024/01/15/id_card.jpg",
  "file_name": "id_card.jpg",
  "customer_name": "John Doe (@johndoe) | instagram",
  "created_at": "2024-01-15T12:00:00Z",
  "updated_at": "2024-01-15T12:00:00Z"
}
```

#### Error Response (400 - Duplicate Key)

```json
{
  "key": ["A data field with key 'birthday' already exists for this customer. Use PUT to update it."]
}
```

---

### 3. Get Single Customer Data

**GET** `/api/message/customer-data/{id}/`

Get a specific customer data entry by ID.

#### Example Request

```javascript
const response = await fetch('/api/message/customer-data/3/', {
  headers: {
    'Authorization': 'Bearer <token>'
  }
});
```

#### Response

Same format as single item in list response.

---

### 4. Update Customer Data

**PUT** `/api/message/customer-data/{id}/`

Update an existing customer data entry. Supports partial updates.

#### Request Body (All fields optional)

| Field | Type | Description |
|-------|------|-------------|
| `key` | string | New key name |
| `value` | string | New text value |
| `file` | file | New file (replaces existing) |
| `remove_file` | boolean | Set `true` to remove existing file |

#### Example: Update Text Value

```javascript
const response = await fetch('/api/message/customer-data/3/', {
  method: 'PUT',
  headers: {
    'Authorization': 'Bearer <token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    value: 'Updated national ID information'
  })
});
```

#### Example: Replace File

```javascript
const formData = new FormData();
formData.append('file', newFileInput.files[0]);

const response = await fetch('/api/message/customer-data/3/', {
  method: 'PUT',
  headers: {
    'Authorization': 'Bearer <token>'
  },
  body: formData
});
```

#### Example: Remove File Only

```javascript
const response = await fetch('/api/message/customer-data/3/', {
  method: 'PUT',
  headers: {
    'Authorization': 'Bearer <token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    remove_file: true
  })
});
```

---

### 5. Delete Customer Data

**DELETE** `/api/message/customer-data/{id}/`

Delete a customer data entry. Also deletes any attached file.

#### Example Request

```javascript
const response = await fetch('/api/message/customer-data/3/', {
  method: 'DELETE',
  headers: {
    'Authorization': 'Bearer <token>'
  }
});
```

#### Response (200 OK)

```json
{
  "message": "Customer data 'id_card' deleted successfully",
  "deleted_key": "id_card"
}
```

---

### 6. Get All Data for a Specific Customer

**GET** `/api/message/customer/{customer_id}/data/`

Get all data entries for a specific customer.

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search in key and value fields |
| `ordering` | string | Order by: `key`, `-key`, `created_at`, `-created_at` |

#### Example Request

```javascript
const response = await fetch('/api/message/customer/1/data/', {
  headers: {
    'Authorization': 'Bearer <token>'
  }
});
```

---

### 7. Bulk Delete Customer Data

**POST** `/api/message/customer-data/bulk-delete/`

Delete multiple customer data entries at once. Also deletes any attached files.

#### Request Body

```json
{
  "data_ids": [1, 2, 3, 4]
}
```

#### Example Request

```javascript
const response = await fetch('/api/message/customer-data/bulk-delete/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    data_ids: [1, 2, 3]
  })
});
```

#### Response (200 OK)

```json
{
  "message": "Successfully deleted 3 customer data item(s)",
  "deleted_count": 3
}
```

---

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique identifier |
| `customer` | integer | Customer ID |
| `user` | integer | Owner user ID |
| `key` | string | Data field name |
| `value` | string | Text value (may be empty if file-only) |
| `file` | string | Relative file path (null if no file) |
| `file_url` | string | Full URL to download file (null if no file) |
| `file_name` | string | Original file name (null if no file) |
| `customer_name` | string | Human-readable customer name |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |

---

## React/Next.js Examples

### Custom Hook for Customer Data

```typescript
// hooks/useCustomerData.ts
import { useState, useCallback } from 'react';

interface CustomerData {
  id: number;
  customer: number;
  key: string;
  value: string;
  file_url: string | null;
  file_name: string | null;
  created_at: string;
  updated_at: string;
}

export function useCustomerData(customerId: number) {
  const [data, setData] = useState<CustomerData[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/message/customer/${customerId}/data/`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      const result = await response.json();
      setData(result);
    } finally {
      setLoading(false);
    }
  }, [customerId]);

  const createData = async (
    key: string,
    value?: string,
    file?: File
  ): Promise<CustomerData> => {
    const formData = new FormData();
    formData.append('customer', String(customerId));
    formData.append('key', key);
    if (value) formData.append('value', value);
    if (file) formData.append('file', file);

    const response = await fetch('/api/message/customer-data/', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.key?.[0] || 'Failed to create');
    }

    const newData = await response.json();
    setData((prev) => [newData, ...prev]);
    return newData;
  };

  const updateData = async (
    id: number,
    updates: { key?: string; value?: string; file?: File; remove_file?: boolean }
  ): Promise<CustomerData> => {
    const formData = new FormData();
    if (updates.key) formData.append('key', updates.key);
    if (updates.value !== undefined) formData.append('value', updates.value);
    if (updates.file) formData.append('file', updates.file);
    if (updates.remove_file) formData.append('remove_file', 'true');

    const response = await fetch(`/api/message/customer-data/${id}/`, {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`,
      },
      body: formData,
    });

    const updatedData = await response.json();
    setData((prev) =>
      prev.map((item) => (item.id === id ? updatedData : item))
    );
    return updatedData;
  };

  const deleteData = async (id: number): Promise<void> => {
    await fetch(`/api/message/customer-data/${id}/`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`,
      },
    });
    setData((prev) => prev.filter((item) => item.id !== id));
  };

  return {
    data,
    loading,
    fetchData,
    createData,
    updateData,
    deleteData,
  };
}
```

### File Upload Component

```tsx
// components/CustomerDataForm.tsx
import { useState } from 'react';

interface Props {
  customerId: number;
  onSuccess: () => void;
}

export function CustomerDataForm({ customerId, onSuccess }: Props) {
  const [key, setKey] = useState('');
  const [value, setValue] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('customer', String(customerId));
      formData.append('key', key);
      if (value) formData.append('value', value);
      if (file) formData.append('file', file);

      const response = await fetch('/api/message/customer-data/', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.key?.[0] || data.non_field_errors?.[0] || 'Error');
      }

      setKey('');
      setValue('');
      setFile(null);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="key">Key (Field Name)</label>
        <input
          id="key"
          type="text"
          value={key}
          onChange={(e) => setKey(e.target.value)}
          placeholder="e.g., birthday, company, contract"
          required
        />
      </div>

      <div>
        <label htmlFor="value">Value (Text)</label>
        <textarea
          id="value"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Enter text value..."
        />
      </div>

      <div>
        <label htmlFor="file">File Attachment</label>
        <input
          id="file"
          type="file"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        {file && <span>Selected: {file.name}</span>}
      </div>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      <button type="submit" disabled={loading || !key || (!value && !file)}>
        {loading ? 'Saving...' : 'Save Data'}
      </button>
    </form>
  );
}
```

---

## Error Codes

| Status | Description |
|--------|-------------|
| 200 | Success |
| 201 | Created successfully |
| 400 | Bad request (validation error, duplicate key) |
| 401 | Unauthorized (invalid/missing token) |
| 404 | Customer data not found or no permission |

---

## Best Practices

1. **Use meaningful keys**: Use descriptive keys like `company_email`, `contract_2024`, `id_card_front`
2. **Handle duplicates**: Check for 400 errors with duplicate key message
3. **File size limits**: Check your server's max upload size (usually 10-50MB)
4. **Cleanup**: Use bulk delete for cleaning up multiple entries
5. **Caching**: Cache customer data lists and refresh on mutations

