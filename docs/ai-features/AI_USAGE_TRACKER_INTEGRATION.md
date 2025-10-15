# AI Usage Tracker Integration Guide

## Overview

The unified AI Usage Tracker automatically updates both:
- ✅ **AIUsageLog** - Detailed per-request tracking with full context
- ✅ **AIUsageTracking** - Daily aggregated statistics for analytics

## 🚀 Quick Start

### Method 1: Simple Function Call (Recommended)

```python
from AI_model.services.usage_tracker import track_ai_usage

# After your AI call
track_ai_usage(
    user=request.user,
    section='chat',
    prompt_tokens=150,
    completion_tokens=80,
    response_time_ms=1200,
    success=True,
    metadata={'conversation_id': str(conversation.id)}
)
```

### Method 2: Context Manager (Auto-timing)

```python
from AI_model.services.usage_tracker import AIUsageTracker

# Automatic timing and error handling
with AIUsageTracker(user, 'chat') as tracker:
    response = gemini_service.generate(prompt)
    tracker.set_tokens(
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens
    )
    tracker.set_metadata({'conversation_id': conv_id})
```

### Method 3: Safe Version (Never Raises Exceptions)

```python
from AI_model.services.usage_tracker import track_ai_usage_safe

# Won't break your code even if tracking fails
log, tracking = track_ai_usage_safe(
    user=request.user,
    section='rag_pipeline',
    prompt_tokens=200,
    completion_tokens=150,
    response_time_ms=1800,
    success=True
)
```

---

## 📝 Integration Examples

### 1. Chat AI Response (Gemini Service)

**File:** `src/AI_model/services/gemini_service.py`

```python
from AI_model.services.usage_tracker import track_ai_usage_safe
import time

class GeminiChatService:
    def generate_response(self, prompt, conversation=None):
        start_time = time.time()
        
        try:
            # Your existing AI call
            response = self.model.generate_content(prompt)
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Track usage (both models updated automatically)
            track_ai_usage_safe(
                user=self.user,
                section='chat',
                prompt_tokens=response.usage_metadata.prompt_token_count,
                completion_tokens=response.usage_metadata.candidates_token_count,
                response_time_ms=response_time_ms,
                success=True,
                model_name='gemini-1.5-flash',
                metadata={
                    'conversation_id': str(conversation.id) if conversation else None,
                    'prompt_length': len(prompt)
                }
            )
            
            return {
                'success': True,
                'response': response.text,
                'response_time_ms': response_time_ms
            }
            
        except Exception as e:
            # Track failure
            response_time_ms = int((time.time() - start_time) * 1000)
            
            track_ai_usage_safe(
                user=self.user,
                section='chat',
                prompt_tokens=0,
                completion_tokens=0,
                response_time_ms=response_time_ms,
                success=False,
                error_message=str(e),
                metadata={'error_type': type(e).__name__}
            )
            
            return {
                'success': False,
                'error': str(e),
                'response_time_ms': response_time_ms
            }
```

---

### 2. RAG Pipeline

**File:** `src/AI_model/services/rag_service.py`

```python
from AI_model.services.usage_tracker import AIUsageTracker

def query_with_rag(user, question):
    # Use context manager for automatic timing
    with AIUsageTracker(user, 'rag_pipeline') as tracker:
        # Retrieve relevant chunks
        chunks = retrieve_chunks(question)
        
        # Build context
        context = build_context(chunks)
        
        # Generate response
        response = generate_with_context(question, context)
        
        # Track tokens
        tracker.set_tokens(
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens
        )
        
        # Add metadata
        tracker.set_metadata({
            'chunks_retrieved': len(chunks),
            'context_length': len(context),
            'question_length': len(question)
        })
        
        return response
```

---

### 3. Prompt Generation

**File:** `src/AI_model/services/prompt_generator.py`

```python
from AI_model.services.usage_tracker import track_ai_usage_safe
import time

def generate_prompt(user, input_text, template):
    start_time = time.time()
    
    try:
        # Generate prompt using AI
        result = ai_model.generate(
            f"Based on this template: {template}\nGenerate: {input_text}"
        )
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Track usage
        track_ai_usage_safe(
            user=user,
            section='prompt_generation',
            prompt_tokens=result.usage.prompt_tokens,
            completion_tokens=result.usage.completion_tokens,
            response_time_ms=response_time_ms,
            success=True,
            metadata={
                'template': template,
                'input_length': len(input_text)
            }
        )
        
        return result.text
        
    except Exception as e:
        track_ai_usage_safe(
            user=user,
            section='prompt_generation',
            response_time_ms=int((time.time() - start_time) * 1000),
            success=False,
            error_message=str(e)
        )
        raise
```

---

### 4. Marketing Workflow

**File:** `src/workflow/services/ai_workflow.py`

```python
from AI_model.services.usage_tracker import track_ai_usage_safe

def execute_ai_workflow_step(workflow, step_data):
    import time
    start = time.time()
    
    try:
        # Execute AI workflow step
        result = workflow_ai.execute(step_data)
        
        # Track usage
        track_ai_usage_safe(
            user=workflow.user,
            section='marketing_workflow',
            prompt_tokens=result.tokens_in,
            completion_tokens=result.tokens_out,
            response_time_ms=int((time.time() - start) * 1000),
            success=True,
            metadata={
                'workflow_id': str(workflow.id),
                'step_name': step_data.get('name'),
                'workflow_type': workflow.workflow_type
            }
        )
        
        return result
        
    except Exception as e:
        track_ai_usage_safe(
            user=workflow.user,
            section='marketing_workflow',
            response_time_ms=int((time.time() - start) * 1000),
            success=False,
            error_message=str(e)
        )
        raise
```

---

### 5. Knowledge Base Q&A

**File:** `src/web_knowledge/services/qa_service.py`

```python
from AI_model.services.usage_tracker import AIUsageTracker

def answer_question(user, question, knowledge_base):
    with AIUsageTracker(user, 'knowledge_qa') as tracker:
        # Search knowledge base
        relevant_docs = search_knowledge(question, knowledge_base)
        
        # Generate answer
        answer = generate_answer(question, relevant_docs)
        
        # Track usage
        tracker.set_tokens(
            prompt_tokens=answer.usage.prompt_tokens,
            completion_tokens=answer.usage.completion_tokens
        )
        tracker.set_metadata({
            'knowledge_base_id': str(knowledge_base.id),
            'docs_found': len(relevant_docs)
        })
        
        return answer.text
```

---

### 6. Product Recommendations

```python
from AI_model.services.usage_tracker import track_ai_usage_safe
import time

def get_ai_product_recommendations(user, customer_profile):
    start = time.time()
    
    try:
        # Get AI recommendations
        recommendations = ai_service.recommend(customer_profile)
        
        track_ai_usage_safe(
            user=user,
            section='product_recommendation',
            prompt_tokens=recommendations.usage.prompt_tokens,
            completion_tokens=recommendations.usage.completion_tokens,
            response_time_ms=int((time.time() - start) * 1000),
            success=True,
            metadata={
                'customer_id': customer_profile.id,
                'recommendations_count': len(recommendations.products)
            }
        )
        
        return recommendations.products
        
    except Exception as e:
        track_ai_usage_safe(
            user=user,
            section='product_recommendation',
            response_time_ms=int((time.time() - start) * 1000),
            success=False,
            error_message=str(e)
        )
        return []
```

---

### 7. Session Memory Summary

```python
from AI_model.services.usage_tracker import track_ai_usage_safe
import time

def generate_session_summary(user, conversation):
    start = time.time()
    
    try:
        # Generate summary
        summary = ai_service.summarize_conversation(conversation)
        
        track_ai_usage_safe(
            user=user,
            section='session_memory',
            prompt_tokens=summary.usage.prompt_tokens,
            completion_tokens=summary.usage.completion_tokens,
            response_time_ms=int((time.time() - start) * 1000),
            success=True,
            metadata={
                'conversation_id': str(conversation.id),
                'message_count': conversation.messages.count()
            }
        )
        
        return summary.text
        
    except Exception as e:
        track_ai_usage_safe(
            user=user,
            section='session_memory',
            response_time_ms=int((time.time() - start) * 1000),
            success=False,
            error_message=str(e)
        )
        raise
```

---

### 8. Intent Detection

```python
from AI_model.services.usage_tracker import AIUsageTracker

def detect_customer_intent(user, message_text):
    with AIUsageTracker(user, 'intent_detection') as tracker:
        # Detect intent using AI
        intent_result = ai_service.detect_intent(message_text)
        
        tracker.set_tokens(
            prompt_tokens=intent_result.usage.prompt_tokens,
            completion_tokens=intent_result.usage.completion_tokens
        )
        tracker.set_metadata({
            'message_length': len(message_text),
            'detected_intent': intent_result.intent,
            'confidence': intent_result.confidence
        })
        
        return intent_result
```

---

### 9. Embedding Generation

```python
from AI_model.services.usage_tracker import track_ai_usage_safe
import time

def generate_embeddings(user, texts):
    start = time.time()
    
    try:
        # Generate embeddings
        embeddings = embedding_service.embed(texts)
        
        # OpenAI embeddings don't return token counts directly
        # Estimate: ~1 token per 4 characters
        estimated_tokens = sum(len(text) // 4 for text in texts)
        
        track_ai_usage_safe(
            user=user,
            section='embedding_generation',
            prompt_tokens=estimated_tokens,
            completion_tokens=0,  # Embeddings don't have output tokens
            response_time_ms=int((time.time() - start) * 1000),
            success=True,
            model_name='text-embedding-3-small',
            metadata={
                'texts_count': len(texts),
                'total_characters': sum(len(t) for t in texts)
            }
        )
        
        return embeddings
        
    except Exception as e:
        track_ai_usage_safe(
            user=user,
            section='embedding_generation',
            response_time_ms=int((time.time() - start) * 1000),
            success=False,
            error_message=str(e)
        )
        raise
```

---

## 🎯 What Gets Tracked Automatically

When you use the unified tracker, **both** models are updated:

### AIUsageLog (Detailed)
- ✅ Unique UUID for each request
- ✅ User information
- ✅ Section/feature name
- ✅ Exact token counts (prompt + completion)
- ✅ Response time in milliseconds
- ✅ Success/failure status
- ✅ Model name
- ✅ Error messages (if failed)
- ✅ Custom metadata (JSON)
- ✅ Timestamp

### AIUsageTracking (Daily Aggregate)
- ✅ Total requests per day
- ✅ Total tokens per day
- ✅ Success/failure counts
- ✅ Average response time
- ✅ Aggregated statistics

---

## 📊 View Your Data

### Via Admin Interface
```
https://api.fiko.net/admin/AI_model/aiusagelog/
https://api.fiko.net/admin/AI_model/aiusagetracking/
```

### Via API
```bash
# Get detailed logs
curl "https://api.fiko.net/api/v1/ai/usage/logs/" \
  -H "Authorization: Bearer TOKEN"

# Get statistics
curl "https://api.fiko.net/api/v1/ai/usage/logs/stats/" \
  -H "Authorization: Bearer TOKEN"
```

---

## 🔍 Query Examples

### Get Today's Usage
```python
from AI_model.models import AIUsageTracking
from datetime import date

today_usage = AIUsageTracking.objects.get(
    user=request.user,
    date=date.today()
)
print(f"Today's tokens: {today_usage.total_tokens}")
```

### Get Section Breakdown
```python
from AI_model.models import AIUsageLog
from django.db.models import Sum

section_usage = AIUsageLog.objects.filter(
    user=request.user
).values('section').annotate(
    total=Sum('total_tokens')
).order_by('-total')
```

---

## ⚡ Best Practices

1. **Always use `track_ai_usage_safe`** in production to prevent tracking failures from breaking your app

2. **Include meaningful metadata** to help with debugging and analytics

3. **Track both successes and failures** to monitor reliability

4. **Use the context manager** when you want automatic timing

5. **Check the logs regularly** via admin interface to spot issues

---

## 🚨 Error Handling

The tracker is designed to **never break your code**:

```python
# Even if tracking fails, your code continues
try:
    result = ai_service.generate(prompt)
    track_ai_usage_safe(...)  # Won't raise exceptions
    return result
except AIServiceError as e:
    # Only catch AI service errors, not tracking errors
    handle_error(e)
```

---

## 📈 Benefits

✅ **Automatic dual tracking** - No need to manage two models  
✅ **Built-in error handling** - Never breaks your application  
✅ **Consistent data** - Both logs and aggregates always match  
✅ **Easy integration** - Just one function call  
✅ **Comprehensive analytics** - Detailed and summary data available  

---

**Last Updated:** 2025-10-11  
**Version:** 1.0

