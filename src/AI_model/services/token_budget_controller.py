"""
Token Budget Controller
Enforces strict 1700 token limit for Gemini input (optimized for Persian)
Uses tiktoken for accurate token counting
"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class TokenBudgetController:
    """
    Strict token budget enforcement
    Target: ≤ 1700 tokens total input to Gemini (optimized for Persian language)
    
    Uses tiktoken for accurate counting (not simple word count estimation)
    """
    
    # Token budget allocation (Optimized for Persian language)
    BUDGET = {
        'system_prompt': 400,      # ✅ Increased for Persian (auto + manual prompts)
        'bio_context': 80,          # Instagram bio for personalization (multilingual)
        'customer_info': 30,        # Customer name, phone, source
        'conversation': 400,        # ✅ Increased for V2 multi-tier memory
        'primary_context': 650,     # ✅ Increased - Main knowledge source
        'secondary_context': 200,   # Optional supplementary
        # Total: 1760 tokens (max 1700 with safety margin)
    }
    
    # Safety margin
    MAX_TOTAL_TOKENS = 1700  # ✅ Increased from 1500 for Persian language
    SAFETY_MARGIN = 50  # Reserve 50 tokens for safety
    
    @classmethod
    def trim_to_budget(cls, components: Dict) -> Dict:
        """
        Trim components to fit within 1700 token budget
        
        Args:
            components: {
                'system_prompt': str,
                'bio_context': str,  # Optional (Instagram bio for personalization)
                'customer_info': str,
                'conversation': str,
                'primary_context': List[Dict],  # [{title, content, type}]
                'secondary_context': List[Dict],
                'user_query': str
            }
        
        Returns:
            Trimmed components with actual token counts:
            {
                'system_prompt': str,
                'system_prompt_tokens': int,
                'bio_context': str,
                'bio_context_tokens': int,
                'customer_info': str,
                'customer_info_tokens': int,
                'conversation': str,
                'conversation_tokens': int,
                'primary_context': List[Dict],
                'primary_context_tokens': int,
                'secondary_context': List[Dict],
                'secondary_context_tokens': int,
                'user_query': str,
                'user_query_tokens': int,
                'total_tokens': int
            }
        """
        result = {}
        
        # 1. User query (mandatory, highest priority)
        user_query = components.get('user_query', '')
        user_query_tokens = cls._count_tokens(user_query)
        
        # If user query alone exceeds reasonable limit, trim it
        if user_query_tokens > 150:
            user_query = cls._trim_text_to_tokens(user_query, 150)
            user_query_tokens = 150
        
        result['user_query'] = user_query
        result['user_query_tokens'] = user_query_tokens
        
        # 2. System prompt (mandatory)
        system_prompt = components.get('system_prompt', '')
        system_prompt_tokens = cls._count_tokens(system_prompt)
        
        if system_prompt_tokens > cls.BUDGET['system_prompt']:
            system_prompt = cls._trim_text_to_tokens(system_prompt, cls.BUDGET['system_prompt'])
            system_prompt_tokens = cls.BUDGET['system_prompt']
        
        result['system_prompt'] = system_prompt
        result['system_prompt_tokens'] = system_prompt_tokens
        
        # 2.5. Bio context for personalization (optional, Instagram only)
        bio_context = components.get('bio_context', '')
        bio_context_tokens = cls._count_tokens(bio_context)
        
        if bio_context_tokens > cls.BUDGET['bio_context']:
            bio_context = cls._trim_text_to_tokens(bio_context, cls.BUDGET['bio_context'])
            bio_context_tokens = cls.BUDGET['bio_context']
        
        result['bio_context'] = bio_context
        result['bio_context_tokens'] = bio_context_tokens
        
        # 3. Customer info (for personalization)
        customer_info = components.get('customer_info', '')
        customer_info_tokens = cls._count_tokens(customer_info)
        
        if customer_info_tokens > cls.BUDGET['customer_info']:
            customer_info = cls._trim_text_to_tokens(customer_info, cls.BUDGET['customer_info'])
            customer_info_tokens = cls.BUDGET['customer_info']
        
        result['customer_info'] = customer_info
        result['customer_info_tokens'] = customer_info_tokens
        
        # 4. Conversation context (important for continuity)
        conversation = components.get('conversation', '')
        conversation_tokens = cls._count_tokens(conversation)
        
        if conversation_tokens > cls.BUDGET['conversation']:
            conversation = cls._trim_text_to_tokens(conversation, cls.BUDGET['conversation'])
            conversation_tokens = cls.BUDGET['conversation']
        
        result['conversation'] = conversation
        result['conversation_tokens'] = conversation_tokens
        
        # Calculate tokens used so far
        used_tokens = (
            result['user_query_tokens'] +
            result['system_prompt_tokens'] +
            result['bio_context_tokens'] +
            result['customer_info_tokens'] +
            result['conversation_tokens']
        )
        
        # Calculate remaining budget
        remaining = cls.MAX_TOTAL_TOKENS - used_tokens - cls.SAFETY_MARGIN
        
        if remaining < 100:
            # Critical: not enough budget left, reduce conversation
            logger.warning(f"⚠️ Critical token budget! Reducing conversation context")
            new_conversation_budget = cls.BUDGET['conversation'] - 100
            conversation = cls._trim_text_to_tokens(conversation, max(100, new_conversation_budget))
            result['conversation'] = conversation
            result['conversation_tokens'] = cls._count_tokens(conversation)
            
            # Recalculate
            used_tokens = (
                result['user_query_tokens'] +
                result['system_prompt_tokens'] +
                result['bio_context_tokens'] +
                result['customer_info_tokens'] +
                result['conversation_tokens']
            )
            remaining = cls.MAX_TOTAL_TOKENS - used_tokens - cls.SAFETY_MARGIN
        
        # 4. Primary context (critical knowledge)
        primary_context = components.get('primary_context', [])
        primary_budget = min(remaining * 0.75, cls.BUDGET['primary_context'])  # 75% of remaining
        
        result['primary_context'], primary_tokens = cls._trim_context_items(
            primary_context,
            int(primary_budget)
        )
        result['primary_context_tokens'] = primary_tokens
        
        # Recalculate remaining
        used_tokens += primary_tokens
        remaining = cls.MAX_TOTAL_TOKENS - used_tokens - cls.SAFETY_MARGIN
        
        # 5. Secondary context (optional, only if budget allows)
        secondary_context = components.get('secondary_context', [])
        
        if remaining > 50 and secondary_context:
            secondary_budget = min(remaining, cls.BUDGET['secondary_context'])
            result['secondary_context'], secondary_tokens = cls._trim_context_items(
                secondary_context,
                int(secondary_budget)
            )
            result['secondary_context_tokens'] = secondary_tokens
        else:
            result['secondary_context'] = []
            result['secondary_context_tokens'] = 0
        
        # Calculate final total
        result['total_tokens'] = (
            result['system_prompt_tokens'] +
            result['bio_context_tokens'] +
            result['customer_info_tokens'] +
            result['user_query_tokens'] +
            result['conversation_tokens'] +
            result['primary_context_tokens'] +
            result['secondary_context_tokens']
        )
        
        # Final safety check
        if result['total_tokens'] > cls.MAX_TOTAL_TOKENS:
            logger.error(
                f"❌ Token budget EXCEEDED: {result['total_tokens']} > {cls.MAX_TOTAL_TOKENS}! "
                f"Emergency trimming..."
            )
            # Emergency: cut secondary completely
            result['secondary_context'] = []
            result['secondary_context_tokens'] = 0
            
            # If still over, reduce primary
            if result['total_tokens'] - result['secondary_context_tokens'] > cls.MAX_TOTAL_TOKENS:
                overage = result['total_tokens'] - result['secondary_context_tokens'] - cls.MAX_TOTAL_TOKENS
                new_primary_budget = max(300, result['primary_context_tokens'] - overage - 50)
                result['primary_context'], primary_tokens = cls._trim_context_items(
                    result['primary_context'],
                    int(new_primary_budget)
                )
                result['primary_context_tokens'] = primary_tokens
            
            # Recalculate
            result['total_tokens'] = (
                result['system_prompt_tokens'] +
                result['bio_context_tokens'] +
                result['customer_info_tokens'] +
                result['user_query_tokens'] +
                result['conversation_tokens'] +
                result['primary_context_tokens']
            )
        
        logger.info(
            f"📊 Token budget: {result['total_tokens']}/{cls.MAX_TOTAL_TOKENS} tokens "
            f"(system: {result['system_prompt_tokens']}, "
            f"bio: {result['bio_context_tokens']}, "
            f"customer: {result['customer_info_tokens']}, "
            f"conv: {result['conversation_tokens']}, "
            f"primary: {result['primary_context_tokens']}, "
            f"secondary: {result['secondary_context_tokens']}, "
            f"query: {result['user_query_tokens']})"
        )
        
        return result
    
    @classmethod
    def _count_tokens(cls, text: str) -> int:
        """
        Count tokens using tiktoken (accurate for GPT models)
        Falls back to conservative estimation if tiktoken fails
        """
        if not text:
            return 0
        
        try:
            import tiktoken
            # Use cl100k_base encoding (for GPT-3.5/4 and Gemini estimation)
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"tiktoken failed: {e}, using fallback estimation")
            # Fallback: Conservative estimation (1 token ≈ 0.6 words for multilingual)
            # Using 1.5x multiplier to be safe
            return int(len(text.split()) * 1.5)
    
    @classmethod
    def _trim_text_to_tokens(cls, text: str, max_tokens: int) -> str:
        """
        Trim text to fit within token budget
        Uses tiktoken for accurate trimming
        """
        if not text:
            return ""
        
        current_tokens = cls._count_tokens(text)
        if current_tokens <= max_tokens:
            return text
        
        try:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
            tokens = encoding.encode(text)
            
            # Trim to max_tokens
            trimmed_tokens = tokens[:max_tokens]
            trimmed_text = encoding.decode(trimmed_tokens)
            
            return trimmed_text + "..."
            
        except Exception as e:
            logger.warning(f"tiktoken trimming failed: {e}, using word-based fallback")
            # Fallback: word-based trimming
            words = text.split()
            # Rough estimate: keep 60% of words to fit token budget
            max_words = int(max_tokens * 0.6)
            return ' '.join(words[:max_words]) + '...'
    
    @classmethod
    def _trim_context_items(cls, items: List[Dict], max_tokens: int) -> tuple:
        """
        Trim list of context items to fit within token budget
        
        Args:
            items: List of dicts with 'title' and 'content'
            max_tokens: Maximum token budget
        
        Returns:
            (trimmed_items, actual_tokens)
        """
        if not items:
            return [], 0
        
        trimmed = []
        total_tokens = 0
        
        for item in items:
            content = item.get('content', '')
            title = item.get('title', '')
            
            # Count tokens for title + content
            full_text = f"{title}: {content}" if title else content
            item_tokens = cls._count_tokens(full_text)
            
            if total_tokens + item_tokens <= max_tokens:
                # Item fits completely
                trimmed.append(item)
                total_tokens += item_tokens
            else:
                # Check if we can fit a trimmed version
                remaining = max_tokens - total_tokens
                if remaining > 100:  # Minimum 100 tokens per item to be useful
                    # Trim the content to fit
                    title_tokens = cls._count_tokens(title) if title else 0
                    content_budget = remaining - title_tokens - 10  # Reserve 10 for formatting
                    
                    if content_budget > 50:
                        trimmed_content = cls._trim_text_to_tokens(content, content_budget)
                        trimmed.append({
                            **item,
                            'content': trimmed_content
                        })
                        total_tokens += remaining
                
                # Budget exhausted
                break
        
        return trimmed, total_tokens

