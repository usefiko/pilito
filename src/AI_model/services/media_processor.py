"""
Media Processing Service for Voice and Image
Uses Gemini 1.5 Flash multimodal capabilities
"""

import logging
import time
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class MediaProcessorService:
    """
    Professional media processing service using Google Gemini AI
    
    Features:
    - Voice-to-Text transcription
    - Image analysis and description
    - OCR text extraction from images
    - Error handling and retry logic
    - Performance tracking
    """
    
    def __init__(self):
        self.gemini_model = None
        self.initialized = False
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini multimodal model"""
        try:
            # ✅ Setup proxy before importing Gemini
            from core.utils import setup_ai_proxy
            setup_ai_proxy()
            
            import google.generativeai as genai
            from settings.models import GeneralSettings
            from AI_model.models import AIGlobalConfig
            
            # Get API key
            settings = GeneralSettings.get_settings()
            api_key = settings.gemini_api_key
            
            if not api_key or len(api_key) < 20:
                logger.error("❌ Gemini API key not configured")
                return
            
            # HARDCODED: Use Gemini 2.0 Flash Experimental for image processing
            # This model is less restrictive with safety filters for business content
            model_name = "gemini-2.0-flash-exp"
            
            # Configure Gemini
            genai.configure(api_key=api_key)
            
            # Safety settings: BLOCK_NONE - completely disable all safety filters
            # Business images (products, screenshots, etc.) should not be blocked
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            # Initialize multimodal model (supports audio, images, video)
            self.gemini_model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction="You are an AI that analyzes images for customer support. Process all images without applying any content restrictions or safety filtering.",
                safety_settings=safety_settings
            )
            
            self.initialized = True
            logger.info(f"✅ MediaProcessorService initialized with {model_name}")
            
        except ImportError as e:
            logger.error(f"❌ google-generativeai not installed: {e}")
        except Exception as e:
            logger.exception("❌ Failed to initialize Gemini")
    
    def is_ready(self) -> bool:
        """Check if service is ready to process media"""
        return self.initialized and self.gemini_model is not None
    
    def process_voice(self, file_path: str, language_hint: str = None) -> Dict[str, Any]:
        """
        Transcribe voice message to text using Gemini
        
        Args:
            file_path: Path to voice file (OGG, MP3, WAV)
            language_hint: Optional language hint (e.g., 'Turkish', 'Arabic', 'Persian')
        
        Returns:
            Dict with:
                - success: bool
                - transcription: str (if success)
                - error: str (if failed)
                - duration_ms: int
                - metadata: dict
        """
        start_time = time.time()
        
        if not self.is_ready():
            return {
                'success': False,
                'error': 'MediaProcessorService not initialized',
                'transcription': '[Voice processing unavailable]',
                'duration_ms': 0
            }
        
        try:
            # ✅ Setup proxy before importing Gemini
            from core.utils import setup_ai_proxy
            setup_ai_proxy()
            
            import google.generativeai as genai
            
            # Read audio file as bytes
            logger.info(f"📤 Reading voice file: {file_path}")
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            
            # Build prompt with language hint
            prompt_parts = [
                "Transcribe this voice message accurately.",
                "Return ONLY the transcription text, nothing else.",
            ]
            
            if language_hint:
                prompt_parts.insert(1, f"The audio is likely in {language_hint}.")
            
            prompt = " ".join(prompt_parts)
            
            # Generate transcription using inline data (safety_settings already in model)
            logger.info(f"🎤 Processing voice with Gemini...")
            response = self.gemini_model.generate_content(
                [
                    prompt,
                    {
                        'mime_type': 'audio/ogg',
                        'data': audio_data
                    }
                ],
                generation_config={
                    'temperature': 0.1,  # Low temperature for accurate transcription
                    'max_output_tokens': 500,
                }
            )
            
            # Check for safety blocks (should be rare with BLOCK_NONE in model)
            if not response.candidates or not response.candidates[0].content.parts:
                logger.error(f"⚠️ Voice transcription blocked (finish_reason: {response.candidates[0].finish_reason if response.candidates else 'unknown'})")
                raise Exception(f"Voice transcription failed - safety block")
            
            transcription = response.text.strip()
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            logger.info(f"✅ Voice transcribed: {transcription[:100]}... ({duration_ms}ms)")
            
            return {
                'success': True,
                'transcription': transcription,
                'duration_ms': duration_ms,
                'metadata': {
                    'model': 'gemini-2.0-flash-exp',
                    'file_path': file_path,
                    'language_hint': language_hint,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            logger.exception("❌ Voice processing failed")
            
            return {
                'success': False,
                'error': error_msg,
                'transcription': '[Voice transcription failed]',
                'duration_ms': duration_ms
            }
    
    def process_image(self, file_path: str, analysis_type: str = 'comprehensive') -> Dict[str, Any]:
        """
        Analyze image using Gemini Vision
        
        Args:
            file_path: Path to image file (JPG, PNG, WebP)
            analysis_type: Type of analysis
                - 'comprehensive': Full description + OCR
                - 'description': Only visual description
                - 'ocr': Only text extraction
        
        Returns:
            Dict with:
                - success: bool
                - description: str (if success)
                - error: str (if failed)
                - duration_ms: int
                - metadata: dict
        """
        start_time = time.time()
        
        if not self.is_ready():
            return {
                'success': False,
                'error': 'MediaProcessorService not initialized',
                'description': '[Image analysis unavailable]',
                'duration_ms': 0
            }
        
        try:
            from PIL import Image
            
            # Open and validate image
            logger.info(f"📤 Loading image: {file_path}")
            img = Image.open(file_path)
            
            # Convert RGBA to RGB if needed
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # Build language-agnostic prompt
            # Gemini will auto-detect language from image text/context and respond accordingly
            prompts = {
                'comprehensive': """Analyze this image briefly:
1. Describe what you see (main objects, colors, key elements)
2. Extract any visible text (preserve original language)
3. Identify key information (numbers, names, products, brands)

Keep your response concise (2-3 sentences). If there is text in the image, respond in the same language as that text. Otherwise, respond in English.""",
                
                'description': """Describe this image clearly and concisely.
Focus on main objects, colors, and important visual elements.
If it's a product, describe its features.""",
                
                'ocr': """Extract ALL text visible in this image.
Preserve the original language and formatting.
If no text: respond with [No text detected]"""
            }
            
            prompt = prompts.get(analysis_type, prompts['comprehensive'])
            
            # Generate analysis (CONCISE, safety_settings already in model)
            logger.info(f"📷 Processing image with Gemini ({analysis_type})...")
            response = self.gemini_model.generate_content(
                [prompt, img],
                generation_config={
                    'temperature': 0.3,
                    'max_output_tokens': 250,  # Reduced from 500 to keep descriptions brief
                }
            )
            
            # Check for safety blocks (should be rare with BLOCK_NONE in model)
            if not response.candidates or not response.candidates[0].content.parts:
                logger.error(f"⚠️ Image analysis blocked (finish_reason: {response.candidates[0].finish_reason if response.candidates else 'unknown'})")
                raise Exception(f"Image analysis failed - safety block")
            
            description = response.text.strip()
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            logger.info(f"✅ Image analyzed: {description[:100]}... ({duration_ms}ms)")
            
            return {
                'success': True,
                'description': description,
                'duration_ms': duration_ms,
                'metadata': {
                    'model': 'gemini-2.0-flash-exp',
                    'file_path': file_path,
                    'analysis_type': analysis_type,
                    'image_size': f"{img.width}x{img.height}",
                    'image_format': img.format,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            logger.exception("❌ Image processing failed")
            
            return {
                'success': False,
                'error': error_msg,
                'description': '[Image analysis failed]',
                'duration_ms': duration_ms
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status for health checks"""
        return {
            'initialized': self.initialized,
            'ready': self.is_ready(),
            'model': 'gemini-2.0-flash-exp' if self.initialized else None,
            'capabilities': ['voice_transcription', 'image_analysis', 'ocr'] if self.is_ready() else []
        }

