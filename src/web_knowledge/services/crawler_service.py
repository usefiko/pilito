"""
Website Crawler Service
Handles crawling websites and extracting content for knowledge base creation
"""
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from typing import List, Dict, Set, Optional, Tuple
import time
import re
from django.utils import timezone
from django.conf import settings
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class WebsiteCrawler:
    """
    Advanced website crawler with respectful crawling practices
    """
    
    def __init__(self, base_url: str, max_pages: int = 30, max_depth: int = 3, 
                 include_external: bool = False, delay: float = 2.0):
        self.base_url = base_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.include_external = include_external
        self.delay = delay  # Respectful crawling delay
        
        # Parse base domain
        parsed_url = urlparse(base_url)
        self.base_domain = parsed_url.netloc
        self.base_scheme = parsed_url.scheme
        
        # Tracking
        self.visited_urls: Set[str] = set()
        self.crawled_pages: List[Dict] = []
        self.failed_urls: List[Dict] = []
        
        # Session for connection reuse
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Fiko WebKnowledge Bot 1.0 (Contact: info@pilito.com)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def crawl(self, progress_callback=None) -> List[Dict]:
        """
        Start crawling the website
        Returns list of crawled page data
        """
        logger.info(f"Starting crawl of {self.base_url}")
        
        # Initialize with base URL
        urls_to_crawl = [(self.base_url, 0)]  # (url, depth)
        
        while urls_to_crawl and len(self.crawled_pages) < self.max_pages:
            current_url, depth = urls_to_crawl.pop(0)
            
            # Skip if already visited or max depth reached
            if current_url in self.visited_urls or depth > self.max_depth:
                continue
            
            try:
                # Crawl current page
                page_data = self._crawl_page(current_url, depth)
                
                if page_data:
                    self.crawled_pages.append(page_data)
                    logger.info(f"Crawled: {current_url} (Page {len(self.crawled_pages)}/{self.max_pages})")
                    
                    # Update progress
                    if progress_callback:
                        progress_percentage = (len(self.crawled_pages) / self.max_pages) * 100
                        progress_callback(progress_percentage, len(self.crawled_pages), current_url)
                    
                    # Extract new URLs to crawl
                    if depth < self.max_depth and len(self.crawled_pages) < self.max_pages:
                        new_urls = self._extract_urls(page_data['links'], depth + 1)
                        urls_to_crawl.extend(new_urls)
                
                # Respectful delay
                time.sleep(self.delay)
                
            except Exception as e:
                logger.error(f"Error crawling {current_url}: {str(e)}")
                self.failed_urls.append({
                    'url': current_url,
                    'error': str(e),
                    'depth': depth
                })
        
        logger.info(f"Crawl completed. {len(self.crawled_pages)} pages crawled, {len(self.failed_urls)} failed")
        return self.crawled_pages
    
    def _crawl_page(self, url: str, depth: int) -> Optional[Dict]:
        """
        Crawl a single page and extract content
        """
        self.visited_urls.add(url)
        
        try:
            # Make request
            response = self.session.get(url, timeout=20, allow_redirects=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if 'text/html' not in content_type:
                logger.warning(f"Skipping non-HTML content: {url}")
                return None
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract page data
            page_data = {
                'url': url,
                'final_url': response.url,
                'title': self._extract_title(soup),
                'meta_description': self._extract_meta_description(soup),
                'meta_keywords': self._extract_meta_keywords(soup),
                'raw_content': response.text,
                'cleaned_content': self._extract_text_content(soup),
                'h1_tags': self._extract_headings(soup, 'h1'),
                'h2_tags': self._extract_headings(soup, 'h2'),
                'links': self._extract_links(soup, url),
                'depth': depth,
                'word_count': 0,
                'last_modified': self._extract_last_modified(response),
                'crawled_at': timezone.now().isoformat(),
                'status_code': response.status_code,
                'content_length': len(response.text),
            }
            
            # Calculate word count
            if page_data['cleaned_content']:
                page_data['word_count'] = len(page_data['cleaned_content'].split())
            
            return page_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Parsing error for {url}: {str(e)}")
            raise
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else ''
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '').strip()
        
        # Try Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        return og_desc.get('content', '').strip() if og_desc else ''
    
    def _extract_meta_keywords(self, soup: BeautifulSoup) -> str:
        """Extract meta keywords"""
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        return meta_keywords.get('content', '').strip() if meta_keywords else ''
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """
        Extract clean text content from HTML
        """
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _extract_headings(self, soup: BeautifulSoup, tag: str) -> List[str]:
        """Extract heading tags (h1, h2, etc.)"""
        headings = soup.find_all(tag)
        return [h.get_text().strip() for h in headings if h.get_text().strip()]
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract all links from the page"""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().strip()
            
            # Convert relative URLs to absolute
            full_url = urljoin(base_url, href)
            
            # Clean URL (remove fragments)
            parsed = urlparse(full_url)
            clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, 
                                  parsed.params, parsed.query, ''))
            
            links.append({
                'url': clean_url,
                'text': text,
                'original_href': href
            })
        
        return links
    
    def _extract_urls(self, links: List[Dict], depth: int) -> List[Tuple[str, int]]:
        """
        Extract URLs for further crawling
        """
        urls_to_crawl = []
        
        for link in links:
            url = link['url']
            
            # Skip if already visited
            if url in self.visited_urls:
                continue
            
            # Parse URL
            parsed_url = urlparse(url)
            
            # Skip empty URLs, fragments, or malformed URLs
            if not parsed_url.netloc or not parsed_url.scheme:
                continue
            
            # Skip non-HTTP(S) protocols
            if parsed_url.scheme not in ['http', 'https']:
                continue
            
            # Skip external domains if not allowed
            if not self.include_external and parsed_url.netloc != self.base_domain:
                continue
            
            # Skip common file extensions
            path = parsed_url.path.lower()
            skip_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                             '.zip', '.rar', '.tar', '.gz', '.jpg', '.jpeg', '.png', '.gif',
                             '.svg', '.css', '.js', '.ico', '.xml', '.rss']
            
            if any(path.endswith(ext) for ext in skip_extensions):
                continue
            
            urls_to_crawl.append((url, depth))
        
        return urls_to_crawl
    
    def _extract_last_modified(self, response) -> Optional[str]:
        """Extract last modified date from HTTP headers"""
        last_modified = response.headers.get('last-modified')
        if last_modified:
            return last_modified
        
        # Try date header
        date_header = response.headers.get('date')
        return date_header if date_header else None
    
    def close(self):
        """Close the session"""
        if hasattr(self, 'session'):
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class ContentExtractor:
    """
    Enhanced content extraction and cleaning service
    """
    
    @staticmethod
    def extract_main_content(html: str, cleaned_text: str) -> Dict[str, str]:
        """
        Extract main content sections from HTML
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try to find main content area
        main_content = ''
        
        # Common main content selectors
        main_selectors = [
            'main', 'article', '[role="main"]',
            '.main-content', '.content', '.post-content',
            '#main', '#content', '#post', '#article'
        ]
        
        for selector in main_selectors:
            main_element = soup.select_one(selector)
            if main_element:
                # Remove navigation, ads, and other non-content elements
                for unwanted in main_element.select('nav, aside, .ad, .advertisement, .sidebar'):
                    unwanted.decompose()
                
                main_content = main_element.get_text()
                break
        
        # If no main content found, use body text
        if not main_content:
            main_content = cleaned_text
        
        # Clean up text
        main_content = ContentExtractor._clean_text(main_content)
        
        return {
            'main_content': main_content,
            'content_length': len(main_content),
            'word_count': len(main_content.split()) if main_content else 0
        }
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ''
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\"\'\n]', ' ', text)
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def extract_key_information(content: str) -> Dict[str, List[str]]:
        """
        Extract key information like emails, phone numbers, addresses
        """
        result = {
            'emails': [],
            'phone_numbers': [],
            'urls': [],
            'dates': []
        }
        
        if not content:
            return result
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        result['emails'] = list(set(re.findall(email_pattern, content)))
        
        # Phone pattern (basic)
        phone_pattern = r'[\+]?[1-9]?[0-9]{7,15}'
        result['phone_numbers'] = list(set(re.findall(phone_pattern, content)))
        
        # URL pattern
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        result['urls'] = list(set(re.findall(url_pattern, content)))
        
        return result
    
    @staticmethod
    def create_summary(content: str, max_length: int = 1200) -> str:
        """
        Create AI-powered summary using Gemini 2.5-Pro
        Falls back to extractive summary if AI is unavailable
        """
        if not content or len(content) <= max_length:
            return content
        
        # Try AI-powered summarization with Gemini Pro
        try:
            # ✅ Setup proxy BEFORE importing Gemini (required for Iran servers)
            from core.utils import setup_ai_proxy
            setup_ai_proxy()
            
            from settings.models import GeneralSettings
            import google.generativeai as genai
            
            settings_obj = GeneralSettings.get_settings()
            gemini_api_key = settings_obj.gemini_api_key
            
            if gemini_api_key and len(gemini_api_key) >= 20:
                # Configure Gemini
                genai.configure(api_key=gemini_api_key)
                
                # Use Pro for high-quality summarization
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-pro",
                    generation_config={
                        "temperature": 0.3,  # Lower for factual summaries
                        "top_p": 0.9,
                        "max_output_tokens": 500,
                    },
                    safety_settings={
                        "HARASSMENT": "BLOCK_NONE",
                        "HATE_SPEECH": "BLOCK_NONE",
                        "SEXUALLY_EXPLICIT": "BLOCK_NONE",
                        "DANGEROUS_CONTENT": "BLOCK_NONE",
                    }
                )
                
                # Limit content for API (Pro can handle more but we limit for cost)
                content_preview = content[:4000] if len(content) > 4000 else content
                
                prompt = f"""Summarize this webpage content concisely in 150-200 words.

Content:
{content_preview}

Requirements:
- Focus on main topics and key information
- Include specific details (prices, contact info, features)
- Keep the same language as the original content
- Be factual and accurate
- Make it useful for customer service

Summary:"""

                response = model.generate_content(prompt)
                
                if response and response.text:
                    summary = response.text.strip()
                    # Limit to max_length if needed
                    if len(summary) > max_length:
                        summary = summary[:max_length].rsplit('.', 1)[0] + '.'
                    return summary
        
        except Exception as e:
            # Log but continue to fallback
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"AI summarization failed, using extractive fallback: {e}")
        
        # Fallback: Simple extractive summary
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return content[:max_length] + '...'
        
        # Select first few sentences that fit within max_length
        summary = ''
        for sentence in sentences:
            if len(summary + sentence + '. ') <= max_length:
                summary += sentence + '. '
            else:
                break
        
        return summary.strip() or content[:max_length] + '...'
