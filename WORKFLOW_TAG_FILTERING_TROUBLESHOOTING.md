# Workflow Tag Filtering Troubleshooting Guide

## 🐛 Issue: When Node Matches All Messages Instead of Only Tagged Customers

If your workflow with a "when" node configured with specific tags is triggering for ALL received messages instead of only messages from customers with those tags, this guide will help you diagnose and fix the issue.

---

## 🔍 Quick Diagnosis

### Step 1: Run the Diagnostic Command

```bash
cd /path/to/pilito/src
python manage.py debug_when_node_tags
```

This will show you:
- ✅ All when nodes with tag filtering
- ✅ Whether tags are properly configured
- ✅ Which customers have matching tags
- ✅ Recommendations for fixing issues

### Step 2: Check a Specific Workflow

```bash
python manage.py debug_when_node_tags --workflow YOUR_WORKFLOW_ID
```

### Step 3: Check a Specific When Node

```bash
python manage.py debug_when_node_tags --when-node YOUR_WHEN_NODE_ID
```

---

## 🎯 Common Causes & Solutions

### Cause 1: Tags Field is Empty

**Symptom:**
- When node shows no tags in the diagnostic output
- Log shows: `ℹ️  No tag filtering - tags field is empty or not configured`

**Solution:**
1. Edit the when node in the UI
2. Add the tag(s) you want to filter by
3. Save the when node
4. Verify with diagnostic command

**Example:**
```bash
# Before (WRONG)
Tags configured: []

# After (CORRECT)
Tags configured: ['VIP', 'Premium']
```

---

### Cause 2: Wrong When Type

**Symptom:**
- You're using `when_type='add_tag'` but expecting it to filter messages

**Explanation:**
- `add_tag` when type triggers when a tag is ADDED to a customer
- For filtering messages by customer tags, use `when_type='receive_message'` with tags configured

**Solution:**
1. If you want to filter messages by customer tags:
   - Use `when_type='receive_message'`
   - Configure the tags field with the tags to filter by

2. If you want to trigger when a tag is added:
   - Use `when_type='add_tag'`
   - Configure the tags field with the tags to listen for

---

### Cause 3: Tags Not Saved Properly

**Symptom:**
- You configured tags in the UI but they're not showing in the diagnostic

**Possible Reasons:**
1. Frontend not sending tags to backend
2. Serializer not accepting the tags
3. Tags being overwritten on save

**Solution:**
Check the Django admin or database directly:

```python
# In Django shell
from workflow.models import WhenNode

when_node = WhenNode.objects.get(id='YOUR_WHEN_NODE_ID')
print(f"Tags: {when_node.tags}")
print(f"Type: {type(when_node.tags)}")
print(f"Length: {len(when_node.tags) if when_node.tags else 0}")
```

If tags are empty, manually set them:

```python
when_node.tags = ['VIP', 'Premium']
when_node.save()
print(f"Updated tags: {when_node.tags}")
```

---

### Cause 4: Case Sensitivity (FIXED)

**Symptom:**
- Tags are configured but don't match customer tags due to case differences
- Example: When node has "VIP" but customer has "vip"

**Solution:**
This has been fixed! Tag comparison is now case-insensitive. Update your code to the latest version.

**Verification:**
Check logs for:
```
Normalized: user_tags=['vip', 'premium'], when_tags=['vip', 'premium']
```

---

## 📊 Understanding Tag Filtering

### How It Works

For `when_type='receive_message'` with tags configured:

1. **Message Received** → Workflow checks when nodes
2. **When Node Evaluation**:
   - ✅ Check keywords (if configured)
   - ✅ Check channels (if configured)
   - ✅ **Check customer tags** (if configured)
3. **Tag Matching Logic**:
   - Get customer's tags from database
   - Normalize both customer tags and when node tags (lowercase, trim)
   - Check if customer has at least ONE of the required tags
   - If match: ✅ Workflow triggers
   - If no match: ❌ Workflow blocked

### Example

```python
# When Node Configuration
when_node.when_type = 'receive_message'
when_node.tags = ['VIP', 'Premium']

# Customer 1
customer1.tags = ['VIP', 'Active']
# Result: ✅ Matches (has VIP)

# Customer 2
customer2.tags = ['Basic', 'Active']
# Result: ❌ No match

# Customer 3
customer3.tags = []
# Result: ❌ No match
```

---

## 🔍 Debugging Steps

### 1. Enable Debug Logging

Check your Django logs when a message is received. You should see:

```
🔍 Checking receive_message when node conditions:
   Keywords configured: []
   Channels configured: []
   Tags configured: ['VIP', 'Premium']

🏷️  Tag filtering enabled - required tags: ['VIP', 'Premium']
🏷️ Loaded customer tags for filtering: customer_id=123, tags=['vip', 'active']
✅ Tag match found - Customer has required tag from: ['VIP', 'Premium']
```

### 2. Check for Empty Tags

If you see:
```
ℹ️  No tag filtering - tags field is empty or not configured
```

This means the tags field is empty or `[]`, so ALL messages will match.

### 3. Check Customer Tags

Verify the customer actually has tags:

```python
from message.models import Customer

customer = Customer.objects.get(id=123)
tags = list(customer.tag.values_list('name', flat=True))
print(f"Customer tags: {tags}")
```

### 4. Check Tag Names Match

Ensure tag names match (case doesn't matter):

```python
# When node tags
['VIP', 'Premium']

# Customer tags (any of these will match)
['vip']      # ✅ Matches
['PREMIUM']  # ✅ Matches
['VIP']      # ✅ Matches
['Basic']    # ❌ No match
[]           # ❌ No match
```

---

## 🛠️ Manual Fixes

### Fix 1: Update When Node Tags via Django Shell

```python
from workflow.models import WhenNode

# Get your when node
when_node = WhenNode.objects.get(id='YOUR_ID')

# Set tags (replace with your actual tags)
when_node.tags = ['VIP', 'Premium', 'Gold']
when_node.save()

# Verify
print(f"Tags: {when_node.tags}")
```

### Fix 2: Update via Django Admin

1. Go to `/admin/workflow/whennode/`
2. Find your when node
3. Edit the `tags` field (JSON format):
   ```json
   ["VIP", "Premium"]
   ```
4. Save

### Fix 3: Update via API

```bash
curl -X PATCH \
  'http://localhost:8000/api/v1/workflow/nodes/YOUR_NODE_ID/' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "tags": ["VIP", "Premium"]
  }'
```

---

## ✅ Verification

After fixing, verify:

### 1. Run Diagnostic

```bash
python manage.py debug_when_node_tags --when-node YOUR_NODE_ID
```

Should show:
```
✅ Tags configured: ['VIP', 'Premium']
📊 Number of tags: 2
```

### 2. Send Test Message

1. Tag a test customer with one of the required tags
2. Send a message from that customer
3. Check logs - should see tag match confirmation
4. Workflow should trigger ✅

3. Send message from un-tagged customer
4. Workflow should NOT trigger ✅

---

## 📝 Best Practices

### DO ✅

- **Use meaningful tag names** - "VIP", "Premium", "Active"
- **Document your tags** - Keep a list of all tags used
- **Test thoroughly** - Test both matching and non-matching customers
- **Check logs** - Use diagnostic command before deploying

### DON'T ❌

- **Don't leave tags empty** - If you want all messages, remove the when node tags configuration
- **Don't use special characters** - Stick to alphanumeric and spaces
- **Don't rely on exact case** - The system is case-insensitive
- **Don't forget to save** - Always save after editing

---

## 🆘 Still Not Working?

If tag filtering still isn't working after trying these fixes:

### 1. Check the Logs

Look for these messages in your Django logs:
```
🏷️  Tag filtering enabled - required tags: [...]
❌ WORKFLOW BLOCKED: Customer tags [...] don't match required tags: [...]
```

### 2. Verify Database State

```bash
python manage.py shell
```

```python
from workflow.models import WhenNode
from message.models import Customer

# Check when node
wn = WhenNode.objects.get(id='YOUR_ID')
print(f"When node tags: {wn.tags}")
print(f"When node type: {wn.when_type}")

# Check customer
customer = Customer.objects.get(id=CUSTOMER_ID)
tags = list(customer.tag.values_list('name', flat=True))
print(f"Customer tags: {tags}")

# Manual comparison (should match the code logic)
normalized_customer = [str(t).lower().strip() for t in tags if t]
normalized_when = [str(t).lower().strip() for t in wn.tags if t]
has_match = any(t in normalized_customer for t in normalized_when)
print(f"Should match: {has_match}")
```

### 3. Check Recent Code Changes

Ensure you have the latest version with:
- ✅ Case-insensitive tag comparison
- ✅ Enhanced logging
- ✅ Tag normalization

### 4. Contact Support

Provide:
- When node ID
- Workflow ID
- Customer ID
- Relevant log output
- Output from diagnostic command

---

## 📚 Related Documentation

- **Tag APIs:** `CUSTOMER_TAGS_API_DOCS.md`
- **Tag Search:** `TAG_SEARCH_GUIDE.md`
- **Tag Fix Summary:** `WORKFLOW_TAG_FIX_SUMMARY.md`
- **Diagnostic Command:** `src/workflow/management/commands/debug_when_node_tags.py`

---

**Created:** 2025-10-29  
**Version:** 1.0  
**Status:** Ready to use

