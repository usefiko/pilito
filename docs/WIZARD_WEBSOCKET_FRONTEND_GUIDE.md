# Wizard Status WebSocket - Frontend Integration Guide

## 📋 Overview

This guide shows you how to implement **real-time wizard status updates** using WebSocket, so users see changes **instantly** without page refresh.

**Benefits:**
- ✅ Real-time updates (< 100ms latency)
- ✅ No polling needed
- ✅ Better UX - instant feedback
- ✅ Lower network usage

---

## 🌐 Supported Languages

This WebSocket endpoint supports **multi-language** applications:
- 🇺🇸 English
- 🇹🇷 Turkish (Türkçe)
- 🇸🇦 Arabic (العربية)

**All field names are in English** - translate them in your frontend using i18n libraries.

---

## 🔌 WebSocket Endpoint

### Connection URL

```
ws://your-domain.com/ws/wizard-status/
```

**Development:**
```
ws://localhost:8000/ws/wizard-status/
```

**Production:**
```
wss://api.fiko.net/ws/wizard-status/
```

### Authentication

WebSocket uses the **same authentication** as your HTTP requests:
- Cookie-based session (if using Django sessions)
- JWT token in query string: `ws://domain/ws/wizard-status/?token=YOUR_JWT_TOKEN`

---

## 📡 Message Protocol

### Server → Client Messages

#### 1. Initial Status (sent on connect)

```json
{
  "type": "wizard_status",
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
  },
  "timestamp": "2025-10-22T12:34:56.789Z"
}
```

#### 2. Status Update (automatic on changes)

Same format as above, sent automatically when:
- User updates profile (name, phone, business_type)
- Manual prompt is saved
- Instagram/Telegram channel is connected/disconnected

### Client → Server Messages

#### Refresh Request

```json
{
  "type": "refresh"
}
```

Manually request fresh status update.

---

## 💻 Implementation Examples

### React + TypeScript

#### Basic Implementation

```typescript
import { useEffect, useState } from 'react';

interface WizardStatus {
  type: 'wizard_status';
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
  timestamp: string;
}

const WizardStatusLive: React.FC = () => {
  const [status, setStatus] = useState<WizardStatus | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    // Establish WebSocket connection
    const websocket = new WebSocket('ws://localhost:8000/ws/wizard-status/');
    
    websocket.onopen = () => {
      console.log('Connected to Wizard Status WebSocket');
      setIsConnected(true);
    };
    
    websocket.onmessage = (event) => {
      const data: WizardStatus = JSON.parse(event.data);
      console.log('Wizard Status Update:', data);
      setStatus(data); // UI updates automatically!
    };
    
    websocket.onerror = (error) => {
      console.error('WebSocket Error:', error);
    };
    
    websocket.onclose = () => {
      console.log('WebSocket Disconnected');
      setIsConnected(false);
    };
    
    setWs(websocket);
    
    // Cleanup on unmount
    return () => {
      websocket.close();
    };
  }, []);

  const refreshStatus = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'refresh' }));
    }
  };

  if (!status) {
    return <div>Connecting...</div>;
  }

  return (
    <div className="wizard-status">
      <h2>Wizard Status (Live)</h2>
      
      <div className="connection-status">
        {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
      </div>
      
      <ProgressBar status={status} />
      <ChecklistItems status={status} />
      
      <button 
        disabled={!status.can_complete}
        onClick={completeWizard}
      >
        Complete Wizard
      </button>
      
      <button onClick={refreshStatus}>
        🔄 Refresh
      </button>
    </div>
  );
};
```

#### Progress Bar Component

```typescript
interface ProgressBarProps {
  status: WizardStatus;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ status }) => {
  const completed = Object.values(status.details).filter(v => v === true).length;
  const total = 6; // Total requirements
  const percentage = Math.round((completed / total) * 100);

  return (
    <div className="progress-container">
      <div 
        className="progress-bar" 
        style={{ width: `${percentage}%` }}
      >
        {percentage}%
      </div>
      <p>{completed} / {total} completed</p>
    </div>
  );
};
```

#### Checklist Component

```typescript
const ChecklistItems: React.FC<{ status: WizardStatus }> = ({ status }) => {
  const { details } = status;
  
  return (
    <div className="checklist">
      <ChecklistItem 
        completed={details.first_name} 
        label="First Name" 
        link="/settings/account"
      />
      <ChecklistItem 
        completed={details.last_name} 
        label="Last Name" 
        link="/settings/account"
      />
      <ChecklistItem 
        completed={details.phone_number} 
        label="Phone Number" 
        link="/settings/account"
      />
      <ChecklistItem 
        completed={details.business_type} 
        label="Business Type" 
        link="/settings/account"
      />
      <ChecklistItem 
        completed={details.manual_prompt} 
        label="Manual Prompt" 
        link="/settings/ai-prompts"
      />
      <ChecklistItem 
        completed={details.channel_connected} 
        label="Channel Connected" 
        link="/settings/channels"
      />
    </div>
  );
};

interface ChecklistItemProps {
  completed: boolean;
  label: string;
  link: string;
}

const ChecklistItem: React.FC<ChecklistItemProps> = ({ completed, label, link }) => (
  <div className={`checklist-item ${completed ? 'completed' : 'pending'}`}>
    <span className="icon">{completed ? '✅' : '❌'}</span>
    <span className="label">{label}</span>
    {!completed && (
      <a href={link} className="action-link">
        Complete →
      </a>
    )}
  </div>
);
```

---

### Vue 3 + Composition API

```vue
<template>
  <div class="wizard-status">
    <h2>Wizard Status (Live)</h2>
    
    <div class="connection">
      {{ isConnected ? '🟢 Connected' : '🔴 Disconnected' }}
    </div>
    
    <div v-if="status" class="status-content">
      <!-- Progress Bar -->
      <div class="progress">
        <div 
          class="progress-fill" 
          :style="{ width: progressPercentage + '%' }"
        >
          {{ progressPercentage }}%
        </div>
      </div>
      
      <!-- Checklist -->
      <div class="checklist">
        <div 
          v-for="(item, key) in checklistItems" 
          :key="key"
          :class="['item', item.completed ? 'done' : 'pending']"
        >
          <span>{{ item.completed ? '✅' : '❌' }}</span>
          <span>{{ item.label }}</span>
          <a v-if="!item.completed" :href="item.link">Complete →</a>
        </div>
      </div>
      
      <!-- Actions -->
      <button 
        :disabled="!status.can_complete"
        @click="completeWizard"
      >
        Complete Wizard
      </button>
      
      <button @click="refreshStatus">🔄 Refresh</button>
    </div>
    
    <div v-else>
      Connecting...
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';

interface WizardStatus {
  type: 'wizard_status';
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
  timestamp: string;
}

const status = ref<WizardStatus | null>(null);
const isConnected = ref(false);
let ws: WebSocket | null = null;

const progressPercentage = computed(() => {
  if (!status.value) return 0;
  const completed = Object.values(status.value.details).filter(v => v === true).length;
  return Math.round((completed / 6) * 100);
});

const checklistItems = computed(() => {
  if (!status.value) return {};
  
  return {
    first_name: {
      completed: status.value.details.first_name,
      label: 'First Name',
      link: '/settings/account'
    },
    last_name: {
      completed: status.value.details.last_name,
      label: 'Last Name',
      link: '/settings/account'
    },
    phone_number: {
      completed: status.value.details.phone_number,
      label: 'Phone Number',
      link: '/settings/account'
    },
    business_type: {
      completed: status.value.details.business_type,
      label: 'Business Type',
      link: '/settings/account'
    },
    manual_prompt: {
      completed: status.value.details.manual_prompt,
      label: 'Manual Prompt',
      link: '/settings/ai-prompts'
    },
    channel_connected: {
      completed: status.value.details.channel_connected,
      label: 'Channel Connected',
      link: '/settings/channels'
    }
  };
});

const connectWebSocket = () => {
  ws = new WebSocket('ws://localhost:8000/ws/wizard-status/');
  
  ws.onopen = () => {
    console.log('Connected to Wizard Status WebSocket');
    isConnected.value = true;
  };
  
  ws.onmessage = (event) => {
    const data: WizardStatus = JSON.parse(event.data);
    console.log('Wizard Status Update:', data);
    status.value = data;
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket Error:', error);
  };
  
  ws.onclose = () => {
    console.log('WebSocket Disconnected');
    isConnected.value = false;
  };
};

const refreshStatus = () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'refresh' }));
  }
};

const completeWizard = async () => {
  // Call complete wizard API
  try {
    const response = await fetch('/api/v1/accounts/wizard-complete', {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    const result = await response.json();
    if (result.success) {
      alert('Wizard completed successfully!');
    }
  } catch (error) {
    console.error('Failed to complete wizard:', error);
  }
};

onMounted(() => {
  connectWebSocket();
});

onUnmounted(() => {
  if (ws) {
    ws.close();
  }
});
</script>

<style scoped>
.wizard-status {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.connection {
  margin-bottom: 20px;
  font-weight: bold;
}

.progress {
  background: #f0f0f0;
  border-radius: 10px;
  height: 30px;
  overflow: hidden;
  margin-bottom: 20px;
}

.progress-fill {
  background: linear-gradient(90deg, #4caf50, #8bc34a);
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  transition: width 0.3s ease;
}

.checklist {
  margin-bottom: 20px;
}

.item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.item.done {
  opacity: 0.7;
}

.item a {
  margin-left: auto;
  color: #6366f1;
  text-decoration: none;
}

.item a:hover {
  text-decoration: underline;
}

button {
  padding: 10px 20px;
  margin-right: 10px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>
```

---

### Vanilla JavaScript

```javascript
// wizard-status.js

class WizardStatusWebSocket {
  constructor(url, callbacks = {}) {
    this.url = url;
    this.ws = null;
    this.callbacks = {
      onStatusUpdate: callbacks.onStatusUpdate || (() => {}),
      onConnect: callbacks.onConnect || (() => {}),
      onDisconnect: callbacks.onDisconnect || (() => {}),
      onError: callbacks.onError || (() => {})
    };
  }

  connect() {
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = () => {
      console.log('Connected to Wizard Status WebSocket');
      this.callbacks.onConnect();
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Wizard Status Update:', data);
      this.callbacks.onStatusUpdate(data);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket Error:', error);
      this.callbacks.onError(error);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket Disconnected');
      this.callbacks.onDisconnect();
    };
  }

  refresh() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'refresh' }));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Usage
const wizardWS = new WizardStatusWebSocket('ws://localhost:8000/ws/wizard-status/', {
  onStatusUpdate: (status) => {
    updateUI(status);
  },
  onConnect: () => {
    document.querySelector('.connection-status').textContent = '🟢 Connected';
  },
  onDisconnect: () => {
    document.querySelector('.connection-status').textContent = '🔴 Disconnected';
  }
});

wizardWS.connect();

function updateUI(status) {
  // Update progress bar
  const completed = Object.values(status.details).filter(v => v === true).length;
  const percentage = Math.round((completed / 6) * 100);
  document.querySelector('.progress-fill').style.width = percentage + '%';
  document.querySelector('.progress-text').textContent = percentage + '%';
  
  // Update checklist
  Object.keys(status.details).forEach(key => {
    const element = document.querySelector(`[data-field="${key}"]`);
    if (element) {
      element.classList.toggle('completed', status.details[key]);
      element.querySelector('.icon').textContent = status.details[key] ? '✅' : '❌';
    }
  });
  
  // Update complete button
  const completeBtn = document.querySelector('.complete-wizard-btn');
  completeBtn.disabled = !status.can_complete;
}
```

---

## 🌍 Internationalization (i18n)

### Field Label Translations

Create translation dictionaries in your frontend:

**English:**
```javascript
const fieldLabels = {
  first_name: 'First Name',
  last_name: 'Last Name',
  phone_number: 'Phone Number',
  business_type: 'Business Type',
  manual_prompt: 'Manual Prompt',
  channel_connected: 'Channel Connected'
};
```

**Turkish:**
```javascript
const fieldLabels = {
  first_name: 'Ad',
  last_name: 'Soyad',
  phone_number: 'Telefon Numarası',
  business_type: 'İş Türü',
  manual_prompt: 'Manuel İstem',
  channel_connected: 'Kanal Bağlı'
};
```

**Arabic:**
```javascript
const fieldLabels = {
  first_name: 'الاسم الأول',
  last_name: 'اسم العائلة',
  phone_number: 'رقم الهاتف',
  business_type: 'نوع العمل',
  manual_prompt: 'الأمر اليدوي',
  channel_connected: 'القناة متصلة'
};
```

### React i18n Example

```typescript
import { useTranslation } from 'react-i18next';

const WizardStatus = () => {
  const { t } = useTranslation();
  
  return (
    <div>
      <h2>{t('wizard.title')}</h2>
      <ChecklistItem 
        label={t('wizard.fields.first_name')}
        completed={status.details.first_name}
      />
    </div>
  );
};
```

---

## 🔄 Auto-reconnection

Implement automatic reconnection on disconnect:

```typescript
const useWizardWebSocket = () => {
  const [status, setStatus] = useState<WizardStatus | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const connect = useCallback(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/wizard-status/');
    
    ws.onopen = () => {
      console.log('Connected');
      // Clear any pending reconnection
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
    
    ws.onmessage = (event) => {
      setStatus(JSON.parse(event.data));
    };
    
    ws.onclose = () => {
      console.log('Disconnected, reconnecting in 3s...');
      // Auto-reconnect after 3 seconds
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connect();
      }, 3000);
    };
    
    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connect();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  return { status };
};
```

---

## 🐛 Debugging

### Check Connection

```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8000/ws/wizard-status/');

ws.onopen = () => console.log('✅ Connected');
ws.onerror = (e) => console.error('❌ Error:', e);
ws.onmessage = (e) => console.log('📨 Message:', JSON.parse(e.data));
```

### Network Tab

1. Open Browser DevTools (F12)
2. Go to Network tab
3. Filter by "WS" (WebSocket)
4. Look for `wizard-status` connection
5. Check messages in/out

### Backend Logs

```bash
# In Django terminal, you should see:
# User 123 connected to wizard-status WebSocket
# Wizard status updated for user 123
# User 123 disconnected from wizard-status WebSocket
```

---

## ⚡ Performance Tips

1. **Single Connection:** Only one WebSocket per page
2. **Cleanup:** Always close connection on unmount
3. **Throttle Updates:** Don't update UI too frequently
4. **Lazy Load:** Connect only when wizard page is active

---

## 🔒 Security

- ✅ Authentication required (same as HTTP APIs)
- ✅ User-specific groups (users only see their own status)
- ✅ No sensitive data exposed
- ✅ HTTPS/WSS in production

---

## 📊 Comparison: HTTP Polling vs WebSocket

| Feature | HTTP Polling | WebSocket |
|---------|-------------|-----------|
| **Latency** | 2-3 seconds | < 100ms |
| **Network Usage** | High (constant requests) | Low (one connection) |
| **Server Load** | High | Low |
| **Battery Impact** | High | Low |
| **Implementation** | Simple | Medium |

---

## ✅ Testing Checklist

- [ ] Connect to WebSocket successfully
- [ ] Receive initial status on connect
- [ ] Update first name → see instant ✅
- [ ] Update phone → see instant ✅
- [ ] Save manual prompt → see instant ✅
- [ ] Connect Instagram → see instant ✅
- [ ] Disconnect and reconnect works
- [ ] Multiple tabs stay in sync
- [ ] Works in production (WSS)

---

## 🎯 Summary

**What You Get:**
- 🚀 Real-time updates (no refresh needed)
- 📱 Better UX with instant feedback
- 🔋 Lower network/battery usage
- 🌐 Multi-language ready (no hardcoded text)

**Integration Steps:**
1. Connect to `ws://domain/ws/wizard-status/`
2. Listen for `wizard_status` messages
3. Update UI automatically
4. Translate field names in your frontend

**Support:**
- Check backend logs for connection issues
- Use browser DevTools Network tab for debugging
- See `/docs/WIZARD_COMPLETE_FRONTEND_GUIDE.md` for HTTP API fallback

---

**Good luck! 🚀**

