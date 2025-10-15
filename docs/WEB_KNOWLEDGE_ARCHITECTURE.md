# 🌐 Web Knowledge System - Complete Architecture Guide

**راهنمای جامع معماری سیستم دانش از وب**

> **نسخه:** 2.0  
> **تاریخ:** October 2025  
> **وضعیت:** Production-Ready

---

## 📋 فهرست مطالب

1. [نمای کلی سیستم](#1-نمای-کلی-سیستم)
2. [معماری کامل](#2-معماری-کامل)
3. [فاز 1: Web Crawling (خزیدن وب)](#3-فاز-1-web-crawling)
4. [فاز 2: AI Analysis (آنالیز با هوش مصنوعی)](#4-فاز-2-ai-analysis)
5. [فاز 3: Knowledge Storage (ذخیره‌سازی دانش)](#5-فاز-3-knowledge-storage)
6. [فاز 4: Serving with OpenAI (سرو با OpenAI)](#6-فاز-4-serving-with-openai)
7. [Q&A System (سیستم سوال و جواب)](#7-qa-system)
8. [Products System (سیستم محصولات)](#8-products-system)
9. [API Endpoints](#9-api-endpoints)
10. [Database Schema](#10-database-schema)
11. [Performance & Optimization](#11-performance--optimization)

---

## 1. نمای کلی سیستم

### **🎯 هدف**
تبدیل خودکار محتوای وبسایت‌ها به یک **پایگاه دانش هوشمند** که توسط AI قابل جستجو و پاسخگویی است.

### **🔄 جریان کلی (High-Level Flow)**

```
┌─────────────────┐
│  User Submits   │
│   Website URL   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    PHASE 1: WEB CRAWLING                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Crawl Job  │───▶│  Parse HTML  │───▶│  Clean Text  │  │
│  │   (Celery)   │    │  (BeautifulSoup)  │  (Readability)   │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                   PHASE 2: AI ANALYSIS                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Q&A Gen     │    │  Product     │    │  Summarize   │  │
│  │ (Gemini 2.5) │    │ Extraction   │    │   Content    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│               PHASE 3: KNOWLEDGE STORAGE                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   QAPair     │    │   Product    │    │ WebsitePage  │  │
│  │   Model      │    │    Model     │    │    Model     │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                    │                    │          │
│         └────────────────────┼────────────────────┘          │
│                              ▼                               │
│                  ┌────────────────────────┐                  │
│                  │  TenantKnowledge DB    │                  │
│                  │  (Chunked + Embedded)  │                  │
│                  └────────────────────────┘                  │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│           PHASE 4: SERVING (AI CHATBOT QUERY)               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ User Query   │───▶│  Embedding   │───▶│   Vector     │  │
│  │              │    │  (OpenAI)    │    │   Search     │  │
│  └──────────────┘    └──────────────┘    └──────┬───────┘  │
│                                                   │          │
│                                                   ▼          │
│                                       ┌────────────────────┐ │
│                                       │  Gemini Response   │ │
│                                       │  (with context)    │ │
│                                       └────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. معماری کامل

### **🏗️ Component Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Website    │  │   Products   │  │      AI Chatbot      │  │
│  │   Manager    │  │    List      │  │   (Chat Interface)   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼──────────────────┼───────────────────────┼─────────────┘
          │                  │                       │
          ▼                  ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DJANGO REST API                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  web_knowledge│  │  web_knowledge│  │     AI_model         │  │
│  │   /websites/  │  │   /products/ │  │   /ask-question/     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼──────────────────┼───────────────────────┼─────────────┘
          │                  │                       │
          ▼                  ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                       BUSINESS LOGIC                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Celery Tasks (Async)                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │ crawl_website│  │ process_page │  │ generate_qa  │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                      Services Layer                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │ProductExtract│  │ContextRetriev│  │GeminiService │   │   │
│  │  │     or       │  │      er      │  │              │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  │                                                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │  Embedding   │  │SessionMemory │  │ QueryRouter  │   │   │
│  │  │   Service    │  │   Manager    │  │              │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Gemini AI  │  │  OpenAI API  │  │     Redis Cache      │  │
│  │  (Analysis)  │  │ (Embeddings) │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  PostgreSQL  │  │  pgvector    │  │     Celery Beat      │  │
│  │   (Main DB)  │  │  (Vectors)   │  │   (Scheduling)       │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. فاز 1: Web Crawling

### **📍 مسئولیت**
دریافت URL سایت و استخراج تمام صفحات و محتوای آن‌ها.

### **🔧 Components**

#### **3.1. Models**

**فایل:** `src/web_knowledge/models.py`

```python
class WebsiteSource(models.Model):
    """سایت اصلی که باید کرال بشه"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    url = models.URLField()
    
    # Crawl settings
    max_pages = models.IntegerField(default=50)
    max_depth = models.IntegerField(default=3)
    respect_robots_txt = models.BooleanField(default=True)
    
    # AI settings
    auto_extract_products = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)


class WebsitePage(models.Model):
    """هر صفحه کرال شده"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    website = models.ForeignKey(WebsiteSource, related_name='pages')
    url = models.URLField(unique=True)
    
    # Content
    raw_html = models.TextField()  # HTML خام
    cleaned_content = models.TextField()  # متن تمیز
    summary = models.TextField(blank=True)
    
    # Metadata
    title = models.CharField(max_length=500)
    word_count = models.IntegerField(default=0)
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed')
        ],
        default='pending'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)


class CrawlJob(models.Model):
    """وضعیت کرال"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    website = models.ForeignKey(WebsiteSource)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed')
        ]
    )
    
    # Progress tracking
    pages_discovered = models.IntegerField(default=0)
    pages_crawled = models.IntegerField(default=0)
    pages_failed = models.IntegerField(default=0)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
```

---

#### **3.2. Crawling Service**

**فایل:** `src/web_knowledge/services/crawler_service.py`

```python
import requests
from bs4 import BeautifulSoup
from readability import Document
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)


class WebCrawler:
    """
    کرالر وب - مسئول استخراج محتوا از صفحات
    """
    
    def __init__(self, website: WebsiteSource):
        self.website = website
        self.visited_urls = set()
        self.queue = [website.url]
        self.max_pages = website.max_pages
        self.max_depth = website.max_depth
    
    def crawl(self) -> dict:
        """
        شروع کرال
        
        Returns:
            {
                'pages_crawled': 10,
                'pages_failed': 1,
                'pages': [WebsitePage, ...]
            }
        """
        pages_created = []
        failed_count = 0
        
        while self.queue and len(pages_created) < self.max_pages:
            url = self.queue.pop(0)
            
            if url in self.visited_urls:
                continue
            
            try:
                page = self._crawl_page(url)
                if page:
                    pages_created.append(page)
                    
                    # پیدا کردن لینک‌های جدید
                    new_links = self._extract_links(page.raw_html, url)
                    self.queue.extend(new_links)
                
                self.visited_urls.add(url)
                
            except Exception as e:
                logger.error(f"Failed to crawl {url}: {e}")
                failed_count += 1
        
        return {
            'pages_crawled': len(pages_created),
            'pages_failed': failed_count,
            'pages': pages_created
        }
    
    def _crawl_page(self, url: str) -> WebsitePage:
        """
        کرال یک صفحه
        """
        # دریافت HTML
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; FikoBot/1.0)'
        })
        response.raise_for_status()
        
        html = response.text
        
        # استخراج محتوای اصلی با Readability
        doc = Document(html)
        title = doc.title()
        cleaned_html = doc.summary()
        
        # تبدیل HTML به متن
        soup = BeautifulSoup(cleaned_html, 'html.parser')
        cleaned_content = soup.get_text(separator='\n', strip=True)
        
        # حذف خطوط خالی
        cleaned_content = '\n'.join([
            line for line in cleaned_content.split('\n')
            if line.strip()
        ])
        
        # ساخت WebsitePage
        page = WebsitePage.objects.create(
            website=self.website,
            url=url,
            title=title,
            raw_html=html[:50000],  # محدود به 50KB
            cleaned_content=cleaned_content,
            word_count=len(cleaned_content.split()),
            processing_status='pending'
        )
        
        logger.info(f"✅ Crawled: {url} ({page.word_count} words)")
        
        return page
    
    def _extract_links(self, html: str, base_url: str) -> list:
        """
        استخراج لینک‌های داخلی صفحه
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # تبدیل به URL کامل
            full_url = urljoin(base_url, href)
            
            # فقط لینک‌های داخلی همین دامنه
            if self._is_same_domain(full_url, self.website.url):
                # حذف fragment (#section)
                full_url = full_url.split('#')[0]
                
                if full_url not in self.visited_urls:
                    links.append(full_url)
        
        return list(set(links))  # حذف تکراری‌ها
    
    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """چک کردن اینکه دو URL از یک دامنه هستن"""
        domain1 = urlparse(url1).netloc
        domain2 = urlparse(url2).netloc
        return domain1 == domain2
```

---

#### **3.3. Celery Task**

**فایل:** `src/web_knowledge/tasks.py`

```python
from celery import shared_task
from web_knowledge.models import WebsiteSource, CrawlJob
from web_knowledge.services.crawler_service import WebCrawler


@shared_task(bind=True, max_retries=3)
def crawl_website_task(self, website_id: str, crawl_job_id: str):
    """
    تسک Celery برای کرال وبسایت (async)
    
    این تسک background اجرا می‌شه و سنگین‌ترین بخش سیستمه
    """
    try:
        website = WebsiteSource.objects.get(id=website_id)
        crawl_job = CrawlJob.objects.get(id=crawl_job_id)
        
        # شروع کرال
        crawl_job.status = 'running'
        crawl_job.save()
        
        crawler = WebCrawler(website)
        result = crawler.crawl()
        
        # آپدیت وضعیت
        crawl_job.status = 'completed'
        crawl_job.pages_discovered = len(crawler.visited_urls)
        crawl_job.pages_crawled = result['pages_crawled']
        crawl_job.pages_failed = result['pages_failed']
        crawl_job.completed_at = timezone.now()
        crawl_job.save()
        
        # فرستادن صفحات برای پردازش AI
        for page in result['pages']:
            process_page_content_task.delay(str(page.id))
        
        logger.info(
            f"✅ Crawl completed for {website.name}: "
            f"{result['pages_crawled']} pages"
        )
        
        return {
            'success': True,
            'pages_crawled': result['pages_crawled']
        }
        
    except Exception as e:
        logger.error(f"❌ Crawl failed: {e}")
        
        # Retry با exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
```

---

## 4. فاز 2: AI Analysis

### **📍 مسئولیت**
تحلیل محتوای کرال شده با AI:
1. تولید Q&A
2. استخراج محصولات
3. خلاصه‌سازی

### **🔧 Components**

#### **4.1. Q&A Generation**

**فایل:** `src/web_knowledge/tasks.py`

```python
@shared_task(bind=True)
def process_page_content_task(self, page_id: str):
    """
    پردازش محتوای یک صفحه با AI
    
    شامل:
    1. تولید Q&A pairs
    2. استخراج محصولات (اگه فعال باشه)
    3. خلاصه‌سازی
    """
    try:
        page = WebsitePage.objects.get(id=page_id)
        
        # تغییر وضعیت به processing
        page.processing_status = 'processing'
        page.save()
        
        # ═══════════════════════════════════════════
        # بخش 1: تولید Q&A با Gemini
        # ═══════════════════════════════════════════
        
        qa_pairs = generate_qa_from_content(page)
        
        if qa_pairs:
            logger.info(f"✅ Generated {len(qa_pairs)} Q&A pairs for {page.url}")
        
        # ═══════════════════════════════════════════
        # بخش 2: استخراج محصولات (اگه فعال باشه)
        # ═══════════════════════════════════════════
        
        if page.website.auto_extract_products:
            try:
                from web_knowledge.services.product_extractor import ProductExtractor
                
                extractor = ProductExtractor(page.website.user)
                products = extractor.extract_and_save(page)
                
                if products:
                    logger.info(
                        f"✅ Extracted {len(products)} products from {page.url}"
                    )
            except Exception as e:
                logger.error(f"Product extraction failed: {e}")
                # ادامه می‌دیم چون Q&A موفق بوده
        
        # ═══════════════════════════════════════════
        # بخش 3: خلاصه‌سازی محتوا
        # ═══════════════════════════════════════════
        
        summary = summarize_page_content(page)
        if summary:
            page.summary = summary
        
        # تغییر وضعیت به completed
        page.processing_status = 'completed'
        page.save()
        
        logger.info(f"✅ Page processing completed: {page.url}")
        
        return {
            'success': True,
            'qa_pairs': len(qa_pairs),
            'products': len(products) if 'products' in locals() else 0
        }
        
    except Exception as e:
        logger.error(f"❌ Page processing failed for {page_id}: {e}")
        
        page.processing_status = 'failed'
        page.save()
        
        raise


def generate_qa_from_content(page: WebsitePage) -> list:
    """
    تولید Q&A pairs با Gemini 2.5 Flash
    
    این تابع از Gemini استفاده می‌کنه تا سوال و جواب
    متداول از محتوای صفحه تولید کنه
    """
    import google.generativeai as genai
    from settings.models import GeneralSettings
    
    # Configuration
    api_key = GeneralSettings.get_settings().gemini_api_key
    genai.configure(api_key=api_key)
    
    # Safety settings (برای محتوای فارسی)
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
    ]
    
    model = genai.GenerativeModel(
        'gemini-2.5-flash',  # سریع و ارزان برای تولید Q&A
        safety_settings=safety_settings
    )
    
    # Prompt برای تولید Q&A
    prompt = f"""Based on the following content, generate 5-10 frequently asked questions (FAQ) and their answers.

RULES:
- Questions should be natural and commonly asked
- Answers should be accurate based ONLY on the provided content
- Return JSON format: {{"qa_pairs": [{{"question": "...", "answer": "..."}}, ...]}}
- If content doesn't have enough information for 5 Q&As, generate fewer

CONTENT:
Title: {page.title}
URL: {page.url}

{page.cleaned_content[:4000]}

Return ONLY valid JSON:"""
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.3,
                'max_output_tokens': 2000,
            },
            safety_settings=safety_settings
        )
        
        # Parse JSON
        import json
        import re
        
        response_text = response.text.strip()
        
        # حذف markdown code blocks
        if '```' in response_text:
            response_text = re.sub(r'```json\n?|\n?```', '', response_text).strip()
        
        result = json.loads(response_text)
        
        # ذخیره Q&A pairs
        qa_pairs = []
        for qa in result.get('qa_pairs', []):
            qa_pair = QAPair.objects.create(
                user=page.website.user,
                page=page,
                question=qa['question'],
                answer=qa['answer'],
                source_type='website',
                is_active=True
            )
            qa_pairs.append(qa_pair)
        
        return qa_pairs
        
    except Exception as e:
        logger.error(f"Q&A generation failed for {page.url}: {e}")
        return []
```

---

#### **4.2. Product Extraction**

**فایل:** `src/web_knowledge/services/product_extractor.py`

```python
class ProductExtractor:
    """
    استخراج خودکار محصولات با AI
    
    از Gemini 2.5 Pro استفاده می‌کنه برای دقت بالا
    """
    
    def __init__(self, user):
        self.user = user
        self.gemini_model = self._init_gemini()
    
    def _init_gemini(self):
        """راه‌اندازی Gemini 2.5 Pro"""
        import google.generativeai as genai
        from settings.models import GeneralSettings
        
        api_key = GeneralSettings.get_settings().gemini_api_key
        genai.configure(api_key=api_key)
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
        ]
        
        model = genai.GenerativeModel(
            'gemini-2.5-pro',  # بالاترین دقت برای استخراج محصول
            safety_settings=safety_settings
        )
        
        return model
    
    def extract_products_ai(self, page: WebsitePage) -> list:
        """
        استخراج محصولات با Gemini 2.5 Pro
        
        Returns:
            [
                {
                    'title': 'نام محصول',
                    'price': 150000,
                    'currency': 'IRT',
                    'description': '...',
                    'brand': 'برند',
                    'features': ['ویژگی 1', 'ویژگی 2'],
                    ...
                },
                ...
            ]
        """
        # Prompt برای استخراج محصول
        prompt = f"""Extract product/service information from this page.

PAGE CONTENT:
Title: {page.title}
URL: {page.url}

{page.cleaned_content[:4000]}

EXTRACT:
1. title: Product name
2. price: Numeric price only (e.g., 150000 not "$150,000")
3. currency: USD, EUR, IRT, etc.
4. description: Detailed description
5. brand: Brand name
6. category: Product category
7. features: Array of key features
8. in_stock: Boolean

Return JSON:
{{
  "has_products": true,
  "products": [
    {{
      "title": "...",
      "price": 150000,
      "currency": "IRT",
      "description": "...",
      "brand": "...",
      "category": "...",
      "features": ["..."],
      "in_stock": true
    }}
  ]
}}

If NO products found, return: {{"has_products": false, "products": []}}

Return ONLY valid JSON:"""
        
        try:
            response = self.gemini_model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,  # دقت بالا
                    'max_output_tokens': 3000,
                },
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
                ]
            )
            
            # Parse JSON
            import json
            import re
            
            response_text = response.text.strip()
            
            if '```' in response_text:
                response_text = re.sub(r'```json\n?|\n?```', '', response_text).strip()
            
            result = json.loads(response_text)
            
            if result.get('has_products') and result.get('products'):
                logger.info(
                    f"✅ Gemini 2.5 Pro extracted {len(result['products'])} "
                    f"products from {page.url}"
                )
                return result['products']
            
            return []
            
        except Exception as e:
            logger.error(f"AI extraction failed for {page.url}: {e}")
            return []
    
    def save_products(self, products_data: list, source_page, source_website) -> list:
        """
        ذخیره محصولات در دیتابیس
        
        بعد از save، signal خودکار محصول رو به
        TenantKnowledge اضافه می‌کنه (برای جستجو با AI)
        """
        from web_knowledge.models import Product
        from decimal import Decimal
        
        saved_products = []
        
        for data in products_data:
            try:
                # چک کردن تکراری
                existing = Product.objects.filter(
                    user=self.user,
                    title__iexact=data.get('title', '').strip()
                ).first()
                
                if existing:
                    logger.info(f"⏭️ Product already exists: {data.get('title')}")
                    continue
                
                # ساخت Product
                product = Product.objects.create(
                    user=self.user,
                    title=data.get('title', 'Untitled').strip(),
                    description=data.get('description', ''),
                    price=Decimal(str(data.get('price'))) if data.get('price') else None,
                    currency=data.get('currency', 'USD'),
                    brand=data.get('brand', ''),
                    category=data.get('category', ''),
                    features=data.get('features', []),
                    in_stock=data.get('in_stock', True),
                    link=source_page.url,
                    source_website=source_website,
                    source_page=source_page,
                    extraction_method='ai_auto',
                    extraction_confidence=0.95,
                    is_active=True
                )
                
                saved_products.append(product)
                
                logger.info(
                    f"✅ Saved product: {product.title} "
                    f"({product.price} {product.currency})"
                )
                
                # 🎯 IMPORTANT: Signal خودکار محصول رو به
                # TenantKnowledge اضافه می‌کنه (فایل signals.py)
                # دیگه نیازی به manual chunking نیست!
                
            except Exception as e:
                logger.error(f"Failed to save product: {e}")
                continue
        
        return saved_products
```

---

## 5. فاز 3: Knowledge Storage

### **📍 مسئولیت**
ذخیره‌سازی دانش استخراج شده در فرمتی که AI بتونه جستجو کنه.

### **🔧 TenantKnowledge Model**

**فایل:** `src/AI_model/models.py`

```python
class TenantKnowledge(models.Model):
    """
    پایگاه دانش هر کاربر (با pgvector)
    
    این model همه دانش user رو ذخیره می‌کنه:
    - Q&A pairs
    - Products
    - Website content
    - Manual prompts
    
    با embedding برای semantic search
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # نوع محتوا
    chunk_type = models.CharField(
        max_length=20,
        choices=[
            ('faq', 'FAQ'),
            ('product', 'Product'),
            ('website', 'Website Content'),
            ('manual', 'Manual Prompt')
        ]
    )
    
    # شناسه منبع (مثلاً product_id یا qa_pair_id)
    source_id = models.UUIDField(null=True)
    document_id = models.UUIDField(null=True)  # گروه‌بندی chunks مربوط به هم
    
    # محتوا
    section_title = models.CharField(max_length=500)
    full_text = models.TextField()  # متن کامل
    tldr = models.TextField()  # خلاصه برای جستجوی سریع
    
    # Embeddings (برای semantic search)
    tldr_embedding = VectorField(dimensions=1536, null=True)  # OpenAI embedding
    full_embedding = VectorField(dimensions=1536, null=True)
    
    # Metadata
    language = models.CharField(max_length=10, default='en')
    word_count = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'chunk_type']),
            models.Index(fields=['source_id']),
        ]
        # Index برای pgvector
        # CREATE INDEX ON tenant_knowledge USING ivfflat (tldr_embedding vector_cosine_ops);
```

---

### **🔧 Auto-Sync با Signals**

**فایل:** `src/web_knowledge/signals.py`

```python
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver(post_save, sender='web_knowledge.Product')
def sync_product_to_knowledge_base(sender, instance, created, **kwargs):
    """
    هر وقت Product ساخته یا update می‌شه،
    خودکار به TenantKnowledge اضافه می‌شه
    
    این یعنی محصولات AUTOMATIC توسط AI قابل جستجو هستن!
    """
    try:
        from AI_model.models import TenantKnowledge
        from AI_model.services.embedding_service import EmbeddingService
        
        # اگه inactive شد، پاکش کن
        if not instance.is_active:
            TenantKnowledge.objects.filter(
                user=instance.user,
                chunk_type='product',
                source_id=instance.id
            ).delete()
            logger.info(f"🗑️ Removed inactive product: {instance.title}")
            return
        
        # ساخت متن کامل برای embedding
        full_text = f"Product: {instance.title}\n"
        full_text += f"Type: {instance.get_product_type_display()}\n"
        
        if instance.description:
            full_text += f"Description: {instance.description}\n"
        
        if instance.price:
            full_text += f"Price: {instance.price} {instance.currency}\n"
            
            if instance.original_price and instance.original_price > instance.price:
                discount = ((instance.original_price - instance.price) / instance.original_price) * 100
                full_text += f"Discount: {discount:.0f}% OFF\n"
        
        if instance.features:
            full_text += f"Features: {', '.join(instance.features[:5])}\n"
        
        if instance.brand:
            full_text += f"Brand: {instance.brand}\n"
        
        if instance.link:
            full_text += f"Link: {instance.link}\n"
        
        # تولید embeddings با OpenAI
        embedding_service = EmbeddingService()
        
        # خلاصه برای TL;DR
        tldr = f"{instance.title} - {instance.price} {instance.currency}"
        if instance.short_description:
            tldr += f" - {instance.short_description[:100]}"
        
        tldr_embedding = embedding_service.get_embedding(tldr)
        full_embedding = embedding_service.get_embedding(full_text)
        
        if not tldr_embedding or not full_embedding:
            logger.warning(f"Failed to generate embeddings for: {instance.title}")
            return
        
        # ساخت یا آپدیت chunk
        chunk, chunk_created = TenantKnowledge.objects.update_or_create(
            user=instance.user,
            chunk_type='product',
            source_id=instance.id,
            defaults={
                'section_title': instance.title,
                'full_text': full_text,
                'tldr': tldr,
                'tldr_embedding': tldr_embedding,
                'full_embedding': full_embedding,
                'language': 'fa' if _is_persian(instance.title) else 'en',
                'word_count': len(full_text.split()),
                'metadata': {
                    'price': float(instance.price) if instance.price else None,
                    'currency': instance.currency,
                    'brand': instance.brand or '',
                    'link': instance.link or '',
                    'extraction_method': instance.extraction_method,
                }
            }
        )
        
        action = "Added" if chunk_created else "Updated"
        logger.info(f"✅ {action} product in knowledge base: {instance.title}")
        
    except Exception as e:
        logger.error(f"Failed to sync product to knowledge base: {e}")


def _is_persian(text: str) -> bool:
    """تشخیص زبان فارسی"""
    return any('\u0600' <= c <= '\u06FF' for c in text)
```

---

## 6. فاز 4: Serving with OpenAI

### **📍 مسئولیت**
وقتی user سوال می‌پرسه، سیستم:
1. سوال رو با **OpenAI embed** می‌کنه
2. با **pgvector** مرتبط‌ترین chunks رو پیدا می‌کنه
3. به **Gemini** می‌فرسته برای تولید پاسخ

### **🔧 Components**

#### **6.1. Embedding Service**

**فایل:** `src/AI_model/services/embedding_service.py`

```python
class EmbeddingService:
    """
    سرویس تولید embedding با OpenAI
    
    از OpenAI text-embedding-3-large استفاده می‌کنه
    برای تبدیل متن به vector
    """
    
    def __init__(self):
        self.openai_client = self._init_openai()
        self.gemini_model = self._init_gemini_fallback()
    
    def _init_openai(self):
        """راه‌اندازی OpenAI برای embedding"""
        from openai import OpenAI
        from settings.models import GeneralSettings
        
        api_key = GeneralSettings.get_settings().openai_api_key
        
        if not api_key:
            logger.warning("OpenAI API key not configured")
            return None
        
        client = OpenAI(api_key=api_key)
        logger.info("✅ OpenAI embedding initialized")
        
        return client
    
    def get_embedding(self, text: str) -> list:
        """
        تبدیل متن به embedding vector
        
        Args:
            text: متن ورودی
        
        Returns:
            Vector با 1536 dimension (OpenAI text-embedding-3-large)
        """
        try:
            # محدود کردن طول متن (max 8191 tokens)
            text = text[:30000]  # ~8000 tokens
            
            # تولید embedding با OpenAI
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-large",  # بهترین model OpenAI
                input=text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            
            logger.debug(f"✅ Generated embedding: {len(embedding)} dimensions")
            
            return embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            
            # Fallback به Gemini
            return self._get_gemini_embedding(text)
    
    def _get_gemini_embedding(self, text: str) -> list:
        """Fallback: استفاده از Gemini برای embedding"""
        try:
            import google.generativeai as genai
            
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text[:20000],
                task_type="retrieval_document"
            )
            
            # Gemini embedding 768 dimension داره، ولی باید 1536 بشه
            # پس padding می‌زنیم
            embedding = result['embedding']
            embedding = embedding + [0.0] * (1536 - len(embedding))
            
            return embedding
            
        except Exception as e:
            logger.error(f"Gemini embedding also failed: {e}")
            return None
```

---

#### **6.2. Context Retriever**

**فایل:** `src/AI_model/services/context_retriever.py`

```python
class ContextRetriever:
    """
    Retrieval Augmented Generation (RAG) با pgvector
    
    جستجوی semantic با cosine similarity
    """
    
    @classmethod
    def retrieve_context(
        cls,
        query: str,
        user,
        primary_source: str,  # 'products', 'faq', 'website', etc.
        secondary_sources: list,
        primary_budget: int,
        secondary_budget: int,
        routing_info: dict = None
    ) -> dict:
        """
        جستجوی مرتبط‌ترین context برای query
        
        Args:
            query: سوال user
            user: کاربر
            primary_source: منبع اصلی جستجو
            secondary_sources: منابع فرعی
            primary_budget: حداکثر token برای primary
            secondary_budget: حداکثر token برای secondary
        
        Returns:
            {
                'primary_context': [
                    {
                        'title': 'محصول X',
                        'content': 'توضیحات...',
                        'score': 0.95,
                        'type': 'product'
                    },
                    ...
                ],
                'secondary_context': [...],
                'metadata': {
                    'primary_source': 'products',
                    'avg_similarity': 0.85
                }
            }
        """
        from AI_model.services.embedding_service import EmbeddingService
        
        # 1. تبدیل query به embedding (با OpenAI)
        embedding_service = EmbeddingService()
        query_embedding = embedding_service.get_embedding(query)
        
        if not query_embedding:
            logger.error("Failed to generate query embedding")
            return {
                'primary_context': [],
                'secondary_context': [],
                'metadata': {'error': 'embedding_failed'}
            }
        
        # 2. جستجو در primary source
        primary_results = cls._search_source(
            user=user,
            source=primary_source,
            query_embedding=query_embedding,
            top_k=5,
            token_budget=primary_budget
        )
        
        # 3. جستجو در secondary sources
        secondary_results = []
        for source in secondary_sources[:2]:  # max 2 secondary
            results = cls._search_source(
                user=user,
                source=source,
                query_embedding=query_embedding,
                top_k=3,
                token_budget=secondary_budget
            )
            secondary_results.extend(results)
        
        # محاسبه میانگین similarity
        all_scores = [r['score'] for r in primary_results + secondary_results]
        avg_similarity = sum(all_scores) / len(all_scores) if all_scores else 0
        
        return {
            'primary_context': primary_results,
            'secondary_context': secondary_results,
            'metadata': {
                'primary_source': primary_source,
                'avg_similarity': round(avg_similarity, 3),
                'total_results': len(primary_results) + len(secondary_results)
            }
        }
    
    @classmethod
    def _search_source(
        cls,
        user,
        source: str,
        query_embedding: list,
        top_k: int,
        token_budget: int
    ) -> list:
        """
        جستجوی semantic در یک source با pgvector
        
        از cosine similarity استفاده می‌کنه
        """
        try:
            from AI_model.models import TenantKnowledge, PGVECTOR_AVAILABLE
            from pgvector.django import CosineDistance
            
            # تبدیل source به chunk_type
            SOURCE_TO_CHUNK_TYPE = {
                'faq': 'faq',
                'products': 'product',
                'website': 'website',
                'manual': 'manual'
            }
            
            chunk_type = SOURCE_TO_CHUNK_TYPE.get(source, source)
            
            # Query با pgvector
            chunks = TenantKnowledge.objects.filter(
                user=user,
                chunk_type=chunk_type,
                tldr_embedding__isnull=False
            ).annotate(
                # محاسبه cosine distance
                distance=CosineDistance('tldr_embedding', query_embedding)
            ).order_by('distance')[:top_k * 2]  # گرفتن 2x برای فیلتر
            
            results = []
            total_tokens = 0
            
            for chunk in chunks:
                similarity = 1 - chunk.distance  # تبدیل distance به similarity
                
                # فیلتر: فقط نتایج با similarity > 0.1
                if similarity < 0.1:
                    continue
                
                # محاسبه tokens تقریبی
                chunk_tokens = chunk.word_count * 1.3
                
                if total_tokens + chunk_tokens > token_budget:
                    break  # بودجه تموم شد
                
                results.append({
                    'title': chunk.section_title,
                    'content': chunk.full_text,
                    'type': chunk.chunk_type,
                    'score': round(similarity, 3),
                    'source_id': chunk.source_id,
                    'word_count': chunk.word_count,
                    'metadata': chunk.metadata
                })
                
                total_tokens += chunk_tokens
                
                if len(results) >= top_k:
                    break
            
            logger.info(
                f"🔍 Found {len(results)} results from {source} "
                f"(avg similarity: {sum(r['score'] for r in results) / len(results) if results else 0:.2f})"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed for source {source}: {e}")
            return []
```

---

## 7. Q&A System

### **📍 Model**

**فایل:** `src/web_knowledge/models.py`

```python
class QAPair(models.Model):
    """
    سوال و جواب متداول
    
    می‌تونه از چند منبع بیاد:
    1. Auto-generated (AI از صفحات website)
    2. Manual (user خودش می‌نویسه)
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Source
    source_type = models.CharField(
        max_length=20,
        choices=[
            ('website', 'Website'),
            ('manual', 'Manual Entry')
        ],
        default='manual'
    )
    page = models.ForeignKey(
        WebsitePage,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="صفحه‌ای که این Q&A از اون generate شده"
    )
    
    # Content
    question = models.TextField()
    answer = models.TextField()
    
    # Metadata
    category = models.CharField(max_length=100, blank=True)
    tags = ArrayField(models.CharField(max_length=50), default=list, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['source_type']),
        ]
    
    def __str__(self):
        return f"Q: {self.question[:50]}"
```

### **📍 Auto-Ingestion به TenantKnowledge**

Q&A pairs هم مثل Products خودکار به TenantKnowledge اضافه می‌شن:

**فایل:** `src/AI_model/services/knowledge_ingestion_service.py`

```python
@classmethod
def _ingest_faq(cls, user) -> int:
    """
    اضافه کردن Q&A pairs به TenantKnowledge
    
    این تابع معمولاً توسط management command اجرا می‌شه
    یا manual توسط user trigger می‌شه
    """
    try:
        from web_knowledge.models import QAPair
        from AI_model.models import TenantKnowledge
        from AI_model.services.embedding_service import EmbeddingService
        
        # گرفتن همه Q&A های فعال
        qa_pairs = QAPair.objects.filter(user=user, is_active=True)
        
        chunks_created = 0
        embedding_service = EmbeddingService()
        
        for qa in qa_pairs:
            # ساخت متن کامل
            full_text = f"Q: {qa.question}\nA: {qa.answer}"
            
            # TL;DR (خلاصه): فقط سوال
            tldr = qa.question
            
            # تولید embeddings
            tldr_embedding = embedding_service.get_embedding(tldr)
            full_embedding = embedding_service.get_embedding(full_text)
            
            if not tldr_embedding or not full_embedding:
                logger.warning(f"Failed to generate embeddings for Q&A {qa.id}")
                continue
            
            # ساخت chunk
            TenantKnowledge.objects.update_or_create(
                user=user,
                chunk_type='faq',
                source_id=qa.id,
                defaults={
                    'section_title': qa.question[:200],
                    'full_text': full_text,
                    'tldr': tldr,
                    'tldr_embedding': tldr_embedding,
                    'full_embedding': full_embedding,
                    'language': _detect_language(qa.question),
                    'word_count': len(full_text.split()),
                    'metadata': {
                        'category': qa.category or '',
                        'tags': qa.tags or [],
                        'source_type': qa.source_type
                    }
                }
            )
            chunks_created += 1
        
        return chunks_created
        
    except Exception as e:
        logger.error(f"FAQ ingestion failed: {e}")
        raise
```

---

## 8. Products System

### **📍 Complete Product Model**

**فایل:** `src/web_knowledge/models.py`

```python
class Product(models.Model):
    """
    محصولات و سرویس‌ها
    
    ویژگی‌های کلیدی:
    - Auto-extraction با AI
    - Auto-sync به TenantKnowledge (با signal)
    - Support برای قیمت پیچیده (تخفیف، دوره پرداخت، etc.)
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # ══════ اطلاعات اصلی ══════
    title = models.CharField(max_length=255)
    product_type = models.CharField(
        max_length=20,
        choices=[
            ('product', 'Product'),
            ('service', 'Service'),
            ('software', 'Software'),
            ('course', 'Course'),
            ('tool', 'Tool'),
            ('other', 'Other'),
        ],
        default='product'
    )
    
    # توضیحات
    short_description = models.CharField(max_length=500, blank=True)
    description = models.TextField()
    long_description = models.TextField(blank=True)
    
    # ══════ قیمت‌گذاری ══════
    price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    original_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    currency = models.CharField(
        max_length=10,
        choices=[
            ('USD', 'US Dollar'),
            ('EUR', 'Euro'),
            ('IRT', 'Iranian Toman'),
            ('IRR', 'Iranian Rial'),
        ],
        default='USD'
    )
    
    billing_period = models.CharField(
        max_length=20,
        choices=[
            ('one_time', 'One-time'),
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
        ],
        default='one_time'
    )
    
    # ══════ جزئیات ══════
    brand = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100, blank=True)
    features = ArrayField(models.TextField(), default=list, blank=True)
    specifications = models.JSONField(default=dict, blank=True)
    
    # ══════ تصاویر ══════
    main_image = models.URLField(blank=True)
    images = ArrayField(models.URLField(), default=list, blank=True)
    
    # ══════ موجودی ══════
    in_stock = models.BooleanField(default=True)
    stock_quantity = models.IntegerField(null=True, blank=True)
    
    # ══════ SEO ══════
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    keywords = ArrayField(models.CharField(max_length=50), default=list, blank=True)
    tags = ArrayField(models.CharField(max_length=50), default=list, blank=True)
    
    # ══════ لینک ══════
    link = models.URLField(blank=True, help_text="لینک صفحه محصول")
    
    # ══════ Source Tracking (برای AI extraction) ══════
    source_website = models.ForeignKey(
        WebsiteSource,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    source_page = models.ForeignKey(
        WebsitePage,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    
    extraction_method = models.CharField(
        max_length=20,
        choices=[
            ('manual', 'Manual'),
            ('ai_auto', 'AI Auto'),
            ('ai_assisted', 'AI Assisted'),
        ],
        default='manual'
    )
    
    extraction_confidence = models.FloatField(
        default=1.0,
        help_text="اعتماد AI به استخراج (0-1)"
    )
    
    extraction_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="اطلاعات اضافه (model, timestamp, etc.)"
    )
    
    # ══════ Status ══════
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['extraction_method']),
            models.Index(fields=['source_website']),
        ]
    
    # ══════ Computed Properties ══════
    
    @property
    def final_price(self):
        """قیمت نهایی بعد از تخفیف"""
        if not self.price:
            return None
        
        if self.discount_amount:
            return self.price - self.discount_amount
        elif self.discount_percentage:
            discount = (self.price * self.discount_percentage) / 100
            return self.price - discount
        
        return self.price
    
    @property
    def has_discount(self):
        """آیا تخفیف داره؟"""
        return bool(self.discount_amount or self.discount_percentage)
    
    @property
    def discount_info(self):
        """اطلاعات تخفیف به صورت readable"""
        if self.discount_percentage:
            return f"{self.discount_percentage}% OFF"
        elif self.discount_amount:
            return f"-{self.discount_amount} {self.currency}"
        return None
    
    @property
    def is_auto_extracted(self):
        """آیا با AI استخراج شده؟"""
        return self.extraction_method == 'ai_auto'
```

---

## 9. API Endpoints

### **📍 REST API**

**فایل:** `src/web_knowledge/urls.py`

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from web_knowledge import views

router = DefaultRouter()
router.register(r'websites', views.WebsiteSourceViewSet, basename='website')
router.register(r'pages', views.WebsitePageViewSet, basename='page')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'qa-pairs', views.QAPairViewSet, basename='qa-pair')

urlpatterns = [
    path('', include(router.urls)),
]
```

### **📍 Key Endpoints**

#### **1. شروع کرال**

```http
POST /api/v1/web-knowledge/websites/create-and-crawl/

Request Body:
{
  "name": "WACACO Iran",
  "url": "https://www.wacaco.ir/",
  "max_pages": 50,
  "max_depth": 3,
  "auto_extract_products": true
}

Response:
{
  "website_id": "uuid",
  "crawl_job_id": "uuid",
  "status": "running",
  "message": "Crawl started"
}
```

#### **2. چک کردن وضعیت کرال**

```http
GET /api/v1/web-knowledge/websites/{website_id}/crawl-status/

Response:
{
  "status": "completed",
  "pages_discovered": 30,
  "pages_crawled": 30,
  "pages_failed": 0,
  "qa_pairs_generated": 45,
  "products_extracted": 12,
  "progress_percentage": 100
}
```

#### **3. لیست محصولات**

```http
GET /api/v1/web-knowledge/products/

Query Parameters:
- website_id: فیلتر بر اساس سایت
- has_discount: فقط محصولات تخفیف‌دار
- min_price, max_price: محدوده قیمت
- search: جستجو در عنوان و توضیحات

Response:
{
  "count": 12,
  "results": [
    {
      "id": "uuid",
      "title": "نانوپرسو قرمز گدازه",
      "price": "8249000",
      "original_price": "9799000",
      "currency": "IRT",
      "discount_percentage": "15.82",
      "has_discount": true,
      "brand": "WACACO",
      "features": ["قابل حمل", "18 بار فشار", "..."],
      "in_stock": true,
      "link": "https://www.wacaco.ir/...",
      "extraction_method": "ai_auto",
      "is_auto_extracted": true
    },
    ...
  ]
}
```

#### **4. پرسیدن سوال از AI**

```http
POST /api/v1/ai/ask-question/

Request Body:
{
  "question": "قیمت پیکوپرسو چنده؟",
  "conversation_id": "uuid" // اختیاری
}

Response:
{
  "success": true,
  "response": "قیمت پیکوپرسو 13,989,000 تومان هست. این دستگاه...",
  "response_time_ms": 2341,
  "metadata": {
    "intent": "pricing",
    "primary_source": "products",
    "avg_similarity": 0.89,
    "sources_used": [
      {
        "type": "product",
        "title": "پیکوپرسو",
        "score": 0.95
      }
    ]
  }
}
```

---

## 10. Database Schema

### **📊 ER Diagram (Text)**

```
┌─────────────────┐
│  WebsiteSource  │
├─────────────────┤
│ id (UUID)       │
│ user_id (FK)    │
│ name            │
│ url             │
│ max_pages       │
│ auto_extract... │
└────────┬────────┘
         │ 1:N
         ▼
┌─────────────────┐       ┌─────────────────┐
│  WebsitePage    │──────▶│    QAPair       │
├─────────────────┤ 1:N   ├─────────────────┤
│ id (UUID)       │       │ id (UUID)       │
│ website_id (FK) │       │ user_id (FK)    │
│ url             │       │ page_id (FK)    │
│ title           │       │ question        │
│ cleaned_content │       │ answer          │
│ summary         │       │ source_type     │
│ processing_...  │       └─────────────────┘
└────────┬────────┘
         │ 1:N
         ▼
┌─────────────────┐
│    Product      │
├─────────────────┤
│ id (UUID)       │
│ user_id (FK)    │
│ source_page(FK) │
│ title           │
│ price           │
│ description     │
│ features        │
│ extraction_...  │
└────────┬────────┘
         │
         │ Auto-sync via Signal
         ▼
┌─────────────────────────┐
│   TenantKnowledge       │
├─────────────────────────┤
│ id (UUID)               │
│ user_id (FK)            │
│ chunk_type (enum)       │◀─────┐
│ source_id (UUID)        │      │
│ full_text               │      │
│ tldr                    │      │
│ tldr_embedding (vector) │──────┤
│ full_embedding (vector) │      │ pgvector
│ metadata (JSON)         │      │ for search
└─────────────────────────┘──────┘
```

---

## 11. Performance & Optimization

### **⚡ Caching Strategy**

```python
# Redis cache برای نتایج جستجو
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# مثال: Cache کردن context retrieval
from django.core.cache import cache

def retrieve_with_cache(query, user):
    cache_key = f"context:{user.id}:{hash(query)}"
    
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    result = ContextRetriever.retrieve_context(query, user, ...)
    
    # Cache برای 1 ساعت
    cache.set(cache_key, result, 3600)
    
    return result
```

### **⚡ Database Indexes**

```sql
-- pgvector index برای fast similarity search
CREATE INDEX ON ai_model_tenantknowledge 
USING ivfflat (tldr_embedding vector_cosine_ops) 
WITH (lists = 100);

CREATE INDEX ON ai_model_tenantknowledge 
USING ivfflat (full_embedding vector_cosine_ops) 
WITH (lists = 100);

-- Regular indexes
CREATE INDEX idx_tenant_knowledge_user_type 
ON ai_model_tenantknowledge(user_id, chunk_type);

CREATE INDEX idx_product_user_active 
ON web_knowledge_product(user_id, is_active);
```

### **⚡ Celery Optimization**

```python
# Task routing
CELERY_TASK_ROUTES = {
    'web_knowledge.tasks.crawl_website_task': {'queue': 'crawl'},
    'web_knowledge.tasks.process_page_content_task': {'queue': 'ai'},
}

# Worker pools
# Crawl: I/O bound → eventlet
# AI: CPU bound → prefork
celery -A core worker -Q crawl -P eventlet -c 10
celery -A core worker -Q ai -P prefork -c 4
```

---

## 12. خلاصه جریان کامل

### **🔄 End-to-End Flow**

```
1. USER submits website URL
         ↓
2. WebsiteSource created in DB
         ↓
3. Celery task: crawl_website_task
   - Fetch HTML
   - Parse with BeautifulSoup
   - Clean with Readability
   - Save as WebsitePage (status: pending)
         ↓
4. For each WebsitePage → Celery task: process_page_content_task
         ↓
   ┌────────────────────────────────┐
   │  4a. Q&A Generation            │
   │  - Prompt to Gemini 2.5 Flash  │
   │  - Parse JSON response         │
   │  - Save as QAPair              │
   │  - Ingest to TenantKnowledge   │
   └────────────────────────────────┘
         ↓
   ┌────────────────────────────────┐
   │  4b. Product Extraction        │
   │  - Pre-filter (rule-based)     │
   │  - AI extraction (Gemini 2.5 Pro)│
   │  - Save as Product             │
   │  - Signal → TenantKnowledge    │
   │    (with OpenAI embedding)     │
   └────────────────────────────────┘
         ↓
5. TenantKnowledge chunks ready for search
         ↓
6. USER asks question in chatbot
         ↓
7. Query → OpenAI embedding
         ↓
8. pgvector search → Find top matches
         ↓
9. Matched chunks → Gemini prompt
         ↓
10. Gemini generates response with context
         ↓
11. Response returned to USER
```

---

## 📚 مستندات مرتبط

- **[DEPLOYMENT_INSTRUCTIONS.md](./DEPLOYMENT_INSTRUCTIONS.md)** - راهنمای deploy
- **[AI_RESPONSE_ALGORITHM_ARCHITECTURE.md](./AI_RESPONSE_ALGORITHM_ARCHITECTURE.md)** - معماری کامل AI chatbot
- **[PERSONA_TONE_IMPLEMENTATION_GUIDE.md](./PERSONA_TONE_IMPLEMENTATION_GUIDE.md)** - شخصیت‌سازی AI

---

## 🎯 نتیجه‌گیری

این سیستم یک **پایپلاین کامل از web crawling تا AI serving** رو پیاده‌سازی کرده:

✅ **Automated**: همه چیز خودکار (crawl → extract → index → serve)  
✅ **Scalable**: با Celery + Redis + PostgreSQL  
✅ **Accurate**: Gemini 2.5 Pro برای استخراج، OpenAI برای embedding  
✅ **Fast**: pgvector برای جستجوی میلیون‌ها vector در milliseconds  
✅ **Production-Ready**: با error handling، retry logic، monitoring

**نتیجه:** یک chatbot که می‌تونه دقیقاً از روی محتوای سایت شما پاسخ بده، بدون نیاز به manual data entry! 🚀

