"""
Views for web_knowledge app
Provides REST API endpoints for website knowledge management
"""
import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# ✅ Setup proxy BEFORE any AI imports (required for Iran servers)
from core.utils import setup_ai_proxy
setup_ai_proxy()

from .models import WebsiteSource, WebsitePage, QAPair, CrawlJob, Product
from settings.models import GeneralSettings, BusinessPrompt
from .serializers import (
    WebsiteSourceSerializer, WebsiteSourceCreateSerializer,
    WebsitePageSerializer, WebsitePageDetailSerializer,
    QAPairSerializer, CrawlJobSerializer,
    StartCrawlSerializer, QASearchSerializer,
    QAPairBulkCreateSerializer, WebsiteAnalyticsSerializer,
    QAFeedbackSerializer, ProductSerializer, ProductCreateSerializer,
    ProductUpdateSerializer, QAPairPartialCreateSerializer,
    GeneratePromptSerializer, ProductCompactSerializer
)
from .tasks import crawl_website_task, generate_qa_pairs_task, recrawl_website_task

logger = logging.getLogger(__name__)


class WebsiteSourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing website sources
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return WebsiteSourceCreateSerializer
        return WebsiteSourceSerializer
    
    def get_queryset(self):
        """Filter to user's websites only"""
        return WebsiteSource.objects.filter(user=self.request.user).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """Create a new website source and return complete data including ID"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            website = serializer.save()
            
            # Return complete website data including ID
            response_serializer = WebsiteSourceSerializer(website)
            return Response({
                'success': True,
                'message': 'Website source created successfully',
                'website': response_serializer.data,
                'id': str(website.id),  # Explicit ID for easy access
                'next_steps': {
                    'start_crawl_url': f'/api/v1/web-knowledge/websites/{website.id}/start_crawl/',
                    'status_url': f'/api/v1/web-knowledge/websites/{website.id}/crawl_status/',
                    'analytics_url': f'/api/v1/web-knowledge/websites/{website.id}/analytics/'
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Delete a website source and all related data"""
        website = self.get_object()
        
        # Collect statistics before deletion
        pages_count = website.pages.count()
        qa_pairs_count = QAPair.objects.filter(page__website=website).count()
        crawl_jobs_count = website.crawl_jobs.count()
        
        website_data = {
            'id': str(website.id),
            'name': website.name,
            'url': website.url,
            'pages_count': pages_count,
            'qa_pairs_count': qa_pairs_count,
            'crawl_jobs_count': crawl_jobs_count
        }
        
        # Delete the website (cascades to pages, Q&A pairs, and crawl jobs)
        website.delete()
        
        return Response({
            'success': True,
            'message': f'Website "{website_data["name"]}" and all related data deleted successfully',
            'deleted_data': {
                'website': website_data,
                'summary': {
                    'pages_deleted': pages_count,
                    'qa_pairs_deleted': qa_pairs_count,
                    'crawl_jobs_deleted': crawl_jobs_count,
                    'total_items_deleted': 1 + pages_count + qa_pairs_count + crawl_jobs_count
                }
            }
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Start crawling a website",
        request_body=StartCrawlSerializer,
        responses={
            200: "Crawl started successfully",
            400: "Bad request",
            404: "Website not found"
        }
    )
    @action(detail=True, methods=['post'])
    def start_crawl(self, request, pk=None):
        """Start crawling a website"""
        website = self.get_object()
        serializer = StartCrawlSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if already crawling
        if website.crawl_status == 'crawling':
            return Response(
                {'error': 'Website is already being crawled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start crawl task
        try:
            task = crawl_website_task.delay(str(website.id))
            
            # Update website status
            website.crawl_status = 'pending'
            website.save(update_fields=['crawl_status'])
            
            return Response({
                'message': 'Crawl started successfully',
                'task_id': task.id,
                'website_id': str(website.id)
            })
            
        except Exception as e:
            logger.error(f"Error starting crawl for website {website.id}: {str(e)}")
            return Response(
                {'error': 'Failed to start crawl'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_description="Get website crawl status",
        responses={200: "Crawl status information"}
    )
    @action(detail=True, methods=['get'])
    def crawl_status(self, request, pk=None):
        """Get crawl status for a website"""
        website = self.get_object()
        
        # Get latest crawl job
        latest_job = website.crawl_jobs.order_by('-created_at').first()
        
        response_data = {
            'website_id': str(website.id),
            'crawl_status': website.crawl_status,
            'crawl_progress': website.crawl_progress,
            'pages_crawled': website.pages_crawled,
            'total_qa_pairs': website.total_qa_pairs,
            'last_crawl_at': website.last_crawl_at,
            'crawl_error_message': website.crawl_error_message,
        }
        
        if latest_job:
            response_data['latest_job'] = CrawlJobSerializer(latest_job).data
        
        return Response(response_data)
    
    @swagger_auto_schema(
        operation_description="Create website and start crawling immediately",
        request_body=WebsiteSourceCreateSerializer,
        responses={
            201: "Website created and crawl started",
            400: "Bad request"
        }
    )
    @action(detail=False, methods=['post'], url_path='create-and-crawl')
    def create_and_crawl(self, request):
        """Create a new website source and immediately start crawling"""
        # First create the website
        serializer = WebsiteSourceCreateSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        website = serializer.save()
        
        # Start crawling immediately
        try:
            from .tasks import crawl_website_task
            task = crawl_website_task.delay(str(website.id))
            
            # Update website status
            website.crawl_status = 'pending'
            website.save(update_fields=['crawl_status'])
            
            # Return complete response
            response_serializer = WebsiteSourceSerializer(website)
            return Response({
                'success': True,
                'message': 'Website created, crawling started, and Q&A generation will begin automatically',
                'website': response_serializer.data,
                'id': str(website.id),
                'task_id': task.id,
                'note': 'Q&A pairs (minimum 3 per page) will be automatically generated for each crawled page',
                'auto_qa_generation': True,
                'urls': {
                    'status': f'/api/v1/web-knowledge/websites/{website.id}/crawl_status/',
                    'analytics': f'/api/v1/web-knowledge/websites/{website.id}/analytics/',
                    'pages': f'/api/v1/web-knowledge/pages/?website={website.id}',
                    'qa_pairs': f'/api/v1/web-knowledge/qa-pairs/?website={website.id}',
                    'enhanced_qa_generation': f'/api/v1/web-knowledge/generate-enhanced-qa/'
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error starting crawl for website {website.id}: {str(e)}")
            
            # Return website info even if crawl failed to start
            response_serializer = WebsiteSourceSerializer(website)
            return Response({
                'success': True,
                'message': 'Website created but failed to start crawl',
                'website': response_serializer.data,
                'id': str(website.id),
                'error': str(e),
                'manual_crawl_url': f'/api/v1/web-knowledge/websites/{website.id}/start_crawl/'
            }, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        operation_description="Get all pages for a website with full details",
        responses={200: "List of pages with full details"}
    )
    @action(detail=True, methods=['get'])
    def pages(self, request, pk=None):
        """Get all pages for a website with complete details"""
        from django.db import models
        
        website = self.get_object()
        
        # Get all pages for this website
        pages = WebsitePage.objects.filter(website=website).prefetch_related('qa_pairs', 'extracted_products').order_by('-crawled_at')
        
        # Serialize with detailed information
        pages_data = []
        for page in pages:
            page_data = {
                'id': str(page.id),
                'url': page.url,
                'title': page.title,
                'summary': page.summary,
                'word_count': page.word_count,
                'processing_status': page.processing_status,
                'processing_error': page.processing_error,
                'meta_description': page.meta_description,
                'meta_keywords': page.meta_keywords,
                'h1_tags': page.h1_tags,
                'h2_tags': page.h2_tags,
                'links_count': len(page.links) if page.links else 0,
                'crawled_at': page.crawled_at,
                'processed_at': page.processed_at,
                'created_at': page.created_at,
                'updated_at': page.updated_at,
                'qa_pairs': {
                    'total': page.qa_pairs.filter(generation_status='completed').count(),
                    'average_confidence': page.qa_pairs.filter(generation_status='completed').aggregate(
                        avg_confidence=models.Avg('confidence_score')
                    )['avg_confidence'] or 0,
                    'featured_count': page.qa_pairs.filter(generation_status='completed', is_featured=True).count()
                },
                'products': {
                    'total': page.extracted_products.filter(is_active=True).count(),
                    'in_stock': page.extracted_products.filter(is_active=True, in_stock=True).count()
                }
            }
            pages_data.append(page_data)
        
        return Response({
            'website_id': str(website.id),
            'website_name': website.name,
            'website_url': website.url,
            'total_pages': len(pages_data),
            'pages': pages_data,
            'summary': {
                'total_words': sum(page['word_count'] for page in pages_data),
                'completed_pages': len([p for p in pages_data if p['processing_status'] == 'completed']),
                'failed_pages': len([p for p in pages_data if p['processing_status'] == 'failed']),
                'total_qa_pairs': sum(page['qa_pairs']['total'] for page in pages_data),
                'pages_with_qa': len([p for p in pages_data if p['qa_pairs']['total'] > 0]),
                'total_products': sum(page['products']['total'] for page in pages_data),
                'pages_with_products': len([p for p in pages_data if p['products']['total'] > 0])
            }
        })
    
    @swagger_auto_schema(
        operation_description="Get all products extracted from this website",
        responses={200: ProductSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], url_path='products')
    def products(self, request, pk=None):
        """Get all products extracted from this website"""
        website = self.get_object()
        
        # Get all products from this website
        products = Product.objects.filter(
            source_website=website
        ).select_related('source_page').order_by('-created_at')
        
        serializer = ProductSerializer(products, many=True)
        
        return Response({
            'website_id': str(website.id),
            'website_name': website.name,
            'website_url': website.url,
            'total_products': products.count(),
            'active_products': products.filter(is_active=True).count(),
            'in_stock_products': products.filter(in_stock=True).count(),
            'products': serializer.data
        })


class WebsitePageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing website pages (view, edit, delete)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return WebsitePageDetailSerializer
        elif self.action in ['update', 'partial_update']:
            from .serializers import WebsitePageUpdateSerializer
            return WebsitePageUpdateSerializer
        return WebsitePageSerializer
    
    def get_queryset(self):
        """Filter to user's pages only"""
        queryset = WebsitePage.objects.filter(
            website__user=self.request.user
        ).select_related('website').order_by('-crawled_at')
        
        # Filter by website if specified
        website_id = self.request.query_params.get('website', None)
        if website_id:
            queryset = queryset.filter(website_id=website_id)
        
        # Filter by processing status if specified
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(processing_status=status)
        
        return queryset
    
    def update(self, request, *args, **kwargs):
        """Update a website page"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Store original data for comparison
        original_content = instance.cleaned_content
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Save the updated page
        updated_page = serializer.save()
        
        # Check if content was significantly changed (for potential Q&A regeneration)
        content_changed = False
        if 'cleaned_content' in serializer.validated_data:
            new_content = serializer.validated_data['cleaned_content']
            # Simple content change detection
            if len(new_content) != len(original_content) or new_content != original_content:
                content_changed = True
        
        # Return detailed response
        response_serializer = WebsitePageDetailSerializer(updated_page)
        response_data = {
            'success': True,
            'message': 'Page updated successfully',
            'page': response_serializer.data,
            'content_changed': content_changed
        }
        
        if content_changed:
            response_data['note'] = 'Content was changed. You may want to regenerate Q&A pairs for this page.'
            response_data['regenerate_qa_url'] = f'/api/v1/web-knowledge/manual-qa-generation/'
        
        return Response(response_data)
    
    @swagger_auto_schema(
        operation_description="Delete a website page and all its Q&A pairs",
        responses={
            200: openapi.Response(
                description="Page deleted successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Page \"Example Page\" and 5 Q&A pairs deleted successfully",
                        "deleted_data": {
                            "page": {
                                "id": "f952823c-22c9-46a7-b661-75ef37d015e9",
                                "title": "Example Page",
                                "url": "https://example.com/page",
                                "qa_pairs_count": 5
                            },
                            "qa_pairs_deleted": 5
                        }
                    }
                }
            ),
            404: openapi.Response(
                description="Page not found",
                examples={
                    "application/json": {
                        "detail": "Not found."
                    }
                }
            ),
            403: openapi.Response(
                description="Permission denied - you can only delete your own pages",
                examples={
                    "application/json": {
                        "detail": "You do not have permission to perform this action."
                    }
                }
            )
        },
        tags=['Web Knowledge - Pages']
    )
    def destroy(self, request, *args, **kwargs):
        """Delete a website page and its Q&A pairs"""
        page = self.get_object()
        
        # Collect statistics before deletion
        qa_pairs_count = page.qa_pairs.count()
        
        page_data = {
            'id': str(page.id),
            'title': page.title,
            'url': page.url,
            'qa_pairs_count': qa_pairs_count
        }
        
        # Delete the page (cascades to Q&A pairs)
        page.delete()
        
        return Response({
            'success': True,
            'message': f'Page "{page_data["title"]}" and {qa_pairs_count} Q&A pairs deleted successfully',
            'deleted_data': {
                'page': page_data,
                'qa_pairs_deleted': qa_pairs_count
            }
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Regenerate Q&A pairs for this page",
        responses={200: "Q&A regeneration started"}
    )
    @action(detail=True, methods=['post'])
    def regenerate_qa(self, request, pk=None):
        """Regenerate Q&A pairs for a specific page"""
        page = self.get_object()
        
        # Delete existing Q&A pairs
        existing_qa_count = page.qa_pairs.count()
        page.qa_pairs.all().delete()
        
        # Generate new Q&A pairs using manual generation
        from .tasks import _generate_fallback_qa_pairs
        qa_pairs_data = _generate_fallback_qa_pairs(page, 5)
        
        # Save new Q&A pairs
        created_count = 0
        for qa_data in qa_pairs_data:
            QAPair.objects.create(
                page=page,
                question=qa_data['question'],
                answer=qa_data['answer'],
                context=qa_data.get('context', ''),
                confidence_score=qa_data.get('confidence', 0.8),
                question_type=qa_data.get('question_type', 'factual'),
                category=qa_data.get('category', 'general'),
                keywords=qa_data.get('keywords', []),
                created_by_ai=qa_data.get('created_by_ai', False),
                generation_status='completed'
            )
            created_count += 1
        
        return Response({
            'success': True,
            'message': f'Q&A pairs regenerated for page "{page.title}"',
            'page_id': str(page.id),
            'page_title': page.title,
            'old_qa_pairs_deleted': existing_qa_count,
            'new_qa_pairs_created': created_count
        })
    
    @swagger_auto_schema(
        operation_description="Update the summary field for this page",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'summary': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='New summary for the page'
                )
            },
            required=['summary']
        ),
        responses={200: "Summary updated successfully"}
    )
    @action(detail=True, methods=['patch'])
    def update_summary(self, request, pk=None):
        """Update only the summary field for a specific page"""
        page = self.get_object()
        
        # Get the new summary from request data
        new_summary = request.data.get('summary', '')
        
        if 'summary' not in request.data:
            return Response({
                'success': False,
                'error': 'summary field is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Store old summary for comparison
        old_summary = page.summary
        
        # Update the summary
        page.summary = new_summary
        page.save(update_fields=['summary', 'updated_at'])
        
        # Return detailed response
        response_data = {
            'success': True,
            'message': 'Page summary updated successfully',
            'page_id': str(page.id),
            'page_title': page.title,
            'page_url': page.url,
            'old_summary': old_summary,
            'new_summary': new_summary,
            'summary_changed': old_summary != new_summary,
            'updated_at': page.updated_at
        }
        
        return Response(response_data)


class QAPairViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Q&A pairs with full CRUD operations
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            from .serializers import QAPairCreateSerializer
            return QAPairCreateSerializer
        return QAPairSerializer
    
    def get_queryset(self):
        """Filter to user's Q&A pairs only with advanced filtering"""
        # Filter Q&A pairs that belong to user (either through page->website or directly by user)
        from django.db.models import Q
        queryset = QAPair.objects.filter(
            Q(page__website__user=self.request.user) | Q(user=self.request.user),
            generation_status='completed'
        ).select_related('page', 'page__website').order_by('-confidence_score', '-created_at')
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by question type
        question_type = self.request.query_params.get('question_type', None)
        if question_type:
            queryset = queryset.filter(question_type=question_type)
        
        # Filter by website
        website_id = self.request.query_params.get('website', None)
        if website_id:
            queryset = queryset.filter(page__website_id=website_id)
        
        # Filter by approval status
        approved_only = self.request.query_params.get('approved_only', None)
        if approved_only and approved_only.lower() == 'true':
            queryset = queryset.filter(is_approved=True)
        
        # Filter by AI or manual creation
        created_by = self.request.query_params.get('created_by', None)
        if created_by == 'ai':
            queryset = queryset.filter(created_by_ai=True)
        elif created_by == 'manual':
            queryset = queryset.filter(created_by_ai=False)
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Increment view count when retrieving a Q&A pair"""
        instance = self.get_object()
        instance.increment_view_count()
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Toggle featured status of Q&A pair",
        responses={200: "Featured status updated"}
    )
    @action(detail=True, methods=['post'])
    def toggle_featured(self, request, pk=None):
        """Toggle featured status of a Q&A pair"""
        qa_pair = self.get_object()
        qa_pair.is_featured = not qa_pair.is_featured
        qa_pair.save(update_fields=['is_featured'])
        
        return Response({
            'success': True,
            'message': 'Featured status updated',
            'is_featured': qa_pair.is_featured
        })
    
    @swagger_auto_schema(
        operation_description="Toggle approval status of Q&A pair",
        responses={200: "Approval status updated"}
    )
    @action(detail=True, methods=['post'])
    def toggle_approval(self, request, pk=None):
        """Toggle approval status of a Q&A pair"""
        qa_pair = self.get_object()
        qa_pair.is_approved = not qa_pair.is_approved
        qa_pair.save(update_fields=['is_approved'])
        
        return Response({
            'success': True,
            'message': 'Approval status updated',
            'is_approved': qa_pair.is_approved
        })
    
    @swagger_auto_schema(
        operation_description="Get Q&A pairs by category",
        responses={200: QAPairSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get Q&A pairs grouped by category"""
        categories = QAPair.objects.filter(
            page__website__user=request.user,
            generation_status='completed',
            is_approved=True
        ).values_list('category', flat=True).distinct()
        
        result = {}
        for category in categories:
            qa_pairs = self.get_queryset().filter(category=category)[:10]
            result[category] = QAPairSerializer(qa_pairs, many=True).data
        
        return Response(result)
    
    def destroy(self, request, *args, **kwargs):
        """Delete a Q&A pair"""
        qa_pair = self.get_object()
        
        qa_data = {
            'id': str(qa_pair.id),
            'question': qa_pair.question,
            'page_title': qa_pair.page.title,
            'website_name': qa_pair.page.website.name
        }
        
        # Delete the Q&A pair
        qa_pair.delete()
        
        return Response({
            'success': True,
            'message': f'Q&A pair deleted successfully',
            'deleted_qa': qa_data
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Bulk delete Q&A pairs",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'qa_pair_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description='List of Q&A pair IDs to delete'
                )
            },
            required=['qa_pair_ids']
        ),
        responses={200: "Q&A pairs deleted successfully"}
    )
    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """Bulk delete Q&A pairs"""
        qa_pair_ids = request.data.get('qa_pair_ids', [])
        
        if not qa_pair_ids:
            return Response({
                'error': 'qa_pair_ids is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get Q&A pairs that belong to the user
        qa_pairs = QAPair.objects.filter(
            id__in=qa_pair_ids,
            page__website__user=request.user
        )
        
        if not qa_pairs.exists():
            return Response({
                'error': 'No Q&A pairs found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Collect information before deletion
        deleted_qa_info = []
        for qa_pair in qa_pairs:
            deleted_qa_info.append({
                'id': str(qa_pair.id),
                'question': qa_pair.question,
                'page_title': qa_pair.page.title,
                'website_name': qa_pair.page.website.name
            })
        
        # Delete the Q&A pairs
        deleted_count = qa_pairs.count()
        qa_pairs.delete()
        
        return Response({
            'success': True,
            'message': f'{deleted_count} Q&A pairs deleted successfully',
            'deleted_count': deleted_count,
            'deleted_qa_pairs': deleted_qa_info
        })


class ManualQAGenerationAPIView(APIView):
    """
    API view for manually triggering Q&A generation (for debugging)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Manually trigger Q&A generation for specific pages (debugging)",
        responses={200: "Q&A generation triggered"}
    )
    def post(self, request):
        """Manually trigger Q&A generation for debugging"""
        from .tasks import _generate_fallback_qa_pairs
        
        page_id = request.data.get('page_id')
        website_id = request.data.get('website_id')
        
        if not page_id and not website_id:
            return Response({
                'error': 'Either page_id or website_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            created_qa_pairs = []
            
            if page_id:
                # Generate Q&A for specific page
                page = WebsitePage.objects.get(id=page_id, website__user=request.user)
                qa_pairs_data = _generate_fallback_qa_pairs(page, 5)
                
                for qa_data in qa_pairs_data:
                    # Check if Q&A with same or similar question already exists for this website
                    existing_qa = QAPair.objects.filter(
                        page__website=page.website,
                        question=qa_data['question']
                    ).first()
                    
                    if not existing_qa:
                        qa_pair = QAPair.objects.create(
                            page=page,
                            question=qa_data['question'],
                            answer=qa_data['answer'],
                            context=qa_data.get('context', ''),
                            confidence_score=qa_data.get('confidence', 0.8),
                            question_type=qa_data.get('question_type', 'factual'),
                            category=qa_data.get('category', 'general'),
                            keywords=qa_data.get('keywords', []),
                            created_by_ai=qa_data.get('created_by_ai', False),
                            generation_status='completed'
                        )
                        created_qa_pairs.append({
                            'id': str(qa_pair.id),
                            'question': qa_pair.question,
                            'answer': qa_pair.answer[:100] + '...',
                            'category': qa_pair.category
                        })
                
                return Response({
                    'success': True,
                    'message': f'Created {len(created_qa_pairs)} Q&A pairs for page',
                    'page_id': str(page.id),
                    'page_title': page.title,
                    'qa_pairs': created_qa_pairs
                })
            
            elif website_id:
                # Generate Q&A for all pages in website
                website = WebsiteSource.objects.get(id=website_id, user=request.user)
                pages = website.pages.filter(processing_status='completed')
                
                total_created = 0
                pages_processed = []
                
                for page in pages:
                    qa_pairs_data = _generate_fallback_qa_pairs(page, 3)
                    page_qa_count = 0
                    
                    for qa_data in qa_pairs_data:
                        # Check if Q&A with same or similar question already exists for this website
                        existing_qa = QAPair.objects.filter(
                            page__website=page.website,
                            question=qa_data['question']
                        ).first()
                        
                        if not existing_qa:
                            qa_pair = QAPair.objects.create(
                                page=page,
                                question=qa_data['question'],
                                answer=qa_data['answer'],
                                context=qa_data.get('context', ''),
                                confidence_score=qa_data.get('confidence', 0.8),
                                question_type=qa_data.get('question_type', 'factual'),
                                category=qa_data.get('category', 'general'),
                                keywords=qa_data.get('keywords', []),
                                created_by_ai=qa_data.get('created_by_ai', False),
                                generation_status='completed'
                            )
                            page_qa_count += 1
                            total_created += 1
                    
                    pages_processed.append({
                        'page_id': str(page.id),
                        'page_title': page.title,
                        'qa_pairs_created': page_qa_count
                    })
                
                return Response({
                    'success': True,
                    'message': f'Created {total_created} Q&A pairs for {len(pages)} pages',
                    'website_id': str(website.id),
                    'website_name': website.name,
                    'total_qa_pairs_created': total_created,
                    'pages_processed': pages_processed
                })
            
        except (WebsitePage.DoesNotExist, WebsiteSource.DoesNotExist):
            return Response({
                'error': 'Page or website not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in manual Q&A generation: {str(e)}")
            return Response({
                'error': 'Failed to generate Q&A pairs',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EnhancedQAGenerationAPIView(APIView):
    """
    API view for enhanced bulk Q&A generation with categories
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Generate comprehensive Q&A pairs for a website with categories",
        request_body=QAPairBulkCreateSerializer,
        responses={200: "Enhanced Q&A generation started"}
    )
    def post(self, request):
        """Start enhanced Q&A generation for a website"""
        from .serializers import QAPairBulkCreateSerializer
        
        serializer = QAPairBulkCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        website_id = serializer.validated_data['website_id']
        max_qa_per_page = serializer.validated_data['max_qa_per_page']
        categories = serializer.validated_data['categories']
        question_types = serializer.validated_data['question_types']
        
        try:
            website = WebsiteSource.objects.get(id=website_id, user=request.user)
            
            # Get pages that need enhanced Q&A generation
            pages_needing_qa = website.pages.filter(
                processing_status='completed',
                word_count__gte=100
            )
            
            if not pages_needing_qa.exists():
                return Response({
                    'message': 'No pages available for Q&A generation',
                    'pages_processed': 0
                })
            
            # Queue enhanced Q&A generation tasks
            from .tasks import generate_enhanced_qa_pairs_task
            task_ids = []
            
            for page in pages_needing_qa:
                task = generate_enhanced_qa_pairs_task.delay(
                    str(page.id), 
                    max_qa_per_page,
                    categories,
                    question_types
                )
                task_ids.append(task.id)
            
            return Response({
                'success': True,
                'message': f'Enhanced Q&A generation started for {len(task_ids)} pages',
                'task_ids': task_ids,
                'pages_queued': len(task_ids),
                'categories': categories,
                'question_types': question_types,
                'max_qa_per_page': max_qa_per_page
            })
            
        except WebsiteSource.DoesNotExist:
            return Response(
                {'error': 'Website not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error in enhanced Q&A generation: {str(e)}")
            return Response(
                {'error': 'Failed to start enhanced Q&A generation'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QASearchAPIView(APIView):
    """
    API view for searching Q&A pairs
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Search Q&A pairs",
        request_body=QASearchSerializer,
        responses={200: QAPairSerializer(many=True)}
    )
    def post(self, request):
        """Search Q&A pairs based on query"""
        serializer = QASearchSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        query = serializer.validated_data['query']
        website_id = serializer.validated_data.get('website_id')
        limit = serializer.validated_data['limit']
        include_context = serializer.validated_data['include_context']
        
        # Build base queryset
        queryset = QAPair.objects.filter(
            page__website__user=request.user,
            generation_status='completed'
        )
        
        # Filter by website if specified
        if website_id:
            queryset = queryset.filter(page__website_id=website_id)
        
        # Search in questions and answers
        search_filter = (
            Q(question__icontains=query) |
            Q(answer__icontains=query) |
            Q(context__icontains=query) if include_context else 
            Q(question__icontains=query) | Q(answer__icontains=query)
        )
        
        queryset = queryset.filter(search_filter).select_related(
            'page', 'page__website'
        ).order_by('-confidence_score', '-created_at')[:limit]
        
        serializer = QAPairSerializer(queryset, many=True)
        return Response(serializer.data)


class PartialQACreateAPIView(APIView):
    """
    API view for creating Q&A pairs without requiring page and context
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Create Q&A pair without requiring page/context",
        request_body=QAPairPartialCreateSerializer,
        responses={201: QAPairSerializer}
    )
    def post(self, request):
        """Create a Q&A pair with minimal requirements"""
        serializer = QAPairPartialCreateSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            qa_pair = serializer.save()
            
            # Return complete Q&A data
            response_serializer = QAPairSerializer(qa_pair)
            return Response({
                'success': True,
                'message': 'Q&A pair created successfully',
                'qa_pair': response_serializer.data,
                'id': str(qa_pair.id)
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing products and services
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ProductCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProductUpdateSerializer
        return ProductSerializer
    
    def get_queryset(self):
        """Filter to user's products only with comprehensive filtering"""
        # Return empty queryset for unauthenticated users (e.g., Swagger schema generation)
        if not self.request.user.is_authenticated:
            return Product.objects.none()
        
        queryset = Product.objects.filter(user=self.request.user).select_related(
            'source_website', 'source_page'
        ).order_by('-created_at')
        
        # Filter by product type
        product_type = self.request.query_params.get('product_type', None)
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Filter by in stock status
        in_stock = self.request.query_params.get('in_stock', None)
        if in_stock is not None:
            in_stock_bool = in_stock.lower() == 'true'
            queryset = queryset.filter(in_stock=in_stock_bool)
        
        # Filter by extraction method
        extraction_method = self.request.query_params.get('extraction_method', None)
        if extraction_method:
            queryset = queryset.filter(extraction_method=extraction_method)
        
        # Filter by source website
        website_id = self.request.query_params.get('website_id', None)
        if website_id:
            queryset = queryset.filter(source_website_id=website_id)
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category__icontains=category)
        
        # Filter by brand
        brand = self.request.query_params.get('brand', None)
        if brand:
            queryset = queryset.filter(brand__icontains=brand)
        
        # Filter by currency
        currency = self.request.query_params.get('currency', None)
        if currency:
            queryset = queryset.filter(currency=currency)
        
        # Filter by billing period
        billing_period = self.request.query_params.get('billing_period', None)
        if billing_period:
            queryset = queryset.filter(billing_period=billing_period)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price', None)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        
        max_price = self.request.query_params.get('max_price', None)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Filter products with discounts
        has_discount = self.request.query_params.get('has_discount', None)
        if has_discount and has_discount.lower() == 'true':
            queryset = queryset.filter(
                Q(discount_percentage__isnull=False, discount_percentage__gt=0) |
                Q(discount_amount__isnull=False, discount_amount__gt=0)
            )
        
        # Search by title, description, or keywords
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(short_description__icontains=search) |
                Q(category__icontains=search) |
                Q(brand__icontains=search)
            )
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create a new product"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save()
            
            # Return complete product data
            response_serializer = ProductSerializer(product)
            return Response({
                'success': True,
                'message': 'Product created successfully',
                'product': response_serializer.data,
                'id': str(product.id)
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Update a product"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Save the updated product
        updated_product = serializer.save()
        
        # Return detailed response
        response_serializer = ProductSerializer(updated_product)
        return Response({
            'success': True,
            'message': 'Product updated successfully',
            'product': response_serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Delete a product"""
        product = self.get_object()
        
        product_data = {
            'id': str(product.id),
            'title': product.title,
            'product_type': product.product_type
        }
        
        # Delete the product
        product.delete()
        
        return Response({
            'success': True,
            'message': f'Product "{product_data["title"]}" deleted successfully',
            'deleted_product': product_data
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Get product type choices",
        responses={200: "List of product type choices"}
    )
    @action(detail=False, methods=['get'], url_path='choices/product-types')
    def product_types(self, request):
        """Get available product types"""
        types = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in Product.PRODUCT_TYPE_CHOICES
        ]
        return Response({
            'product_types': types
        })
    
    @swagger_auto_schema(
        operation_description="Get currency choices",
        responses={200: "List of currency choices"}
    )
    @action(detail=False, methods=['get'], url_path='choices/currencies')
    def currencies(self, request):
        """Get available currencies"""
        currencies = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in Product.CURRENCY_CHOICES
        ]
        return Response({
            'currencies': currencies
        })
    
    @swagger_auto_schema(
        operation_description="Get billing period choices",
        responses={200: "List of billing period choices"}
    )
    @action(detail=False, methods=['get'], url_path='choices/billing-periods')
    def billing_periods(self, request):
        """Get available billing periods"""
        periods = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in Product.BILLING_PERIOD_CHOICES
        ]
        return Response({
            'billing_periods': periods
        })
    
    @swagger_auto_schema(
        operation_description="Get extraction method choices",
        responses={200: "List of extraction method choices"}
    )
    @action(detail=False, methods=['get'], url_path='choices/extraction-methods')
    def extraction_methods(self, request):
        """Get available extraction methods"""
        methods = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in Product.EXTRACTION_METHOD_CHOICES
        ]
        return Response({
            'extraction_methods': methods
        })
    
    @swagger_auto_schema(
        operation_description="Get all available choices for dropdowns",
        responses={200: "All choices data"}
    )
    @action(detail=False, methods=['get'], url_path='choices/all')
    def all_choices(self, request):
        """Get all available choices for frontend dropdowns"""
        return Response({
            'product_types': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in Product.PRODUCT_TYPE_CHOICES
            ],
            'currencies': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in Product.CURRENCY_CHOICES
            ],
            'billing_periods': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in Product.BILLING_PERIOD_CHOICES
            ],
            'extraction_methods': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in Product.EXTRACTION_METHOD_CHOICES
            ]
        })
    
    @swagger_auto_schema(
        operation_description="Get products statistics",
        responses={200: "Statistics data"}
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get comprehensive products statistics"""
        queryset = self.get_queryset()
        
        stats = {
            'total_products': queryset.count(),
            'active_products': queryset.filter(is_active=True).count(),
            'in_stock_products': queryset.filter(in_stock=True).count(),
            'by_type': list(queryset.values('product_type').annotate(
                count=Count('id')
            ).order_by('-count')),
            'by_extraction_method': list(queryset.values('extraction_method').annotate(
                count=Count('id')
            ).order_by('-count')),
            'by_currency': list(queryset.values('currency').annotate(
                count=Count('id')
            ).order_by('-count')),
            'with_links': queryset.exclude(link='').count(),
            'with_prices': queryset.exclude(price__isnull=True).count(),
            'with_discounts': queryset.filter(
                Q(discount_percentage__isnull=False, discount_percentage__gt=0) |
                Q(discount_amount__isnull=False, discount_amount__gt=0)
            ).count(),
            'auto_extracted': queryset.filter(extraction_method__in=['ai_auto', 'ai_assisted']).count(),
            'manual': queryset.filter(extraction_method='manual').count(),
            'recent_products': ProductCompactSerializer(
                queryset[:5], many=True
            ).data
        }
        
        return Response(stats)
    
    @swagger_auto_schema(
        operation_description="Get products by website source",
        responses={200: ProductSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='by-website')
    def by_website(self, request):
        """Get products grouped by website source"""
        website_id = request.query_params.get('website_id')
        
        if not website_id:
            return Response({
                'error': 'website_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify website belongs to user
        try:
            website = WebsiteSource.objects.get(id=website_id, user=request.user)
        except WebsiteSource.DoesNotExist:
            return Response({
                'error': 'Website not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get products from this website
        products = Product.objects.filter(
            user=request.user,
            source_website=website
        ).select_related('source_page').order_by('-created_at')
        
        serializer = ProductSerializer(products, many=True)
        
        return Response({
            'website_id': str(website.id),
            'website_name': website.name,
            'website_url': website.url,
            'total_products': products.count(),
            'products': serializer.data
        })
    
    @swagger_auto_schema(
        operation_description="Get unique categories from user's products",
        responses={200: "List of categories"}
    )
    @action(detail=False, methods=['get'], url_path='categories')
    def categories(self, request):
        """Get unique categories from user's products"""
        categories = Product.objects.filter(
            user=request.user,
            category__isnull=False
        ).exclude(category='').values_list('category', flat=True).distinct()
        
        return Response({
            'categories': sorted(list(categories))
        })
    
    @swagger_auto_schema(
        operation_description="Get unique brands from user's products",
        responses={200: "List of brands"}
    )
    @action(detail=False, methods=['get'], url_path='brands')
    def brands(self, request):
        """Get unique brands from user's products"""
        brands = Product.objects.filter(
            user=request.user,
            brand__isnull=False
        ).exclude(brand='').values_list('brand', flat=True).distinct()
        
        return Response({
            'brands': sorted(list(brands))
        })
    
    @swagger_auto_schema(
        operation_description="Bulk update products (activation, stock status, etc.)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'product_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description='List of product IDs to update'
                ),
                'is_active': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Set active status (optional)'
                ),
                'in_stock': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Set stock status (optional)'
                ),
            },
            required=['product_ids']
        ),
        responses={200: "Products updated successfully"}
    )
    @action(detail=False, methods=['post'], url_path='bulk-update')
    def bulk_update(self, request):
        """Bulk update products"""
        product_ids = request.data.get('product_ids', [])
        
        if not product_ids:
            return Response({
                'error': 'product_ids is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get products that belong to the user
        products = Product.objects.filter(
            id__in=product_ids,
            user=request.user
        )
        
        if not products.exists():
            return Response({
                'error': 'No products found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Update fields if provided
        update_fields = []
        
        if 'is_active' in request.data:
            products.update(is_active=request.data['is_active'])
            update_fields.append('is_active')
        
        if 'in_stock' in request.data:
            products.update(in_stock=request.data['in_stock'])
            update_fields.append('in_stock')
        
        return Response({
            'success': True,
            'message': f'{products.count()} products updated successfully',
            'updated_count': products.count(),
            'updated_fields': update_fields
        })
    
    @swagger_auto_schema(
        operation_description="Bulk delete products",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'product_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description='List of product IDs to delete'
                )
            },
            required=['product_ids']
        ),
        responses={200: "Products deleted successfully"}
    )
    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, request):
        """Bulk delete products"""
        product_ids = request.data.get('product_ids', [])
        
        if not product_ids:
            return Response({
                'error': 'product_ids is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get products that belong to the user
        products = Product.objects.filter(
            id__in=product_ids,
            user=request.user
        )
        
        if not products.exists():
            return Response({
                'error': 'No products found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Collect information before deletion
        deleted_count = products.count()
        deleted_info = list(products.values('id', 'title', 'product_type'))
        
        # Delete the products
        products.delete()
        
        return Response({
            'success': True,
            'message': f'{deleted_count} products deleted successfully',
            'deleted_count': deleted_count,
            'deleted_products': deleted_info
        })


class PageSummaryUpdateAPIView(APIView):
    """
    API view for updating page summaries
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Update page summary by page ID or URL",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'page_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Page ID (UUID)'
                ),
                'page_url': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Page URL (alternative to page_id)'
                ),
                'website_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Website ID (required if using page_url)'
                ),
                'summary': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='New summary for the page'
                )
            },
            required=['summary']
        ),
        responses={
            200: openapi.Response(
                description="Summary updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'page_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'old_summary': openapi.Schema(type=openapi.TYPE_STRING),
                        'new_summary': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: openapi.Response(description="Bad request"),
            404: openapi.Response(description="Page not found"),
        }
    )
    def patch(self, request):
        """
        Update page summary by page ID or URL
        """
        page_id = request.data.get('page_id')
        page_url = request.data.get('page_url')
        website_id = request.data.get('website_id')
        new_summary = request.data.get('summary')
        
        # Validate required fields
        if not new_summary and 'summary' not in request.data:
            return Response({
                'success': False,
                'error': 'summary field is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not page_id and not page_url:
            return Response({
                'success': False,
                'error': 'Either page_id or page_url is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if page_url and not website_id:
            return Response({
                'success': False,
                'error': 'website_id is required when using page_url'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Find the page
            if page_id:
                page = WebsitePage.objects.get(
                    id=page_id,
                    website__user=request.user
                )
            else:
                page = WebsitePage.objects.get(
                    url=page_url,
                    website_id=website_id,
                    website__user=request.user
                )
            
            # Store old summary for comparison
            old_summary = page.summary
            
            # Update the summary
            page.summary = new_summary if new_summary is not None else ''
            page.save(update_fields=['summary', 'updated_at'])
            
            return Response({
                'success': True,
                'message': 'Page summary updated successfully',
                'page_id': str(page.id),
                'page_title': page.title,
                'page_url': page.url,
                'website_name': page.website.name,
                'old_summary': old_summary,
                'new_summary': page.summary,
                'summary_changed': old_summary != page.summary,
                'updated_at': page.updated_at
            })
            
        except WebsitePage.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Page not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating page summary: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to update summary',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class GeneratePromptAsyncAPIView(APIView):
    """
    API endpoint for generating AI prompts asynchronously with status tracking
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'manual_prompt': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Manual prompt to enhance for chat answering'
                )
            },
            required=['manual_prompt']
        ),
        responses={
            202: openapi.Response(
                description="Generation started successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'task_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'status_url': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: openapi.Response(description="Bad request"),
        },
        operation_description="Start async AI prompt generation (returns immediately with task_id)"
    )
    def post(self, request):
        """
        Start async prompt generation (returns immediately)
        Frontend should poll status_url to check progress
        """
        try:
            # Get manual_prompt from request
            manual_prompt = request.data.get('manual_prompt', '').strip()
            
            if not manual_prompt:
                return Response({
                    'success': False,
                    'message': 'manual_prompt is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Start async task
            from .tasks import generate_prompt_async_task
            task = generate_prompt_async_task.delay(request.user.id, manual_prompt)
            
            # Store initial status in cache
            from django.core.cache import cache
            cache.set(f'prompt_generation_{task.id}', {
                'status': 'queued',
                'progress': 0,
                'message': 'Task queued, waiting to start...',
                'created_at': timezone.now().isoformat()
            }, timeout=600)
            
            logger.info(f"Started async prompt generation task {task.id} for user {request.user.username}")
            
            return Response({
                'success': True,
                'task_id': task.id,
                'status': 'queued',
                'message': 'Prompt generation started. Use task_id to check status.',
                'status_url': f'/api/v1/web-knowledge/generate-prompt-async/status/{task.id}/'
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            logger.error(f"Error starting async prompt generation: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Failed to start prompt generation',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GeneratePromptStatusAPIView(APIView):
    """
    API endpoint to check status of async prompt generation
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Check status of async prompt generation",
        responses={
            200: openapi.Response(
                description="Status information",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Status: queued, processing, completed, failed'
                        ),
                        'progress': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description='Progress percentage (0-100)'
                        ),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'prompt': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Generated prompt (only when completed)'
                        ),
                        'generated_by_ai': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Error message (only when failed)'
                        ),
                    }
                )
            ),
            404: openapi.Response(description="Task not found"),
        }
    )
    def get(self, request, task_id):
        """
        Get status of prompt generation task
        
        Response statuses:
        - queued: Task is waiting to start
        - processing: AI is generating the prompt
        - completed: Generation finished successfully
        - failed: Generation failed
        """
        try:
            from django.core.cache import cache
            
            # Get status from cache
            status_data = cache.get(f'prompt_generation_{task_id}')
            
            if not status_data:
                # Check if task exists
                from celery.result import AsyncResult
                task = AsyncResult(task_id)
                
                if task.state == 'PENDING':
                    return Response({
                        'status': 'not_found',
                        'message': 'Task not found. It may have expired or never existed.'
                    }, status=status.HTTP_404_NOT_FOUND)
                elif task.state == 'FAILURE':
                    return Response({
                        'status': 'failed',
                        'progress': 100,
                        'message': 'Task failed',
                        'error': str(task.info)
                    })
                else:
                    return Response({
                        'status': task.state.lower(),
                        'progress': 0,
                        'message': f'Task state: {task.state}'
                    })
            
            return Response(status_data)
            
        except Exception as e:
            logger.error(f"Error checking prompt generation status: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to check status',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GeneratePromptAPIView(APIView):
    """
    API endpoint for generating AI prompts based on manual_prompt and business_type (SYNCHRONOUS)
    For async generation with progress tracking, use GeneratePromptAsyncAPIView instead
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'manual_prompt': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Manual prompt to enhance for chat answering'
                )
            },
            required=['manual_prompt']
        ),
        responses={
            200: openapi.Response(
                description="Prompt generated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'prompt': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'generated_by_ai': openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            description='Indicates if prompt was generated by AI (true) or using fallback (false)'
                        ),
                        'warning': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Warning message if AI generation failed (optional)'
                        ),
                    }
                )
            ),
            400: openapi.Response(description="Bad request"),
            500: openapi.Response(description="Server error")
        },
        operation_description="Generate enhanced chat prompt based on manual_prompt and user's business_type"
    )
    def post(self, request):
        """
        Generate enhanced prompt for chat answering based on manual_prompt and business_type
        """
        try:
            # Get manual_prompt from request
            manual_prompt = request.data.get('manual_prompt', '').strip()
            
            if not manual_prompt:
                return Response({
                    'success': False,
                    'message': 'manual_prompt is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = request.user
            business_type = user.business_type if hasattr(user, 'business_type') else None
            
            # Find matching BusinessPrompt based on business_type
            business_prompt_obj = None
            if business_type:
                business_prompt_obj = BusinessPrompt.objects.filter(
                    name__iexact=business_type.strip()
                ).first()
            
            # ✅ NEW: Check tokens BEFORE AI generation
            try:
                subscription = request.user.subscription
                
                if not subscription.is_subscription_active():
                    logger.warning(f"User {request.user.username} subscription not active for prompt enhancement")
                    return Response({
                        'success': False,
                        'message': 'Subscription is not active',
                        'error': 'Please renew your subscription to use AI prompt enhancement'
                    }, status=status.HTTP_402_PAYMENT_REQUIRED)
                
                # Estimate tokens needed (prompt enhancement usually ~500-1000 tokens)
                estimated_tokens = 700
                if subscription.tokens_remaining < estimated_tokens:
                    logger.warning(
                        f"User {request.user.username} has insufficient tokens for prompt enhancement. "
                        f"Need: {estimated_tokens}, Available: {subscription.tokens_remaining}"
                    )
                    return Response({
                        'success': False,
                        'message': 'Insufficient tokens',
                        'error': f'You need at least {estimated_tokens} tokens for prompt enhancement. Available: {subscription.tokens_remaining}',
                        'tokens_remaining': subscription.tokens_remaining
                    }, status=status.HTTP_402_PAYMENT_REQUIRED)
                
                logger.info(f"Token pre-check passed for prompt enhancement (user: {request.user.username})")
                    
            except Exception as token_check_error:
                logger.error(f"Token pre-check failed for prompt enhancement: {token_check_error}")
                # Continue with fallback (without AI) instead of failing
            
            # Use AI to rewrite and improve the manual_prompt based on business_type.prompt
            try:
                # ✅ Setup proxy BEFORE importing Gemini (required for Iran servers)
                from core.utils import setup_ai_proxy
                setup_ai_proxy()
                
                import google.generativeai as genai
                from AI_model.services.gemini_service import get_gemini_api_key
                from AI_model.models import AIGlobalConfig
                
                api_key = get_gemini_api_key()
                if not api_key:
                    raise ValueError("Gemini API key not configured")
                
                genai.configure(api_key=api_key)
                
                # Use Pro model for high-quality prompt generation
                model_name = 'gemini-2.5-pro'
                
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config={
                        'temperature': 0.7,
                        'max_output_tokens': 3000,
                    }
                )
                
                # Build instruction for AI based on BusinessPrompt.prompt (dynamic per business type)
                if business_prompt_obj and business_prompt_obj.prompt:
                    # Use dynamic business prompt template
                    instruction = f"""{business_prompt_obj.prompt}

---

## User's Raw Input:
{manual_prompt}

---

## Your Task:
Transform the user's raw input above into a complete, professional, and structured Manual Prompt following the guidelines and format specified in the business prompt template above.

Output ONLY the final structured Manual Prompt.
Do NOT add any explanations or comments outside the prompt structure.
Ensure all information from the user's input is preserved and properly formatted."""
                else:
                    # Fallback if no business prompt is set
                    instruction = f"""You are an AI assistant helping to create a professional manual prompt for a {business_type or 'business'}.

User's Input:
{manual_prompt}

Task: Rewrite and improve the user's input into a professional, clear, and well-structured manual prompt ready for an AI assistant. Keep all important details (contact info, addresses, services, etc.) but make it professional, organized, and concise.

Output ONLY the improved prompt, nothing else."""
                
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
                
                # Generate improved prompt with AI and safety settings
                response = model.generate_content(
                    instruction,
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
                try:
                    from AI_model.services.usage_tracker import track_ai_usage_safe
                    track_ai_usage_safe(
                        user=request.user,
                        section='prompt_generation',
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        response_time_ms=response_time_ms,
                        success=True,
                        model_name=model_name,
                        metadata={'business_type': business_type}
                    )
                    logger.info(f"✅ AI usage tracked for prompt generation (user: {request.user.username}, tokens: {prompt_tokens + completion_tokens})")
                except Exception as tracking_error:
                    logger.error(f"Failed to track AI usage for prompt generation: {tracking_error}")
                
                # ✅ Consume tokens for billing
                if response:
                    try:
                        actual_tokens = prompt_tokens + completion_tokens
                        if actual_tokens > 0:
                            from billing.services import consume_tokens_for_user
                            consume_tokens_for_user(
                                request.user,
                                actual_tokens,
                                description='Prompt enhancement (AI)'
                            )
                            logger.info(f"💰 Consumed {actual_tokens} tokens for prompt enhancement (user: {request.user.username})")
                    except Exception as token_error:
                        logger.error(f"Failed to consume tokens for prompt enhancement: {token_error}")
                
                if hasattr(response, 'text') and response.text:
                    enhanced_prompt = response.text.strip()
                else:
                    raise ValueError("No response from AI")
                
                return Response({
                    'success': True,
                    'prompt': enhanced_prompt,
                    'message': 'Prompt generated successfully using AI',
                    'generated_by_ai': True
                }, status=status.HTTP_200_OK)
                
            except Exception as ai_error:
                error_msg = str(ai_error)
                logger.error(f"AI generation failed: {error_msg}")
                
                # Track failed AI usage
                try:
                    from AI_model.services.usage_tracker import track_ai_usage_safe
                    track_ai_usage_safe(
                        user=request.user,
                        section='prompt_generation',
                        prompt_tokens=0,
                        completion_tokens=0,
                        response_time_ms=0,
                        success=False,
                        model_name='gemini-2.5-pro',
                        error_message=error_msg,
                        metadata={'business_type': business_type, 'error': error_msg}
                    )
                except Exception as tracking_error:
                    logger.error(f"Failed to track failed AI usage: {tracking_error}")
                
                # Fallback to simple combination if AI fails
                if business_prompt_obj and business_prompt_obj.prompt:
                    enhanced_prompt = f"""{business_prompt_obj.prompt}

{manual_prompt}"""
                else:
                    enhanced_prompt = manual_prompt
                
                return Response({
                    'success': True,
                    'prompt': enhanced_prompt,
                    'message': 'Prompt generated (AI unavailable, using fallback)',
                    'generated_by_ai': False,
                    'warning': 'AI generation failed, using simple combination'
                }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating prompt: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Failed to generate prompt',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)