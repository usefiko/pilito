"""
Q&A Generator Service
Uses AI (Gemini) to generate question-answer pairs from website content
Enhanced version with smart validation and quality control
"""
import logging
import json
import re
from typing import List, Dict, Optional, Tuple
from django.conf import settings

# ✅ Setup proxy BEFORE importing Gemini (required for Iran servers)
from core.utils import setup_ai_proxy
setup_ai_proxy()

import google.generativeai as genai

logger = logging.getLogger(__name__)


class QAGenerator:
    """
    AI-powered Q&A generation service using Google Gemini
    Enhanced with smart validation and deduplication
    """
    
    def __init__(self, user=None):
        self.user = user  # ✅ NEW: Track user for token consumption
        self.model = None
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini AI model"""
        try:
            # Get API key from GeneralSettings (where it's actually stored)
            from settings.models import GeneralSettings
            from AI_model.models import AIGlobalConfig
            
            settings_obj = GeneralSettings.get_settings()
            gemini_api_key = settings_obj.gemini_api_key
            
            if not gemini_api_key or len(gemini_api_key) < 20:
                logger.error("Gemini API key not found in GeneralSettings")
                return
            
            # Get AI config for model settings
            ai_config = AIGlobalConfig.get_config()
            # ✅ ALWAYS use Pro for Q&A generation (high quality needed)
            model_name = "gemini-2.5-pro"
            
            # Configure Gemini
            genai.configure(api_key=gemini_api_key)
            
            # Initialize model with optimized settings for Q&A generation
            # Using Pro for superior quality in Q&A extraction
            self.model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )
            
            logger.info(f"✅ Gemini AI model ({model_name}) initialized for Q&A generation (Pro for quality)")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI model: {str(e)}")
            self.model = None
    
    def generate_qa_pairs(self, content: str, page_title: str = "", 
                         max_pairs: int = 5) -> List[Dict]:
        """
        Generate Q&A pairs from content
        
        Args:
            content: Text content to generate Q&A from
            page_title: Title of the page (for context)
            max_pairs: Maximum number of Q&A pairs to generate
            
        Returns:
            List of Q&A dictionaries with question, answer, context, and confidence
        """
        if not self.model:
            logger.error("Gemini model not initialized")
            return []
        
        if not content or len(content.strip()) < 100:
            logger.warning("Content too short for Q&A generation")
            return []
        
        # ✅ NEW: Check tokens BEFORE generation (prevent free AI usage)
        if self.user:
            # Estimate tokens needed (rough: 4 chars = 1 token + overhead)
            estimated_tokens = (len(content) // 4) + (max_pairs * 200)  # ~200 tokens per Q&A
            
            try:
                subscription = self.user.subscription
                
                if not subscription.is_subscription_active():
                    logger.warning(
                        f"User {self.user.username} subscription is not active. "
                        f"Skipping Q&A generation to prevent free usage."
                    )
                    return []
                
                if subscription.tokens_remaining < estimated_tokens:
                    logger.warning(
                        f"User {self.user.username} has insufficient tokens for Q&A generation. "
                        f"Estimated need: {estimated_tokens}, Available: {subscription.tokens_remaining}. "
                        f"Skipping to prevent partial free usage."
                    )
                    return []
                
                logger.info(
                    f"Token pre-check passed for user {self.user.username}. "
                    f"Estimated: {estimated_tokens}, Available: {subscription.tokens_remaining}"
                )
                    
            except Exception as e:
                logger.error(f"Token pre-check failed for Q&A generation: {e}")
                return []
        
        try:
            # Split content into chunks if too long
            content_chunks = self._split_content(content)
            all_qa_pairs = []
            
            for chunk in content_chunks:
                chunk_pairs = self._generate_qa_from_chunk(chunk, page_title, max_pairs)
                all_qa_pairs.extend(chunk_pairs)
                
                # Limit total pairs
                if len(all_qa_pairs) >= max_pairs:
                    all_qa_pairs = all_qa_pairs[:max_pairs]
                    break
            
            # Post-process and validate Q&A pairs
            validated_pairs = self._validate_qa_pairs(all_qa_pairs)
            
            logger.info(f"Generated {len(validated_pairs)} high-quality Q&A pairs from content")
            return validated_pairs
            
        except Exception as e:
            logger.error(f"Error generating Q&A pairs: {str(e)}")
            return []
    
    def _split_content(self, content: str, max_chunk_size: int = 3000) -> List[str]:
        """
        Split content into manageable chunks for AI processing
        """
        if len(content) <= max_chunk_size:
            return [content]
        
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk + paragraph) <= max_chunk_size:
                current_chunk += paragraph + '\n\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + '\n\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _generate_qa_from_chunk(self, content: str, page_title: str, 
                               max_pairs: int) -> List[Dict]:
        """
        Generate Q&A pairs from a single content chunk
        """
        try:
            # Create prompt for Q&A generation
            prompt = self._create_qa_prompt(content, page_title, max_pairs)
            
            # Configure safety settings to reduce false blocks
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
            ]
            
            # Track timing
            import time
            start_time = time.time()
            
            # Generate response with safety settings
            response = self.model.generate_content(
                prompt,
                safety_settings=safety_settings
            )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # ✅ Extract token usage
            prompt_tokens = 0
            completion_tokens = 0
            if hasattr(response, 'usage_metadata'):
                prompt_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
                completion_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
            
            # ✅ Track AI usage in AIUsageLog and AIUsageTracking
            if self.user:
                try:
                    from AI_model.services.usage_tracker import track_ai_usage_safe
                    track_ai_usage_safe(
                        user=self.user,
                        section='knowledge_qa',
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        response_time_ms=response_time_ms,
                        success=True,
                        model_name='gemini-2.5-pro',
                        metadata={'page_title': page_title, 'content_length': len(content)}
                    )
                    logger.info(f"✅ AI usage tracked for Q&A generation (user: {self.user.username}, tokens: {prompt_tokens + completion_tokens})")
                except Exception as tracking_error:
                    logger.error(f"Failed to track AI usage for Q&A generation: {tracking_error}")
                
                # ✅ Consume tokens for billing
                try:
                    actual_tokens = prompt_tokens + completion_tokens
                    if actual_tokens > 0:
                        from billing.services import consume_tokens_for_user
                        consume_tokens_for_user(
                            self.user,
                            actual_tokens,
                            description='Web Knowledge Q&A generation'
                        )
                        logger.info(f"💰 Consumed {actual_tokens} tokens for Q&A generation (user: {self.user.username})")
                except Exception as token_error:
                    logger.error(f"Failed to consume tokens for Q&A generation: {token_error}")
            
            if not response or not response.text:
                logger.warning("Empty response from Gemini for Q&A generation")
                return []
            
            # Parse Q&A pairs from response
            qa_pairs = self._parse_qa_response(response.text, content)
            
            return qa_pairs
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating Q&A from chunk: {error_msg}")
            
            # Track failed AI usage
            if self.user:
                try:
                    from AI_model.services.usage_tracker import track_ai_usage_safe
                    import time
                    track_ai_usage_safe(
                        user=self.user,
                        section='knowledge_qa',
                        prompt_tokens=0,
                        completion_tokens=0,
                        response_time_ms=0,
                        success=False,
                        model_name='gemini-2.5-pro',
                        error_message=error_msg,
                        metadata={'page_title': page_title, 'error': error_msg}
                    )
                except Exception as tracking_error:
                    logger.error(f"Failed to track failed AI usage: {tracking_error}")
            
            return []
    
    def _create_qa_prompt(self, content: str, page_title: str, max_pairs: int) -> str:
        """
        Create an enhanced prompt for high-quality Q&A generation
        """
        # Clean page title - remove URL if present
        clean_title = page_title
        if page_title and ('http://' in page_title or 'https://' in page_title or '.com' in page_title or '.net' in page_title):
            # If title is a URL, don't use it
            clean_title = "the business"
            logger.debug(f"Cleaned title from URL: {page_title} -> {clean_title}")
        
        # Limit content to first 2000 chars for prompt
        content_preview = content[:2000] if len(content) > 2000 else content
        
        prompt = f"""
You are an expert customer service representative creating natural, helpful Q&A pairs from website content.

Website/Page Topic: {clean_title}

Content to analyze:
{content_preview}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL RULES - MUST FOLLOW:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ NEVER DO:
1. DO NOT include URLs, website addresses, domain names, or "https://" in questions
2. DO NOT create generic template questions without specific answers
3. DO NOT create questions if content doesn't have clear answers
4. DO NOT use phrases like "for https://..." or "this website" or "this site"
5. DO NOT copy-paste from content without making it conversational

✅ ALWAYS DO:
1. Create natural questions as if a real customer is asking
2. Provide COMPLETE, SPECIFIC answers with actual details from the content
3. Use real information: prices, times, contact info, features, etc.
4. Make questions conversational and friendly
5. Ensure answers are actionable and helpful

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GOOD vs BAD EXAMPLES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ BAD:
Q: "What are the pricing options for https://example.com?"
A: "The pricing information is available on this website."

✅ GOOD:
Q: "What are your pricing plans?"
A: "We offer three plans: Starter at $14/month with 1000 AI tokens, Pro at $29/month with 5000 tokens, and Enterprise with custom pricing. All plans include a 14-day free trial."

❌ BAD:
Q: "How can I contact this website?"
A: "Contact information is available on the contact page."

✅ GOOD:
Q: "What's the best way to reach your support team?"
A: "You can email us at support@example.com or call +1-555-0123. Our team is available Monday-Friday, 9 AM to 6 PM EST. For urgent issues, use the live chat on our website."

❌ BAD:
Q: "What are the terms of use for https://example.com?"
A: "The terms of use and legal information for https://example.com are outlined on this page."

✅ GOOD:
Q: "What are the main terms of use?"
A: "Users must be 18 years or older, agree not to use the service for illegal activities, and maintain account security. We reserve the right to suspend accounts that violate our policies. Full terms are available in our Terms of Service."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TASK:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate {max_pairs} high-quality Q&A pairs covering these topics IF INFORMATION IS AVAILABLE:

1. **Specific Services/Products**: What exactly does this business offer?
2. **Pricing & Plans**: How much does it cost? What plans are available?
3. **Contact Methods**: How can customers reach you? (email, phone, hours)
4. **How-To Processes**: How do customers use your service/product?
5. **Policies**: Important terms, privacy, refund policies
6. **Features & Benefits**: What makes this unique or valuable?

IMPORTANT: Only create Q&A pairs if you have SPECIFIC information from the content. Skip generic questions without concrete answers.

Format as JSON:
{{
  "qa_pairs": [
    {{
      "question": "Natural, conversational question without URLs",
      "answer": "Complete answer with specific details, numbers, contact info from content",
      "confidence": 0.95,
      "question_type": "factual|procedural|explanatory|comparison|practical",
      "category": "general|contact|services|pricing|support|policies",
      "keywords": ["specific", "relevant", "keywords"]
    }}
  ]
}}

Generate ONLY high-quality, specific Q&A pairs with real information. Quality over quantity!
"""
        return prompt
    
    def _parse_qa_response(self, response_text: str, original_content: str) -> List[Dict]:
        """
        Parse Q&A pairs from Gemini's response
        """
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                logger.error("No JSON found in Q&A generation response")
                return []
            
            json_text = json_match.group()
            data = json.loads(json_text)
            
            qa_pairs = []
            for item in data.get('qa_pairs', []):
                if not isinstance(item, dict):
                    continue
                
                question = item.get('question', '').strip()
                answer = item.get('answer', '').strip()
                confidence = float(item.get('confidence', 0.8))
                question_type = item.get('question_type', 'factual')
                category = item.get('category', 'general')
                keywords = item.get('keywords', [])
                
                if question and answer:
                    qa_pairs.append({
                        'question': question,
                        'answer': answer,
                        'confidence': min(max(confidence, 0.0), 1.0),
                        'question_type': question_type,
                        'category': category,
                        'keywords': keywords if isinstance(keywords, list) else [],
                        'context': self._extract_relevant_context(question, answer, original_content),
                        'generation_status': 'completed',
                        'created_by_ai': True
                    })
            
            return qa_pairs
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Q&A response: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error parsing Q&A response: {str(e)}")
            return []
    
    def _extract_relevant_context(self, question: str, answer: str, 
                                 content: str, max_context_length: int = 500) -> str:
        """
        Extract relevant context from the original content for the Q&A pair
        """
        answer_words = set(answer.lower().split())
        sentences = re.split(r'[.!?]+', content)
        
        best_sentence = ""
        best_score = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
            
            sentence_words = set(sentence.lower().split())
            overlap = len(answer_words.intersection(sentence_words))
            score = overlap / len(answer_words) if answer_words else 0
            
            if score > best_score:
                best_score = score
                best_sentence = sentence
        
        if len(best_sentence) > max_context_length:
            best_sentence = best_sentence[:max_context_length] + "..."
        
        return best_sentence or content[:max_context_length] + "..."
    
    def _validate_qa_pairs(self, qa_pairs: List[Dict]) -> List[Dict]:
        """
        Validate and filter Q&A pairs with strict quality checks
        """
        validated_pairs = []
        seen_questions_normalized = set()
        
        for pair in qa_pairs:
            question = pair.get('question', '').strip()
            answer = pair.get('answer', '').strip()
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # Quality Checks
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            
            # ❌ Check 1: Minimum length
            if len(question) < 10 or len(answer) < 30:
                logger.debug(f"⏭️  Skipped (too short): Q={len(question)} chars, A={len(answer)} chars")
                continue
            
            # ❌ Check 2: No URLs in question
            if self._contains_url(question):
                logger.debug(f"⏭️  Skipped (contains URL): {question[:80]}")
                continue
            
            # ❌ Check 3: No generic/vague questions
            if self._is_generic_question(question):
                logger.debug(f"⏭️  Skipped (too generic): {question[:80]}")
                continue
            
            # ❌ Check 4: Answer quality check
            if self._is_low_quality_answer(answer):
                logger.debug(f"⏭️  Skipped (low quality answer): {answer[:80]}")
                continue
            
            # ❌ Check 5: Duplicate check (normalized)
            normalized_q = self._normalize_question(question)
            if normalized_q in seen_questions_normalized:
                logger.debug(f"⏭️  Skipped (duplicate): {question[:80]}")
                continue
            
            # ❌ Check 6: Similar to existing questions
            is_similar = False
            for existing_pair in validated_pairs:
                if self._are_questions_similar(question, existing_pair['question'], threshold=0.6):
                    logger.debug(f"⏭️  Skipped (similar to existing): {question[:80]}")
                    is_similar = True
                    break
            
            if is_similar:
                continue
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # Post-processing
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            
            # Clean question
            if not question.endswith('?'):
                question += '?'
            question = question[0].upper() + question[1:] if question else question
            pair['question'] = question
            
            # Clean answer
            answer = self._clean_answer(answer)
            pair['answer'] = answer
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(pair)
            if quality_score < 0.4:
                logger.debug(f"⏭️  Skipped (low quality score {quality_score:.2f}): {question[:80]}")
                continue
            
            pair['quality_score'] = quality_score
            
            # ✅ Passed all checks!
            validated_pairs.append(pair)
            seen_questions_normalized.add(normalized_q)
            logger.debug(f"✅ Validated (score: {quality_score:.2f}): {question[:80]}")
        
        logger.info(f"📊 Validation: {len(validated_pairs)} passed out of {len(qa_pairs)} generated")
        return validated_pairs
    
    def _contains_url(self, text: str) -> bool:
        """Check if text contains URL or domain"""
        url_patterns = [
            r'https?://',
            r'www\.',
            r'\.(com|net|org|io|co|edu|gov)',
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in url_patterns)
    
    def _is_generic_question(self, question: str) -> bool:
        """Check if question is too generic or vague"""
        q_lower = question.lower()
        generic_patterns = [
            'what is this',
            'what does this',
            'tell me about this',
            'how can i use this',
            'what is the purpose',
            'what information',
            'this website',
            'this site',
            'this page',
            'this business provide',
        ]
        return any(pattern in q_lower for pattern in generic_patterns)
    
    def _is_low_quality_answer(self, answer: str) -> bool:
        """Check if answer is low quality or vague"""
        a_lower = answer.lower()
        
        # Check for vague answers
        vague_patterns = [
            'information is available',
            'you can find',
            'please visit',
            'check the website',
            'is outlined on',
            'are detailed on',
        ]
        
        if any(pattern in a_lower for pattern in vague_patterns):
            return True
        
        # Answer too short and generic
        if len(answer) < 50 and answer.count('.') <= 1:
            return True
        
        return False
    
    def _normalize_question(self, question: str) -> str:
        """Normalize question for better duplicate detection"""
        q = question.lower().rstrip('?').strip()
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'can', 'do', 'does', 'how', 'what', 'when', 'where', 'why', 'your', 'my', 'our', 'their'}
        words = [w for w in q.split() if w not in stop_words]
        
        # Sort words for better matching
        return ' '.join(sorted(words))
    
    def _clean_answer(self, answer: str) -> str:
        """Clean and improve answer quality"""
        # Remove URLs from answer
        answer = re.sub(r'https?://[^\s]+', '[website]', answer)
        
        # Remove domain names
        answer = re.sub(r'\b\w+\.(com|net|org|io)\b', '[website]', answer)
        
        # Ensure proper punctuation
        if answer and not answer.endswith(('.', '!', '?')):
            answer += '.'
        
        # Capitalize first letter
        if answer:
            answer = answer[0].upper() + answer[1:]
        
        return answer
    
    def _are_questions_similar(self, q1: str, q2: str, threshold: float = 0.6) -> bool:
        """Check if two questions are too similar"""
        # Normalize both questions
        words1 = set(self._normalize_question(q1).split())
        words2 = set(self._normalize_question(q2).split())
        
        if not words1 or not words2:
            return False
        
        # Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        similarity = intersection / union if union > 0 else 0
        
        if similarity >= threshold:
            return True
        
        # Check if one is subset of another (e.g., "pricing" vs "pricing options")
        if words1.issubset(words2) or words2.issubset(words1):
            return True
        
        return False
    
    def _calculate_quality_score(self, qa_pair: Dict) -> float:
        """Calculate quality score for Q&A pair (0.0 to 1.0)"""
        score = 0.0
        question = qa_pair.get('question', '')
        answer = qa_pair.get('answer', '')
        
        # ✅ Check question length (10-150 optimal)
        if 10 <= len(question) <= 150:
            score += 0.15
        
        # ✅ Check answer length (30-800 optimal)
        if 30 <= len(answer) <= 800:
            score += 0.15
        elif len(answer) > 800:
            score += 0.1
        
        # ✅ Question starts with question word
        question_starters = ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'can', 'do', 'does', 'is', 'are']
        if any(question.lower().startswith(word) for word in question_starters):
            score += 0.2
        
        # ✅ Answer contains specific information (numbers, times, emails, etc.)
        has_specific_info = bool(re.search(r'(\d+|email|phone|address|hours?|price|cost|\$|€|£|@|monday|tuesday|wednesday|thursday|friday)', answer.lower()))
        if has_specific_info:
            score += 0.15
        
        # ✅ Answer word count (more detailed = better)
        answer_words = len(answer.split())
        if answer_words >= 10:
            score += 0.1
        if answer_words >= 20:
            score += 0.1
        
        # ✅ Use existing confidence from AI
        confidence = qa_pair.get('confidence', 0.5)
        score += confidence * 0.15
        
        return min(score, 1.0)
    
    def generate_single_qa(self, content: str, specific_topic: str = None) -> Optional[Dict]:
        """Generate a single Q&A pair, optionally focused on a specific topic"""
        if not self.model or not content:
            return None
        
        try:
            topic_instruction = f"Focus on the topic: {specific_topic}. " if specific_topic else ""
            
            prompt = f"""
{topic_instruction}Based on the following content, generate ONE high-quality question-answer pair.

RULES:
- NO URLs in the question
- Question must be natural and conversational
- Answer must be complete with specific details
- NO generic or vague answers

Content:
{content[:1000]}

Format as JSON: {{"question": "...", "answer": "...", "confidence": 0.95}}

Generate only the JSON, no other text.
"""
            
            # Configure safety settings to reduce false blocks
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
            ]
            
            response = self.model.generate_content(
                prompt,
                safety_settings=safety_settings
            )
            
            # ✅ NEW: Consume tokens for single Q&A generation
            if self.user and response:
                try:
                    if hasattr(response, 'usage_metadata') and hasattr(response.usage_metadata, 'total_token_count'):
                        actual_tokens = response.usage_metadata.total_token_count
                        from billing.services import consume_tokens_for_user
                        consume_tokens_for_user(
                            self.user,
                            actual_tokens,
                            description='Web Knowledge single Q&A generation'
                        )
                        logger.info(f"Consumed {actual_tokens} tokens for single Q&A (user: {self.user.username})")
                except Exception as token_error:
                    logger.error(f"Failed to consume tokens for single Q&A: {token_error}")
            
            if response and response.text:
                qa_pairs = self._parse_qa_response(response.text, content)
                return qa_pairs[0] if qa_pairs else None
            
        except Exception as e:
            logger.error(f"Error generating single Q&A: {str(e)}")
        
        return None
    
    def is_available(self) -> bool:
        """Check if the Q&A generator is available and properly configured"""
        return self.model is not None


class QAOptimizer:
    """
    Service for optimizing and improving Q&A pairs
    """
    
    @staticmethod
    def improve_question(question: str, context: str) -> str:
        """Improve a question to make it more natural and clear"""
        question = question.strip()
        
        if not question.endswith('?'):
            question += '?'
        
        if question:
            question = question[0].upper() + question[1:]
        
        return question
    
    @staticmethod
    def improve_answer(answer: str, context: str) -> str:
        """Improve an answer to make it more comprehensive and clear"""
        answer = answer.strip()
        
        if answer and not answer.endswith(('.', '!', '?')):
            answer += '.'
        
        if answer:
            answer = answer[0].upper() + answer[1:]
        
        return answer
    
    @staticmethod
    def calculate_quality_score(qa_pair: Dict) -> float:
        """Calculate a quality score for a Q&A pair"""
        question = qa_pair.get('question', '')
        answer = qa_pair.get('answer', '')
        
        score = 0.0
        
        # Length checks
        if 10 <= len(question) <= 200:
            score += 0.2
        if 20 <= len(answer) <= 1000:
            score += 0.2
        
        # Content quality
        if question.endswith('?'):
            score += 0.1
        if any(word in question.lower() for word in ['what', 'how', 'why', 'when', 'where', 'who']):
            score += 0.1
        
        # Answer quality
        if len(answer.split()) >= 5:
            score += 0.1
        if answer.endswith(('.', '!', '?')):
            score += 0.1
        
        # Use existing confidence if available
        confidence = qa_pair.get('confidence', 0.5)
        score += confidence * 0.2
        
        return min(score, 1.0)
