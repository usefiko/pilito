"""
Persian-Aware Chunking Utilities
Optimized for Persian/Farsi text processing in RAG systems
"""
import re
import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChunkMetadata:
    """Metadata for a chunk (used in RAG retrieval)"""
    page_title: str = ""
    page_url: str = ""
    keywords: List[str] = None
    h1_tags: List[str] = None
    h2_tags: List[str] = None
    chunk_index: int = 0
    total_chunks: int = 1
    language: str = "fa"  # fa or en


class PersianChunker:
    """
    Advanced chunking for Persian text
    
    Features:
    - Token-based (not word-based) for accurate control
    - Overlap strategy to prevent context loss
    - Metadata extraction for better RAG retrieval
    - Persian-specific sentence/paragraph detection
    """
    
    # Chunk size in tokens (industry standard: 512)
    DEFAULT_CHUNK_SIZE = 512  # tokens (~640 words Persian)
    DEFAULT_OVERLAP = 128     # tokens (25% overlap)
    
    # Persian sentence endings
    PERSIAN_SENTENCE_ENDINGS = ['۔', '؟', '!', '.', '?']
    
    @classmethod
    def chunk_text_with_metadata(
        cls,
        text: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP,
        page_title: str = "",
        page_url: str = "",
        h1_tags: List[str] = None,
        h2_tags: List[str] = None
    ) -> List[Tuple[str, ChunkMetadata]]:
        """
        Split text into chunks with metadata
        
        Args:
            text: Text to chunk
            chunk_size: Target size in tokens
            overlap: Overlap size in tokens
            page_title: Page title for metadata
            page_url: Page URL for metadata
            h1_tags: H1 tags from page
            h2_tags: H2 tags from page
            
        Returns:
            List of (chunk_text, metadata) tuples
        """
        if not text or not text.strip():
            return []
        
        # Detect language
        language = cls._detect_language(text)
        
        # Tokenize (Persian-aware)
        tokens = cls._tokenize_persian(text)
        
        if len(tokens) <= chunk_size:
            # Text is small, return as single chunk
            metadata = ChunkMetadata(
                page_title=page_title,
                page_url=page_url,
                keywords=cls._extract_keywords_persian(text),
                h1_tags=h1_tags or [],
                h2_tags=h2_tags or [],
                chunk_index=0,
                total_chunks=1,
                language=language
            )
            return [(text, metadata)]
        
        # Split into chunks with overlap
        chunks_data = []
        i = 0
        chunk_index = 0
        
        while i < len(tokens):
            # Get chunk tokens
            chunk_tokens = tokens[i:i + chunk_size]
            
            # Find good break point (sentence boundary)
            if i + chunk_size < len(tokens):
                # Try to end at sentence boundary
                chunk_tokens = cls._find_sentence_boundary(
                    tokens, i, i + chunk_size, language
                )
            
            # Convert tokens back to text
            chunk_text = cls._tokens_to_text(chunk_tokens, language)
            
            # Extract keywords from this chunk
            keywords = cls._extract_keywords_persian(chunk_text)
            
            # Create metadata
            metadata = ChunkMetadata(
                page_title=page_title,
                page_url=page_url,
                keywords=keywords,
                h1_tags=h1_tags or [],
                h2_tags=h2_tags or [],
                chunk_index=chunk_index,
                total_chunks=-1,  # Will update later
                language=language
            )
            
            chunks_data.append((chunk_text, metadata))
            
            # Move forward with overlap
            i += (chunk_size - overlap)
            chunk_index += 1
        
        # Update total_chunks count
        total = len(chunks_data)
        for _, meta in chunks_data:
            meta.total_chunks = total
        
        logger.debug(
            f"✅ Chunked {len(tokens)} tokens into {total} chunks "
            f"(size={chunk_size}, overlap={overlap}, lang={language})"
        )
        
        return chunks_data
    
    @classmethod
    def _tokenize_persian(cls, text: str) -> List[str]:
        """
        Tokenize Persian text
        
        Persian tokenization is different from English:
        - No spaces between some words (e.g., می‌خواهم)
        - ZWNJ (Zero-Width Non-Joiner) handling
        - Arabic/Persian numerals
        
        For simplicity, we use word-level tokenization
        (Real token counting would require tiktoken/transformers)
        
        NOTE: chunk_size parameter is in words, but actual tokens will be ~4.26x for Persian
        (e.g., chunk_size=100 words ≈ 426 tokens for Persian text)
        """
        # Normalize ZWNJ and spaces
        text = re.sub(r'\u200c+', '\u200c', text)  # Normalize ZWNJ
        text = re.sub(r'\s+', ' ', text)           # Normalize spaces
        
        # Split by whitespace (basic tokenization)
        tokens = text.split()
        
        return tokens
    
    @classmethod
    def _tokens_to_text(cls, tokens: List[str], language: str) -> str:
        """Convert tokens back to text"""
        return ' '.join(tokens)
    
    @classmethod
    def _find_sentence_boundary(
        cls,
        tokens: List[str],
        start: int,
        end: int,
        language: str
    ) -> List[str]:
        """
        Find a good sentence boundary for chunk end
        Tries to end chunk at sentence ending
        """
        # Look back up to 50 tokens for sentence ending
        for i in range(end - 1, max(start, end - 50), -1):
            token = tokens[i]
            
            # Check if ends with sentence marker
            if any(token.endswith(marker) for marker in cls.PERSIAN_SENTENCE_ENDINGS):
                return tokens[start:i + 1]
        
        # No good boundary found, use original end
        return tokens[start:end]
    
    @classmethod
    def _detect_language(cls, text: str) -> str:
        """
        Detect if text is Persian or English
        
        Returns:
            'fa' for Persian, 'en' for English
        """
        if not text:
            return 'en'
        
        # Count Persian characters (Unicode range: 0600-06FF)
        persian_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF')
        total_chars = len(text.replace(' ', ''))
        
        if total_chars == 0:
            return 'en'
        
        # If more than 30% Persian characters, it's Persian
        persian_ratio = persian_chars / total_chars
        return 'fa' if persian_ratio > 0.3 else 'en'
    
    @classmethod
    def _extract_keywords_persian(cls, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from Persian text
        
        Simple TF-based approach (no IDF, just frequency)
        """
        if not text:
            return []
        
        # Normalize
        text = text.lower()
        
        # Remove stopwords (basic Persian stopwords)
        persian_stopwords = {
            'و', 'در', 'به', 'از', 'که', 'این', 'با', 'را', 'برای', 'یک',
            'است', 'هست', 'می', 'شود', 'خود', 'تا', 'کند', 'بر', 'هم', 'آن',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been'
        }
        
        # Extract words (3+ characters)
        words = re.findall(r'[\u0600-\u06FFa-zA-Z]{3,}', text)
        
        # Filter stopwords and count
        word_freq = {}
        for word in words:
            if word not in persian_stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Return top keywords
        keywords = [word for word, freq in sorted_words[:max_keywords]]
        
        return keywords
    
    @classmethod
    def extract_tldr_persian(cls, text: str, max_words: int = 100) -> str:
        """
        Extract TL;DR for Persian text (extractive method)
        
        Strategy:
        1. First sentence (intro)
        2. Middle sentences (main content)
        3. Last sentence (conclusion)
        """
        if not text or not text.strip():
            return ''
        
        # Detect language
        language = cls._detect_language(text)
        
        # Split into sentences
        if language == 'fa':
            # Persian sentence splitting
            sentences = re.split(r'[.!؟۔]+', text)
        else:
            # English sentence splitting
            sentences = re.split(r'[.!?]+', text)
        
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 15]
        
        if not sentences:
            # No sentences, just truncate
            words = text.split()
            return ' '.join(words[:max_words]) + ('...' if len(words) > max_words else '')
        
        # Check if already short enough
        word_count = len(text.split())
        if word_count <= max_words:
            return text
        
        # Strategy: First + Middle + Last
        summary_sentences = []
        current_words = 0
        
        # 1. First sentence (always)
        if sentences:
            first = sentences[0]
            summary_sentences.append(first)
            current_words += len(first.split())
        
        # 2. Last sentence (if space)
        if len(sentences) > 1:
            last = sentences[-1]
            last_words = len(last.split())
            if current_words + last_words < max_words * 0.7:
                summary_sentences.append(last)
                current_words += last_words
        
        # 3. Middle sentences (fill remaining space)
        middle_start = 1
        middle_end = len(sentences) - 1 if len(sentences) > 2 else len(sentences)
        
        for i in range(middle_start, middle_end):
            sent = sentences[i]
            sent_words = len(sent.split())
            
            if current_words + sent_words <= max_words:
                # Insert before last sentence
                if len(summary_sentences) > 1:
                    summary_sentences.insert(-1, sent)
                else:
                    summary_sentences.append(sent)
                current_words += sent_words
            else:
                break
        
        # Join sentences
        if language == 'fa':
            summary = '۔ '.join(summary_sentences)
            if not summary.endswith('۔'):
                summary += '۔'
        else:
            summary = '. '.join(summary_sentences)
            if not summary.endswith('.'):
                summary += '.'
        
        # Final trim if still too long
        words = summary.split()
        if len(words) > max_words:
            summary = ' '.join(words[:max_words]) + '...'
        
        return summary

