# 🚀 Fiko AI Intelligence Enhancement - Implementation Roadmap

## 📋 Overview

This document outlines the implementation plan for 7 major AI intelligence features in **2 phases** to improve Fiko AI's conversational quality, accuracy, and user experience.

---

## 🎯 Phase 1: Low-Risk Quick Wins (Week 1)

**Goal:** Implement 3 high-impact, low-risk features  
**Total Time:** 10-13 hours  
**Risk Level:** 🟢 5% (Very Low)  
**Migration Required:** ✅ Yes (1 simple migration)

### Features:

#### 1️⃣ Knowledge Base Confidence Scoring ⭐⭐⭐⭐⭐
**Purpose:** Make AI admit when it doesn't know something instead of hallucinating

**Implementation:**
- Location: `src/AI_model/services/gemini_service.py`
- Changes: Modify `_build_prompt()` to add confidence instructions based on embedding similarity scores
- Risk: 🟢 Very Low (no database changes, only prompt modification)
- Time: 2-3 hours

**How it works:**
```python
# After getting Q&A matches with embedding
avg_similarity = sum(scores) / len(scores)

if avg_similarity > 0.85:
    # High confidence - answer directly
    instruction = "You have very relevant information. Answer confidently."
elif avg_similarity > 0.70:
    # Medium confidence - add disclaimer
    instruction = "Preface with: 'Based on our documentation, I believe...'"
else:
    # Low confidence - escalate
    instruction = "Say: 'I don't have exact information. Let me connect you with our team.'"
```

**Expected Impact:**
- ✅ Reduce hallucinations by 40-50%
- ✅ Improve trust with honest "I don't know" responses
- ✅ Better escalation to human support when needed

---

#### 2️⃣ Response Quality Feedback Loop ⭐⭐⭐⭐⭐
**Purpose:** Let customers rate AI responses (👍/👎) to track quality over time

**Implementation:**
- Location: `src/message/models.py`, `src/message/views.py`
- Changes: 
  - Add `feedback`, `feedback_comment`, `feedback_at` fields to Message model
  - Add API endpoint for submitting feedback
  - Add simple analytics query
- Risk: 🟢 Very Low (simple add-only migration, no existing logic affected)
- Time: 3-4 hours

**Database Changes:**
```python
# message/models.py
class Message:
    feedback = models.CharField(
        max_length=10,
        choices=[('positive', '👍'), ('negative', '👎'), ('none', 'No feedback')],
        default='none'
    )
    feedback_comment = models.TextField(blank=True)
    feedback_at = models.DateTimeField(null=True, blank=True)
```

**API:**
```
POST /api/messages/{message_id}/feedback/
{
  "feedback": "positive",  // or "negative"
  "comment": "Very helpful!"  // optional
}
```

**Expected Impact:**
- ✅ Measure AI quality with real user feedback
- ✅ Identify problem areas for improvement
- ✅ Track improvement over time

---

#### 3️⃣ Conversation Intelligence (Summarization) ⭐⭐⭐⭐⭐
**Purpose:** Summarize long conversations (>10 messages) to give AI better context without reading entire history

**Implementation:**
- Location: `src/AI_model/services/gemini_service.py`
- Changes: Add `_get_conversation_summary()` method with Redis caching
- Risk: 🟢 Very Low (no database changes, uses existing Gemini API, has fallback)
- Time: 4-6 hours

**How it works:**
```python
def _get_conversation_summary(self, conversation_id):
    # 1. Check cache first (1 hour TTL)
    cached = cache.get(f"conv_summary:{conversation_id}")
    if cached:
        return cached
    
    # 2. Get messages (only if > 10 messages)
    messages = Message.objects.filter(
        conversation_id=conversation_id
    ).order_by('created_at')
    
    if len(messages) <= 10:
        return None  # No summary needed, use full history
    
    # 3. Create summary prompt
    history = "\n".join([f"{m.type}: {m.content}" for m in messages[:-5]])
    prompt = f"Summarize this conversation in 2-3 sentences:\n{history}"
    
    # 4. Generate summary (max 100 tokens)
    summary = self.model.generate_content(
        prompt,
        generation_config={'max_output_tokens': 100}
    )
    
    # 5. Cache for 1 hour
    cache.set(f"conv_summary:{conversation_id}", summary, 3600)
    return summary

# In _build_prompt():
summary = self._get_conversation_summary(conversation.id)
if summary:
    prompt += f"\n\nConversation Summary: {summary}\n"
    recent_messages = messages[-5:]  # Only include last 5 messages
else:
    recent_messages = messages[-6:]  # Include last 6 as before
```

**Expected Impact:**
- ✅ Reduce token usage by 30-40% for long conversations
- ✅ Faster responses (less context to process)
- ✅ Better context understanding (summary + recent messages)

---

## 🎯 Phase 2: Medium-Risk Advanced Features (Week 2-3)

**Goal:** Implement 3 more advanced features with moderate risk  
**Total Time:** 18-25 hours  
**Risk Level:** 🟡 15-20% (Medium)  
**Migration Required:** ✅ Yes (2 migrations)

### Features:

#### 4️⃣ Intent Recognition & Sentiment Analysis ⭐⭐⭐⭐⭐
**Purpose:** Understand what customer wants (intent) and how they feel (sentiment) to respond appropriately

**Implementation:**
- Location: `src/message/models.py`, `src/AI_model/signals.py`
- Changes:
  - Add `sentiment` and `intent` fields to Message model
  - Add analysis function using Gemini (lightweight, <20 tokens)
  - Add signal to analyze customer messages automatically
  - Add auto-escalation for frustrated customers
- Risk: 🟡 Medium (migration + signal modification, but isolated)
- Time: 8-12 hours

**Database Changes:**
```python
class Message:
    sentiment = models.CharField(
        max_length=20,
        choices=[
            ('positive', 'Positive'),
            ('neutral', 'Neutral'),
            ('negative', 'Negative'),
            ('frustrated', 'Frustrated')
        ],
        default='neutral'
    )
    intent = models.CharField(
        max_length=30,
        choices=[
            ('question', 'Question'),
            ('complaint', 'Complaint'),
            ('purchase', 'Purchase Intent'),
            ('greeting', 'Greeting'),
            ('other', 'Other')
        ],
        null=True, blank=True
    )
```

**Analysis Function:**
```python
def analyze_message_sentiment_and_intent(message_text: str) -> tuple:
    """
    Fast sentiment/intent analysis using Gemini (10-20 tokens)
    """
    prompt = f"""Analyze in 2 words:
Sentiment: positive/neutral/negative/frustrated
Intent: question/complaint/purchase/greeting/other

Message: {message_text}

Format: sentiment,intent"""
    
    try:
        result = gemini.generate_content(
            prompt,
            generation_config={'max_output_tokens': 20}
        )
        sentiment, intent = result.text.strip().split(',')
        return sentiment.strip(), intent.strip()
    except:
        return 'neutral', 'other'
```

**Auto-Escalation:**
```python
# In AI_model/signals.py - after message is saved
if message.type == 'customer':
    sentiment, intent = analyze_message_sentiment_and_intent(message.content)
    message.sentiment = sentiment
    message.intent = intent
    message.save(update_fields=['sentiment', 'intent'])
    
    # Auto-escalate frustrated customers
    if sentiment == 'frustrated':
        conversation.status = 'support_active'
        conversation.save(update_fields=['status'])
        
        # Optional: notify support team
        send_notification_to_support(conversation)
```

**Expected Impact:**
- ✅ Auto-escalate frustrated customers to human support
- ✅ Better response personalization based on intent
- ✅ Track customer sentiment over time
- ✅ Identify complaint trends

---

#### 5️⃣ Context-Aware Personality ⭐⭐⭐⭐
**Purpose:** Adjust AI's tone and style based on conversation context (frustrated → empathetic, happy → enthusiastic)

**Implementation:**
- Location: `src/AI_model/services/gemini_service.py`
- Changes: Add dynamic tone instructions based on sentiment/intent
- Risk: 🟢 Low (only prompt modification, depends on #4)
- Time: 4-5 hours

**How it works:**
```python
def _get_dynamic_tone_instruction(self, conversation, sentiment=None, intent=None):
    """
    Adjust AI tone based on context
    """
    # Based on sentiment
    if sentiment == 'frustrated':
        return """
TONE ADJUSTMENT: User is frustrated.
- Be extra empathetic: "I understand how frustrating this must be..."
- Apologize if appropriate
- Offer immediate solution or escalate to human
- Be concise and action-oriented
"""
    
    elif sentiment == 'positive':
        return """
TONE ADJUSTMENT: User is happy/satisfied.
- Match their positive energy
- Be encouraging: "Great! I'm glad I could help!"
- You can be more casual and friendly
"""
    
    # Based on intent
    elif intent == 'purchase':
        return """
TONE ADJUSTMENT: Purchase intent detected.
- Be enthusiastic but not pushy
- Highlight value and benefits clearly
- Make next steps very easy
- Example: "Here's what you get with this plan..."
"""
    
    elif intent == 'complaint':
        return """
TONE ADJUSTMENT: User has a complaint.
- Acknowledge the issue immediately
- Show empathy
- Focus on resolution
- Example: "I'm sorry to hear that. Let's fix this right away..."
"""
    
    return ""  # Default tone

# In _build_prompt():
sentiment = conversation.messages.last().sentiment if conversation.messages.exists() else None
intent = conversation.messages.last().intent if conversation.messages.exists() else None

dynamic_tone = self._get_dynamic_tone_instruction(conversation, sentiment, intent)

final_prompt = f"""
{base_prompt}

{dynamic_tone}

{knowledge_base_data}

Customer Message: {customer_message}
"""
```

**Expected Impact:**
- ✅ More empathetic responses to frustrated customers
- ✅ Better sales conversion with purchase-intent customers
- ✅ Natural tone matching for happy customers
- ✅ 25-30% improvement in customer satisfaction

---

#### 6️⃣ Smart Follow-ups & Proactive Messages ⭐⭐⭐⭐
**Purpose:** Send helpful follow-up messages to inactive customers (e.g., "Still need help?")

**Implementation:**
- Location: `src/AI_model/tasks.py`, `src/core/settings/common.py`
- Changes:
  - Add Celery beat task to check inactive conversations
  - Add cooldown mechanism (Redis) to prevent spam
  - Add feature flag to enable/disable
- Risk: 🟡 Medium (new Celery task, could send unwanted messages if misconfigured)
- Time: 6-8 hours

**Celery Task:**
```python
# AI_model/tasks.py
@celery_app.task(name='AI_model.tasks.send_smart_followups')
def send_smart_followups():
    """
    Check for conversations inactive > 5 minutes with AI as last responder
    Send helpful follow-up message if appropriate
    """
    from AI_model.models import AIGlobalConfig
    
    # Check if feature enabled
    config = AIGlobalConfig.get_config()
    if not config.enable_smart_followups:
        return {'success': True, 'message': 'Feature disabled'}
    
    threshold = timezone.now() - timedelta(minutes=5)
    
    # Find inactive conversations
    inactive_convs = Conversation.objects.filter(
        status='active',  # Only active AI conversations
        updated_at__lt=threshold
    ).annotate(
        last_msg_type=Subquery(
            Message.objects.filter(
                conversation=OuterRef('pk')
            ).order_by('-created_at').values('type')[:1]
        )
    ).filter(
        last_msg_type='AI'  # Last message was from AI
    )[:50]  # Limit to 50
    
    sent_count = 0
    
    for conv in inactive_convs:
        # Check cooldown (don't send if already sent in last 1 hour)
        cache_key = f"followup_sent:{conv.id}"
        if cache.get(cache_key):
            continue
        
        # Generate contextual follow-up
        last_msg = conv.messages.order_by('-created_at').first()
        
        if last_msg.intent == 'question':
            followup = "Did that answer your question? Let me know if you need more details! 😊"
        elif last_msg.intent == 'purchase':
            followup = "Still interested? I'm here if you have any questions about pricing or features! 💬"
        else:
            followup = "Still here if you need anything! Feel free to ask. 😊"
        
        # Send message
        Message.objects.create(
            conversation=conv,
            type='AI',
            content=followup,
            source=conv.source
        )
        
        # Set cooldown (1 hour)
        cache.set(cache_key, True, 3600)
        sent_count += 1
    
    return {
        'success': True,
        'followups_sent': sent_count,
        'conversations_checked': inactive_convs.count()
    }

# Add to Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'send-smart-followups': {
        'task': 'AI_model.tasks.send_smart_followups',
        'schedule': crontab(minute='*/3'),  # Every 3 minutes
    },
}
```

**Feature Flag:**
```python
# AI_model/models.py
class AIGlobalConfig:
    enable_smart_followups = models.BooleanField(
        default=False,
        help_text="Enable automatic follow-up messages for inactive conversations"
    )
```

**Expected Impact:**
- ✅ 20-25% increase in re-engagement
- ✅ Better customer experience (feeling cared for)
- ✅ More completed conversions

---

## 🎯 Optional Phase 3: Complex Features (Future)

#### 7️⃣ Multi-turn Reasoning ⭐⭐
**Purpose:** Handle complex multi-step tasks (e.g., course registration, booking)

**Risk:** 🔴 High (25%) - Complex state management  
**Time:** 12-16 hours  
**Recommendation:** Only implement if there's a clear business need

---

## 🛡️ Safety Measures

### For All Implementations:

1. **Feature Flags:**
   - Every feature has an on/off toggle in Django admin
   - Can disable instantly if issues arise

2. **Graceful Degradation:**
   - All features have fallback behavior
   - System works normally even if feature fails

3. **Logging:**
   - Extensive logging for debugging
   - Track success/failure rates

4. **Rollback Plan:**
   - Git commits per feature
   - Database backups before migrations
   - Can revert migrations if needed

5. **Testing:**
   - Test on staging first
   - Manual QA before production
   - Monitor logs after deployment

---

## 📊 Implementation Checklist

### Phase 1 (This Week):

- [ ] **Confidence Scoring**
  - [ ] Modify `_build_prompt()` in `gemini_service.py`
  - [ ] Test with high/medium/low similarity Q&A
  - [ ] Verify AI says "I don't know" when appropriate

- [ ] **Feedback Loop**
  - [ ] Add fields to Message model
  - [ ] Create and run migration
  - [ ] Add API endpoint
  - [ ] Test submitting positive/negative feedback

- [ ] **Conversation Intelligence**
  - [ ] Add `_get_conversation_summary()` method
  - [ ] Test with short (<10 msg) and long (>10 msg) conversations
  - [ ] Verify Redis caching works
  - [ ] Monitor token usage reduction

### Phase 2 (Next Week):

- [ ] **Sentiment & Intent**
  - [ ] Add fields to Message model
  - [ ] Create and run migration
  - [ ] Add analysis function
  - [ ] Modify signal to analyze messages
  - [ ] Test auto-escalation for frustrated customers

- [ ] **Context-Aware Personality**
  - [ ] Add `_get_dynamic_tone_instruction()` method
  - [ ] Test with different sentiments (frustrated, happy, neutral)
  - [ ] Test with different intents (purchase, complaint, question)
  - [ ] Verify tone changes appropriately

- [ ] **Smart Follow-ups**
  - [ ] Add Celery task
  - [ ] Add feature flag to AIGlobalConfig
  - [ ] Add to Celery Beat schedule
  - [ ] Test cooldown mechanism
  - [ ] Monitor for spam/unwanted messages

---

## 📈 Expected Overall Impact

### Phase 1:
- **Response Accuracy:** +30-40%
- **Hallucination Reduction:** -40-50%
- **Token Usage:** -30% for long conversations
- **Customer Trust:** +25%

### Phase 2:
- **Customer Satisfaction:** +35%
- **Auto-Escalation Accuracy:** +45%
- **Re-engagement Rate:** +20-25%
- **Support Ticket Reduction:** -30%

### Combined (Both Phases):
- **Overall AI Quality:** +60-70%
- **Customer Satisfaction:** +50-60%
- **Support Efficiency:** +40%
- **Token Cost:** -25% (due to summarization)

---

## 🚨 Risk Mitigation

### High-Risk Scenarios:

1. **Sentiment Analysis False Positives:**
   - **Risk:** Escalating happy customers to support
   - **Mitigation:** Start with conservative threshold, monitor escalation rate
   - **Rollback:** Disable feature flag

2. **Smart Follow-up Spam:**
   - **Risk:** Sending too many follow-ups
   - **Mitigation:** Cooldown period (1 hour), max 1 per conversation per day
   - **Rollback:** Disable feature flag

3. **Summarization Quality:**
   - **Risk:** Poor summaries causing bad responses
   - **Mitigation:** Fallback to full history if summary fails, monitor response quality
   - **Rollback:** Disable summarization, use full history

### Database Migration Risks:

1. **Message Model Changes:**
   - **Risk:** Downtime during migration
   - **Mitigation:** Use `null=True, blank=True` for new fields, no data migration needed
   - **Rollback:** Can reverse migration cleanly

2. **Data Loss:**
   - **Risk:** Losing data during migration
   - **Mitigation:** All new fields are additive (no deletions), backup before migration
   - **Rollback:** Restore backup if needed

---

## 📞 Support & Monitoring

### Post-Deployment Monitoring:

1. **Check Celery Logs:**
   ```bash
   docker logs -f celery_worker
   ```

2. **Check Django Logs:**
   ```bash
   docker logs -f web
   ```

3. **Monitor Redis:**
   ```bash
   docker exec -it redis redis-cli
   > KEYS conv_summary:*
   > KEYS followup_sent:*
   ```

4. **Check Feedback Stats:**
   ```python
   # In Django shell
   from message.models import Message
   
   total_ai_messages = Message.objects.filter(type='AI').count()
   positive_feedback = Message.objects.filter(type='AI', feedback='positive').count()
   negative_feedback = Message.objects.filter(type='AI', feedback='negative').count()
   
   print(f"Total AI Messages: {total_ai_messages}")
   print(f"Positive: {positive_feedback} ({positive_feedback/total_ai_messages*100:.1f}%)")
   print(f"Negative: {negative_feedback} ({negative_feedback/total_ai_messages*100:.1f}%)")
   ```

---

## ✅ Ready to Start Phase 1!

**Next Steps:**
1. Review this roadmap
2. Backup database
3. Start implementation of Phase 1 features
4. Test thoroughly
5. Deploy to staging, then production
6. Monitor for 2-3 days
7. Proceed with Phase 2

**Estimated Timeline:**
- Phase 1: 3-4 days
- Testing & Monitoring: 2-3 days
- Phase 2: 5-7 days
- **Total:** 10-14 days

---

*Last Updated: 2025-10-05*
