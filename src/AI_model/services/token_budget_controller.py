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
        # ✅ Extract CRITICAL rules before trimming to preserve them
        system_prompt = components.get('system_prompt', '')
        critical_rules = cls._extract_critical_rules(system_prompt)
        
        system_prompt_tokens = cls._count_tokens(system_prompt)
        
        if system_prompt_tokens > cls.BUDGET['system_prompt']:
            # Trim system prompt but preserve critical rules
            trimmed_prompt = cls._trim_text_to_tokens(system_prompt, cls.BUDGET['system_prompt'])
            # Re-add critical rules if they were removed
            if critical_rules and critical_rules not in trimmed_prompt:
                # Calculate space for critical rules
                critical_tokens = cls._count_tokens(critical_rules)
                available_space = cls.BUDGET['system_prompt'] - cls._count_tokens(trimmed_prompt)
                if available_space >= critical_tokens:
                    system_prompt = trimmed_prompt + "\n\n" + critical_rules
                else:
                    # If no space, trim more to make room for critical rules
                    space_for_prompt = cls.BUDGET['system_prompt'] - critical_tokens - 20  # 20 for separator
                    if space_for_prompt > 100:  # At least 100 tokens for main prompt
                        system_prompt = cls._trim_text_to_tokens(system_prompt, space_for_prompt) + "\n\n" + critical_rules
                    else:
                        # Critical rules are more important, keep them
                        system_prompt = trimmed_prompt + "\n\n" + critical_rules
            else:
                system_prompt = trimmed_prompt
            system_prompt_tokens = cls._count_tokens(system_prompt)
        
        result['system_prompt'] = system_prompt
        result['system_prompt_tokens'] = system_prompt_tokens
        result['critical_rules'] = critical_rules  # Store for later use
        
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
        secondary_context = components.get('secondary_context', [])
        
        # Smart budget allocation: If primary is empty, give its budget to secondary
        if not primary_context and secondary_context:
            # Primary is empty: Use all remaining budget for secondary
            secondary_budget = min(remaining, cls.BUDGET['primary_context'] + cls.BUDGET['secondary_context'])
            result['secondary_context'], secondary_tokens = cls._trim_context_items(
                secondary_context,
                int(secondary_budget)
            )
            result['secondary_context_tokens'] = secondary_tokens
            result['primary_context'] = []
            result['primary_context_tokens'] = 0
        else:
            # Normal case: Primary gets 75%, Secondary gets remaining
            primary_budget = min(remaining * 0.75, cls.BUDGET['primary_context'])
            
            result['primary_context'], primary_tokens = cls._trim_context_items(
                primary_context,
                int(primary_budget)
            )
            result['primary_context_tokens'] = primary_tokens
            
            # Recalculate remaining
            used_tokens += primary_tokens
            remaining = cls.MAX_TOTAL_TOKENS - used_tokens - cls.SAFETY_MARGIN
            
            # 5. Secondary context (optional, only if budget allows)
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
        ⭐ IMPROVED RAG APPROACH (Intercom, LangChain, LlamaIndex):
        Smart token distribution: Prioritize first 2 results (usually most relevant),
        then distribute remaining budget across other results.
        
        Strategy:
        1. First result: 50% of budget (ensures important info is NOT trimmed)
        2. Second result: 25% of budget (backup if answer is in second result)
        3. Others: 25% total (distributed evenly, ensures diversity)
        
        This ensures that:
        - If answer is in Result 1 → Gets 325 tokens (enough for complete info)
        - If answer is in Result 2 → Gets 162 tokens (substantial info)
        - If answer is in Result 3-5 → Still gets 50-80 tokens each (basic info)
        
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
        
        # Strategy: Prioritize first 2 results, then distribute remaining
        # First result: 50% (325 tokens) - Ensures important info is NOT trimmed
        # Second result: 25% (162 tokens) - Backup if answer is in second result
        # Others: 25% (163 tokens total) - Distribute evenly
        first_result_budget = int(max_tokens * 0.50)  # 50% for first result (325 tokens)
        second_result_budget = int(max_tokens * 0.25)  # 25% for second result (162 tokens)
        remaining_budget = max_tokens - first_result_budget - second_result_budget  # 25% for others
        
        # Calculate budget for remaining items (try to fit 2-3 more items)
        target_remaining_items = min(3, len(items) - 2) if len(items) > 2 else 0  # Try to fit 3 more items
        if target_remaining_items > 0:
            avg_tokens_per_remaining = remaining_budget // target_remaining_items
        else:
            avg_tokens_per_remaining = remaining_budget
        
        min_tokens_per_item = 100  # Minimum to be useful
        
        for i, item in enumerate(items):
            content = item.get('content', '')
            title = item.get('title', '')
            
            # Calculate tokens needed
            title_tokens = cls._count_tokens(title) if title else 0
            full_tokens = cls._count_tokens(f"{title}: {content}") if title else cls._count_tokens(content)
            
            # Allocate tokens for this item
            if i == 0:
                # First result: 50% of budget (325 tokens)
                allocated_tokens = first_result_budget
            elif i == 1:
                # Second result: 25% of budget (162 tokens)
                allocated_tokens = second_result_budget
            elif i - 2 < target_remaining_items:  # i=2,3,4 → i-2=0,1,2 < 3
                # Remaining results: Distribute evenly
                allocated_tokens = avg_tokens_per_remaining
            else:
                # Beyond target: Use remaining budget
                allocated_tokens = max_tokens - total_tokens
            
            # Check if item fits in allocated budget
            if full_tokens <= allocated_tokens:
                # Item fits completely
                trimmed.append(item)
                total_tokens += full_tokens
            else:
                # Trim content to fit allocated budget
                content_budget = allocated_tokens - title_tokens - 10  # Reserve 10 for formatting
                
                if content_budget >= min_tokens_per_item:
                    trimmed_content = cls._trim_text_to_tokens(content, content_budget)
                    trimmed.append({
                        **item,
                        'content': trimmed_content
                    })
                    total_tokens += allocated_tokens
                else:
                    # Not enough budget for this item, stop
                    break
            
            # Stop if budget exhausted
            if total_tokens >= max_tokens:
                break
        
        return trimmed, total_tokens
    
    @classmethod
    def _extract_critical_rules(cls, system_prompt: str) -> str:
        """
        Extract CRITICAL rules (Anti-Hallucination and Link Handling) from system prompt
        These rules MUST be preserved even if system prompt is trimmed
        
        Args:
            system_prompt: Full system prompt text
            
        Returns:
            Extracted critical rules as string, or empty string if not found
        """
        if not system_prompt:
            return ""
        
        critical_sections = []
        
        # Extract Anti-Hallucination rules
        if "🚨 CRITICAL - Anti-Hallucination:" in system_prompt or "CRITICAL - Anti-Hallucination:" in system_prompt:
            # Find the section
            start_marker = "🚨 CRITICAL - Anti-Hallucination:" if "🚨 CRITICAL - Anti-Hallucination:" in system_prompt else "CRITICAL - Anti-Hallucination:"
            start_idx = system_prompt.find(start_marker)
            
            if start_idx != -1:
                # Find the end of this section (next section marker or end of prompt)
                remaining = system_prompt[start_idx:]
                end_markers = [
                    "🔗 CRITICAL - Links & URLs:",
                    "🔗 CRITICAL - Links",
                    "⚡ Additional Instructions:",
                    "🎓 Pilito",
                    "🔹 SCENARIO:"
                ]
                
                end_idx = len(remaining)
                for marker in end_markers:
                    marker_idx = remaining.find(marker, len(start_marker))
                    if marker_idx != -1 and marker_idx < end_idx:
                        end_idx = marker_idx
                
                anti_hallucination = remaining[:end_idx].strip()
                if anti_hallucination:
                    critical_sections.append(anti_hallucination)
        
        # Extract Link Handling rules
        if "🔗 CRITICAL - Links & URLs:" in system_prompt or "🔗 CRITICAL - Links" in system_prompt:
            # Find the section
            start_marker = "🔗 CRITICAL - Links & URLs:" if "🔗 CRITICAL - Links & URLs:" in system_prompt else "🔗 CRITICAL - Links"
            start_idx = system_prompt.find(start_marker)
            
            if start_idx != -1:
                # Find the end of this section (next section marker or end of prompt)
                remaining = system_prompt[start_idx:]
                end_markers = [
                    "🚨 CRITICAL - Anti-Hallucination:",
                    "⚡ Additional Instructions:",
                    "🎓 Pilito",
                    "🔹 SCENARIO:"
                ]
                
                end_idx = len(remaining)
                for marker in end_markers:
                    marker_idx = remaining.find(marker, len(start_marker))
                    if marker_idx != -1 and marker_idx < end_idx:
                        end_idx = marker_idx
                
                link_handling = remaining[:end_idx].strip()
                if link_handling:
                    critical_sections.append(link_handling)
        
        # Combine all critical sections
        if critical_sections:
            return "\n\n".join(critical_sections)
        
        return ""

