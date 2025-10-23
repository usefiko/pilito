"""
Session Memory Manager - Rolling Conversation Summaries
Prevents token accumulation by REPLACING summaries (not appending)
Target: ≤150 tokens per summary
"""
import logging
from typing import Optional, Tuple
from django.core.cache import cache

logger = logging.getLogger(__name__)


class SessionMemoryManager:
    """
    Manages rolling conversation summaries
    
    CRITICAL: Summary is REPLACED not APPENDED
    ❌ Wrong: summary = old_summary + new_summary (accumulation!)
    ✅ Correct: summary = new_summary (replaces old)
    
    Update frequency: Every 5 messages
    Target: ≤150 tokens
    """
    
    SUMMARY_UPDATE_FREQUENCY = 5  # Update every N messages
    MAX_SUMMARY_TOKENS = 150
    RECENT_MESSAGES_COUNT = 3  # Always include 3 most recent (unsummarized)
    MAX_CONVERSATION_LENGTH = 200  # Warn when conversation exceeds this
    
    @classmethod
    def get_conversation_context(cls, conversation) -> str:
        """
        Get conversation context for prompt
        
        Returns:
            String with format:
            "Previous conversation: {summary}\n\nRecent messages:\nUser: ...\nAssistant: ..."
        """
        try:
            from AI_model.models import SessionMemory
            from message.models import Message
            
            # Get or create session memory
            memory, created = SessionMemory.objects.get_or_create(
                conversation=conversation,
                defaults={
                    'user': conversation.user,
                    'cumulative_summary': '',
                    'message_count': 0
                }
            )
            
            # Get all messages for this conversation
            messages = Message.objects.filter(
                conversation=conversation
            ).order_by('created_at')
            
            total_messages = messages.count()
            
            # Warn if conversation is too long
            if total_messages > cls.MAX_CONVERSATION_LENGTH:
                logger.warning(
                    f"⚠️ Conversation {conversation.id} has {total_messages} messages "
                    f"(max recommended: {cls.MAX_CONVERSATION_LENGTH}). "
                    f"Consider starting a new conversation for better performance."
                )
            
            # Check if we need to update summary
            if cls._should_update_summary(total_messages, memory.message_count):
                logger.info(
                    f"🧠 Updating summary for conversation {conversation.id} "
                    f"({total_messages} messages, last update at {memory.message_count})"
                )
                cls._update_summary(memory, messages, total_messages)
            
            # Build context string
            context_parts = []
            
            # 1. Summary (if exists)
            if memory.cumulative_summary and memory.cumulative_summary.strip():
                context_parts.append(f"Previous conversation summary:\n{memory.cumulative_summary}")
            
            # 2. Recent messages (last N messages, unsummarized)
            recent_messages = messages[max(0, total_messages - cls.RECENT_MESSAGES_COUNT):]
            if recent_messages:
                def format_message(msg):
                    role = 'User' if msg.type == 'customer' else 'Assistant'
                    
                    # Add media context prefix if this is an image or voice message
                    if msg.type == 'customer' and hasattr(msg, 'message_type'):
                        if msg.message_type == 'image':
                            return f"{role} [sent an image]: {msg.content}"
                        elif msg.message_type == 'voice':
                            return f"{role} [sent a voice message]: {msg.content}"
                    
                    return f"{role}: {msg.content}"
                
                recent_str = "\n".join([format_message(msg) for msg in recent_messages])
                context_parts.append(f"Recent messages:\n{recent_str}")
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"❌ Failed to get conversation context: {e}")
            # Fallback: return recent messages only
            try:
                from message.models import Message
                recent = Message.objects.filter(
                    conversation=conversation
                ).order_by('-created_at')[:cls.RECENT_MESSAGES_COUNT]
                
                if recent:
                    def format_fallback_message(msg):
                        role = 'User' if msg.type == 'customer' else 'Assistant'
                        if msg.type == 'customer' and hasattr(msg, 'message_type'):
                            if msg.message_type == 'image':
                                return f"{role} [sent an image]: {msg.content}"
                            elif msg.message_type == 'voice':
                                return f"{role} [sent a voice message]: {msg.content}"
                        return f"{role}: {msg.content}"
                    
                    return "Recent messages:\n" + "\n".join([
                        format_fallback_message(msg) for msg in reversed(recent)
                    ])
            except:
                pass
            
            return ""
    
    @classmethod
    def _should_update_summary(cls, current_count: int, last_update_count: int) -> bool:
        """
        Determine if summary should be updated
        Update every SUMMARY_UPDATE_FREQUENCY messages
        """
        if current_count < cls.SUMMARY_UPDATE_FREQUENCY:
            # Not enough messages yet
            return False
        
        if last_update_count == 0:
            # First summary
            return True
        
        messages_since_update = current_count - last_update_count
        return messages_since_update >= cls.SUMMARY_UPDATE_FREQUENCY
    
    @classmethod
    def _update_summary(cls, memory, messages, total_count: int):
        """
        Generate new summary and REPLACE old one
        
        CRITICAL: This REPLACES the summary, not appends!
        ❌ Wrong: memory.cumulative_summary += new_summary
        ✅ Correct: memory.cumulative_summary = new_summary
        """
        try:
            # Get messages that need summarization (exclude most recent ones)
            messages_to_summarize = messages[:max(0, total_count - cls.RECENT_MESSAGES_COUNT)]
            
            if not messages_to_summarize:
                logger.debug("No messages to summarize")
                return
            
            # ✅ Skip trivial updates (empty/very short messages)
            recent_messages = messages[max(0, total_count - 5):]
            recent_content_length = sum(len(m.content.strip()) for m in recent_messages)
            
            if recent_content_length < 100:
                logger.debug(
                    f"⏭️ Skipping summary update - recent messages too short "
                    f"({recent_content_length} chars)"
                )
                return
            
            # Build conversation text
            conversation_text = "\n".join([
                f"{'User' if msg.type == 'customer' else 'Assistant'}: {msg.content}"
                for msg in messages_to_summarize
            ])
            
            # Generate summary using Gemini (with fallback)
            new_summary = cls._generate_summary(conversation_text)
            
            if new_summary:
                # ✅ CRITICAL: REPLACE old summary, don't append!
                memory.cumulative_summary = new_summary  # ← REPLACE not +=
                memory.message_count = total_count
                memory.save()
                
                # ✅ Dynamic cache TTL based on conversation length
                cache_key = f"session_memory:{memory.conversation_id}"
                ttl = 3600 if total_count < 50 else 7200  # Longer TTL for mature conversations
                cache.set(cache_key, new_summary, ttl)
                
                logger.info(
                    f"✅ Summary updated for conversation {memory.conversation_id} "
                    f"(messages: {total_count}, summary_tokens: {cls._estimate_tokens(new_summary)}, cache_ttl: {ttl}s)"
                )
            
        except Exception as e:
            logger.error(f"❌ Failed to update summary: {e}")
    
    @classmethod
    def _generate_summary(cls, conversation_text: str) -> str:
        """
        Generate concise summary using Gemini with chunk-based approach
        Returns JSON with summary and topics for analytics
        Target: ≤150 tokens
        """
        try:
            # ✅ Setup proxy before importing Gemini
            from core.utils import setup_ai_proxy
            setup_ai_proxy()
            
            import google.generativeai as genai
            from settings.models import GeneralSettings
            import json
            
            # Get API key from GeneralSettings
            settings = GeneralSettings.get_settings()
            if not settings.gemini_api_key:
                logger.error("❌ Gemini API key not configured in GeneralSettings")
                return None
            
            genai.configure(api_key=settings.gemini_api_key)
            
            # Configure safety settings (balanced approach for business content)
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
            ]
            
            # ✅ Use gemini-2.0-flash-exp (verified working model)
            # Note: gemini-2.0-pro and gemini-2.5-* models not available for this API key
            primary_model = 'gemini-2.0-flash-exp'
            fallback_model = 'gemini-2.0-flash-exp'  # Same model for fallback
            
            model = genai.GenerativeModel(primary_model, safety_settings=safety_settings)
            
            # Chunk-based summarization for long conversations
            conversation_lines = conversation_text.split('\n')
            try:
                # ✅ Use chunking only for very long conversations (50+ messages)
                # For conversations 20-50 messages, direct summarization is more efficient
                if len(conversation_lines) > 50:  # If more than 50 messages, use chunking
                    summary_text = cls._chunk_based_summarization(model, conversation_lines, safety_settings)
                else:
                    # Direct summarization for shorter conversations (more efficient, 1 API call)
                    summary_text = cls._direct_summarization(model, conversation_text, safety_settings)
            except Exception as e:
                # ✅ Fallback to faster model on timeout/error
                if 'timeout' in str(e).lower() or 'deadline' in str(e).lower():
                    logger.warning(f"⚠️ {primary_model} timeout, falling back to {fallback_model}")
                    fallback_model_obj = genai.GenerativeModel(fallback_model, safety_settings=safety_settings)
                    
                    if len(conversation_lines) > 20:
                        summary_text = cls._chunk_based_summarization(fallback_model_obj, conversation_lines, safety_settings)
                    else:
                        summary_text = cls._direct_summarization(fallback_model_obj, conversation_text, safety_settings)
                else:
                    raise
            
            # Parse JSON response with cleanup
            if summary_text:
                try:
                    # ✅ Clean up response - extract JSON object
                    import re
                    clean_match = re.search(r"\{.*\}", summary_text, re.DOTALL)
                    if clean_match:
                        summary_text = clean_match.group()
                    
                    summary_data = json.loads(summary_text)
                    # Store full JSON for potential analytics, but return only summary text
                    summary = summary_data.get('summary', summary_text)
                    topics = summary_data.get('topics', [])
                    
                    logger.debug(f"📊 Summary topics extracted: {topics}")
                    return summary
                except json.JSONDecodeError:
                    # If JSON parsing fails, use the raw text
                    logger.warning("⚠️ Could not parse JSON summary, using raw text")
                    # Try to extract meaningful text (remove markdown, code blocks, etc.)
                    cleaned = summary_text.replace('```json', '').replace('```', '').strip()
                    return cleaned if len(cleaned) > 20 else None
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Summary generation failed: {e}")
            # Fallback: Extract first and last message
            try:
                lines = conversation_text.split('\n')
                if len(lines) >= 2:
                    first = lines[0][:150]
                    last = lines[-1][:150]
                    return f"Conversation started with: {first}. Latest: {last}."
            except:
                pass
            
            return "Ongoing conversation about various topics."
    
    @classmethod
    def _direct_summarization(cls, model, conversation_text: str, safety_settings: list) -> str:
        """Direct summarization for shorter conversations"""
        prompt = f"""Summarize this business conversation in 2-3 sentences (max 120 tokens).

FOCUS ONLY ON:
1. **Products mentioned**: names, prices asked, features discussed
2. **User intent**: browsing, comparing, ready to buy, asking about policy
3. **Key questions**: shipping, discount, warranty, payment
4. **Stage**: early interest, comparing options, purchase decision

SKIP:
- Who the assistant is or what platform it's on
- Generic greetings or small talk
- Repeated questions (mention once only)

BE SPECIFIC:
✅ "User compared Picopresso (asked price) vs Nanopresso for camping use"
❌ "User asked about products and pricing"

Conversation:
{conversation_text[:4000]}

Return JSON:
{{"summary": "specific 2-3 sentence summary", "topics": ["product1", "intent", "question_type"]}}

JSON:"""
        
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.3,
                    'max_output_tokens': 250,
                    'top_p': 0.8
                },
                safety_settings=safety_settings
            )
            
            # Check for safety blocks
            if not response.candidates or response.candidates[0].finish_reason == 2:
                logger.warning(f"⚠️ Summary blocked by Gemini (finish_reason=2)")
                return None
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"❌ Direct summarization failed: {e}")
            return None
    
    @classmethod
    def _chunk_based_summarization(cls, model, conversation_lines: list, safety_settings: list) -> str:
        """
        Chunk-based summarization for long conversations
        Optimized: Larger chunks + limited API calls to avoid quota issues
        """
        try:
            # ✅ Optimization: Larger chunk size (15 messages instead of 5)
            chunk_size = 15
            max_chunks = 20  # Limit to 20 chunks max (avoid quota issues)
            
            # For very long conversations, sample intelligently
            if len(conversation_lines) > (chunk_size * max_chunks):
                # Take first 1/3, middle 1/3, and last 1/3
                total = len(conversation_lines)
                third = total // 3
                sampled_lines = (
                    conversation_lines[:third] +  # Beginning
                    conversation_lines[third:2*third] +  # Middle
                    conversation_lines[-third:]  # End
                )
                conversation_lines = sampled_lines
                logger.info(f"📊 Conversation too long ({total} lines), sampled to {len(sampled_lines)} lines")
            
            chunks = [conversation_lines[i:i+chunk_size] for i in range(0, len(conversation_lines), chunk_size)]
            
            # Limit chunks
            if len(chunks) > max_chunks:
                chunks = chunks[:max_chunks]
                logger.info(f"📊 Limited chunks to {max_chunks} (from {len(chunks)})")
            
            partial_summaries = []
            
            # Summarize each chunk
            for idx, chunk in enumerate(chunks):
                chunk_text = '\n'.join(chunk)
                
                chunk_prompt = f"""Summarize in 1 sentence: products mentioned, prices asked, user intent.
Skip: greetings, platform explanations, repetitions.

{chunk_text}

Summary:"""
                
                try:
                    response = model.generate_content(
                        chunk_prompt,
                        generation_config={'temperature': 0.3, 'max_output_tokens': 100},
                        safety_settings=safety_settings
                    )
                    
                    if response.candidates and response.candidates[0].finish_reason != 2:
                        partial_summaries.append(response.text.strip())
                except Exception as e:
                    # ✅ Stop on quota errors to avoid wasting API calls
                    if '429' in str(e) or 'quota' in str(e).lower():
                        logger.warning(f"⚠️ Quota exceeded at chunk {idx+1}, stopping chunked summarization")
                        break
                    logger.warning(f"⚠️ Chunk {idx+1} summarization failed: {e}")
                    continue
            
            # Merge partial summaries into final summary
            if partial_summaries:
                merged_text = ' '.join(partial_summaries)
                
                # ✅ Try to merge with AI, but use partial summaries as fallback
                try:
                    final_prompt = f"""Merge into 2 sentences (max 100 tokens):
- Products mentioned + prices
- User intent (browsing/comparing/buying)
- Key questions (shipping/discount/warranty)

Summaries:
{merged_text}

JSON:
{{"summary": "concise merged summary", "topics": ["product", "intent"]}}"""
                    
                    response = model.generate_content(
                        final_prompt,
                        generation_config={'temperature': 0.3, 'max_output_tokens': 250},
                        safety_settings=safety_settings
                    )
                    
                    if response.candidates and response.candidates[0].finish_reason != 2:
                        return response.text.strip()
                except Exception as e:
                    # ✅ Fallback: use partial summaries directly (better than nothing!)
                    if '429' in str(e) or 'quota' in str(e).lower():
                        logger.warning(f"⚠️ Quota exceeded on merge, using partial summaries directly")
                        # Return first 3 partial summaries (most important parts)
                        return ' '.join(partial_summaries[:3])
                    raise
            
            # ✅ If no partial summaries, return None (will use fallback in main function)
            logger.warning("⚠️ No partial summaries available")
            return None
            
        except Exception as e:
            logger.error(f"❌ Chunk-based summarization failed: {e}")
            # ✅ Even on error, try to return partial summaries if we have any
            if 'partial_summaries' in locals() and partial_summaries:
                logger.warning(f"⚠️ Returning {len(partial_summaries)} partial summaries despite error")
                return ' '.join(partial_summaries[:3])  # Use first 3 partials
            return None
    
    
    @classmethod
    def _estimate_tokens(cls, text: str) -> int:
        """
        Estimate token count
        Uses tiktoken if available, falls back to word count
        """
        if not text:
            return 0
        
        try:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except:
            # Fallback: word count * 1.3 (conservative for multilingual)
            return int(len(text.split()) * 1.3)
    
    @classmethod
    def clear_memory(cls, conversation):
        """Clear session memory for a conversation"""
        try:
            from AI_model.models import SessionMemory
            SessionMemory.objects.filter(conversation=conversation).delete()
            
            cache_key = f"session_memory:{conversation.id}"
            cache.delete(cache_key)
            
            logger.info(f"🗑️ Cleared session memory for conversation {conversation.id}")
        except Exception as e:
            logger.error(f"❌ Failed to clear memory: {e}")

