"""
AI-Powered Product/Service Extractor
Uses Gemini 1.5 Pro for high-accuracy extraction from website content
"""

import logging
import json
import re
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Optional, Tuple
from django.utils import timezone

logger = logging.getLogger(__name__)


class ProductExtractor:
    """
    Hybrid AI + Rule-based Product Extractor
    Uses Gemini 1.5 Pro for maximum accuracy in product extraction
    """
    
    # Rule-based indicators for pre-filtering
    PRODUCT_KEYWORDS = [
        # English
        'price', 'buy', 'purchase', 'shop', 'product', 'cart', 'order', 'sale',
        'discount', 'offer', 'deal', 'checkout', 'shipping',
        # Turkish
        'fiyat', 'satın', 'ürün', 'sipariş', 'al', 'sepet', 'indirim',
        # Arabic
        'سعر', 'شراء', 'منتج', 'طلب', 'خصم', 'عرض', 'سلة',
        # Persian
        'قیمت', 'خرید', 'محصول', 'سفارش', 'تخفیف', 'فروش', 'پرداخت'
    ]
    
    PRICE_PATTERNS = [
        r'\$\s*\d+(?:[.,]\d{1,2})?',  # $150.00 or $150,00
        r'\d+(?:[.,]\d{1,2})?\s*(?:USD|EUR|TRY|AED|SAR|دلار|لیر|ریال|تومان)',
        r'(?:قیمت|السعر|Fiyat|Price|Cost)[:]\s*\d+',
        r'\d+(?:[.,]\d{1,2})?\s*(?:dollar|euro|lira)',
    ]
    
    def __init__(self, user):
        self.user = user
        self.gemini_model = self._init_gemini()
    
    def _init_gemini(self):
        """Initialize Gemini 1.5 Pro model for maximum accuracy"""
        try:
            # ✅ Setup proxy BEFORE importing Gemini (required for Iran servers)
            from core.utils import setup_ai_proxy
            setup_ai_proxy()
            
            import google.generativeai as genai
            from settings.models import GeneralSettings
            
            api_key = GeneralSettings.get_settings().gemini_api_key
            if not api_key:
                logger.warning("Gemini API key not configured")
                return None
            
            genai.configure(api_key=api_key)
            
            # Configure safety settings to BLOCK_NONE (prevent false blocks on product content)
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            # Use Gemini 2.0 Flash-Exp for product extraction (16x cheaper, faster, less blocks)
            model = genai.GenerativeModel(
                'gemini-2.0-flash-exp',
                safety_settings=safety_settings
            )
            
            logger.info("✅ ProductExtractor initialized with Gemini 2.0 Flash-Exp (fast + cost-effective)")
            return model
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            return None
    
    def should_extract_from_page(self, page) -> Tuple[bool, float]:
        """
        Rule-based pre-filter: Is this page a good candidate for product extraction?
        
        Args:
            page: WebsitePage instance
        
        Returns:
            Tuple of (should_extract: bool, confidence: float)
        """
        content_lower = page.cleaned_content.lower()
        
        # Check 1: Product keywords density
        keyword_matches = sum(
            1 for kw in self.PRODUCT_KEYWORDS
            if kw in content_lower
        )
        
        # Check 2: Price patterns
        price_matches = sum(
            1 for pattern in self.PRICE_PATTERNS
            if re.search(pattern, page.cleaned_content, re.IGNORECASE | re.MULTILINE)
        )
        
        # Check 3: Page structure (H1 tags, sufficient content)
        has_product_structure = bool(page.h1_tags) and len(page.cleaned_content) > 100
        
        # Check 4: URL patterns
        url_lower = page.url.lower()
        has_product_url = any(
            word in url_lower 
            for word in ['product', 'shop', 'item', 'store', 'buy', 'محصول', 'ürün', 'منتج']
        )
        
        # Calculate confidence score
        confidence = 0.0
        
        if keyword_matches >= 5:
            confidence += 0.5
        elif keyword_matches >= 3:
            confidence += 0.3
        elif keyword_matches >= 1:
            confidence += 0.1
        
        if price_matches >= 2:
            confidence += 0.3
        elif price_matches >= 1:
            confidence += 0.2
        
        if has_product_structure:
            confidence += 0.1
        
        if has_product_url:
            confidence += 0.1
        
        # Decision threshold
        should_extract = confidence >= 0.4
        
        logger.info(
            f"Pre-filter: {page.url} → Extract: {should_extract} "
            f"(confidence: {confidence:.2f}, keywords: {keyword_matches}, prices: {price_matches})"
        )
        
        return should_extract, confidence
    
    def extract_products_ai(self, page) -> List[Dict]:
        """
        AI-based product extraction using Gemini 1.5 Pro
        
        Args:
            page: WebsitePage instance
        
        Returns:
            List of extracted product dictionaries
        """
        if not self.gemini_model:
            logger.warning("Gemini not available, skipping AI extraction")
            return []
        
        # Prepare content (limit to 5000 chars for Pro model)
        content_preview = page.cleaned_content[:5000]
        
        # Enhanced prompt for Gemini 1.5 Pro
        prompt = f"""
You are an expert AI assistant specialized in extracting product and service information from web pages with maximum accuracy.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PAGE INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Page Title: {page.title}
URL: {page.url}

Content:
{content_preview}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR TASK:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Analyze this webpage and determine if it presents products or services for sale.

If YES, extract detailed information for EACH product/service:

**Required Fields:**
1. title: Exact product/service name (string)
2. product_type: One of: service, product, software, consultation, course, tool, other
3. short_description: Brief 1-2 sentence description (max 200 chars)
4. description: Detailed description (2-4 sentences, max 500 chars)

**Pricing Fields:**
5. price: Current selling price (number only, no currency symbols)
6. original_price: Original price before discount (number only, or null)
7. currency: Currency code (USD, EUR, TRY, AED, SAR, IRR, IRT)
8. billing_period: For subscriptions (one_time, monthly, yearly, weekly, daily, or null)

**Feature Fields:**
9. features: Array of key features/benefits (max 5 items, each max 100 chars)
10. brand: Brand name if mentioned (string or null)
11. category: Product category (Electronics, Fashion, Software, etc., or null)
12. in_stock: Is it available? (boolean, default true)

**SEO/Tags:**
13. tags: Array of relevant search tags (max 5 items)
14. main_image: URL of main product image if visible in HTML (or null)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ DO NOT extract if this is:
- Contact page, About Us, Blog post, News article, Terms of Service
- General information page without specific products/services

✅ DO extract if this is:
- Individual product page with specific item
- Service offering page with pricing
- Product listing page (extract each product separately)
- Pricing/plans page (extract each plan as a product)

⚠️ ACCURACY RULES:
- Prices MUST be numbers only (150.00, not "$150" or "150 dollars")
- If no price found, set price to null (not 0)
- Features MUST be concise and specific (not generic marketing text)
- Descriptions MUST be informative (not just "great product")
- Tags MUST be relevant for search (not random words)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT (JSON ONLY):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{{
  "has_products": true,
  "products": [
    {{
      "title": "Product Name",
      "product_type": "product",
      "short_description": "Brief description",
      "description": "Full detailed description with key information",
      "price": 150.00,
      "original_price": 200.00,
      "currency": "USD",
      "billing_period": "monthly",
      "features": ["Feature 1", "Feature 2", "Feature 3"],
      "brand": "Brand Name",
      "category": "Electronics",
      "in_stock": true,
      "tags": ["tag1", "tag2", "tag3"],
      "main_image": "https://example.com/image.jpg"
    }}
  ]
}}

If this page does NOT contain products/services, return:
{{
  "has_products": false,
  "products": []
}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPORTANT: Return ONLY valid JSON. No explanations, no markdown.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        try:
            # Safety settings for generate_content (same as model init)
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
            ]
            
            # Generate with Gemini 2.5 Pro
            response = self.gemini_model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,  # Very low for maximum accuracy
                    'max_output_tokens': 3000,
                    'top_p': 0.9,
                    'top_k': 40,
                },
                safety_settings=safety_settings
            )
            
            # Parse JSON response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if '```' in response_text:
                response_text = re.sub(r'```json\n?|\n?```', '', response_text).strip()
            
            # Parse JSON
            result = json.loads(response_text)
            
            if result.get('has_products') and result.get('products'):
                products_count = len(result['products'])
                logger.info(f"✅ Gemini 2.5 Pro extracted {products_count} products from {page.url}")
                
                # Validate each product
                validated_products = []
                for product in result['products']:
                    if self._validate_product_data(product):
                        validated_products.append(product)
                    else:
                        logger.warning(f"⚠️ Skipped invalid product: {product.get('title', 'Unknown')}")
                
                return validated_products
            else:
                logger.info(f"ℹ️ No products found by AI on {page.url}")
                return []
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI JSON response for {page.url}: {e}")
            logger.debug(f"Response was: {response.text[:500]}")
            return []
        except Exception as e:
            logger.error(f"AI extraction failed for {page.url}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []
    
    def _validate_product_data(self, product: Dict) -> bool:
        """
        Validate extracted product data
        
        Args:
            product: Product dictionary
        
        Returns:
            True if valid, False otherwise
        """
        # Must have title
        if not product.get('title') or len(product['title'].strip()) < 3:
            logger.warning("Product missing valid title")
            return False
        
        # Must have description
        if not product.get('description') or len(product['description'].strip()) < 10:
            logger.warning(f"Product '{product.get('title')}' missing valid description")
            return False
        
        # Product type must be valid
        valid_types = ['service', 'product', 'software', 'consultation', 'course', 'tool', 'other']
        if product.get('product_type') not in valid_types:
            logger.warning(f"Product '{product.get('title')}' has invalid type")
            return False
        
        return True
    
    def save_products(self, products_data: List[Dict], source_page, source_website) -> List:
        """
        Save extracted products to database
        
        Args:
            products_data: List of product dictionaries
            source_page: WebsitePage instance
            source_website: WebsiteSource instance
        
        Returns:
            List of saved Product instances
        """
        from web_knowledge.models import Product
        
        saved_products = []
        
        for data in products_data:
            try:
                # Check for duplicates (same title + user)
                existing = Product.objects.filter(
                    user=self.user,
                    title__iexact=data.get('title', '').strip()
                ).first()
                
                if existing:
                    logger.info(f"⏭️ Product already exists: {data.get('title')}")
                    continue
                
                # Prepare product data
                product_data = {
                    'user': self.user,
                    'title': data.get('title', 'Untitled Product').strip(),
                    'product_type': data.get('product_type', 'product'),
                    'short_description': (data.get('short_description', '') or '')[:500],
                    'description': data.get('description', '').strip(),
                    'long_description': data.get('description', '').strip(),
                    
                    # Pricing
                    'price': self._parse_decimal(data.get('price')),
                    'original_price': self._parse_decimal(data.get('original_price')),
                    'currency': data.get('currency', 'USD'),
                    'billing_period': data.get('billing_period'),
                    
                    # Details
                    'features': data.get('features', []) or [],
                    'brand': (data.get('brand', '') or '').strip(),
                    'category': (data.get('category', '') or '').strip(),
                    'in_stock': data.get('in_stock', True),
                    'tags': data.get('tags', []) or [],
                    'keywords': data.get('tags', []) or [],
                    
                    # Media
                    'main_image': (data.get('main_image', '') or '').strip(),
                    
                    # Link to product page
                    'link': source_page.url,
                    
                    # Source tracking
                    'source_website': source_website,
                    'source_page': source_page,
                    'extraction_method': 'ai_auto',
                    'extraction_confidence': 0.92,  # High confidence from Gemini 2.0 Flash-Exp
                    'extraction_metadata': {
                        'model': 'gemini-2.0-flash-exp',
                        'extracted_at': timezone.now().isoformat(),
                        'page_title': source_page.title,
                        'page_url': source_page.url,
                        'word_count': source_page.word_count,
                    },
                    
                    'is_active': True,
                }
                
                # Calculate discount if applicable
                if product_data['price'] and product_data['original_price']:
                    if product_data['original_price'] > product_data['price']:
                        discount = product_data['original_price'] - product_data['price']
                        discount_pct = (discount / product_data['original_price']) * 100
                        product_data['discount_percentage'] = Decimal(str(round(discount_pct, 2)))
                
                # Create product
                product = Product.objects.create(**product_data)
                
                saved_products.append(product)
                
                # Log with details
                price_str = f"${product.price} {product.currency}" if product.price else "No price"
                logger.info(f"✅ Saved product: {product.title} ({price_str})")
                
            except Exception as e:
                logger.error(f"Failed to save product '{data.get('title', 'Unknown')}': {e}")
                import traceback
                logger.debug(traceback.format_exc())
                continue
        
        return saved_products
    
    def _parse_decimal(self, value) -> Optional[Decimal]:
        """
        Parse value to Decimal
        
        Args:
            value: Value to parse
        
        Returns:
            Decimal or None
        """
        if value is None:
            return None
        
        try:
            # Handle string or number
            if isinstance(value, str):
                # Remove common currency symbols and spaces
                value = value.replace('$', '').replace(',', '').strip()
            
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            logger.warning(f"Could not parse decimal value: {value}")
            return None
    
    def extract_and_save(self, page) -> List:
        """
        Main entry point: Hybrid extraction with rule pre-filter + AI extraction + Save
        
        Args:
            page: WebsitePage instance
        
        Returns:
            List of saved Product instances
        """
        try:
            # Step 1: Pre-filter (fast, rule-based)
            should_extract, confidence = self.should_extract_from_page(page)
            
            if not should_extract:
                logger.info(f"⏩ Skipped {page.url} (confidence: {confidence:.2f} < 0.4)")
                return []
            
            # Step 2: AI Extraction (Gemini 2.5 Pro)
            products_data = self.extract_products_ai(page)
            
            if not products_data:
                logger.info(f"ℹ️ No products extracted from {page.url}")
                return []
            
            # Step 3: Save to database
            saved_products = self.save_products(
                products_data,
                source_page=page,
                source_website=page.website
            )
            
            if saved_products:
                logger.info(
                    f"🎉 Successfully extracted and saved {len(saved_products)} products "
                    f"from {page.url}"
                )
            
            return saved_products
        
        except Exception as e:
            logger.error(f"Product extraction failed for {page.url}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

