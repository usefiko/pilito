"""
Session Memory Manager V2 - Multi-Tier Conversation Context
Inspired by Intercom, Zendesk, and ChatGPT best practices

Key improvements over V1:
- Multi-tier memory (Verbatim + Recent + Mid + Old)
- Key facts extraction
- Progressive summarization
- Better token efficiency
- Industry-standard approach
"""
import logging
from typing import Optional, Dict, List, Tuple
from django.core.cache import cache
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class SessionMemoryManagerV2:
    """
    Multi-Tier Session Memory Manager
    
    Tiers:
    1. Verbatim (Tier 1): Last 5 messages - Full content
    2. Recent (Tier 2): Messages 6-15 - Detailed summary
    3. Mid (Tier 3): Messages 16-50 - Medium summary
    4. Old (Tier 4): Messages 51+ - High-level summary
    5. Key Facts: Structured extracted data
    """
    
    # Configuration
    TIER_VERBATIM_COUNT = 5      # Last N messages kept verbatim
    TIER_RECENT_COUNT = 10       # Next N messages (detailed summary)
    TIER_MID_COUNT = 35          # Next N messages (medium summary)
    # Rest: OLD tier (high-level summary)
    
    UPDATE_THRESHOLD = 5         # Update summary every N new messages
    
    # Token budgets per tier
    TOKEN_BUDGET = {
        'verbatim': 400,         # ~5 messages × 80 tokens
        'recent': 200,           # Detailed summary
        'mid': 250,              # Medium summary
        'old': 200,              # High-level summary
        'key_facts': 150,        # Structured data
    }
    
    @classmethod
    def get_conversation_context(cls, conversation) -> Dict:
        """
        Get multi-tier conversation context
        
        Returns:
            Dict with tiers and metadata
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
            
            # Get all messages
            messages = list(Message.objects.filter(
                conversation=conversation
            ).order_by('created_at'))
            
            total_count = len(messages)
            
            if total_count == 0:
                return cls._empty_context()
            
            # Check if update needed
            if cls._should_update_summary(total_count, memory.message_count):
                logger.info(
                    f"🧠 V2: Updating multi-tier summary for conversation {conversation.id} "
                    f"({total_count} messages, last update: {memory.message_count})"
                )
                cls._update_multi_tier_summary(memory, messages, total_count)
            
            # Build context from memory
            context = cls._build_context_from_memory(memory, messages, total_count)
            
            return context
            
        except Exception as e:
            logger.error(f"❌ V2: Failed to get conversation context: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return cls._empty_context()
    
    @classmethod
    def get_conversation_context_string(cls, conversation) -> str:
        """
        Get conversation context as formatted string (for prompt)
        """
        context = cls.get_conversation_context(conversation)
        
        parts = []
        
        # Old tier summary
        if context.get('old_summary'):
            parts.append(f"[EARLY CONVERSATION - Messages 1-{context['old_range'][1]}]\n{context['old_summary']}")
        
        # Mid tier summary
        if context.get('mid_summary'):
            parts.append(f"[MID CONVERSATION - Messages {context['mid_range'][0]}-{context['mid_range'][1]}]\n{context['mid_summary']}")
        
        # Recent tier summary
        if context.get('recent_summary'):
            parts.append(f"[RECENT MESSAGES - Messages {context['recent_range'][0]}-{context['recent_range'][1]}]\n{context['recent_summary']}")
        
        # Key facts
        if context.get('key_facts'):
            facts_str = "\n".join([f"• {fact}" for fact in context['key_facts']])
            parts.append(f"[KEY FACTS]\n{facts_str}")
        
        # Verbatim messages (most recent)
        if context.get('verbatim'):
            verbatim_str = "\n".join([
                f"{'User' if msg['type'] == 'customer' else 'AI'}: {msg['content']}"
                for msg in context['verbatim']
            ])
            parts.append(f"[CURRENT MESSAGES - Last {len(context['verbatim'])}]\n{verbatim_str}")
        
        return "\n\n".join(parts)
    
    @classmethod
    def _empty_context(cls) -> Dict:
        """Return empty context structure"""
        return {
            'verbatim': [],
            'recent_summary': None,
            'mid_summary': None,
            'old_summary': None,
            'key_facts': [],
            'total_messages': 0,
            'estimated_tokens': 0
        }
    
    @classmethod
    def _should_update_summary(cls, current_count: int, last_update_count: int) -> bool:
        """Check if summary needs updating"""
        if current_count < cls.TIER_VERBATIM_COUNT:
            return False  # Too few messages
        
        if last_update_count == 0:
            return True  # First summary
        
        messages_since_update = current_count - last_update_count
        return messages_since_update >= cls.UPDATE_THRESHOLD
    
    @classmethod
    def _update_multi_tier_summary(cls, memory, messages: List, total_count: int):
        """
        Generate and save multi-tier summaries
        """
        try:
            summaries = {}
            
            # Tier 1: Verbatim (skip - will be loaded fresh each time)
            verbatim_start = max(0, total_count - cls.TIER_VERBATIM_COUNT)
            
            # Tier 2: Recent summary (messages just before verbatim)
            recent_end = verbatim_start
            recent_start = max(0, recent_end - cls.TIER_RECENT_COUNT)
            if recent_start < recent_end:
                recent_messages = messages[recent_start:recent_end]
                summaries['recent'] = cls._generate_tier_summary(
                    recent_messages,
                    tier='recent',
                    detail='detailed'
                )
            
            # Tier 3: Mid summary
            mid_end = recent_start
            mid_start = max(0, mid_end - cls.TIER_MID_COUNT)
            if mid_start < mid_end:
                mid_messages = messages[mid_start:mid_end]
                summaries['mid'] = cls._generate_tier_summary(
                    mid_messages,
                    tier='mid',
                    detail='medium'
                )
            
            # Tier 4: Old summary (everything before mid)
            if mid_start > 0:
                old_messages = messages[:mid_start]
                summaries['old'] = cls._generate_tier_summary(
                    old_messages,
                    tier='old',
                    detail='overview'
                )
            
            # Extract key facts from all messages
            key_facts = cls._extract_key_facts(messages)
            
            # Build structured summary and save
            structured_summary = {
                'recent': summaries.get('recent'),
                'mid': summaries.get('mid'),
                'old': summaries.get('old'),
                'key_facts': key_facts,
                'ranges': {
                    'recent': [recent_start, recent_end] if recent_start < recent_end else None,
                    'mid': [mid_start, mid_end] if mid_start < mid_end else None,
                    'old': [0, mid_start] if mid_start > 0 else None,
                },
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Save as JSON in cumulative_summary
            import json
            memory.cumulative_summary = json.dumps(structured_summary, ensure_ascii=False)
            memory.message_count = total_count
            memory.save()
            
            # Cache it
            cache_key = f"session_memory_v2:{memory.conversation_id}"
            cache.set(cache_key, structured_summary, 3600)
            
            logger.info(
                f"✅ V2: Multi-tier summary updated for conversation {memory.conversation_id} "
                f"(total: {total_count}, tiers: {len(summaries)})"
            )
            
        except Exception as e:
            logger.error(f"❌ V2: Failed to update multi-tier summary: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    @classmethod
    def _build_context_from_memory(cls, memory, messages: List, total_count: int) -> Dict:
        """Build context dict from stored memory"""
        try:
            import json
            
            # Parse stored summary
            if memory.cumulative_summary and memory.cumulative_summary.strip():
                try:
                    stored = json.loads(memory.cumulative_summary)
                except:
                    stored = {}
            else:
                stored = {}
            
            # Tier 1: Verbatim (always fresh)
            verbatim_start = max(0, total_count - cls.TIER_VERBATIM_COUNT)
            verbatim_messages = messages[verbatim_start:]
            
            # Format verbatim messages with media context
            verbatim_list = []
            for msg in verbatim_messages:
                msg_dict = {
                    'type': msg.type,
                    'content': msg.content,
                    'created_at': msg.created_at.isoformat()
                }
                
                # Add media type context for customer messages
                if msg.type == 'customer' and hasattr(msg, 'message_type'):
                    if msg.message_type == 'image':
                        msg_dict['content'] = f"[sent an image]: {msg.content}"
                    elif msg.message_type == 'voice':
                        msg_dict['content'] = f"[sent a voice message]: {msg.content}"
                
                verbatim_list.append(msg_dict)
            
            context = {
                'verbatim': verbatim_list,
                'recent_summary': stored.get('recent'),
                'mid_summary': stored.get('mid'),
                'old_summary': stored.get('old'),
                'key_facts': stored.get('key_facts', []),
                'recent_range': stored.get('ranges', {}).get('recent'),
                'mid_range': stored.get('ranges', {}).get('mid'),
                'old_range': stored.get('ranges', {}).get('old'),
                'total_messages': total_count,
                'estimated_tokens': cls._estimate_context_tokens(stored, len(verbatim_messages))
            }
            
            return context
            
        except Exception as e:
            logger.error(f"❌ V2: Failed to build context: {e}")
            return cls._empty_context()
    
    @classmethod
    def _generate_tier_summary(cls, messages: List, tier: str, detail: str) -> Optional[str]:
        """
        Generate summary for a specific tier
        
        Args:
            messages: List of Message objects
            tier: 'recent', 'mid', or 'old'
            detail: 'detailed', 'medium', or 'overview'
        """
        if not messages:
            return None
        
        try:
            # ✅ Setup proxy before importing Gemini
            from core.utils import setup_ai_proxy
            setup_ai_proxy()
            
            import google.generativeai as genai
            from settings.models import GeneralSettings
            
            # Get API key
            settings = GeneralSettings.get_settings()
            if not settings.gemini_api_key:
                logger.warning("⚠️ V2: Gemini API key not configured")
                return None
            
            genai.configure(api_key=settings.gemini_api_key)
            
            # Configure safety settings - BLOCK_NONE for all business content
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            model = genai.GenerativeModel(
                'gemini-2.5-flash',
                safety_settings=safety_settings
            )
            
            # Build conversation text
            conversation_text = "\n".join([
                f"{'User' if msg.type == 'customer' else 'AI'}: {msg.content}"
                for msg in messages
            ])
            
            # Tier-specific prompts
            if detail == 'detailed':
                prompt = f"""Summarize these recent messages in 3-4 sentences.
Focus on: main questions, key answers, decisions made, current discussion topic.
Be specific and informative.

Messages ({len(messages)} total):
{conversation_text[:2000]}

Detailed summary (3-4 sentences):"""
                max_tokens = 250
                
            elif detail == 'medium':
                prompt = f"""Summarize these mid-conversation messages in 2-3 sentences.
Focus on: main topics discussed, important information exchanged, progress made.
Be concise but informative.

Messages ({len(messages)} total):
{conversation_text[:2500]}

Medium summary (2-3 sentences):"""
                max_tokens = 200
                
            else:  # overview
                prompt = f"""Summarize these early conversation messages in 1-2 sentences.
Focus on: how conversation started, initial topics, overall context.
Be very brief.

Messages ({len(messages)} total):
{conversation_text[:3000]}

Brief overview (1-2 sentences):"""
                max_tokens = 150
            
            # Try primary model (gemini-2.5-flash)
            try:
                response = model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.3,
                        'max_output_tokens': max_tokens,
                        'top_p': 0.8
                    }
                )
                
                # Check for safety blocks
                if not response.candidates or not response.candidates[0].content.parts:
                    finish_reason = response.candidates[0].finish_reason if response.candidates else None
                    logger.warning(f"⚠️ V2: gemini-2.5-flash blocked for {tier} summary (finish_reason: {finish_reason})")
                    logger.warning(f"🔄 V2: Attempting fallback to gemini-2.0-flash-exp...")
                    raise Exception(f"Primary model blocked: {finish_reason}")
                
            except Exception as primary_error:
                # Fallback to gemini-2.0-flash-exp
                logger.info(f"🔄 V2: Using fallback model for {tier} summary")
                fallback_model = genai.GenerativeModel(
                    'gemini-2.0-flash-exp',
                    safety_settings=safety_settings
                )
                
                response = fallback_model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.3,
                        'max_output_tokens': max_tokens,
                        'top_p': 0.8
                    }
                )
                
                if not response.candidates or not response.candidates[0].content.parts:
                    logger.error(f"❌ V2: Fallback model also blocked for {tier} summary")
                    raise Exception(f"Both primary and fallback models blocked")
                
                logger.info(f"✅ V2: Fallback successful for {tier} summary")
            
            summary = response.text.strip()
            logger.debug(f"📝 V2: Generated {tier} summary: {len(summary)} chars")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ V2: Failed to generate {tier} summary: {e}")
            # Fallback: simple concatenation
            try:
                first = messages[0].content[:100]
                last = messages[-1].content[:100]
                return f"Discussed: {first}... → ...{last}"
            except:
                return None
    
    @classmethod
    def _extract_key_facts(cls, messages: List) -> List[str]:
        """
        Extract key facts from conversation using AI
        
        Returns structured facts like:
        - Products mentioned
        - Prices discussed
        - Decisions made
        - Customer preferences
        """
        if not messages or len(messages) < 5:
            return []
        
        try:
            # ✅ Setup proxy before importing Gemini
            from core.utils import setup_ai_proxy
            setup_ai_proxy()
            
            import google.generativeai as genai
            from settings.models import GeneralSettings
            
            settings = GeneralSettings.get_settings()
            if not settings.gemini_api_key:
                return []
            
            genai.configure(api_key=settings.gemini_api_key)
            
            # Configure safety settings - BLOCK_NONE for all business content
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            model = genai.GenerativeModel(
                'gemini-2.5-flash',
                safety_settings=safety_settings
            )
            
            # Build conversation text (sample from beginning, middle, end)
            total = len(messages)
            sample_messages = []
            
            # First 5
            sample_messages.extend(messages[:5])
            # Middle 5
            if total > 20:
                mid = total // 2
                sample_messages.extend(messages[mid-2:mid+3])
            # Last 5
            sample_messages.extend(messages[-5:])
            
            conversation_text = "\n".join([
                f"{'User' if msg.type == 'customer' else 'AI'}: {msg.content}"
                for msg in sample_messages
            ])
            
            prompt = f"""Extract key facts from this conversation. Return 3-7 concise bullet points.
Focus on:
- Products/services mentioned
- Prices or costs discussed
- Decisions or commitments made
- Important customer preferences or requirements
- Current status or next steps

Conversation sample:
{conversation_text[:2000]}

Key facts (3-7 bullet points):"""
            
            # Try primary model (gemini-2.5-flash)
            try:
                response = model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.2,
                        'max_output_tokens': 200,
                    }
                )
                
                # Check for safety blocks
                if not response.candidates or not response.candidates[0].content.parts:
                    finish_reason = response.candidates[0].finish_reason if response.candidates else None
                    logger.warning(f"⚠️ V2: gemini-2.5-flash blocked for key facts (finish_reason: {finish_reason})")
                    logger.warning(f"🔄 V2: Attempting fallback to gemini-2.0-flash-exp...")
                    raise Exception(f"Primary model blocked: {finish_reason}")
                
            except Exception as primary_error:
                # Fallback to gemini-2.0-flash-exp
                logger.info(f"🔄 V2: Using fallback model for key facts extraction")
                fallback_model = genai.GenerativeModel(
                    'gemini-2.0-flash-exp',
                    safety_settings=safety_settings
                )
                
                response = fallback_model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.2,
                        'max_output_tokens': 200,
                    }
                )
                
                if not response.candidates or not response.candidates[0].content.parts:
                    logger.error(f"❌ V2: Fallback model also blocked for key facts")
                    raise Exception(f"Both primary and fallback models blocked")
                
                logger.info(f"✅ V2: Fallback successful for key facts extraction")
            
            # Parse bullet points
            facts_text = response.text.strip()
            facts = []
            for line in facts_text.split('\n'):
                line = line.strip()
                # Remove bullet markers
                for marker in ['•', '-', '*', '–']:
                    if line.startswith(marker):
                        line = line[1:].strip()
                        break
                # Remove numbering
                import re
                line = re.sub(r'^\d+[\.\)]\s*', '', line)
                
                if line and len(line) > 10:  # Minimum length
                    facts.append(line)
            
            logger.info(f"📋 V2: Extracted {len(facts)} key facts")
            return facts[:7]  # Max 7 facts
            
        except Exception as e:
            logger.error(f"❌ V2: Failed to extract key facts: {e}")
            return []
    
    @classmethod
    def _estimate_context_tokens(cls, stored: Dict, verbatim_count: int) -> int:
        """Estimate total token count for context"""
        total = 0
        
        # Verbatim
        total += verbatim_count * 80  # Estimate 80 tokens per message
        
        # Summaries
        if stored.get('recent'):
            total += 200
        if stored.get('mid'):
            total += 250
        if stored.get('old'):
            total += 200
        
        # Key facts
        facts = stored.get('key_facts', [])
        total += len(facts) * 20  # Estimate 20 tokens per fact
        
        return total
    
    @classmethod
    def _estimate_tokens(cls, text: str) -> int:
        """Estimate token count from text"""
        if not text:
            return 0
        
        try:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except:
            # Fallback: word count * 1.3
            return int(len(text.split()) * 1.3)
    
    @classmethod
    def clear_memory(cls, conversation):
        """Clear session memory for a conversation"""
        try:
            from AI_model.models import SessionMemory
            SessionMemory.objects.filter(conversation=conversation).delete()
            
            cache_key = f"session_memory_v2:{conversation.id}"
            cache.delete(cache_key)
            
            logger.info(f"🗑️ V2: Cleared session memory for conversation {conversation.id}")
        except Exception as e:
            logger.error(f"❌ V2: Failed to clear memory: {e}")

