# Async AI Prompt Generation with Status Tracking

## 🎯 Overview

The prompt generation system now supports **asynchronous processing** with real-time status tracking. This provides a much better user experience by:

1. **Immediate Response** - Returns instantly instead of blocking for 5-10 seconds
2. **Progress Updates** - Shows real-time progress (0-100%)  
3. **Status Messages** - Informative messages at each step
4. **Error Handling** - Clear error messages if something fails

---

## 📊 Current vs New Behavior

### ❌ Old Synchronous Behavior
```
Frontend → POST /generate-prompt/ → [WAITING 5-10s...] → Response
```
**Problems:**
- Frontend blocked for 5-10 seconds
- No progress indication
- Poor UX (user thinks app is frozen)
- No way to cancel

### ✅ New Asynchronous Behavior
```
Frontend → POST /generate-prompt-async/ → Immediate response with task_id
Frontend → Poll GET /status/{task_id}/ → Progress updates (0%, 30%, 50%, 90%, 100%)
```
**Benefits:**
- Frontend gets immediate response (< 100ms)
- Show loading spinner with progress bar
- Better UX with status messages
- Can implement cancellation if needed

---

## 🚀 API Endpoints

### 1. Start Async Generation (Recommended)

```http
POST /api/v1/web-knowledge/generate-prompt-async/
```

**Request:**
```json
{
  "manual_prompt": "Your manual prompt text here..."
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "task_id": "abc123-def456-ghi789",
  "status": "queued",
  "message": "Prompt generation started. Use task_id to check status.",
  "status_url": "/api/v1/web-knowledge/generate-prompt-async/status/abc123-def456-ghi789/"
}
```

### 2. Check Generation Status

```http
GET /api/v1/web-knowledge/generate-prompt-async/status/{task_id}/
```

**Status Responses:**

#### ⏳ Queued (0%)
```json
{
  "status": "queued",
  "progress": 0,
  "message": "Task queued, waiting to start...",
  "created_at": "2025-01-10T12:00:00Z"
}
```

#### 🔄 Initializing (10%)
```json
{
  "status": "processing",
  "progress": 10,
  "message": "Initializing AI generation...",
  "created_at": "2025-01-10T12:00:00Z"
}
```

#### 🔍 Checking Tokens (30%)
```json
{
  "status": "processing",
  "progress": 30,
  "message": "Checking tokens...",
  "created_at": "2025-01-10T12:00:00Z"
}
```

#### 🤖 Generating with AI (50%)
```json
{
  "status": "processing",
  "progress": 50,
  "message": "Generating enhanced prompt with AI...",
  "created_at": "2025-01-10T12:00:00Z"
}
```

#### ⏰ Waiting for AI (70%)
```json
{
  "status": "processing",
  "progress": 70,
  "message": "Waiting for AI response...",
  "created_at": "2025-01-10T12:00:00Z"
}
```

#### ✨ Finalizing (90%)
```json
{
  "status": "processing",
  "progress": 90,
  "message": "Finalizing...",
  "created_at": "2025-01-10T12:00:00Z"
}
```

#### ✅ Completed (100%)
```json
{
  "status": "completed",
  "progress": 100,
  "message": "Prompt generated successfully",
  "prompt": "Your enhanced AI-generated prompt here...",
  "generated_by_ai": true,
  "created_at": "2025-01-10T12:00:00Z",
  "completed_at": "2025-01-10T12:00:05Z"
}
```

#### ❌ Failed
```json
{
  "status": "failed",
  "progress": 100,
  "message": "Insufficient tokens",
  "error": "You need at least 700 tokens for prompt enhancement. Available: 250",
  "created_at": "2025-01-10T12:00:00Z"
}
```

### 3. Synchronous Generation (Legacy - Still Available)

```http
POST /api/v1/web-knowledge/generate-prompt/
```

**⚠️ Note:** This endpoint still works but blocks for 5-10 seconds. Use async version for better UX.

---

## 💻 Frontend Implementation

### React Example with Hooks

```jsx
import React, { useState, useEffect, useRef } from 'react';

function PromptGenerator() {
  const [manualPrompt, setManualPrompt] = useState('');
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [generatedPrompt, setGeneratedPrompt] = useState(null);
  const [error, setError] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const pollingInterval = useRef(null);

  // Start async generation
  const handleGenerate = async () => {
    try {
      setIsGenerating(true);
      setError(null);
      setProgress(0);
      
      const response = await fetch('/api/v1/web-knowledge/generate-prompt-async/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ manual_prompt: manualPrompt })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setTaskId(data.task_id);
        // Start polling
        startPolling(data.task_id);
      } else {
        setError(data.message);
        setIsGenerating(false);
      }
    } catch (err) {
      setError('Failed to start generation');
      setIsGenerating(false);
    }
  };

  // Poll for status
  const startPolling = (taskId) => {
    pollingInterval.current = setInterval(async () => {
      try {
        const response = await fetch(
          `/api/v1/web-knowledge/generate-prompt-async/status/${taskId}/`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          }
        );
        
        const data = await response.json();
        
        setStatus(data.status);
        setProgress(data.progress || 0);
        
        if (data.status === 'completed') {
          // Success!
          setGeneratedPrompt(data.prompt);
          setIsGenerating(false);
          stopPolling();
        } else if (data.status === 'failed') {
          // Error
          setError(data.error || data.message);
          setIsGenerating(false);
          stopPolling();
        }
        // Otherwise keep polling (status: queued or processing)
        
      } catch (err) {
        setError('Failed to check status');
        setIsGenerating(false);
        stopPolling();
      }
    }, 1000); // Poll every 1 second
  };

  // Stop polling
  const stopPolling = () => {
    if (pollingInterval.current) {
      clearInterval(pollingInterval.current);
      pollingInterval.current = null;
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => stopPolling();
  }, []);

  return (
    <div className="prompt-generator">
      <h2>AI Prompt Generator</h2>
      
      <textarea
        value={manualPrompt}
        onChange={(e) => setManualPrompt(e.target.value)}
        placeholder="Enter your manual prompt..."
        rows={8}
        disabled={isGenerating}
      />
      
      <button 
        onClick={handleGenerate} 
        disabled={isGenerating || !manualPrompt.trim()}
      >
        {isGenerating ? 'Generating...' : 'Generate AI Prompt'}
      </button>
      
      {isGenerating && (
        <div className="generation-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="progress-text">
            {progress}% - {status?.message || 'Processing...'}
          </p>
        </div>
      )}
      
      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}
      
      {generatedPrompt && (
        <div className="result">
          <h3>✅ Generated Prompt:</h3>
          <pre>{generatedPrompt}</pre>
          <button onClick={() => {
            navigator.clipboard.writeText(generatedPrompt);
            alert('Copied to clipboard!');
          }}>
            Copy to Clipboard
          </button>
        </div>
      )}
    </div>
  );
}

export default PromptGenerator;
```

### JavaScript/Fetch Example

```javascript
class PromptGeneratorAPI {
  constructor(apiBaseUrl, authToken) {
    this.apiBaseUrl = apiBaseUrl;
    this.authToken = authToken;
    this.pollingInterval = null;
  }

  // Start async generation
  async startGeneration(manualPrompt, onProgress, onComplete, onError) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/generate-prompt-async/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ manual_prompt: manualPrompt })
      });

      const data = await response.json();

      if (data.success) {
        // Start polling
        this.pollStatus(data.task_id, onProgress, onComplete, onError);
        return data.task_id;
      } else {
        onError(data.message);
        return null;
      }
    } catch (error) {
      onError('Failed to start generation');
      return null;
    }
  }

  // Poll for status
  pollStatus(taskId, onProgress, onComplete, onError) {
    this.pollingInterval = setInterval(async () => {
      try {
        const response = await fetch(
          `${this.apiBaseUrl}/generate-prompt-async/status/${taskId}/`,
          {
            headers: {
              'Authorization': `Bearer ${this.authToken}`
            }
          }
        );

        const data = await response.json();

        // Call progress callback
        onProgress({
          status: data.status,
          progress: data.progress || 0,
          message: data.message
        });

        if (data.status === 'completed') {
          this.stopPolling();
          onComplete(data.prompt, data.generated_by_ai);
        } else if (data.status === 'failed') {
          this.stopPolling();
          onError(data.error || data.message);
        }
      } catch (error) {
        this.stopPolling();
        onError('Failed to check status');
      }
    }, 1000); // Poll every 1 second
  }

  // Stop polling
  stopPolling() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  }
}

// Usage Example
const promptAPI = new PromptGeneratorAPI(
  'http://localhost:8000/api/v1/web-knowledge',
  'your-auth-token'
);

promptAPI.startGeneration(
  'My manual prompt text...',
  
  // onProgress callback
  (progress) => {
    console.log(`${progress.progress}%: ${progress.message}`);
    updateProgressBar(progress.progress);
    updateStatusMessage(progress.message);
  },
  
  // onComplete callback
  (prompt, generatedByAI) => {
    console.log('Generated:', prompt);
    console.log('By AI:', generatedByAI);
    displayGeneratedPrompt(prompt);
  },
  
  // onError callback
  (error) => {
    console.error('Error:', error);
    showErrorMessage(error);
  }
);
```

---

## 🎨 UI/UX Recommendations

### Progress Indicator

```html
<div class="prompt-generation-loader">
  <!-- Progress bar -->
  <div class="progress-bar">
    <div class="progress-fill" style="width: 50%"></div>
  </div>
  
  <!-- Status message -->
  <p class="status-message">50% - Generating enhanced prompt with AI...</p>
  
  <!-- Optional: Animated spinner -->
  <div class="spinner"></div>
</div>
```

### CSS Example

```css
.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #8BC34A);
  transition: width 0.3s ease;
}

.status-message {
  margin-top: 8px;
  font-size: 14px;
  color: #666;
  text-align: center;
}

.spinner {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #4CAF50;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 16px auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
```

---

## ⚙️ Configuration

### Polling Interval
- **Recommended:** 1000ms (1 second)
- **Minimum:** 500ms (don't go lower to avoid server overload)
- **Maximum:** 3000ms (status updates may feel sluggish)

### Timeout
- Status is stored in cache for **10 minutes (600 seconds)**
- After 10 minutes, status data expires
- Frontend should handle `404 Not Found` gracefully

### Retry Logic
```javascript
const MAX_RETRIES = 3;
let retryCount = 0;

async function checkStatusWithRetry(taskId) {
  try {
    const response = await fetch(`/status/${taskId}/`);
    const data = await response.json();
    retryCount = 0; // Reset on success
    return data;
  } catch (error) {
    retryCount++;
    if (retryCount < MAX_RETRIES) {
      // Wait and retry
      await new Promise(resolve => setTimeout(resolve, 2000));
      return checkStatusWithRetry(taskId);
    } else {
      throw new Error('Max retries exceeded');
    }
  }
}
```

---

## 🔍 Status Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│                    Status Lifecycle                      │
└─────────────────────────────────────────────────────────┘

┌──────────┐
│ Queued   │  Progress: 0%
│ (0%)     │  Message: "Task queued, waiting to start..."
└────┬─────┘
     │
     ▼
┌──────────┐
│Processing│  Progress: 10-90%
│(10-90%)  │  Messages:
└────┬─────┘  - "Initializing AI generation..." (10%)
     │        - "Checking tokens..." (30%)
     │        - "Generating with AI..." (50%)
     │        - "Waiting for AI response..." (70%)
     │        - "Finalizing..." (90%)
     │
     ▼
┌──────────┐       ┌──────────┐
│Completed │       │ Failed   │
│ (100%)   │       │ (100%)   │
└──────────┘       └──────────┘
 Success!          Error occurred
```

---

## 📱 Mobile Considerations

1. **Background Handling**: Stop polling when app goes to background
2. **Network Changes**: Handle network disconnections gracefully
3. **Battery**: Use exponential backoff if generation takes too long
4. **Notifications**: Consider push notification when complete (optional)

```javascript
// React Native example
useEffect(() => {
  const subscription = AppState.addEventListener('change', (nextAppState) => {
    if (nextAppState === 'background') {
      stopPolling();
    } else if (nextAppState === 'active' && taskId) {
      startPolling(taskId); // Resume
    }
  });

  return () => subscription.remove();
}, [taskId]);
```

---

## 🐛 Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `manual_prompt is required` | Empty prompt | Validate input before submit |
| `Subscription is not active` | User subscription expired | Show upgrade prompt |
| `Insufficient tokens` | Not enough tokens | Show token purchase options |
| `Task not found` | Task expired (>10 min) | Start new generation |
| `AI generation failed` | Gemini API error | Falls back to simple combination |

### Error UI Example

```jsx
{error && (
  <div className="error-alert">
    <span className="error-icon">⚠️</span>
    <div className="error-content">
      <h4>Generation Failed</h4>
      <p>{error}</p>
      {error.includes('tokens') && (
        <button onClick={handlePurchaseTokens}>
          Purchase More Tokens
        </button>
      )}
      {error.includes('subscription') && (
        <button onClick={handleUpgradeSubscription}>
          Upgrade Subscription
        </button>
      )}
      <button onClick={handleRetry}>Try Again</button>
    </div>
  </div>
)}
```

---

## 📊 Comparison: Sync vs Async

| Feature | Synchronous (Old) | Asynchronous (New) |
|---------|-------------------|-------------------|
| **Response Time** | 5-10 seconds | < 100ms |
| **Progress Updates** | ❌ No | ✅ Yes (0-100%) |
| **Status Messages** | ❌ No | ✅ Yes |
| **User Experience** | 😞 Poor | 😊 Excellent |
| **Can Show Loading** | ⚠️ Simple spinner | ✅ Progress bar |
| **Error Handling** | ⚠️ Basic | ✅ Detailed |
| **Cancellable** | ❌ No | ✅ Possible |
| **Backend Load** | ⚠️ Blocks worker | ✅ Background task |

---

## 🚦 Migration Guide

### Step 1: Update Frontend to Use Async Endpoint

**Before:**
```javascript
const response = await fetch('/generate-prompt/', {
  method: 'POST',
  body: JSON.stringify({ manual_prompt: text })
});
const data = await response.json();
// Use data.prompt
```

**After:**
```javascript
// Start generation
const response = await fetch('/generate-prompt-async/', {
  method: 'POST',
  body: JSON.stringify({ manual_prompt: text })
});
const { task_id } = await response.json();

// Poll for status
const pollInterval = setInterval(async () => {
  const statusRes = await fetch(`/generate-prompt-async/status/${task_id}/`);
  const status = await statusRes.json();
  
  if (status.status === 'completed') {
    clearInterval(pollInterval);
    // Use status.prompt
  }
}, 1000);
```

### Step 2: Add Progress UI

Add progress bar and status message components to your UI.

### Step 3: Test Thoroughly

Test edge cases:
- Network disconnections
- Expired tasks (after 10 minutes)
- Token errors
- Subscription errors

---

## 🎯 Best Practices

1. **✅ Show Progress** - Always display progress bar (0-100%)
2. **✅ Show Status** - Display current status message
3. **✅ Handle Errors** - Show user-friendly error messages
4. **✅ Add Timeout** - Stop polling after 2 minutes maximum
5. **✅ Cleanup** - Clear intervals on unmount
6. **✅ Retry Logic** - Implement retry for network errors
7. **✅ Loading State** - Disable input during generation
8. **❌ Don't Poll Too Fast** - Use 1 second intervals
9. **❌ Don't Block UI** - Keep UI responsive during generation
10. **❌ Don't Forget Cleanup** - Always clear intervals

---

## 📞 Support

**Need Help?**
- Check the examples above
- Review error messages carefully
- Test with the synchronous endpoint first
- Contact backend team if issues persist

**Backend Endpoints:**
- Async Start: `POST /api/v1/web-knowledge/generate-prompt-async/`
- Status Check: `GET /api/v1/web-knowledge/generate-prompt-async/status/{task_id}/`
- Sync (Legacy): `POST /api/v1/web-knowledge/generate-prompt/`

---

**Last Updated:** January 2025  
**Version:** 1.0

