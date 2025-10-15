# AI Usage Log - Quick Start Guide

## ✅ What Was Fixed

Your admin panel for AI usage logging (`/admin/AI_model/aiusagelog/`) was not showing all AI usage correctly. This has been fixed!

**Problem:** AI services were only updating daily summaries but not creating individual request logs.

**Solution:** All AI services now properly track every request in `AIUsageLog` with full details (tokens, response time, errors).

---

## 🚀 Quick Test (2 minutes)

### 1. Run the test script:
```bash
cd /Users/nima/Projects/Fiko-Backend
python test_ai_usage_tracking.py
```

This will:
- Create test AI usage log entries
- Show statistics
- Verify tracking is working

### 2. Check the admin panel:
```
1. Go to: http://your-domain/admin/AI_model/aiusagelog/
2. You should see the test entries created
3. Click on any entry to see full details
```

### 3. Test with real usage:
```
1. Send a chat message through your app
2. Refresh the admin panel
3. You should see a new entry with:
   - Section: "Customer Chat"
   - Tokens used
   - Response time
   - Success status
```

---

## 📊 What You'll See in Admin Panel

### List View:
- **Timestamp** - When the AI request happened
- **User** - Who made the request (clickable link)
- **Section** - Which feature used AI (color-coded):
  - 🟢 Customer Chat
  - 🔵 Prompt Generation
  - 🟣 Knowledge Base Q&A
  - 🟠 Marketing Workflow
  - (and more...)
- **Tokens** - Total tokens with breakdown (↑input / ↓output)
- **Response Time** - How long it took (color: green/orange/red)
- **Status** - ✓ Success or ✗ Failed
- **Model** - Which AI model was used

### Detail View (click any entry):
Shows complete information:
- User details
- Section/feature
- Model name
- Token breakdown (prompt/completion/total)
- Response time
- Success status
- Error message (if failed)
- Metadata (conversation ID, business type, etc.)
- Timestamp

### Filters (right sidebar):
- Filter by success/failure
- Filter by section (chat, Q&A, etc.)
- Filter by AI model
- Filter by date
- Filter by user

### Search (top):
Search by:
- Username or email
- Section name
- Model name
- Error message
- Request ID

---

## 📈 What's Being Tracked

### 1. Customer Chat (`section='chat'`)
- Every AI response to customers
- Model: gemini-1.5-flash
- Includes: conversation ID, tokens, response time

### 2. Q&A Generation (`section='knowledge_qa'`)
- Website content → Q&A pairs
- Model: gemini-2.5-pro
- Includes: page title, content length

### 3. Prompt Enhancement (`section='prompt_generation'`)
- Manual prompt improvements
- Model: gemini-2.5-pro
- Includes: business type, async flag

### More sections:
- `marketing_workflow` - Marketing automation
- `product_recommendation` - Product suggestions
- `rag_pipeline` - RAG system
- `web_knowledge` - Web processing
- `session_memory` - Conversation summaries
- `intent_detection` - Intent classification
- `embedding_generation` - Text embeddings

---

## 🔍 Common Queries

### See all failed AI requests:
```
Admin panel → Filter: "Failed" ✗
```

### See chat usage for a specific user:
```
Admin panel → Filter: User = "username" + Section = "Customer Chat"
```

### See high token usage requests:
```
Admin panel → Sort by "Tokens" (click column header)
```

### See slow requests:
```
Admin panel → Sort by "Response Time"
```

### Export to Excel:
```
Admin panel → Select entries → Actions → "Export"
```

---

## 🐛 Troubleshooting

### "No entries in admin panel"
1. Check if AI is actually being used (send a test chat)
2. Run test script: `python test_ai_usage_tracking.py`
3. Check logs: `tail -f logs/celery.log | grep TRACK`

### "Some AI usage not showing"
1. Check which feature you're using
2. Verify it's in the fixed list (see "What's Being Tracked" above)
3. Check logs for tracking errors

### "Want to see logs for specific date"
Use the date filter in admin panel or:
```python
# In Django shell
from AI_model.models import AIUsageLog
from datetime import date

# Today's logs
logs = AIUsageLog.objects.filter(created_at__date=date.today())

# Specific date
logs = AIUsageLog.objects.filter(created_at__date=date(2025, 10, 11))
```

---

## 📞 Verification Checklist

✅ Run test script successfully  
✅ See test entries in admin panel  
✅ Send real chat message  
✅ See chat entry in logs  
✅ Check token counts are accurate  
✅ Verify response times are showing  
✅ Test filters work  
✅ Test search works  
✅ Export works  

---

## 🎯 What's Next

Your AI usage tracking is now complete and working! You can:

1. **Monitor Usage**: See which users/features use most AI
2. **Track Costs**: Monitor token consumption per user
3. **Debug Issues**: See failed requests with error messages
4. **Analyze Performance**: Track response times
5. **Billing Verification**: Ensure tokens match billing

---

**Status**: ✅ Ready to use  
**Last Updated**: 2025-10-11  
**Need Help?**: Check `AI_USAGE_LOG_FIX.md` for technical details

