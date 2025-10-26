# Wizard Auto-Complete - How It Works

## 🎯 Overview

The wizard now **automatically completes** when all requirements are met. No button click needed!

---

## ✨ How It Works

### Automatic Completion

When a user:
1. ✅ Fills `first_name`
2. ✅ Fills `last_name`  
3. ✅ Fills `phone_number`
4. ✅ Selects `business_type`
5. ✅ Saves `manual_prompt`
6. ✅ Connects Instagram **OR** Telegram

→ **Wizard automatically sets `wizard_complete = True`**

### Real-time Flow

```
User saves profile
    ↓
Django Signal fires
    ↓
check_and_complete_wizard() runs
    ↓
All requirements met? → YES
    ↓
wizard_complete = True (auto-saved)
    ↓
WebSocket notifies frontend
    ↓
Frontend sees wizard_complete: true
    ↓
Redirect to Dashboard ✨
```

---

## 🔧 Implementation

### Backend Signal (Automatic)

```python
# src/accounts/signals.py

def check_and_complete_wizard(user):
    """Auto-complete wizard if all requirements met"""
    
    # Skip if already completed
    if user.wizard_complete:
        return False
    
    # Check all requirements
    if not (user.first_name and user.last_name and 
            user.phone_number and user.business_type):
        return False
    
    # Check manual_prompt exists
    try:
        ai_prompts = AIPrompts.objects.get(user=user)
        if not ai_prompts.manual_prompt.strip():
            return False
    except AIPrompts.DoesNotExist:
        return False
    
    # Check at least one channel connected
    instagram_connected = InstagramChannel.objects.filter(
        user=user, is_connect=True
    ).exists()
    telegram_connected = TelegramChannel.objects.filter(
        user=user, is_connect=True
    ).exists()
    
    if not (instagram_connected or telegram_connected):
        return False
    
    # ✅ All requirements met - auto-complete!
    user.wizard_complete = True
    user.save(update_fields=['wizard_complete'])
    return True


# Triggered on every relevant change
@receiver(post_save, sender=User)
def notify_wizard_on_user_update(sender, instance, created, **kwargs):
    if not created:
        check_and_complete_wizard(instance)  # ← Auto-check
        notify_wizard_status(instance.id)

@receiver(post_save, sender='settings.AIPrompts')
def notify_wizard_on_prompts_update(sender, instance, **kwargs):
    check_and_complete_wizard(instance.user)  # ← Auto-check
    notify_wizard_status(instance.user.id)

# Same for Instagram and Telegram channels...
```

---

## 💻 Frontend Implementation

### Option 1: HTTP Polling (Simple)

```javascript
// Check status every 2 seconds
setInterval(async () => {
  const response = await fetch('/api/v1/accounts/wizard-complete');
  const status = await response.json();
  
  if (status.wizard_complete) {
    // Redirect to dashboard
    window.location.href = '/dashboard';
  }
}, 2000);
```

### Option 2: WebSocket (Real-time) ⭐ Recommended

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/wizard-status/');

ws.onmessage = (event) => {
  const status = JSON.parse(event.data);
  
  if (status.wizard_complete) {
    // Redirect instantly when completed
    window.location.href = '/dashboard';
  }
  
  // Update progress UI
  updateProgressBar(status.details);
};
```

### React Example

```typescript
const WizardPage = () => {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/wizard-status/');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStatus(data);
      
      // Auto-redirect when completed
      if (data.wizard_complete) {
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 1000); // Show success animation first
      }
    };
    
    return () => ws.close();
  }, []);

  if (!status) return <div>Loading...</div>;

  // Show completion animation
  if (status.wizard_complete) {
    return (
      <div className="wizard-success">
        <h1>🎉 Wizard Completed!</h1>
        <p>Redirecting to dashboard...</p>
      </div>
    );
  }

  // Show progress
  return (
    <div className="wizard-progress">
      <h2>Complete Your Profile</h2>
      <ProgressChecklist status={status} />
      {/* No complete button needed! */}
    </div>
  );
};
```

---

## 📊 Status Response

### Before Completion

```json
{
  "type": "wizard_status",
  "wizard_complete": false,
  "can_complete": true,    // All requirements met, will auto-complete soon
  "missing_fields": [],
  "details": {
    "first_name": true,
    "last_name": true,
    "phone_number": true,
    "business_type": true,
    "manual_prompt": true,
    "channel_connected": true
  }
}
```

### After Auto-Completion

```json
{
  "type": "wizard_status",
  "wizard_complete": true,  // ← Automatically set!
  "can_complete": true,
  "missing_fields": [],
  "details": {
    "first_name": true,
    "last_name": true,
    "phone_number": true,
    "business_type": true,
    "manual_prompt": true,
    "channel_connected": true
  }
}
```

---

## 🎬 User Journey

### Scenario: New User

1. **User registers** → `wizard_complete: false`

2. **User fills profile:**
   - First name: "John" ✅
   - Last name: "Doe" ✅
   - Phone: "+1234567890" ✅
   - Business Type: "E-commerce" ✅
   - Still incomplete: `wizard_complete: false`

3. **User saves manual prompt** ✅
   - Still incomplete (no channel)
   - `wizard_complete: false`

4. **User connects Instagram** ✅
   - **Signal fires**
   - **Auto-check runs**
   - **All requirements met!**
   - **`wizard_complete = True`** ← Automatic!
   - **WebSocket notifies frontend**

5. **Frontend receives update:**
   - `wizard_complete: true`
   - Shows success animation
   - Redirects to dashboard

**Total time:** Instant! (< 100ms after last requirement met)

---

## 🔄 Edge Cases

### Case 1: User disconnects channel

```python
# If user disconnects the only connected channel
user.wizard_complete = True  # Stays true (once completed, stays completed)
```

**Reason:** Once wizard is completed, we don't reverse it.

### Case 2: Incomplete user tries to access dashboard

```python
# In dashboard view
if not request.user.wizard_complete:
    return redirect('/wizard')
```

### Case 3: User manually calls PATCH endpoint

```python
# PATCH /api/v1/accounts/wizard-complete
# Response: "Wizard already completed" (if already auto-completed)
# OR: Auto-completes if requirements are met
```

**Note:** PATCH endpoint is **deprecated** but kept for backward compatibility.

---

## 🆚 Comparison: Before vs After

| Feature | Before (Manual) | After (Auto) |
|---------|----------------|--------------|
| **User action** | Must click "Complete" button | No action needed |
| **UX** | Extra step | Seamless |
| **Complexity** | Button + validation | Automatic |
| **Speed** | User has to find button | Instant |
| **Confusion** | "Where's the button?" | "It just works!" |

---

## ⚠️ Important Notes

### 1. Once Completed, Stays Completed

Once `wizard_complete = True`, it **never goes back to false** automatically.

**Reason:** User has already seen the wizard. Even if they disconnect a channel later, they shouldn't see wizard again.

### 2. Admin Can Reset

Admins can manually set `wizard_complete = False` in Django admin if needed.

### 3. Frontend Should Check on Load

```javascript
// On app load
const status = await fetchWizardStatus();
if (!status.wizard_complete) {
  // Show wizard or redirect to wizard
  window.location.href = '/wizard';
}
```

### 4. WebSocket is Optional

HTTP polling still works, but WebSocket gives instant updates.

---

## 🧪 Testing

### Test Auto-Completion

1. **Create new user**
2. **Fill profile** → not completed yet
3. **Save manual prompt** → not completed yet  
4. **Connect Instagram** → **BOOM! Auto-completed** ✨
5. **Check database:** `wizard_complete = True`
6. **Check WebSocket:** Receives `wizard_complete: true`
7. **Frontend redirects** to dashboard

### Test Each Requirement

```python
# Test script
user = User.objects.get(email='test@example.com')

# Missing first_name
user.first_name = ''
user.save()
# wizard_complete should stay False

# Fill first_name
user.first_name = 'John'
user.save()
# Check if completed (only if all others are filled)
```

---

## 📚 Related Documentation

- **WebSocket Guide:** `/docs/WIZARD_WEBSOCKET_FRONTEND_GUIDE.md`
- **HTTP API Guide:** `/docs/WIZARD_COMPLETE_FRONTEND_GUIDE.md`
- **Implementation:** `/docs/WIZARD_WEBSOCKET_IMPLEMENTATION.md`

---

## ✅ Summary

**Backend:**
- ✅ Auto-completion via signals
- ✅ Real-time WebSocket notifications
- ✅ No manual PATCH needed

**Frontend:**
- ✅ Just listen for `wizard_complete: true`
- ✅ Redirect when completed
- ✅ No "Complete" button needed

**UX:**
- ✅ Seamless experience
- ✅ Instant feedback
- ✅ No confusion

**Everything is automatic! 🎉**

