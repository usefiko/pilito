from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from django.utils import timezone
from integrations.models import (
    IntegrationToken, WooCommerceEventLog,
    WordPressContent, WordPressContentEventLog
)
from integrations.backends.integration_auth import IntegrationTokenAuthentication
from integrations.serializers import (
    IntegrationTokenSerializer,
    IntegrationTokenCreateSerializer,
    WooCommerceEventLogSerializer,
    WooCommerceWebhookSerializer,
    WordPressContentSerializer,
    WordPressContentWebhookSerializer
)
from integrations.services import TokenGenerator, WooCommerceProcessor, WordPressContentProcessor
import logging
import time

logger = logging.getLogger(__name__)


class IntegrationTokenViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Integration Tokens
    
    list: Get tokens (admin: همه / user: خودش)
    retrieve: Get specific token
    create: Create new token (via generate action)
    destroy: Delete/deactivate token
    """
    permission_classes = [IsAuthenticated]
    serializer_class = IntegrationTokenSerializer
    queryset = IntegrationToken.objects.all().select_related('user')
    
    def get_queryset(self):
        """Admin can see all tokens, users can see only their own"""
        if self.request.user.is_staff:
            return self.queryset.order_by('-created_at')
        return self.queryset.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate new integration token
        
        POST /api/v1/integrations/tokens/generate/
        """
        serializer = IntegrationTokenCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Determine user (admin can create for others)
        user_id = serializer.validated_data.get('user_id')
        if user_id and request.user.is_staff:
            from accounts.models import User
            user = User.objects.get(id=user_id)
        else:
            user = request.user
        
        # Get integration type
        integration_type = serializer.validated_data.get('integration_type', 'woocommerce')
        
        # Generate token
        if integration_type == 'woocommerce':
            token_string = TokenGenerator.generate_woocommerce_token()
        elif integration_type == 'shopify':
            token_string = TokenGenerator.generate_shopify_token()
        else:
            return Response(
                {'error': 'Invalid integration type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token_preview = TokenGenerator.get_token_preview(token_string)
        
        # Create token
        token = IntegrationToken.objects.create(
            user=user,
            token=token_string,
            token_preview=token_preview,
            integration_type=integration_type,
            name=serializer.validated_data['name'],
            allowed_ips=serializer.validated_data.get('allowed_ips', []),
            expires_at=serializer.validated_data.get('expires_at')
        )
        
        logger.info(f"✅ Token created: {token.id} for user {user.email}")
        
        return Response({
            'id': str(token.id),
            'token': token_string,  # ⚠️ Shown only once!
            'token_preview': token_preview,
            'integration_type': integration_type,
            'name': token.name,
            'user': {
                'id': user.id,
                'email': user.email
            },
            'created_at': token.created_at,
            'message': '⚠️ این token فقط یکبار نمایش داده می‌شود. لطفاً آن را کپی کنید.'
        }, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete (deactivate) token"""
        token = self.get_object()
        token.is_active = False
        token.save(update_fields=['is_active'])
        
        logger.info(f"🗑️ Token deactivated: {token.id}")
        
        return Response({
            'message': 'Token deactivated successfully'
        }, status=status.HTTP_200_OK)


class WooCommerceWebhookView(APIView):
    """
    Receive WooCommerce webhook events
    
    POST /api/integrations/woocommerce/webhook/
    """
    authentication_classes = [IntegrationTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        start_time = time.time()
        
        # Validate payload
        serializer = WooCommerceWebhookSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        payload = serializer.validated_data
        event_id = payload['event_id']
        event_type = payload['event_type']
        product_data = payload['product']
        
        # Check for duplicate (idempotency)
        if WooCommerceEventLog.objects.filter(event_id=event_id).exists():
            logger.info(f"⏭️ Duplicate event skipped: {event_id}")
            return Response({
                'status': 'skipped',
                'message': 'این رویداد قبلاً پردازش شده است',
                'event_id': event_id
            }, status=status.HTTP_200_OK)
        
        # Get token from auth
        token = request.auth  # IntegrationToken instance
        
        # Create event log
        event_log = WooCommerceEventLog.objects.create(
            event_id=event_id,
            event_type=event_type,
            user=request.user,
            token=token,
            woo_product_id=product_data.get('id', 0),
            payload=request.data,
            source_ip=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        
        # Import task here to avoid circular import
        from integrations.tasks import process_woocommerce_product
        
        # Dispatch async task
        process_woocommerce_product.apply_async(
            args=[request.data, request.user.id, str(event_log.id)],
            countdown=2  # Small delay to batch rapid changes
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"✅ Event accepted: {event_type} for product {product_data.get('id')} "
            f"(user: {request.user.email}, time: {processing_time}ms)"
        )
        
        return Response({
            'status': 'accepted',
            'message': 'رویداد دریافت شد و در صف پردازش قرار گرفت',
            'event_id': event_id,
            'processing_time_ms': processing_time
        }, status=status.HTTP_202_ACCEPTED)
    
    def _get_client_ip(self, request):
        """Get client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class WooCommerceHealthCheckView(APIView):
    """
    Test connection from WordPress plugin
    
    GET /api/integrations/woocommerce/health/
    """
    authentication_classes = [IntegrationTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        token = request.auth
        
        return Response({
            'status': 'ok',
            'message': 'اتصال برقرار است',
            'user': {
                'id': request.user.id,
                'email': request.user.email,
                'username': request.user.username
            },
            'token': {
                'id': str(token.id),
                'integration_type': token.integration_type,
                'name': token.name,
                'last_used_at': token.last_used_at,
                'usage_count': token.usage_count
            },
            'timestamp': timezone.now()
        }, status=status.HTTP_200_OK)


class WooCommerceEventLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing WooCommerce Event Logs (Admin only)
    
    list: Get all event logs
    retrieve: Get specific event log
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = WooCommerceEventLogSerializer
    queryset = WooCommerceEventLog.objects.all().select_related('user', 'token')
    
    def get_queryset(self):
        """Filter by query params"""
        queryset = self.queryset.order_by('-created_at')
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by event type
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by success status
        success = self.request.query_params.get('success')
        if success is not None:
            success_bool = success.lower() == 'true'
            queryset = queryset.filter(processed_successfully=success_bool)
        
        # Filter by WooCommerce product ID
        woo_product_id = self.request.query_params.get('woo_product_id')
        if woo_product_id:
            queryset = queryset.filter(woo_product_id=woo_product_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get statistics about event logs"""
        from django.db.models import Count, Avg
        
        queryset = self.get_queryset()
        
        stats = {
            'total_events': queryset.count(),
            'successful': queryset.filter(processed_successfully=True).count(),
            'failed': queryset.filter(processed_successfully=False).count(),
            'by_event_type': dict(
                queryset.values('event_type')
                .annotate(count=Count('id'))
                .values_list('event_type', 'count')
            ),
            'average_processing_time_ms': queryset.aggregate(
                avg=Avg('processing_time_ms')
            )['avg']
        }
        
        return Response(stats)


class WordPressContentWebhookView(APIView):
    """
    Receive WordPress Pages/Posts webhook events
    
    POST /api/integrations/wordpress/content-webhook/
    """
    authentication_classes = [IntegrationTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        start_time = time.time()
        
        # Validate payload
        serializer = WordPressContentWebhookSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        payload = serializer.validated_data
        event_id = payload['event_id']
        event_type = payload['event_type']
        content_data = payload['content']
        
        # Check for duplicate
        if WordPressContentEventLog.objects.filter(event_id=event_id).exists():
            logger.info(f"⏭️ Duplicate event skipped: {event_id}")
            return Response({
                'status': 'skipped',
                'message': 'این رویداد قبلاً پردازش شده است',
                'event_id': event_id
            }, status=status.HTTP_200_OK)
        
        # Get token
        token = request.auth
        
        # Create event log
        event_log = WordPressContentEventLog.objects.create(
            event_id=event_id,
            event_type=event_type,
            user=request.user,
            token=token,
            wp_post_id=content_data.get('id', 0),
            payload=request.data
        )
        
        # Dispatch async task
        from integrations.tasks import process_wordpress_content
        
        process_wordpress_content.apply_async(
            args=[request.data, request.user.id, str(event_log.id)],
            countdown=2
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"✅ WordPress content event accepted: {event_type} for post {content_data.get('id')} "
            f"(user: {request.user.email}, time: {processing_time}ms)"
        )
        
        return Response({
            'status': 'accepted',
            'message': 'محتوا دریافت شد و در صف پردازش قرار گرفت',
            'event_id': event_id,
            'processing_time_ms': processing_time
        }, status=status.HTTP_202_ACCEPTED)


class WordPressContentHealthCheckView(APIView):
    """
    Test connection for WordPress pages/posts
    
    GET /api/integrations/wordpress/content-health/
    """
    authentication_classes = [IntegrationTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        token = request.auth
        
        return Response({
            'status': 'ok',
            'message': 'اتصال برقرار است',
            'user': {
                'id': request.user.id,
                'email': request.user.email,
            },
            'timestamp': timezone.now()
        })

