from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.db.models import Q
import logging

from .models import AIGlobalConfig, AIUsageTracking, AIUsageLog, TenantKnowledge, SessionMemory, IntentKeyword, IntentRouting, PGVECTOR_AVAILABLE
from .serializers import (
    AIGlobalConfigSerializer, AIUsageTrackingSerializer,
    AIUsageLogSerializer, AIUsageLogCreateSerializer, AIUsageLogStatsSerializer,
    AskQuestionRequestSerializer, AskQuestionResponseSerializer,
    ConversationStatusRequestSerializer, ConversationStatusResponseSerializer,
    BulkConversationStatusRequestSerializer, UserDefaultHandlerRequestSerializer,
    UserDefaultHandlerResponseSerializer, UsageStatsResponseSerializer,
    GlobalUsageStatsResponseSerializer, AIConfigurationStatusSerializer,
    RAGStatusResponseSerializer
)

logger = logging.getLogger(__name__)


class AskQuestionAPIView(APIView):
    """
    API to ask questions to AI and get responses
    Uses existing Message model for storage
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Ask a question to the AI",
        request_body=AskQuestionRequestSerializer,
        responses={
            200: AskQuestionResponseSerializer,
            400: 'Bad request',
            500: 'AI service error'
        }
    )
    def post(self, request):
        serializer = AskQuestionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        question = serializer.validated_data['question']
        conversation_id = serializer.validated_data.get('conversation_id')
        
        try:
            from AI_model.services.gemini_service import GeminiChatService
            from message.models import Conversation
            
            # Initialize AI service
            ai_service = GeminiChatService(request.user)
            
            if not ai_service.is_configured():
                return Response({
                    'success': False,
                    'error': 'AI is not configured for your account',
                    'response': None,
                    'response_time_ms': 0
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get conversation for context if provided
            conversation = None
            if conversation_id:
                try:
                    conversation = Conversation.objects.get(id=conversation_id, user=request.user)
                except Conversation.DoesNotExist:
                    pass
            
            # Generate AI response
            ai_response = ai_service.generate_response(question, conversation)
            
            # If we have a conversation and the response is successful, create a message
            message_id = None
            if conversation and ai_response['success']:
                ai_message = ai_service.create_ai_message(conversation, ai_response)
                if ai_message:
                    message_id = ai_message.id
            
            response_data = {
                'success': ai_response['success'],
                'response': ai_response.get('response'),
                'response_time_ms': ai_response.get('response_time_ms', 0),
                'metadata': ai_response.get('metadata', {})
            }
            
            if message_id:
                response_data['message_id'] = message_id
            
            if not ai_response['success']:
                response_data['error'] = ai_response.get('error', 'Unknown error')
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in AskQuestionAPIView: {str(e)}")
            return Response({
                'success': False,
                'error': str(e),
                'response': None,
                'response_time_ms': 0
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIGlobalConfigAPIView(APIView):
    """
    API to get and update global AI configuration
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get global AI configuration",
        responses={200: AIGlobalConfigSerializer}
    )
    def get(self, request):
        config = AIGlobalConfig.get_config()
        serializer = AIGlobalConfigSerializer(config)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Update global AI configuration (staff only)",
        request_body=AIGlobalConfigSerializer,
        responses={200: AIGlobalConfigSerializer, 403: 'Permission denied'}
    )
    def put(self, request):
        if not request.user.is_staff:
            return Response(
                {'error': 'Staff permissions required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        config = AIGlobalConfig.get_config()
        serializer = AIGlobalConfigSerializer(config, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AIConfigurationStatusAPIView(APIView):
    """
    API to check AI configuration status for current user
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Check AI configuration status",
        responses={200: AIConfigurationStatusSerializer}
    )
    def get(self, request):
        try:
            from AI_model.utils import validate_ai_configuration
            
            validation = validate_ai_configuration(request.user)
            
            response_data = {
                'ai_configured': validation['is_valid'],
                'global_enabled': validation['global_enabled'],
                'api_key_configured': validation['has_api_key'],
                'model_initialized': validation['user_configured'],
                'has_prompts': validation['has_prompts'],
                'issues': validation['issues']
            }
            
            # Add model name if available
            try:
                from AI_model.services.gemini_service import GeminiChatService
                ai_service = GeminiChatService(request.user)
                config_status = ai_service.get_configuration_status()
                response_data['model_name'] = config_status.get('model_name')
            except Exception:
                pass
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error checking AI configuration: {str(e)}")
            return Response({
                'ai_configured': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Conversation Status Management Views
class ConversationStatusAPIView(APIView):
    """
    API to get and update conversation status for AI/Manual handling
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get conversation status",
        responses={
            200: ConversationStatusResponseSerializer,
            404: 'Conversation not found'
        }
    )
    def get(self, request, conversation_id):
        from message.models import Conversation
        conversation = get_object_or_404(
            Conversation, 
            id=conversation_id, 
            user=request.user
        )
        
        # Check if AI is configured for this user
        from AI_model.services.gemini_service import GeminiChatService
        
        try:
            ai_service = GeminiChatService(request.user)
            ai_configured = ai_service.is_configured()
        except Exception:
            ai_configured = False
        
        response_data = {
            'conversation_id': conversation.id,
            'status': conversation.status,
            'ai_handling': conversation.status == 'active',
            'user_default_handler': request.user.default_reply_handler,
            'can_switch_to_ai': ai_configured and conversation.status != 'active',
            'can_switch_to_manual': conversation.status == 'active',
            'customer_name': str(conversation.customer),
            'source': conversation.source,
            'created_at': conversation.created_at,
            'updated_at': conversation.updated_at,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Update conversation status (switch between AI and Manual handling)",
        request_body=ConversationStatusRequestSerializer,
        responses={
            200: openapi.Response(
                description="Status updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'conversation_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'old_status': openapi.Schema(type=openapi.TYPE_STRING),
                        'new_status': openapi.Schema(type=openapi.TYPE_STRING),
                        'ai_handling': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: 'Invalid status or transition not allowed',
            404: 'Conversation not found'
        }
    )
    def put(self, request, conversation_id):
        from message.models import Conversation
        from AI_model.services.message_integration import MessageSystemIntegration
        
        conversation = get_object_or_404(
            Conversation, 
            id=conversation_id, 
            user=request.user
        )
        
        serializer = ConversationStatusRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        new_status = serializer.validated_data['status']
        
        # Check if switching to AI is allowed
        if new_status == 'active':
            from AI_model.services.gemini_service import GeminiChatService
            
            try:
                ai_service = GeminiChatService(request.user)
                if not ai_service.is_configured():
                    return Response(
                        {'error': 'AI is not properly configured for your account'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Exception as e:
                return Response(
                    {'error': f'Error checking AI configuration: {str(e)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        old_status = conversation.status
        
        # Update conversation status
        conversation.status = new_status
        conversation.save()
        
        # Handle AI session activation/deactivation
        integration = MessageSystemIntegration(request.user)
        
        if new_status == 'active':
            # Enable AI for conversation
            integration.enable_ai_for_conversation(conversation)
            message = "Conversation switched to AI handling"
        else:
            # Disable AI for conversation
            integration.disable_ai_for_conversation(conversation)
            message = "Conversation switched to manual/support handling"
        
        logger.info(f"User {request.user.username} changed conversation {conversation_id} status from '{old_status}' to '{new_status}'")
        
        response_data = {
            'conversation_id': conversation.id,
            'old_status': old_status,
            'new_status': new_status,
            'ai_handling': new_status == 'active',
            'message': message
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class BulkConversationStatusAPIView(APIView):
    """
    API to update multiple conversations status at once
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Update status for multiple conversations",
        request_body=BulkConversationStatusRequestSerializer,
        responses={
            200: 'Bulk update completed',
            400: 'Invalid request'
        }
    )
    def put(self, request):
        from message.models import Conversation
        from AI_model.services.message_integration import MessageSystemIntegration
        
        serializer = BulkConversationStatusRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        conversation_ids = serializer.validated_data['conversation_ids']
        new_status = serializer.validated_data['status']
        
        # Check AI configuration if switching to AI
        if new_status == 'active':
            from AI_model.services.gemini_service import GeminiChatService
            
            try:
                ai_service = GeminiChatService(request.user)
                if not ai_service.is_configured():
                    return Response(
                        {'error': 'AI is not properly configured for your account'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Exception as e:
                return Response(
                    {'error': f'Error checking AI configuration: {str(e)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Update conversations
        conversations = Conversation.objects.filter(
            id__in=conversation_ids,
            user=request.user
        )
        
        updated_count = 0
        integration = MessageSystemIntegration(request.user)
        
        for conversation in conversations:
            old_status = conversation.status
            conversation.status = new_status
            conversation.save()
            
            # Handle AI session
            if new_status == 'active':
                integration.enable_ai_for_conversation(conversation)
            else:
                integration.disable_ai_for_conversation(conversation)
            
            updated_count += 1
            
            logger.info(f"Bulk update: conversation {conversation.id} status changed from '{old_status}' to '{new_status}'")
        
        return Response({
            'updated_count': updated_count,
            'total_requested': len(conversation_ids),
            'new_status': new_status,
            'message': f'Updated {updated_count} conversations to {new_status} status'
        }, status=status.HTTP_200_OK)


class UserDefaultHandlerAPIView(APIView):
    """
    API to get and update user's default reply handler
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get user's default reply handler setting",
        responses={200: UserDefaultHandlerResponseSerializer}
    )
    def get(self, request):
        from message.models import Conversation
        from AI_model.services.gemini_service import GeminiChatService
        
        try:
            ai_service = GeminiChatService(request.user)
            ai_configured = ai_service.is_configured()
        except Exception:
            ai_configured = False
        
        # Count conversations by status
        active_count = Conversation.objects.filter(user=request.user, status='active', is_active=True).count()
        support_active_count = Conversation.objects.filter(user=request.user, status='support_active', is_active=True).count()
        
        return Response({
            'default_reply_handler': request.user.default_reply_handler,
            'ai_configured': ai_configured,
            'active_conversations_count': active_count,
            'support_active_conversations_count': support_active_count,
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Update user's default reply handler",
        request_body=UserDefaultHandlerRequestSerializer,
        responses={200: 'Default handler updated'}
    )
    def put(self, request):
        serializer = UserDefaultHandlerRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        new_handler = serializer.validated_data['default_reply_handler']
        
        # Check if switching to AI is allowed
        if new_handler == 'AI':
            from AI_model.services.gemini_service import GeminiChatService
            
            try:
                ai_service = GeminiChatService(request.user)
                if not ai_service.is_configured():
                    return Response(
                        {'error': 'AI is not properly configured. Please configure AI first.'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Exception as e:
                return Response(
                    {'error': f'Error checking AI configuration: {str(e)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        old_handler = request.user.default_reply_handler
        request.user.default_reply_handler = new_handler
        request.user.save()
        
        logger.info(f"User {request.user.username} changed default_reply_handler from '{old_handler}' to '{new_handler}'")
        
        return Response({
            'old_handler': old_handler,
            'new_handler': new_handler,
            'message': f'Default reply handler updated to {new_handler}'
        }, status=status.HTTP_200_OK)


# Usage Statistics Views
class AIUsageStatsAPIView(APIView):
    """
    API to get AI usage statistics for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get AI usage statistics",
        manual_parameters=[
            openapi.Parameter(
                'days', openapi.IN_QUERY, description="Number of days to include (default: 30)",
                type=openapi.TYPE_INTEGER, default=30
            ),
        ],
        responses={200: UsageStatsResponseSerializer}
    )
    def get(self, request):
        from django.db.models import Sum, Avg
        from datetime import date, timedelta
        
        days = int(request.query_params.get('days', 30))
        
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        # Get usage data for the period
        usage_records = AIUsageTracking.objects.filter(
            user=request.user,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        # Aggregate totals
        aggregates = usage_records.aggregate(
            total_requests=Sum('total_requests'),
            total_tokens=Sum('total_tokens'),
            total_prompt_tokens=Sum('total_prompt_tokens'),
            total_completion_tokens=Sum('total_completion_tokens'),
            successful_requests=Sum('successful_requests'),
            failed_requests=Sum('failed_requests'),
            avg_response_time=Avg('average_response_time_ms')
        )
        
        # Calculate success rate
        total_requests = aggregates['total_requests'] or 0
        successful_requests = aggregates['successful_requests'] or 0
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Prepare daily breakdown
        daily_breakdown = []
        for record in usage_records:
            daily_breakdown.append({
                'date': record.date.isoformat(),
                'requests': record.total_requests,
                'tokens': record.total_tokens,
                'successful_requests': record.successful_requests,
                'failed_requests': record.failed_requests,
                'average_response_time_ms': record.average_response_time_ms,
            })
        
        response_data = {
            'total_requests': aggregates['total_requests'] or 0,
            'total_tokens': aggregates['total_tokens'] or 0,
            'total_prompt_tokens': aggregates['total_prompt_tokens'] or 0,
            'total_completion_tokens': aggregates['total_completion_tokens'] or 0,
            'successful_requests': aggregates['successful_requests'] or 0,
            'failed_requests': aggregates['failed_requests'] or 0,
            'success_rate': round(success_rate, 2),
            'average_response_time_ms': round(aggregates['avg_response_time'] or 0, 2),
            'days_included': days,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'daily_breakdown': daily_breakdown,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class GlobalUsageStatsAPIView(APIView):
    """
    API to get global AI usage statistics (admin only)
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get global AI usage statistics (requires staff permissions)",
        manual_parameters=[
            openapi.Parameter(
                'days', openapi.IN_QUERY, description="Number of days to include (default: 30)",
                type=openapi.TYPE_INTEGER, default=30
            ),
        ],
        responses={
            200: GlobalUsageStatsResponseSerializer,
            403: 'Permission denied'
        }
    )
    def get(self, request):
        from django.db.models import Sum, Avg
        from datetime import date, timedelta
        
        # Check if user is staff
        if not request.user.is_staff:
            return Response(
                {'error': 'Staff permissions required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        days = int(request.query_params.get('days', 30))
        
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        # Get usage data for the period
        usage_records = AIUsageTracking.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        )
        
        # Global aggregates
        global_aggregates = usage_records.aggregate(
            total_requests=Sum('total_requests'),
            total_tokens=Sum('total_tokens'),
            successful_requests=Sum('successful_requests'),
            failed_requests=Sum('failed_requests'),
        )
        
        # Count unique users
        total_users = usage_records.values('user').distinct().count()
        active_users = usage_records.filter(total_requests__gt=0).values('user').distinct().count()
        
        # Calculate success rate
        total_requests = global_aggregates['total_requests'] or 0
        successful_requests = global_aggregates['successful_requests'] or 0
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Top users by request count
        top_users = usage_records.values('user__username', 'user__email').annotate(
            user_total_requests=Sum('total_requests'),
            user_total_tokens=Sum('total_tokens')
        ).order_by('-user_total_requests')[:10]
        
        response_data = {
            'total_users': total_users,
            'active_users': active_users,
            'total_requests': global_aggregates['total_requests'] or 0,
            'total_tokens': global_aggregates['total_tokens'] or 0,
            'successful_requests': global_aggregates['successful_requests'] or 0,
            'failed_requests': global_aggregates['failed_requests'] or 0,
            'success_rate': round(success_rate, 2),
            'days_included': days,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'top_users': list(top_users),
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class RAGStatusAPIView(APIView):
    """
    API to check RAG (Retrieval Augmented Generation) system status
    Returns knowledge base statistics, embedding status, and overall health
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get RAG system status for the authenticated user",
        responses={
            200: RAGStatusResponseSerializer,
            500: 'Server error'
        }
    )
    def get(self, request):
        try:
            from django.utils import timezone
            from datetime import timedelta
            from web_knowledge.models import CrawlJob, WebsitePage, QAPair, Product
            
            user = request.user
            issues = []
            
            # 1. Check pgvector availability
            pgvector_available = PGVECTOR_AVAILABLE
            if not pgvector_available:
                issues.append("pgvector extension not installed")
            
            # 2. Check embedding service availability (FIXED: use is_available instead of embedding_dim)
            embedding_service_available = False
            try:
                from AI_model.services.embedding_service import EmbeddingService
                emb_service = EmbeddingService(use_cache=True)
                # Check if any service is configured (OpenAI or Gemini)
                embedding_service_available = (
                    emb_service.openai_configured or 
                    emb_service.gemini_configured
                )
            except Exception as e:
                issues.append(f"Embedding service error: {str(e)}")
            
            # 3. Get knowledge base statistics
            knowledge_base = {}
            total_chunks = 0
            
            for chunk_type, display_name in TenantKnowledge.CHUNK_TYPE_CHOICES:
                count = TenantKnowledge.objects.filter(
                    user=user,
                    chunk_type=chunk_type
                ).count()
                knowledge_base[chunk_type] = {
                    'count': count,
                    'display_name': display_name
                }
                total_chunks += count
            
            knowledge_base['total'] = total_chunks
            
            # 4. Get embedding statistics
            chunks_with_tldr_embedding = TenantKnowledge.objects.filter(
                user=user,
                tldr_embedding__isnull=False
            ).count()
            
            chunks_with_full_embedding = TenantKnowledge.objects.filter(
                user=user,
                full_embedding__isnull=False
            ).count()
            
            chunks_without_embedding = TenantKnowledge.objects.filter(
                user=user,
                tldr_embedding__isnull=True
            ).count()
            
            embedding_stats = {
                'total_chunks': total_chunks,
                'chunks_with_tldr_embedding': chunks_with_tldr_embedding,
                'chunks_with_full_embedding': chunks_with_full_embedding,
                'chunks_without_embedding': chunks_without_embedding,
                'embedding_coverage': round(
                    (chunks_with_tldr_embedding / total_chunks * 100) if total_chunks > 0 else 0, 
                    2
                )
            }
            
            if chunks_without_embedding > 0:
                issues.append(f"{chunks_without_embedding} chunks missing embeddings")
            
            # 5. Get intent routing configuration
            intent_keywords_count = IntentKeyword.objects.filter(
                Q(user=user) | Q(user__isnull=True),
                is_active=True
            ).count()
            
            intent_routing_count = IntentRouting.objects.filter(is_active=True).count()
            
            intent_routing = {
                'keywords_configured': intent_keywords_count,
                'routing_rules_configured': intent_routing_count,
                'has_custom_keywords': IntentKeyword.objects.filter(user=user, is_active=True).exists()
            }
            
            # 6. Get session memory statistics
            from message.models import Conversation
            
            total_conversations = Conversation.objects.filter(user=user, is_active=True).count()
            conversations_with_memory = SessionMemory.objects.filter(user=user).count()
            
            session_memory = {
                'total_conversations': total_conversations,
                'conversations_with_memory': conversations_with_memory,
                'memory_coverage': round(
                    (conversations_with_memory / total_conversations * 100) if total_conversations > 0 else 0,
                    2
                )
            }
            
            # 7. Get last update timestamp
            last_updated = None
            latest_chunk = TenantKnowledge.objects.filter(user=user).order_by('-updated_at').first()
            if latest_chunk:
                last_updated = latest_chunk.updated_at
            
            # 8. SIMPLIFIED: Check for active processing (2 simple checks only)
            is_processing = False
            processing_message = []
            
            # Check 1: Active crawl jobs (simple .exists() query)
            try:
                has_active_crawl = CrawlJob.objects.filter(
                    website__user=user,
                    job_status__in=['queued', 'running']
                ).exists()
                if has_active_crawl:
                    is_processing = True
                    processing_message.append("Website crawling in progress")
            except Exception as e:
                logger.warning(f"Error checking crawl jobs: {e}")
            
            # Check 2: Pages being processed (simple .exists() query)
            try:
                has_processing_pages = WebsitePage.objects.filter(
                    website__user=user,
                    processing_status__in=['pending', 'processing']
                ).exists()
                if has_processing_pages:
                    is_processing = True
                    processing_message.append("Pages being analyzed")
            except Exception as e:
                logger.warning(f"Error checking pages: {e}")
            
            # Check 3: Pages completed but not yet chunked (gap check)
            try:
                completed_pages_count = WebsitePage.objects.filter(
                    website__user=user,
                    processing_status='completed'
                ).count()
                
                if completed_pages_count > 0:
                    # Check how many are chunked
                    chunked_pages_count = TenantKnowledge.objects.filter(
                        user=user,
                        chunk_type='website'
                    ).values('source_id').distinct().count()
                    
                    # If there's a gap, still processing
                    if chunked_pages_count < completed_pages_count:
                        is_processing = True
                        gap = completed_pages_count - chunked_pages_count
                        processing_message.append(f"Indexing {gap} pages to knowledge base")
            except Exception as e:
                logger.warning(f"Error checking chunking gap: {e}")
            
            # 9.Simple estimated wait time (no complex calculations)
            estimated_wait_seconds = 60 if is_processing else 0
            
            # 10. Determine overall health status (SIMPLIFIED)
            if not pgvector_available or not embedding_service_available:
                health_status = "unavailable"
                issues.insert(0, "RAG system is not fully operational")
            elif is_processing:
                # Use "degraded" for processing state (existing Frontend status)
                health_status = "degraded"
                # Add processing messages to issues
                issues.extend(processing_message)
            elif total_chunks == 0:
                # ✅ FIX: Use "healthy" with info message when knowledge base is empty
                # This is not an error - user just hasn't added data yet
                health_status = "healthy"
                issues.append("پایگاه دانش خالی است. لطفا محتوا اضافه کنید.")
            elif chunks_without_embedding > total_chunks * 0.1:  # More than 10% missing embeddings
                health_status = "degraded"
            else:
                health_status = "healthy"
            
            # 11. RAG enabled check
            rag_enabled = (
                pgvector_available and 
                embedding_service_available and 
                total_chunks > 0 and
                chunks_with_tldr_embedding > 0
            )
            
            # 12. Can query check (NEW: user can only query when system is ready)
            can_query = (
                rag_enabled and 
                health_status in ['healthy', 'degraded'] and
                not is_processing
            )
            
            response_data = {
                'rag_enabled': rag_enabled,
                'pgvector_available': pgvector_available,
                'embedding_service_available': embedding_service_available,
                'knowledge_base': knowledge_base,
                'embedding_stats': embedding_stats,
                'intent_routing': intent_routing,
                'session_memory': session_memory,
                'last_updated': last_updated.isoformat() if last_updated else None,
                'health_status': health_status,
                'can_query': can_query,  # NEW: backward compatible addition
                'estimated_wait_seconds': estimated_wait_seconds if is_processing else 0,  # NEW
                'should_poll': is_processing,  # NEW: tells Frontend if it should keep polling
                'issues': issues
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting RAG status: {str(e)}")
            return Response({
                'rag_enabled': False,
                'pgvector_available': False,
                'embedding_service_available': False,
                'knowledge_base': {},
                'embedding_stats': {},
                'intent_routing': {},
                'session_memory': {},
                'last_updated': None,
                'health_status': 'unavailable',
                'issues': [f"Error retrieving RAG status: {str(e)}"]
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessAIResponseAPIView(APIView):
    """
    Manually process AI response for a message (debugging)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, message_id):
        try:
            from AI_model.tasks import process_ai_response_async
            from message.models import Message
            
            # Check if message exists
            message = Message.objects.get(id=message_id)
            
            # Process immediately
            result = process_ai_response_async.delay(message_id)
            
            return Response({
                'success': True,
                'message': f'AI processing triggered for message {message_id}',
                'task_id': result.id
            })
            
        except Message.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Message {message_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# AI USAGE LOG API VIEWS
# ============================================================================

class AIUsageLogAPIView(APIView):
    """
    API to log and retrieve AI usage records
    
    GET: Retrieve usage logs with filtering
    POST: Create a new usage log entry
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Retrieve AI usage logs with optional filtering",
        manual_parameters=[
            openapi.Parameter(
                'section', openapi.IN_QUERY,
                description="Filter by section/feature (e.g., 'chat', 'prompt_generation')",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'start_date', openapi.IN_QUERY,
                description="Start date for filtering (YYYY-MM-DD)",
                type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE
            ),
            openapi.Parameter(
                'end_date', openapi.IN_QUERY,
                description="End date for filtering (YYYY-MM-DD)",
                type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE
            ),
            openapi.Parameter(
                'success', openapi.IN_QUERY,
                description="Filter by success status (true/false)",
                type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'limit', openapi.IN_QUERY,
                description="Number of records to return (default: 50, max: 500)",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'offset', openapi.IN_QUERY,
                description="Number of records to skip (for pagination)",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: openapi.Response(
                description="List of usage logs",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT)
                        )
                    }
                )
            )
        }
    )
    def get(self, request):
        """Get AI usage logs with filtering"""
        from datetime import datetime
        
        # Start with user's logs
        queryset = AIUsageLog.objects.filter(user=request.user)
        
        # Apply filters
        section = request.query_params.get('section')
        if section:
            queryset = queryset.filter(section=section)
        
        start_date = request.query_params.get('start_date')
        if start_date:
            try:
                start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=start_datetime)
            except ValueError:
                return Response(
                    {'error': 'Invalid start_date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        end_date = request.query_params.get('end_date')
        if end_date:
            try:
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
                # Add one day to include the entire end date
                from datetime import timedelta
                end_datetime = end_datetime + timedelta(days=1)
                queryset = queryset.filter(created_at__lt=end_datetime)
            except ValueError:
                return Response(
                    {'error': 'Invalid end_date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        success_param = request.query_params.get('success')
        if success_param is not None:
            success_value = success_param.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(success=success_value)
        
        # Pagination
        limit = int(request.query_params.get('limit', 50))
        limit = min(limit, 500)  # Max 500 records
        offset = int(request.query_params.get('offset', 0))
        
        total_count = queryset.count()
        queryset = queryset[offset:offset + limit]
        
        # Serialize
        serializer = AIUsageLogSerializer(queryset, many=True)
        
        # Build pagination response
        next_url = None
        previous_url = None
        
        if offset + limit < total_count:
            next_url = f"?limit={limit}&offset={offset + limit}"
            if section:
                next_url += f"&section={section}"
        
        if offset > 0:
            previous_offset = max(0, offset - limit)
            previous_url = f"?limit={limit}&offset={previous_offset}"
            if section:
                previous_url += f"&section={section}"
        
        return Response({
            'count': total_count,
            'next': next_url,
            'previous': previous_url,
            'results': serializer.data
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Log a new AI usage record",
        request_body=AIUsageLogCreateSerializer,
        responses={
            201: AIUsageLogSerializer,
            400: 'Bad request'
        }
    )
    def post(self, request):
        """Create a new AI usage log"""
        serializer = AIUsageLogCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Create usage log
        usage_log = AIUsageLog.log_usage(
            user=request.user,
            section=serializer.validated_data['section'],
            prompt_tokens=serializer.validated_data.get('prompt_tokens', 0),
            completion_tokens=serializer.validated_data.get('completion_tokens', 0),
            response_time_ms=serializer.validated_data.get('response_time_ms', 0),
            success=serializer.validated_data.get('success', True),
            model_name=serializer.validated_data.get('model_name', 'gemini-1.5-flash'),
            error_message=serializer.validated_data.get('error_message'),
            metadata=serializer.validated_data.get('metadata', {})
        )
        
        # Return created log
        response_serializer = AIUsageLogSerializer(usage_log)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class AIUsageLogStatsAPIView(APIView):
    """
    API to get detailed AI usage statistics from logs
    Provides comprehensive analytics with section breakdown
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get detailed AI usage statistics with section breakdown",
        manual_parameters=[
            openapi.Parameter(
                'days', openapi.IN_QUERY,
                description="Number of days to include (default: 30)",
                type=openapi.TYPE_INTEGER, default=30
            ),
            openapi.Parameter(
                'section', openapi.IN_QUERY,
                description="Filter by specific section",
                type=openapi.TYPE_STRING
            ),
        ],
        responses={200: AIUsageLogStatsSerializer}
    )
    def get(self, request):
        """Get AI usage statistics from logs"""
        from django.db.models import Sum, Avg, Count
        from datetime import date, timedelta
        
        days = int(request.query_params.get('days', 30))
        section_filter = request.query_params.get('section')
        
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        # Base queryset
        queryset = AIUsageLog.objects.filter(
            user=request.user,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        if section_filter:
            queryset = queryset.filter(section=section_filter)
        
        # Aggregate totals
        aggregates = queryset.aggregate(
            total_requests=Count('id'),
            sum_total_tokens=Sum('total_tokens'),
            sum_prompt_tokens=Sum('prompt_tokens'),
            sum_completion_tokens=Sum('completion_tokens'),
            successful_requests=Count('id', filter=Q(success=True)),
            failed_requests=Count('id', filter=Q(success=False)),
            avg_response_time=Avg('response_time_ms'),
            avg_tokens_per_request=Avg('total_tokens')
        )
        
        # Calculate success rate
        total_requests = aggregates['total_requests'] or 0
        successful_requests = aggregates['successful_requests'] or 0
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Section breakdown
        section_breakdown = {}
        for section_code, section_name in AIUsageLog.SECTION_CHOICES:
            section_stats = queryset.filter(section=section_code).aggregate(
                count=Count('id'),
                tokens=Sum('total_tokens'),
                avg_response_time=Avg('response_time_ms')
            )
            
            if section_stats['count'] and section_stats['count'] > 0:
                section_breakdown[section_code] = {
                    'display_name': section_name,
                    'count': section_stats['count'],
                    'total_tokens': section_stats['tokens'] or 0,
                    'avg_response_time_ms': round(section_stats['avg_response_time'] or 0, 2),
                    'percentage': round((section_stats['count'] / total_requests * 100), 2) if total_requests > 0 else 0
                }
        
        # Daily breakdown
        daily_breakdown = []
        current_date = start_date
        while current_date <= end_date:
            day_stats = queryset.filter(created_at__date=current_date).aggregate(
                requests=Count('id'),
                tokens=Sum('total_tokens'),
                successful=Count('id', filter=Q(success=True)),
                failed=Count('id', filter=Q(success=False))
            )
            
            daily_breakdown.append({
                'date': current_date.isoformat(),
                'requests': day_stats['requests'] or 0,
                'tokens': day_stats['tokens'] or 0,
                'successful_requests': day_stats['successful'] or 0,
                'failed_requests': day_stats['failed'] or 0
            })
            
            current_date += timedelta(days=1)
        
        # Recent logs (last 10)
        recent_logs = queryset.order_by('-created_at')[:10]
        recent_logs_data = AIUsageLogSerializer(recent_logs, many=True).data
        
        response_data = {
            'total_requests': aggregates['total_requests'] or 0,
            'total_tokens': aggregates['sum_total_tokens'] or 0,
            'total_prompt_tokens': aggregates['sum_prompt_tokens'] or 0,
            'total_completion_tokens': aggregates['sum_completion_tokens'] or 0,
            'successful_requests': aggregates['successful_requests'] or 0,
            'failed_requests': aggregates['failed_requests'] or 0,
            'success_rate': round(success_rate, 2),
            'average_response_time_ms': round(aggregates['avg_response_time'] or 0, 2),
            'average_tokens_per_request': round(aggregates['avg_tokens_per_request'] or 0, 2),
            'days_included': days,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'by_section': section_breakdown,
            'daily_breakdown': daily_breakdown,
            'recent_logs': recent_logs_data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class GlobalAIUsageLogStatsAPIView(APIView):
    """
    API to get global AI usage statistics (admin only)
    Provides system-wide analytics across all users
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get global AI usage statistics (requires staff permissions)",
        manual_parameters=[
            openapi.Parameter(
                'days', openapi.IN_QUERY,
                description="Number of days to include (default: 30)",
                type=openapi.TYPE_INTEGER, default=30
            ),
        ],
        responses={
            200: 'Global usage statistics',
            403: 'Permission denied'
        }
    )
    def get(self, request):
        """Get global AI usage statistics (staff only)"""
        from django.db.models import Sum, Avg, Count
        from datetime import date, timedelta
        
        # Check if user is staff
        if not request.user.is_staff:
            return Response(
                {'error': 'Staff permissions required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        days = int(request.query_params.get('days', 30))
        
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        # Get all logs for the period
        queryset = AIUsageLog.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        # Global aggregates
        global_aggregates = queryset.aggregate(
            total_requests=Count('id'),
            sum_total_tokens=Sum('total_tokens'),
            sum_prompt_tokens=Sum('prompt_tokens'),
            sum_completion_tokens=Sum('completion_tokens'),
            successful_requests=Count('id', filter=Q(success=True)),
            failed_requests=Count('id', filter=Q(success=False)),
            avg_response_time=Avg('response_time_ms')
        )
        
        # Count unique users
        total_users = queryset.values('user').distinct().count()
        
        # Calculate success rate
        total_requests = global_aggregates['total_requests'] or 0
        successful_requests = global_aggregates['successful_requests'] or 0
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Section breakdown
        section_breakdown = {}
        for section_code, section_name in AIUsageLog.SECTION_CHOICES:
            section_stats = queryset.filter(section=section_code).aggregate(
                count=Count('id'),
                tokens=Sum('total_tokens')
            )
            
            if section_stats['count'] and section_stats['count'] > 0:
                section_breakdown[section_code] = {
                    'display_name': section_name,
                    'count': section_stats['count'],
                    'total_tokens': section_stats['tokens'] or 0,
                    'percentage': round((section_stats['count'] / total_requests * 100), 2) if total_requests > 0 else 0
                }
        
        # Top users by request count
        top_users = queryset.values(
            'user__username', 'user__email'
        ).annotate(
            user_total_requests=Count('id'),
            user_total_tokens=Sum('total_tokens')
        ).order_by('-user_total_requests')[:10]
        
        response_data = {
            'total_users': total_users,
            'total_requests': global_aggregates['total_requests'] or 0,
            'total_tokens': global_aggregates['sum_total_tokens'] or 0,
            'total_prompt_tokens': global_aggregates['sum_prompt_tokens'] or 0,
            'total_completion_tokens': global_aggregates['sum_completion_tokens'] or 0,
            'successful_requests': global_aggregates['successful_requests'] or 0,
            'failed_requests': global_aggregates['failed_requests'] or 0,
            'success_rate': round(success_rate, 2),
            'average_response_time_ms': round(global_aggregates['avg_response_time'] or 0, 2),
            'days_included': days,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'by_section': section_breakdown,
            'top_users': list(top_users),
        }
        
        return Response(response_data, status=status.HTTP_200_OK)

