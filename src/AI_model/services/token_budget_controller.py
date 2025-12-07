"""
Token Budget Controller
Enforces strict 2200 token limit for Gemini input (optimized for Persian)
Uses tiktoken for accurate token counting
"""
import logging
from typing import Dict, List
import tiktoken

logger = logging.getLogger(__name__)

# Global cache for tiktoken encoder
_TOKEN_ENCODER = None

def _get_encoder():
    """Get cached tiktoken encoder (singleton pattern)"""
    global _TOKEN_ENCODER
    if _TOKEN_ENCODER is None:
        _TOKEN_ENCODER = tiktoken.get_encoding("cl100k_base")
    return _TOKEN_ENCODER


class TokenBudgetController:
    """
    Strict token budget enforcement
    Target: ≤ 2200 tokens total input to Gemini (optimized for Persian language)
    
    Uses tiktoken for accurate counting (not simple word count estimation)
    """
    
    # Token budget allocation (Optimized for Persian language)
    BUDGET = {
        'system_prompt': 700,      # ✅ INCREASED to 700 - Critical for anti-hallucination rules
        'bio_context': 60,          # Reduced -20 - Instagram bio for personalization
        'customer_info': 30,        # Customer name, phone, source
        'conversation': 250,        # Reduced -50 - Recent conversation context
        'primary_context': 600,     # Reduced -50 - Main knowledge source
        'secondary_context': 510,   # Reduced -180 - Secondary knowledge source
        # Total: 2150 tokens (max 2200 with safety margin)
        # ⚠️ system_prompt has highest priority - contains anti-hallucination rules
    }
    
    # Safety margin
    MAX_TOTAL_TOKENS = 2200  # ✅ INCREASED from 1700 to 2200 for better context coverage
    SAFETY_MARGIN = 50  # Reserve 50 tokens for safety
    
    @classmethod
    def trim_to_budget(cls, components: Dict) -> Dict:
        """
        Trim components to fit within 2200 token budget
        
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
        # ✅ Fixed: Remove critical rules from prompt BEFORE trimming, then add back ONCE at end
        system_prompt = components.get('system_prompt', '')
        critical_rules = cls._extract_critical_rules(system_prompt)
        
        # Remove critical rules from system prompt to avoid duplication
        # They will be added back ONCE at the end
        non_critical_prompt = system_prompt
        if critical_rules:
            # Remove the critical rules section from the prompt
            for marker in ["🚨 CRITICAL - Anti-Hallucination:", "🔗 CRITICAL - Links & URLs:", "🔗 CRITICAL - Links"]:
                if marker in non_critical_prompt:
                    start_idx = non_critical_prompt.find(marker)
                    if start_idx != -1:
                        # Find end of this section
                        remaining = non_critical_prompt[start_idx:]
                        next_section_markers = ["🧠 Language:", "💬 Style:", "📝 Response", "🎯 Greeting", "⚡ Additional", "When lacking"]
                        end_idx = len(remaining)
                        for next_marker in next_section_markers:
                            marker_idx = remaining.find(next_marker)
                            if marker_idx > 0 and marker_idx < end_idx:
                                end_idx = marker_idx
                        non_critical_prompt = non_critical_prompt[:start_idx] + non_critical_prompt[start_idx + end_idx:]
        
        # Count tokens for non-critical part
        non_critical_tokens = cls._count_tokens(non_critical_prompt)
        critical_tokens = cls._count_tokens(critical_rules) if critical_rules else 0
        
        # Reserve space for critical rules
        non_critical_budget = cls.BUDGET['system_prompt'] - critical_tokens - 20  # 20 for separator
        
        if non_critical_tokens > non_critical_budget and non_critical_budget > 100:
            # Trim only the non-critical part
            non_critical_prompt = cls._trim_text_to_tokens(non_critical_prompt, non_critical_budget)
        
        # Combine: non-critical + critical rules (added exactly ONCE)
        if critical_rules:
            system_prompt = non_critical_prompt.strip() + "\n\n" + critical_rules
        else:
            system_prompt = non_critical_prompt.strip()
        
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
            
            # Update used tokens
            used_tokens += secondary_tokens
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
        
        # ✅ LOG TOKEN USAGE FOR MONITORING
        logger.info(
            f"📊 Token Budget Breakdown:\n"
            f"  • System Prompt: {result['system_prompt_tokens']}/{cls.BUDGET['system_prompt']} tokens\n"
            f"  • Bio Context: {result['bio_context_tokens']}/{cls.BUDGET['bio_context']} tokens\n"
            f"  • Customer Info: {result['customer_info_tokens']}/{cls.BUDGET['customer_info']} tokens\n"
            f"  • Conversation: {result['conversation_tokens']}/{cls.BUDGET['conversation']} tokens\n"
            f"  • Primary Context: {result['primary_context_tokens']}/{cls.BUDGET['primary_context']} tokens\n"
            f"  • Secondary Context: {result['secondary_context_tokens']}/{cls.BUDGET['secondary_context']} tokens\n"
            f"  • User Query: {result['user_query_tokens']} tokens\n"
            f"  ━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  • TOTAL: {result['total_tokens']}/{cls.MAX_TOTAL_TOKENS} tokens"
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
        ✅ v2: Greedy fill strategy - maximize budget usage
        
        Strategy:
        1. Sort by score (assume items pre-sorted by RAG)
        2. Take top_k items (default: 20)
        3. Add chunks greedily until budget is full
        4. Handle edge case: first chunk > max_tokens
        
        This ensures:
        - All available budget is used (90-95% efficiency)
        - Maximum number of relevant chunks included
        - No artificial 2-3 chunk limit
        
        IMPORTANT: items MUST be pre-sorted by score (descending)
        
        Args:
            items: List of dicts with 'title' and 'content' (PRE-SORTED by score!)
            max_tokens: Maximum token budget
        
        Returns:
            (trimmed_items, actual_tokens)
        """
        if not items:
            logger.info("📭 No context items received for trimming")
            return [], 0
        
        encoder = _get_encoder()
        
        # Step 1: Take top_k only (avoid noise)
        TOP_K = 20
        sorted_items = items[:TOP_K]
        
        # Step 2: Calculate tokens for each chunk
        items_with_tokens = []
        for item in sorted_items:
            content = item.get('content', '') or ''
            title = item.get('title', '') or ''
            text = f"{title}: {content}" if title else content
            
            tokens = encoder.encode(text)
            items_with_tokens.append({
                **item,
                'tokens': len(tokens),
                '_encoded': tokens  # cache for potential trim
            })
        
        # Step 3: Greedy fill until budget is full
        selected = []
        used_tokens = 0
        
        for i, item in enumerate(items_with_tokens):
            chunk_tokens = item['tokens']
            
            # 🔥 Edge case: chunk > max_tokens
            if chunk_tokens > max_tokens:
                if i == 0:
                    # First chunk: trim to fit
                    logger.warning(
                        f"⚠️ First chunk too large ({chunk_tokens} > {max_tokens}), "
                        f"trimming to fit"
                    )
                    trimmed_tokens = item['_encoded'][:max_tokens]
                    item['content'] = encoder.decode(trimmed_tokens)
                    item['tokens'] = len(trimmed_tokens)
                    selected.append(item)
                    used_tokens = item['tokens']
                else:
                    # Not first: skip this chunk
                    logger.debug(
                        f"⏭️ Skipping large chunk ({chunk_tokens} tokens) at position {i}"
                    )
                continue
            
            # Normal case: check if fits
            if used_tokens + chunk_tokens <= max_tokens:
                selected.append(item)
                used_tokens += chunk_tokens
            else:
                # Budget full, stop
                logger.debug(
                    f"🛑 Budget full: {used_tokens}/{max_tokens} tokens, "
                    f"selected {len(selected)}/{len(items_with_tokens)} chunks"
                )
                break
        
        # Clean up: remove _encoded (temporary data)
        for item in selected:
            item.pop('_encoded', None)
        
        # Step 4: Log for monitoring
        usage_pct = int(used_tokens / max_tokens * 100) if max_tokens > 0 else 0
        logger.info(
            f"📊 Context trimming: {len(items)} → {len(selected)} chunks, "
            f"{used_tokens}/{max_tokens} tokens ({usage_pct}% used)"
        )
        
        return selected, used_tokens
    
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

