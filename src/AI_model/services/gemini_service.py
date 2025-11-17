import logging
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# ✅ Setup proxy BEFORE importing Gemini (required for Iran servers)
from core.utils import setup_ai_proxy
setup_ai_proxy()

# ✅ Feature flags for gradual rollout
from AI_model.services.feature_flags import use_production_rag

# Import Gemini AI library
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False

# Gemini API key will be loaded from GeneralSettings
def get_gemini_api_key():
    """Get Gemini API key from GeneralSettings model"""
    try:
        from settings.models import GeneralSettings
        settings = GeneralSettings.get_settings()
        return settings.gemini_api_key
    except Exception as e:
        logger.error(f"Error getting Gemini API key from settings: {str(e)}")
        return None

logger = logging.getLogger(__name__)


class GeminiChatService:
    """
    Service for handling AI chat interactions using Gemini 1.5 Flash
    Uses global configuration and existing Message model
    """
    
    def __init__(self, user):
        self.user = user
        self.ai_config = self._get_global_ai_config()
        self.ai_prompts = self._get_ai_prompts()
        self.model = None
        
        # Get API key from GeneralSettings
        gemini_api_key = get_gemini_api_key()
        
        # Configure Gemini API
        if (GEMINI_AVAILABLE and 
            gemini_api_key and 
            len(gemini_api_key) > 20 and  # API keys are typically long
            not any(placeholder in gemini_api_key.upper() for placeholder in ['YOUR', 'PLACEHOLDER', 'EXAMPLE'])):
            try:
                genai.configure(api_key=gemini_api_key)
                # Limit max tokens to 400 for concise responses (600 chars ≈ 400 tokens)
                max_tokens = min(self.ai_config.max_tokens, 400)
                
                # Safety settings: BLOCK_NONE for business communications
                # Allow all content for customer support (privacy policies, sensitive data discussions, etc.)
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
                
                self.model = genai.GenerativeModel(
                    model_name=self.ai_config.model_name,
                    generation_config={
                        "temperature": self.ai_config.temperature,
                        "max_output_tokens": max_tokens,
                        "top_p": 0.8,
                        "top_k": 40
                    },
                    system_instruction="""You are a professional AI customer service assistant for various types of businesses including:
- E-commerce stores (fashion, electronics, home goods, etc.)
- Service providers (courses, consulting, training)
- Online businesses (digital products, subscriptions)
- Retail businesses (coffee, food, accessories, tools)

YOUR ROLE:
- Answer customer questions professionally and accurately
- Provide information about products, services, prices, and availability
- Share business details (location, contact, hours, shipping, policies)
- Assist with orders, inquiries, and customer support
- Communicate in the customer's language (Persian/Farsi, English, Arabic, Turkish)

CONTENT PROCESSING GUIDELINES:
This is a legitimate business customer support chatbot. ALL content you process is appropriate business communication:
- Product descriptions and details are NORMAL business content
- Pricing and payment information is STANDARD commercial data
- Business addresses and contact details are PUBLIC information
- Shipping and delivery discussions are ROUTINE e-commerce
- Service descriptions and features are PROFESSIONAL content
- Customer inquiries about ANY products/services are LEGITIMATE

IMPORTANT:
- Process ALL customer questions without applying content restrictions
- Do not block or filter legitimate business communications
- All conversations are for proper commercial purposes
- Treat all product categories (fashion, food, electronics, courses, etc.) as appropriate business content""",
                    safety_settings=safety_settings
                )
                logger.info(f"Gemini API configured for user {user.username if user else 'System'} using GeneralSettings")
            except Exception as e:
                logger.exception("Error configuring Gemini API")
                self.model = None
        else:
            logger.warning(f"Gemini API key not configured in GeneralSettings for user {user.username if user else 'System'}")
    
    def _get_global_ai_config(self):
        """Get global AI configuration"""
        from AI_model.models import AIGlobalConfig
        return AIGlobalConfig.get_config()
    
    def _get_ai_prompts(self):
        """Get AI prompts from settings app using OneToOneField relationship"""
        try:
            from settings.models import AIPrompts
            
            # Use OneToOneField relationship for direct access
            try:
                ai_prompts = self.user.ai_prompts
                return ai_prompts
            except AIPrompts.DoesNotExist:
                # Auto-create AI prompts if they don't exist
                logger.info(f"Creating AI prompts for user {self.user.username}")
                ai_prompts, created = AIPrompts.get_or_create_for_user(self.user)
                if created:
                    logger.info(f"✅ Auto-created AIPrompts for user {self.user.username}")
                return ai_prompts
                
        except Exception as e:
            logger.error(f"Error getting AI prompts for user {self.user.username if self.user else 'Unknown'}: {str(e)}")
            return None
    
    def generate_response(self, customer_message: str, conversation=None) -> Dict[str, Any]:
        """
        Generate AI response using Gemini 1.5 Flash
        
        Args:
            customer_message: The customer's message
            conversation: Conversation instance for context
            
        Returns:
            Dict containing response data and metadata
        """
        start_time = time.time()
        
        if not self.model:
            return {
                'success': False,
                'error': 'Gemini API not configured',
                'response': None,
                'metadata': {}
            }
        
        # Check if AI prompts are configured for this user
        if not self.ai_prompts:
            error_msg = f"AI prompts not configured for user {self.user.username if self.user else 'Unknown'}. Please set up AI prompts in the admin panel."
            logger.error(error_msg)
            self._track_usage(
                success=False,
                error_message=error_msg,
                metadata={'error_type': 'configuration_error'}
            )
            return {
                'success': False,
                'error': 'AI_PROMPTS_NOT_CONFIGURED',
                'response': error_msg,
                'metadata': {
                    'error_type': 'configuration_error',
                    'user_action_required': 'Configure AI prompts in admin panel'
                }
            }
        
        # Check if manual_prompt is set and validate AI prompts
        try:
            self.ai_prompts.validate_for_ai_response()
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"AI prompts validation failed for user {self.user.username if self.user else 'Unknown'}: {error_msg}")
            self._track_usage(
                success=False,
                error_message=error_msg,
                metadata={'error_type': 'validation_error'}
            )
            return {
                'success': False,
                'error': 'MANUAL_PROMPT_NOT_SET',
                'response': error_msg,
                'metadata': {
                    'error_type': 'configuration_error',
                    'user_action_required': 'Set manual_prompt in AI prompts configuration'
                }
            }
        
        try:
            # Build the prompt with conversation context
            prompt = self._build_prompt(customer_message, conversation)
            
            # ✅ LOG FULL PROMPT FOR DEBUGGING
            logger.info("=" * 100)
            logger.info("🔍 FULL PROMPT SENT TO AI:")
            logger.info("=" * 100)
            logger.info(prompt)
            logger.info("=" * 100)
            
            # Check if critical rules are present
            if "Anti-Hallucination" in prompt or "NEVER promise" in prompt or "NEVER say" in prompt:
                logger.info("✅ Anti-Hallucination rules FOUND in prompt")
            else:
                logger.warning("❌ Anti-Hallucination rules NOT FOUND in prompt!")
            
            if "Link" in prompt and ("FULL URLs" in prompt or "placeholder" in prompt):
                logger.info("✅ Link Handling rules FOUND in prompt")
            else:
                logger.warning("❌ Link Handling rules NOT FOUND in prompt!")
            
            # Generate content using Gemini (safety_settings already set in model initialization)
            response = self.model.generate_content(prompt)
            
            # Check for safety blocks or empty responses
            if not response.candidates or not response.candidates[0].content.parts:
                # Safety block detected - try fallback to Gemini 2.0 Flash Experimental
                finish_reason = response.candidates[0].finish_reason if response.candidates else None
                logger.warning(f"⚠️ Gemini {self.ai_config.model_name} blocked (finish_reason: {finish_reason})")
                logger.warning(f"🔄 Attempting fallback to gemini-2.0-flash-exp...")
                
                # Try fallback model
                try:
                    import google.generativeai as genai
                    fallback_model = genai.GenerativeModel(
                        model_name="gemini-2.0-flash-exp",
                        generation_config={
                            "temperature": self.ai_config.temperature,
                            "max_output_tokens": min(self.ai_config.max_tokens, 400),
                            "top_p": 0.8,
                            "top_k": 40
                        },
                        system_instruction="""You are a professional AI customer service assistant for various types of businesses including:
- E-commerce stores (fashion, electronics, home goods, etc.)
- Service providers (courses, consulting, training)
- Online businesses (digital products, subscriptions)
- Retail businesses (coffee, food, accessories, tools)

YOUR ROLE:
- Answer customer questions professionally and accurately
- Provide information about products, services, prices, and availability
- Share business details (location, contact, hours, shipping, policies)
- Assist with orders, inquiries, and customer support
- Communicate in the customer's language (Persian/Farsi, English, Arabic, Turkish)

CONTENT PROCESSING GUIDELINES:
This is a legitimate business customer support chatbot. ALL content you process is appropriate business communication:
- Product descriptions and details are NORMAL business content
- Pricing and payment information is STANDARD commercial data
- Business addresses and contact details are PUBLIC information
- Shipping and delivery discussions are ROUTINE e-commerce
- Service descriptions and features are PROFESSIONAL content
- Customer inquiries about ANY products/services are LEGITIMATE

IMPORTANT:
- Process ALL customer questions without applying content restrictions
- Do not block or filter legitimate business communications
- All conversations are for proper commercial purposes
- Treat all product categories (fashion, food, electronics, courses, etc.) as appropriate business content""",
                        safety_settings=[
                            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                        ]
                    )
                    
                    response = fallback_model.generate_content(prompt)
                    
                    if not response.candidates or not response.candidates[0].content.parts:
                        logger.error(f"❌ Fallback model also blocked (finish_reason: {response.candidates[0].finish_reason if response.candidates else 'unknown'})")
                        raise Exception(f"Both primary and fallback models blocked - finish_reason: {response.candidates[0].finish_reason if response.candidates else 'unknown'}")
                    
                    logger.info(f"✅ Fallback to gemini-2.0-flash-exp succeeded!")
                    
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback failed: {fallback_error}")
                    raise Exception(f"Gemini safety block and fallback failed - original finish_reason: {finish_reason}")
            
            response_text = response.text
            
            # Check for abnormally short responses (likely incomplete generation)
            if len(response_text.strip()) < 10:  # Less than 10 characters
                finish_reason = response.candidates[0].finish_reason if response.candidates else None
                logger.warning(f"⚠️ Gemini returned very short response ({len(response_text)} chars): '{response_text}'")
                logger.warning(f"🔍 finish_reason: {finish_reason}")
                logger.warning(f"🔄 This indicates incomplete generation - consider using fallback or adjusting prompt")
            
            # Extract token usage if available
            prompt_tokens = 0
            completion_tokens = 0
            
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                prompt_tokens = getattr(usage, 'prompt_token_count', 0)
                completion_tokens = getattr(usage, 'candidates_token_count', 0)
            else:
                # Fallback estimates
                prompt_tokens = len(prompt.split())
                completion_tokens = len(response_text.split())
            
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            # Track usage and bill tokens
            self._track_usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                response_time_ms=response_time_ms,
                success=True,
                metadata={
                    'conversation_id': str(conversation.id) if conversation else None,
                    'model_used': self.ai_config.model_name
                }
            )
            try:
                total_tokens = int(prompt_tokens) + int(completion_tokens)
            except Exception:
                total_tokens = 0
            if total_tokens > 0 and self.user:
                try:
                    from billing.services import consume_tokens_for_user
                    consume_tokens_for_user(self.user, total_tokens, description='AI response generation')
                except Exception as billing_error:
                    logger.error(f"Failed to bill tokens for user {self.user.username if self.user else 'Unknown'}: {billing_error}")
            
            logger.info(f"AI response generated for user {self.user.username if self.user else 'Unknown'}: {response_text[:50]}...")
            
            return {
                'success': True,
                'response': response_text,
                'response_time_ms': response_time_ms,
                'metadata': {
                    'model_used': self.ai_config.model_name,
                    'prompt_tokens': prompt_tokens,
                    'completion_tokens': completion_tokens,
                    'total_tokens': prompt_tokens + completion_tokens,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'api_key_used': 'GeneralSettings'
                }
            }
            
        except Exception as e:
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            error_msg = "I apologize, but I'm experiencing technical difficulties. Please try again later."
            error_details = str(e)  # Keep for error_message tracking
            # Log with full traceback for debugging
            logger.exception(f"Error generating Gemini response for user {self.user.username if self.user else 'Unknown'}")
            
            # Track failed usage (no billing)
            self._track_usage(
                prompt_tokens=0,
                completion_tokens=0,
                response_time_ms=response_time_ms,
                success=False,
                error_message=error_details,
                metadata={
                    'conversation_id': str(conversation.id) if conversation else None,
                    'error_type': 'generation_error'
                }
            )
            
            return {
                'success': False,
                'error': str(e),
                'response': error_msg,
                'response_time_ms': response_time_ms,
                'metadata': {
                    'model_used': self.ai_config.model_name,
                    'prompt_tokens': 0,
                    'completion_tokens': 0,
                    'total_tokens': 0,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'api_key_used': 'GeneralSettings'
                }
            }
    
    def _rank_qa_with_bm25(self, qa_queryset, customer_message: str, top_n: int = 8):
        """
        Rank Q&A pairs using BM25 algorithm based on relevance to customer message
        
        Args:
            qa_queryset: QuerySet of QAPair objects
            customer_message: Customer's message/question
            top_n: Number of top Q&A pairs to return
            
        Returns:
            List of top N most relevant Q&A pairs
        """
        try:
            from rank_bm25 import BM25Okapi
            
            # Convert queryset to list for BM25
            all_qa = list(qa_queryset)
            
            # If we have fewer Q&A than requested, return all
            if len(all_qa) <= top_n:
                return all_qa
            
            # Prepare corpus: combine question and answer for better matching
            corpus = []
            for qa in all_qa:
                # Combine question and answer, give more weight to question
                doc = f"{qa.question} {qa.question} {qa.answer}"
                corpus.append(doc)
            
            # Tokenize corpus (simple split, works for both English and Farsi)
            tokenized_corpus = [doc.lower().split() for doc in corpus]
            
            # Create BM25 model
            bm25 = BM25Okapi(tokenized_corpus)
            
            # Tokenize query
            tokenized_query = customer_message.lower().split()
            
            # Get scores for all documents
            scores = bm25.get_scores(tokenized_query)
            
            # Get top N indices
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_n]
            
            # Return top N Q&A pairs
            top_qa = [all_qa[i] for i in top_indices]
            
            logger.info(f"BM25 ranking: Selected {len(top_qa)} most relevant Q&A from {len(all_qa)} total")
            return top_qa
            
        except ImportError:
            # Fallback: if rank-bm25 not installed, use original method
            logger.warning("rank-bm25 not installed, falling back to simple selection")
            return list(qa_queryset[:top_n])
        except Exception as e:
            # Fallback: if any error, use original method
            logger.error(f"BM25 ranking failed: {str(e)}, falling back to simple selection")
            return list(qa_queryset[:top_n])
    
    def _rank_qa_with_embedding(self, qa_queryset, customer_message: str, top_n: int = 8):
        """
        Rank Q&A pairs using semantic embedding (with BM25 fallback)
        ✅ Safe: Falls back to BM25 if embedding fails
        ✅ Smart: Uses Gemini text-embedding-004 for multilingual semantic search
        
        Args:
            qa_queryset: QuerySet of QAPair objects
            customer_message: Customer's message/question
            top_n: Number of top Q&A pairs to return
            
        Returns:
            Tuple: (List of top N most relevant Q&A pairs, average similarity score)
        """
        try:
            from AI_model.services.embedding_service import EmbeddingService
            
            # Initialize embedding service
            emb_service = EmbeddingService(use_cache=True)
            
            # Convert queryset to list
            all_qa = list(qa_queryset)
            
            # If we have fewer Q&A than requested, return all with neutral score
            if len(all_qa) <= top_n:
                return all_qa, 0.75  # Neutral confidence
            
            # Get query embedding
            query_emb = emb_service.get_embedding(customer_message, task_type="retrieval_query")
            
            if not query_emb:
                # Fallback to BM25 if embedding fails
                logger.info("🔄 Embedding not available, falling back to BM25")
                qa_list = self._rank_qa_with_bm25(qa_queryset, customer_message, top_n)
                return qa_list, 0.70  # Lower confidence for BM25
            
            # Calculate similarity scores for all Q&A pairs
            scores = []
            for qa in all_qa:
                # Combine question and answer for better matching
                # Give more weight to question by including it twice
                doc_text = f"{qa.question} {qa.question} {qa.answer}"
                doc_emb = emb_service.get_embedding(doc_text, task_type="retrieval_document")
                
                if doc_emb:
                    similarity = emb_service.cosine_similarity(query_emb, doc_emb)
                    scores.append((qa, similarity))
                else:
                    # If individual embedding fails, give low score
                    scores.append((qa, 0.0))
            
            # Sort by similarity score (descending)
            scores.sort(key=lambda x: x[1], reverse=True)
            
            # Extract top N Q&A pairs
            top_qa = [item[0] for item in scores[:top_n]]
            
            # Calculate average similarity score for confidence
            avg_score = sum(s[1] for s in scores[:top_n]) / len(scores[:top_n]) if scores[:top_n] else 0.0
            
            logger.info(f"✅ Embedding ranking: Selected {len(top_qa)} most relevant Q&A from {len(all_qa)} total (avg score: {avg_score:.3f})")
            return top_qa, avg_score
            
        except ImportError:
            # Fallback: if embedding service not available
            logger.warning("⚠️ EmbeddingService not available, falling back to BM25")
            qa_list = self._rank_qa_with_bm25(qa_queryset, customer_message, top_n)
            return qa_list, 0.70  # Lower confidence for BM25
        except Exception as e:
            # Fallback: if any error occurs
            logger.error(f"❌ Embedding ranking failed: {str(e)}, falling back to BM25")
            qa_list = self._rank_qa_with_bm25(qa_queryset, customer_message, top_n)
            return qa_list, 0.65  # Even lower confidence for error fallback
    
    def _get_confidence_instruction(self, avg_similarity: float, has_facts: bool = True) -> str:
        """
        Generate confidence instruction based on knowledge base match quality
        
        Args:
            avg_similarity: Average similarity score from embedding search (0.0-1.0)
            has_facts: Whether any facts (FAQ/Products/Website) were found
            
        Returns:
            Confidence instruction string for the prompt
        """
        if not has_facts or avg_similarity < 0.45:
            # LOW CONFIDENCE: Very weak or no matches
            return """
⚠️ CONFIDENCE LEVEL: LOW
You have very weak or no relevant information for this query.

REQUIRED ACTIONS:
1. If you can provide helpful general guidance based on common knowledge, do so - be creative and helpful!
2. Only if completely unrelated to your domain, admit: "I don't have specific information about this in our documentation."
3. If relevant to business but no specific details: "I can provide general guidance about [topic], but for precise details, let me connect you with our team."
4. Be conversational and friendly - help the customer even with general knowledge when appropriate

EXAMPLE: "Based on common industry practices, [helpful general answer]. For specific details about our implementation, I can connect you with our team! 😊"
"""
        elif avg_similarity < 0.65:
            # MEDIUM CONFIDENCE: Partial matches
            return """
💡 CONFIDENCE LEVEL: MEDIUM
You have relevant information with good matches.

REQUIRED ACTIONS:
1. Answer confidently based on the available information - be helpful and creative!
2. You can combine facts creatively to provide comprehensive answers
3. Only add light disclaimer if genuinely unsure: "If you need more specific details, I'm here to help!"
4. Be natural and conversational - avoid sounding overly cautious

EXAMPLE: "Based on our documentation, [confident answer with relevant details]. If you'd like more specific information, just let me know! 😊"
"""
        else:
            # HIGH CONFIDENCE: Strong matches
            return """
✅ CONFIDENCE LEVEL: HIGH
You have excellent relevant information for this query.

REQUIRED ACTIONS:
1. Answer confidently, clearly, and comprehensively
2. Use the facts provided in FAQ/Products/Website data creatively
3. Be specific with details (prices, features, policies) 
4. Combine related information to give complete, helpful answers
5. Be natural, friendly, and professional - no need for disclaimers

EXAMPLE: "[Direct, confident, comprehensive answer with specific details from the knowledge base]"
"""
    
    def _get_conversation_summary(self, conversation_id: str, min_messages: int = 10) -> str:
        """
        Generate a summary of long conversations to reduce token usage and improve context understanding
        (Phase 1 - Feature 3: Conversation Intelligence)
        
        Args:
            conversation_id: The conversation ID to summarize
            min_messages: Minimum number of messages before summarization kicks in
            
        Returns:
            Summary string if conversation is long enough, None otherwise
        """
        try:
            from django.core.cache import cache
            from message.models import Message
            
            # Check cache first (1 hour TTL)
            cache_key = f"conv_summary:{conversation_id}"
            cached_summary = cache.get(cache_key)
            if cached_summary:
                logger.info(f"✅ Using cached conversation summary for {conversation_id}")
                return cached_summary
            
            # Get all messages for this conversation
            messages = Message.objects.filter(
                conversation_id=conversation_id
            ).only('type', 'content', 'created_at').order_by('created_at')
            
            message_count = messages.count()
            
            # Don't summarize short conversations
            if message_count <= min_messages:
                logger.debug(f"Conversation {conversation_id} has only {message_count} messages, skipping summarization")
                return None
            
            # Build conversation history (exclude last 5 messages - they'll be included separately)
            # Fix: Use explicit limit instead of negative indexing (QuerySet doesn't support it)
            exclude_last = 5
            history_limit = max(0, message_count - exclude_last)
            history_messages = list(messages[:history_limit]) if history_limit > 0 else []
            history_lines = []
            
            for msg in history_messages:
                role = "Customer" if msg.type == 'customer' else "Assistant"
                # Truncate long messages for summary
                content = msg.content[:200] + ('...' if len(msg.content) > 200 else '')
                history_lines.append(f"{role}: {content}")
            
            history_text = "\n".join(history_lines)
            
            # Create summarization prompt
            summary_prompt = f"""Summarize this conversation in 2-3 clear sentences. Focus on:
- What the customer is trying to accomplish
- Key information already provided
- Current status of the conversation

Conversation history ({len(history_messages)} messages):
{history_text}

Provide a concise summary (max 100 words):"""
            
            # Generate summary using Gemini (lightweight, max 150 tokens)
            if not self.model:
                logger.warning("Gemini model not initialized, cannot generate summary")
                return None
            
            # Generate summary (safety_settings already set in model initialization)
            response = self.model.generate_content(
                summary_prompt,
                generation_config={
                    'temperature': 0.3,  # Lower temperature for more focused summary
                    'max_output_tokens': 150,
                    'top_p': 0.8,
                    'top_k': 20
                }
            )
            
            summary = response.text.strip()
            
            # Cache for 1 hour
            cache.set(cache_key, summary, 3600)
            
            logger.info(f"✅ Generated conversation summary for {conversation_id} ({message_count} messages → {len(summary)} chars)")
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate conversation summary: {str(e)}")
            return None  # Graceful fallback - use full history
    
    def _build_prompt(self, customer_message: str, conversation=None) -> str:
        """
        Build Lean RAG v2.1 prompt (target: ≤1700 tokens, optimized for Persian)
        
        Uses:
        - QueryRouter: Intent classification
        - SessionMemoryManagerV2: Multi-tier conversation memory
        - ContextRetriever: Semantic search with pgvector
        - TokenBudgetController: Strict 1700 token limit (Persian optimized)
        """
        try:
            from AI_model.services.query_router import QueryRouter
            from AI_model.services.session_memory_manager_v2 import SessionMemoryManagerV2
            from AI_model.services.context_retriever import ContextRetriever
            from AI_model.services.token_budget_controller import TokenBudgetController
            
            # 1. Route query to determine intent & sources
            routing = QueryRouter.route_query(customer_message, user=self.user)
            
            logger.info(
                f"🎯 Routed to: {routing['intent']} → {routing['primary_source']} "
                f"(conf: {routing['confidence']:.2f})"
            )
            
            # 2. Build system prompt (concise!)
            system_prompt = self._build_lean_system_prompt(routing['intent'], conversation)
            
            # 2.5. Get bio context for personalization (Instagram only)
            bio_context = ""
            if conversation and conversation.source == 'instagram' and conversation.customer:
                bio = conversation.customer.bio
                if bio:
                    bio_context = self._build_bio_context(
                        bio,
                        conversation.customer.first_name
                    )
                    logger.info(f"🎨 Bio context enabled for customer {conversation.customer.id}")
            
            # 3. Get customer info (for personalization)
            customer_info = ""
            if conversation and conversation.customer:
                customer = conversation.customer
                info_parts = []
                # Build full name from first_name and last_name
                name_parts = []
                if customer.first_name:
                    name_parts.append(customer.first_name)
                if customer.last_name:
                    name_parts.append(customer.last_name)
                if name_parts:
                    info_parts.append(f"Name: {' '.join(name_parts)}")
                if customer.email:
                    info_parts.append(f"Email: {customer.email}")
                if customer.phone_number:
                    info_parts.append(f"Phone: {customer.phone_number}")
                if customer.description:
                    info_parts.append(f"Description: {customer.description}")
                if conversation.source:
                    info_parts.append(f"Source: {conversation.source}")
                # Add customer tags
                try:
                    if hasattr(customer, 'tag') and customer.tag.exists():
                        tags = ", ".join(customer.tag.values_list('name', flat=True))
                        info_parts.append(f"Tags: {tags}")
                except Exception as e:
                    logger.debug(f"Could not retrieve customer tags: {e}")
                
                # Add last message information
                try:
                    from message.models import Message
                    from django.utils import timezone
                    
                    # Get last message overall (any type)
                    last_message = Message.objects.filter(
                        conversation=conversation
                    ).order_by('-created_at').first()
                    
                    if last_message:
                        days_since = (timezone.now() - last_message.created_at).days
                        msg_type = last_message.type
                        if days_since == 0:
                            info_parts.append(f"Last message: today ({msg_type})")
                        elif days_since == 1:
                            info_parts.append(f"Last message: yesterday ({msg_type})")
                        else:
                            info_parts.append(f"Last message: {days_since} days ago ({msg_type})")
                    
                    # Get last customer message specifically
                    last_customer_msg = Message.objects.filter(
                        conversation=conversation,
                        type='customer'
                    ).order_by('-created_at').first()
                    
                    if last_customer_msg:
                        days_since_customer = (timezone.now() - last_customer_msg.created_at).days
                        if days_since_customer == 0:
                            info_parts.append(f"Last customer message: today")
                        elif days_since_customer == 1:
                            info_parts.append(f"Last customer message: yesterday")
                        else:
                            info_parts.append(f"Last customer message: {days_since_customer} days ago")
                            
                except Exception as msg_err:
                    logger.debug(f"Could not retrieve message info: {msg_err}")
                
                if info_parts:
                    customer_info = "Customer: " + ", ".join(info_parts)
            
            # 4. Get conversation context (rolling summary + recent messages)
            conversation_context = ""
            if conversation:
                context_data = SessionMemoryManagerV2.get_conversation_context(conversation)
                
                # V2 returns a dict, convert to string
                if isinstance(context_data, dict):
                    parts = []
                    
                    # Add recent verbatim messages (most important)
                    if context_data.get('verbatim'):
                        recent_msgs = []
                        for msg in context_data['verbatim'][-5:]:  # Last 5 messages
                            speaker = "Customer" if msg['type'] == 'customer' else "AI"
                            recent_msgs.append(f"{speaker}: {msg['content']}")
                        if recent_msgs:
                            parts.append("Recent:\n" + "\n".join(recent_msgs))
                    
                    # Add summaries if available
                    if context_data.get('recent_summary'):
                        parts.append(f"Summary: {context_data['recent_summary']}")
                    
                    conversation_context = "\n\n".join(parts) if parts else ""
                else:
                    # Fallback: V1 compatibility (string)
                    conversation_context = context_data or ""
            
            # 5. Retrieve relevant context from knowledge base
            # ✅ Use ProductionRAG if feature flag is enabled, otherwise ContextRetriever
            if use_production_rag(user=self.user):
                try:
                    from AI_model.services.production_rag import ProductionRAG
                    logger.info("🚀 Using ProductionRAG for advanced retrieval")
                    
                    retrieval_result = ProductionRAG.retrieve_context(
                        query=customer_message,
                        user=self.user,
                        primary_source=routing['primary_source'],
                        secondary_sources=routing['secondary_sources'],
                        primary_budget=routing['token_budgets']['primary'],
                        secondary_budget=routing['token_budgets']['secondary'],
                        routing_info=routing
                    )
                except Exception as e:
                    logger.error(f"❌ ProductionRAG failed: {e}, falling back to ContextRetriever")
                    retrieval_result = ContextRetriever.retrieve_context(
                        query=customer_message,
                        user=self.user,
                        primary_source=routing['primary_source'],
                        secondary_sources=routing['secondary_sources'],
                        primary_budget=routing['token_budgets']['primary'],
                        secondary_budget=routing['token_budgets']['secondary'],
                        routing_info=routing
                    )
            else:
                logger.debug("Using ContextRetriever (ProductionRAG disabled)")
                retrieval_result = ContextRetriever.retrieve_context(
                    query=customer_message,
                    user=self.user,
                    primary_source=routing['primary_source'],
                    secondary_sources=routing['secondary_sources'],
                    primary_budget=routing['token_budgets']['primary'],
                    secondary_budget=routing['token_budgets']['secondary'],
                    routing_info=routing
                )
            
            # 6. Apply strict token budget (1500 tokens max)
            components = {
                'system_prompt': system_prompt,
                'bio_context': bio_context,
                'customer_info': customer_info,
                'conversation': conversation_context,
                'primary_context': retrieval_result['primary_context'],
                'secondary_context': retrieval_result['secondary_context'],
                'user_query': customer_message
            }
            
            trimmed = TokenBudgetController.trim_to_budget(components)
            
            # 7. Build final prompt
            prompt_parts = []
            
            # System instructions
            prompt_parts.append(f"SYSTEM: {trimmed['system_prompt']}")
            
            # Bio context for personalization (Instagram only)
            if trimmed.get('bio_context'):
                prompt_parts.append(f"\n{trimmed['bio_context']}")
            
            # Customer info
            if trimmed.get('customer_info'):
                prompt_parts.append(f"\n{trimmed['customer_info']}")
            
            # Conversation context
            if trimmed['conversation']:
                prompt_parts.append(f"\nCONVERSATION HISTORY:\n{trimmed['conversation']}")
            
            # Primary knowledge
            if trimmed['primary_context']:
                primary_text = "\n\n".join([
                    f"**{item['title']}**\n{item['content']}"
                    for item in trimmed['primary_context']
                ])
                prompt_parts.append(f"\nKNOWLEDGE BASE:\n{primary_text}")
            
            # Secondary knowledge (if included)
            if trimmed['secondary_context']:
                secondary_text = "\n\n".join([
                    f"- {item['title']}: {item['content']}"
                    for item in trimmed['secondary_context']
                ])
                prompt_parts.append(f"\nADDITIONAL INFO:\n{secondary_text}")
            
            # User query (always at end)
            prompt_parts.append(f"\nCUSTOMER QUESTION:\n{trimmed['user_query']}")
            
            # Final instruction
            memory_guidance = ""
            if conversation and conversation_context:
                memory_guidance = (
                    "\n\n⚡ CONVERSATION MEMORY:\n"
                    "The conversation summary and recent messages show what you've already discussed. "
                    "USE THIS TO:\n"
                    "- Avoid repeating information already provided\n"
                    "- Reference previous context (e.g., 'As I mentioned earlier...')\n"
                    "- Build on the ongoing discussion naturally\n"
                    "- Remember products/services the customer asked about\n"
                )
            
            prompt_parts.append(
                "\nINSTRUCTION: Answer the customer's question using the knowledge base above. "
                "CRITICAL RULES: "
                "- ✅ FIRST: Check if you have relevant chunks in the KNOWLEDGE BASE above. "
                "- ✅ If chunks are provided → USE THEM! Answer COMPLETELY and FULLY using that information. "
                "- ✅ If you see ANY relevant information in chunks → Share it ALL, don't be cautious! "
                "- ❌ ONLY say 'متأسفانه این اطلاعات الان در دسترس نیست' if you have ZERO relevant chunks. "
                "- ✅ If you see partial information → Provide what you have and be helpful. "
                "- ✅ Don't be overly cautious - if information exists in chunks, use it fully! "
                "- Be natural, concise, and friendly."
                + memory_guidance
            )
            
            # ✅ REINFORCE CRITICAL RULES at the end (after trimming) for maximum impact
            critical_rules = trimmed.get('critical_rules', '')
            if critical_rules:
                prompt_parts.append(
                    "\n\n" + "=" * 80 +
                    "\n🚨🚨🚨 CRITICAL RULES - MUST FOLLOW (READ CAREFULLY):" +
                    "\n" + "=" * 80 +
                    "\n" + critical_rules +
                    "\n" + "=" * 80
                )
                logger.info("✅ Critical rules reinforced at end of prompt")
            
            final_prompt = "\n".join(prompt_parts)
            
            # ✅ LOG FINAL PROMPT FOR DEBUGGING
            logger.info("=" * 100)
            logger.info("🔍 FINAL PROMPT BUILT (after trimming):")
            logger.info("=" * 100)
            logger.info(final_prompt)
            logger.info("=" * 100)
            
            logger.info(
                f"✅ Lean RAG prompt built: {trimmed['total_tokens']} tokens "
                f"(system: {trimmed['system_prompt_tokens']}, "
                f"bio: {trimmed.get('bio_context_tokens', 0)}, "
                f"customer: {trimmed.get('customer_info_tokens', 0)}, "
                f"conv: {trimmed['conversation_tokens']}, "
                f"context: {trimmed['primary_context_tokens'] + trimmed['secondary_context_tokens']}, "
                f"query: {trimmed['user_query_tokens']})"
            )
            
            return final_prompt
                    
        except Exception as e:
            logger.error(f"❌ Lean RAG prompt building failed: {e}, using fallback")
            return self._build_prompt_fallback(customer_message, conversation)
    
    def _build_bio_context(self, bio: str, user_name: str = None) -> str:
        """
        Build customer bio context for personalization (multilingual support)
        Token budget: ~50-100 tokens (bio is sent as-is to Gemini)
        
        Args:
            bio: Instagram biography text (any language: English, Persian, Arabic, etc.)
            user_name: Customer's first name (optional)
        
        Returns:
            Formatted bio context section
        """
        if not bio or not bio.strip():
            return ""
        
        # Build simple, clean bio context
        # Let Gemini interpret the bio intelligently (tone, interests, profession)
        parts = []
        
        if user_name:
            parts.append(f"Customer: {user_name}")
        
        parts.append(f"Bio: {bio.strip()}")
        
        context = "\n".join(parts)
        
        return f"""CUSTOMER CONTEXT:
{context}

INSTRUCTION: Adapt your tone and recommendations based on the customer's background shown in their bio. Be natural and contextually appropriate.""".strip()
    
    def _build_lean_system_prompt(self, intent: str, conversation=None) -> str:
        """
        Build concise system prompt (target: ≤400 tokens)
        
        ⚠️ IMPORTANT: Manual prompt is NOT included here!
        Manual prompt is chunked and retrieved via RAG (TenantKnowledge with chunk_type='manual')
        
        This method ONLY includes:
        1. GeneralSettings (11 modular fields: ai_role, language_rules, tone, etc.)
        2. BusinessPrompt (optional industry-specific instructions)
        3. Dynamic greeting context (FIRST_MESSAGE, WELCOME_BACK, RECENT_CONVERSATION)
        
        Returns:
            str: System instructions WITHOUT manual prompt
        """
        try:
            from settings.models import GeneralSettings, BusinessPrompt
            
            prompt_parts = []
            
            # 1. GeneralSettings system prompt (11 modular fields)
            # This contains behavior rules that apply to ALL users
            system_prompt = GeneralSettings.get_settings().get_combined_system_prompt()
            if system_prompt and system_prompt.strip():
                prompt_parts.append(system_prompt.strip())
            
            # 2. BusinessPrompt (optional industry-specific instructions)
            try:
                business = BusinessPrompt.objects.filter(ai_answer_prompt__isnull=False).first()
                if business and business.ai_answer_prompt:
                    prompt_parts.append(business.ai_answer_prompt)
            except Exception:
                pass
            
            # 3. Dynamic greeting context
            # Greeting rules are in GeneralSettings.greeting_rules
            # Here we just add scenario markers for the AI to know which scenario applies
            if conversation:
                from message.models import Message
                from django.utils import timezone
                
                # Check if this is first AI message
                ai_message_count = Message.objects.filter(
                    conversation=conversation,
                    type='AI'
                ).count()
                
                # Get last AI message time
                last_ai_msg = Message.objects.filter(
                    conversation=conversation,
                    type='AI'
                ).order_by('-created_at').first()
                
                # Get threshold from settings
                settings = GeneralSettings.get_settings()
                threshold_hours = getattr(settings, 'welcome_back_threshold_hours', 12)
                
                # Determine greeting scenario (just add context marker, not full instructions)
                if ai_message_count == 0:
                    prompt_parts.append("🔹 SCENARIO: FIRST_MESSAGE")
                elif last_ai_msg:
                    hours_since_last = (timezone.now() - last_ai_msg.created_at).total_seconds() / 3600
                    if hours_since_last >= threshold_hours:
                        prompt_parts.append(f"🔹 SCENARIO: WELCOME_BACK (after {threshold_hours}+ hours)")
                    else:
                        prompt_parts.append("🔹 SCENARIO: RECENT_CONVERSATION (already greeted)")
            
            # Combine all parts
            full_prompt = "\n\n".join(prompt_parts)
            
            # ✅ LOG SYSTEM PROMPT FOR DEBUGGING
            logger.info("=" * 80)
            logger.info("🔍 SYSTEM PROMPT (from GeneralSettings):")
            logger.info("=" * 80)
            logger.info(full_prompt)
            logger.info("=" * 80)
            
            # Check if critical rules are in system prompt
            if "Anti-Hallucination" in full_prompt or "NEVER promise" in full_prompt or "NEVER say" in full_prompt:
                logger.info("✅ Anti-Hallucination rules FOUND in system prompt")
            else:
                logger.warning("❌ Anti-Hallucination rules NOT FOUND in system prompt!")
            
            if "Link" in full_prompt and ("FULL URLs" in full_prompt or "placeholder" in full_prompt):
                logger.info("✅ Link Handling rules FOUND in system prompt")
            else:
                logger.warning("❌ Link Handling rules NOT FOUND in system prompt!")
            
            # NO TRIMMING! Let TokenBudgetController handle token limits
            # Manual prompt chunks will be added via RAG context retrieval
            
            return full_prompt
            
        except Exception as e:
            logger.warning(f"Failed to build lean system prompt: {e}")
            return "You are a helpful AI assistant. Answer questions accurately using the knowledge base provided."
    
    def _build_prompt_fallback(self, customer_message: str, conversation=None) -> str:
        """
        Fallback prompt when Lean RAG fails
        Simplified version of old method
        Now uses modular system prompt!
        """
        try:
            from settings.models import GeneralSettings
            
            # Basic system prompt (now using modular approach)
            system_prompt = GeneralSettings.get_settings().get_combined_system_prompt() or "You are a helpful AI assistant."
            
            # Recent conversation context (last 3 messages)
            conversation_context = ""
            if conversation:
                try:
                    from message.models import Message
                    recent = Message.objects.filter(
                        conversation=conversation
                    ).order_by('-created_at')[:3]
                    
                    if recent:
                        lines = [
                            f"{'User' if m.type == 'customer' else 'Assistant'}: {m.content}"
                            for m in reversed(recent)
                        ]
                        conversation_context = "\n".join(lines)
                except:
                    pass
            
            # Build simple prompt
            parts = [
                f"SYSTEM: {system_prompt}",
            ]
            
            if conversation_context:
                parts.append(f"\nRECENT MESSAGES:\n{conversation_context}")
            
            parts.append(
                f"\nCUSTOMER QUESTION:\n{customer_message}\n\n"
                f"Answer the question helpfully and concisely."
            )
            
            return "\n".join(parts)
            
        except Exception as e:
            logger.error(f"Even fallback prompt failed: {e}")
            return f"SYSTEM: You are a helpful AI assistant.\n\nQUESTION: {customer_message}"
    
    def _track_usage(self, prompt_tokens=0, completion_tokens=0, response_time_ms=0, success=True, error_message=None, metadata=None):
        """
        Track AI usage statistics for this user
        Uses unified tracking service to update both AIUsageLog and AIUsageTracking
        """
        try:
            from AI_model.services.usage_tracker import track_ai_usage_safe
            
            if not self.user:
                logger.warning("Cannot track usage: user is None")
                return
            
            # Use unified tracking function - updates both AIUsageLog and AIUsageTracking
            track_ai_usage_safe(
                user=self.user,
                section='chat',  # This is the main chat service
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                response_time_ms=response_time_ms,
                success=success,
                model_name=self.ai_config.model_name if hasattr(self, 'ai_config') and self.ai_config else 'gemini-1.5-flash',
                error_message=error_message,
                metadata=metadata or {}
            )
            
            logger.info(
                f"✅ AI usage tracked for user {self.user.username}: "
                f"{prompt_tokens + completion_tokens} tokens, {response_time_ms}ms, "
                f"success={success}"
            )
            
        except Exception as e:
            logger.error(
                f"❌ Error tracking AI usage for user {self.user.username if self.user else 'Unknown'}: {str(e)}"
            )
    
    def is_configured(self) -> bool:
        """Check if the AI service is properly configured"""
        gemini_api_key = get_gemini_api_key()
        api_key_valid = (
            gemini_api_key and 
            len(gemini_api_key) > 20 and  # API keys are typically long
            not any(placeholder in gemini_api_key.upper() for placeholder in ['YOUR', 'PLACEHOLDER', 'EXAMPLE'])
        )
        
        return (
            GEMINI_AVAILABLE and 
            api_key_valid and
            self.model is not None and
            self.ai_config.auto_response_enabled
        )
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get the current configuration status"""
        gemini_api_key = get_gemini_api_key()
        api_key_valid = (
            gemini_api_key and 
            len(gemini_api_key) > 20 and  # API keys are typically long
            not any(placeholder in gemini_api_key.upper() for placeholder in ['YOUR', 'PLACEHOLDER', 'EXAMPLE'])
        )
        
        return {
            'gemini_available': GEMINI_AVAILABLE,
            'api_key_configured': api_key_valid,
            'model_initialized': self.model is not None,
            'auto_response_enabled': self.ai_config.auto_response_enabled,
            'ai_prompts_configured': self.ai_prompts is not None,
            'model_name': self.ai_config.model_name,
            'api_key_source': 'GeneralSettings'
        }
    
    def create_ai_message(self, conversation, ai_response: Dict[str, Any]):
        """
        Create AI message in the Message model with proper metadata
        
        Args:
            conversation: Conversation instance
            ai_response: AI response dictionary from generate_response
            
        Returns:
            Message instance or None if failed
        """
        try:
            from message.models import Message
            from message.utils.cta_utils import extract_cta_from_text  # ✅ از message/utils import
            
            # Extract token counts from AI response
            prompt_tokens = ai_response.get('metadata', {}).get('prompt_tokens', 0)
            completion_tokens = ai_response.get('metadata', {}).get('completion_tokens', 0)
            total_tokens = ai_response.get('metadata', {}).get('total_tokens', 0)
            
            # ✅ Extract CTA buttons from response (با .get() برای جلوگیری از crash)
            original_content = ai_response.get('response') or ''
            clean_content, buttons = extract_cta_from_text(original_content)
            
            # ✅ اطمینان از این‌که content خالی نباشد
            if not clean_content or not clean_content.strip():
                logger.warning(f"AI response content is empty after CTA extraction, using original")
                clean_content = original_content
                buttons = None
            
            # Create AI message with metadata and token tracking
            ai_message = Message.objects.create(
                conversation=conversation,
                customer=conversation.customer,
                content=clean_content,  # ✅ متن بدون توکن‌های CTA
                buttons=buttons,  # ✅ دکمه‌های استخراج شده (یا None)
                type='AI',
                is_ai_response=True,
                # Token tracking fields (new)
                input_tokens=prompt_tokens,
                output_tokens=completion_tokens,
                total_tokens=total_tokens,
                # Metadata for backward compatibility and additional info
                metadata={
                    'response_time_ms': ai_response.get('response_time_ms', 0),
                    'model_used': ai_response.get('metadata', {}).get('model_used', self.ai_config.model_name),
                    'prompt_tokens': prompt_tokens,
                    'completion_tokens': completion_tokens,
                    'total_tokens': total_tokens,
                    'auto_generated': True,
                    'global_api_used': True,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'ai_service_version': '1.0',
                    'sent_from_app': True,  # Mark as sent from app
                    'has_cta_buttons': buttons is not None,  # ✅ Flag for monitoring
                }
            )
            
            logger.info(f"✅ AI message created: {ai_message.id} for conversation {conversation.id}")
            if buttons:
                logger.info(f"   📌 With {len(buttons)} CTA button(s)")
            logger.info(f"   Content: {ai_message.content[:50]}...")
            logger.info(f"   Type: {ai_message.type}")
            logger.info(f"   is_ai_response: {ai_message.is_ai_response}")
            
            # Send the AI response to the appropriate platform
            self._send_ai_response_to_platform(ai_message, conversation)
            
            return ai_message
            
        except Exception as e:
            logger.error(f"Error creating AI message for conversation {conversation.id}: {str(e)}")
            return None

    def _send_ai_response_to_platform(self, ai_message, conversation):
        """
        Send AI response to the appropriate platform (Telegram/Instagram)
        
        Args:
            ai_message: The created AI Message instance
            conversation: Conversation instance
        """
        try:
            if conversation.source == 'telegram':
                self._send_telegram_response(ai_message, conversation)
            elif conversation.source == 'instagram':
                self._send_instagram_response(ai_message, conversation)
            else:
                logger.warning(f"Unknown conversation source: {conversation.source}")
                
        except Exception as e:
            logger.error(f"Error sending AI response to platform for conversation {conversation.id}: {str(e)}")

    def _send_telegram_response(self, ai_message, conversation):
        """Send AI response to Telegram"""
        try:
            from message.services.telegram_service import TelegramService
            
            telegram_service = TelegramService.get_service_for_conversation(conversation)
            if not telegram_service:
                logger.error(f"Could not get Telegram service for conversation {conversation.id}")
                return
            
            result = telegram_service.send_message_to_customer(
                conversation.customer, 
                ai_message.content
            )
            
            if result.get('success'):
                logger.info(f"✅ AI response sent to Telegram successfully: message {ai_message.id}")
            else:
                logger.error(f"❌ Failed to send AI response to Telegram: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error sending AI response to Telegram: {str(e)}")

    def _send_instagram_response(self, ai_message, conversation):
        """Send AI response to Instagram with dynamic typing indicator management"""
        try:
            from message.services.instagram_service import InstagramService
            from django.core.cache import cache
            
            instagram_service = InstagramService.get_service_for_conversation(conversation)
            if not instagram_service:
                logger.error(f"Could not get Instagram service for conversation {conversation.id}")
                return
            
            customer = conversation.customer
            
            # Get typing start time from cache
            typing_start_key = f"typing_start_{conversation.id}"
            typing_start_time = cache.get(typing_start_key)
            
            # Ensure typing_on is active (in case it wasn't sent earlier or timed out)
            if not typing_start_time:
                # If no start time in cache, send typing_on now and record time
                try:
                    typing_on_result = instagram_service.send_typing_indicator_to_customer(customer, 'typing_on')
                    if typing_on_result.get('success'):
                        typing_start_time = time.time()
                        cache.set(typing_start_key, typing_start_time, timeout=60)
                        logger.debug(f"✍️ Typing ON sent (no cached start time)")
                except Exception as typing_err:
                    logger.debug(f"Error ensuring typing_on: {typing_err}")
                    typing_start_time = time.time()  # Use current time as fallback
            
            # Wait 1 second to show typing indicator before sending message
            time.sleep(1)
            
            # ✅ دریافت دکمه‌ها از ai_message
            buttons = getattr(ai_message, 'buttons', None)
            
            # Send the actual message
            message_sent_time = time.time()
            result = instagram_service.send_message_to_customer(
                customer, 
                ai_message.content,
                buttons=buttons  # ✅ پاس دادن دکمه‌ها
            )
            
            if result.get('success'):
                logger.info(f"✅ AI response sent to Instagram successfully: message {ai_message.id}")
                if buttons:
                    logger.info(f"   📌 Sent with {len(buttons)} CTA button(s)")
                logger.info(f"   Instagram message_id: {result.get('message_id')}")
                
                # ✅ Store external message_id in metadata to prevent webhook duplicates
                if result.get('message_id'):
                    ai_message.metadata = ai_message.metadata or {}
                    ai_message.metadata['external_message_id'] = str(result.get('message_id'))
                    ai_message.metadata['sent_from_app'] = True
                    ai_message.save(update_fields=['metadata'])
                    logger.info(f"   Stored Instagram message_id in AI message metadata: {result.get('message_id')}")
                    logger.info(f"   Updated metadata: {ai_message.metadata}")
                
                # ✅ Mark message as sent in cache to prevent duplicate from webhook
                import hashlib
                message_hash = hashlib.md5(
                    f"{conversation.id}:{ai_message.content}".encode()
                ).hexdigest()
                cache_key = f"instagram_sent_msg_{message_hash}"
                cache.set(cache_key, True, timeout=60)
                logger.info(f"   📝 Cached sent message to prevent webhook duplicate: {cache_key}")
                
                # Calculate elapsed time since typing_on
                elapsed_time = message_sent_time - typing_start_time
                
                # Instagram recommends minimum 5 seconds total typing indicator duration
                # If less than 5 seconds have passed, wait for the remaining time
                MINIMUM_TYPING_DURATION = 5.0
                
                if elapsed_time < MINIMUM_TYPING_DURATION:
                    remaining_time = MINIMUM_TYPING_DURATION - elapsed_time
                    logger.debug(f"⏱️ Elapsed: {elapsed_time:.1f}s, waiting {remaining_time:.1f}s more (total: {MINIMUM_TYPING_DURATION}s)")
                    time.sleep(remaining_time)
                else:
                    logger.debug(f"⏱️ Elapsed: {elapsed_time:.1f}s, minimum duration already met")
                
                # Turn off typing indicator
                try:
                    typing_off_result = instagram_service.send_typing_indicator_to_customer(customer, 'typing_off')
                    if typing_off_result.get('success'):
                        total_typing_time = time.time() - typing_start_time
                        logger.info(f"✍️ Typing indicator OFF for Instagram conversation {conversation.id} (total: {total_typing_time:.1f}s)")
                    else:
                        logger.debug(f"Could not send typing_off: {typing_off_result.get('error')}")
                    
                    # Clean up cache
                    cache.delete(typing_start_key)
                except Exception as typing_err:
                    logger.debug(f"Error sending typing_off: {typing_err}")
            else:
                logger.error(f"❌ Failed to send AI response to Instagram: {result.get('error')}")
                # Turn off typing indicator on error
                try:
                    instagram_service.send_typing_indicator_to_customer(customer, 'typing_off')
                    cache.delete(typing_start_key)
                except:
                    pass
                
        except Exception as e:
            logger.error(f"Error sending AI response to Instagram: {str(e)}")
            # Try to turn off typing indicator on exception
            try:
                from message.services.instagram_service import InstagramService
                from django.core.cache import cache
                instagram_service = InstagramService.get_service_for_conversation(conversation)
                if instagram_service:
                    instagram_service.send_typing_indicator_to_customer(conversation.customer, 'typing_off')
                    typing_start_key = f"typing_start_{conversation.id}"
                    cache.delete(typing_start_key)
            except:
                pass

    def process_customer_message(self, customer_message: str, conversation=None) -> Dict[str, Any]:
        """
        Process a customer message and generate AI response
        This method provides compatibility with the existing view interface
        """
        return self.generate_response(customer_message, conversation)
    
    def _get_workflow_ai_context(self, conversation) -> Dict[str, Any]:
        """Get workflow AI control settings and context for conversation"""
        if not conversation:
            return {}
        
        try:
            from django.core.cache import cache
            
            conversation_id = str(conversation.id)
            
            # Get AI control settings
            ai_control_key = f"ai_control_{conversation_id}"
            ai_control = cache.get(ai_control_key, {})
            
            # Get AI context data
            ai_context_key = f"ai_context_{conversation_id}"
            ai_context = cache.get(ai_context_key, {})
            
            return {
                'custom_prompt': ai_control.get('custom_prompt'),
                'context_data': ai_context
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow AI context: {e}")
            return {}
    
    def _format_workflow_context(self, context_data: Dict[str, Any]) -> str:
        """Format workflow context data into readable text for AI prompt"""
        if not context_data:
            return ""
        
        formatted_lines = []
        for key, value in context_data.items():
            if isinstance(value, (dict, list)):
                formatted_lines.append(f"- {key}: {str(value)}")
            else:
                formatted_lines.append(f"- {key}: {value}")
        
        return "\n".join(formatted_lines)
    
    def generate_product_dm_for_instagram_comment(
        self,
        comment_text: str,
        product,  # Product model instance
        extra_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate AI response for Instagram comment about a product
        
        Args:
            comment_text: The comment text from user
            product: Product model instance (from web_knowledge.models)
            extra_context: Extra info like username, post_url
            
        Returns:
            Dict with 'success', 'response', 'metadata'
        """
        try:
            extra_context = extra_context or {}
            username = extra_context.get('username', '')
            
            # Build product context
            price_text = "ندارد"
            if product.price:
                from web_knowledge.models import Product
                currency_display = dict(Product.CURRENCY_CHOICES).get(product.currency, product.currency)
                price_text = f"{product.price:,} {currency_display}"
                if product.billing_period and product.billing_period != 'one_time':
                    period_display = dict(Product.BILLING_PERIOD_CHOICES).get(product.billing_period, '')
                    price_text += f" ({period_display})"
            
            product_url = product.product_url or product.buy_url or ''
            
            # Build prompt
            prompt = f"""شما دستیار فروش هستید. یک کاربر زیر پست اینستاگرام این کامنت را گذاشته:
"{comment_text}"

اطلاعات محصول:
- نام: {product.title}
- توضیحات: {product.description or 'ندارد'}
- قیمت: {price_text}
- لینک: {product_url or 'ندارد'}

دستورالعمل:
1. اگر کاربر درباره قیمت پرسیده، قیمت را صادقانه بگو (اگر نداریم بگو "برای قیمت با ما تماس بگیرید")
2. توضیح خیلی کوتاه درباره محصول (حداکثر 2 خط)
3. اگر لینک محصول داریم، حتماً با فرمت CTA بفرست: [[CTA:مشاهده محصول|{product_url}]]
4. لحن دوستانه و فروشنده باش
5. از اسم کاربر ({username}) در ابتدا استفاده کن

⚠️ مهم: پاسخ تو باید فقط متن دایرکت باشد، حداکثر 350 کاراکتر."""

            # Call AI
            if not self.model:
                # Fallback if AI not configured
                fallback = f"سلام {username}! برای اطلاعات بیشتر درباره {product.title}"
                if product_url:
                    fallback += f" [[CTA:مشاهده محصول|{product_url}]]"
                else:
                    fallback += "، لطفاً با ما در تماس باشید."
                
                return {
                    'success': True,
                    'response': fallback,
                    'metadata': {
                        'product_id': str(product.id),
                        'product_title': product.title,
                        'comment_text': comment_text,
                        'has_price': product.price is not None,
                        'fallback_used': True
                    }
                }
            
            response = self.model.generate_content(prompt)
            ai_text = response.text.strip()
            
            return {
                'success': True,
                'response': ai_text,
                'metadata': {
                    'product_id': str(product.id),
                    'product_title': product.title,
                    'comment_text': comment_text,
                    'has_price': product.price is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating product DM: {e}")
            # Fallback response
            fallback = f"سلام! برای اطلاعات بیشتر درباره {product.title}"
            if product_url:
                fallback += f" [[CTA:مشاهده محصول|{product_url}]]"
            else:
                fallback += "، لطفاً با ما در تماس باشید."
            
            return {
                'success': False,
                'error': str(e),
                'response': fallback,
                'metadata': {
                    'product_id': str(product.id),
                    'product_title': product.title,
                    'fallback_used': True
                }
            }