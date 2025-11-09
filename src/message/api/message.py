from rest_framework.response import Response
from message.serializers import MessageSerializer
from rest_framework import status, filters
from rest_framework.decorators import api_view, permission_classes
from message.models import Message
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from web_knowledge.models import QAPair


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 500


class UserMessagesAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    serializer_class = MessageSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['content',]
    ordering_fields = ['created_at',]
    filterset_fields = ['created_at','is_answered','is_ai_response','conversation','type']
    @swagger_auto_schema()
    def get(self, request, format=None):
        query = self.filter_queryset(Message.objects.filter(conversation__user=self.request.user))
        page = self.paginate_queryset(query)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(query, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='post',
    operation_description="Submit feedback for an AI response message (Phase 1 - Feature 2: Response Quality Feedback)",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['feedback'],
        properties={
            'feedback': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['positive', 'negative', 'none'],
                description='Feedback type: positive (👍), negative (👎), or none (clear feedback)'
            ),
            'comment': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Optional comment explaining the feedback (max 500 chars)',
                max_length=500
            ),
        },
    ),
    responses={
        200: openapi.Response(
            description='Feedback submitted successfully',
            examples={
                'application/json': {
                    'success': True,
                    'message': 'Feedback submitted successfully',
                    'data': {
                        'message_id': 'abc123',
                        'feedback': 'positive',
                        'comment': 'Very helpful!',
                        'feedback_at': '2025-10-05T10:30:00Z'
                    }
                }
            }
        ),
        400: 'Invalid feedback type or message not found',
        403: 'Not authorized to provide feedback for this message',
        404: 'Message not found',
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_message_feedback(request, message_id):
    """
    Submit feedback for an AI response message
    
    - Only AI messages can receive feedback
    - User must own the conversation
    - Feedback can be updated multiple times
    """
    try:
        # Get message and verify ownership
        message = Message.objects.select_related('conversation', 'conversation__user').get(
            id=message_id,
            conversation__user=request.user
        )
        
        # Verify it's an AI message
        if message.type != 'AI':
            return Response(
                {
                    'success': False,
                    'error': 'Feedback can only be submitted for AI responses'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get and validate feedback
        feedback_type = request.data.get('feedback', '').lower()
        if feedback_type not in ['positive', 'negative', 'none']:
            return Response(
                {
                    'success': False,
                    'error': 'Invalid feedback type. Must be "positive", "negative", or "none"'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get optional comment
        comment = request.data.get('comment', '').strip()[:500]  # Max 500 chars
        
        # Update message feedback
        message.feedback = feedback_type
        message.feedback_comment = comment
        message.feedback_at = timezone.now()
        message.save(update_fields=['feedback', 'feedback_comment', 'feedback_at'])
        
        # If positive or negative feedback, create QAPair in web_knowledge
        if feedback_type in ['positive', 'negative']:
            try:
                # Find the previous message in the same conversation
                previous_message = Message.objects.filter(
                    conversation=message.conversation,
                    created_at__lt=message.created_at
                ).order_by('-created_at').first()
                
                if previous_message:
                    if feedback_type == 'positive':
                        # For positive feedback: previous message as question, current message as answer
                        QAPair.objects.create(
                            question=previous_message.content,
                            answer=message.content,
                            user=message.conversation.user,
                            created_by_ai=True,
                            generation_status='completed',
                            confidence_score=1.0,  # High confidence since it's user-validated
                            context='',  # Can be empty or add conversation context if needed
                        )
                    elif feedback_type == 'negative' and comment:
                        # For negative feedback: previous message as question, comment as answer
                        QAPair.objects.create(
                            question=previous_message.content,
                            answer=comment,
                            user=message.conversation.user,
                            created_by_ai=True,
                            generation_status='completed',
                            confidence_score=1.0,  # High confidence since it's user-validated
                            context='',  # Can be empty or add conversation context if needed
                        )
            except Exception as e:
                # Log error but don't fail the feedback submission
                # You might want to add logging here
                pass
        
        return Response(
            {
                'success': True,
                'message': 'Feedback submitted successfully',
                'data': {
                    'message_id': message.id,
                    'feedback': message.feedback,
                    'comment': message.feedback_comment,
                    'feedback_at': message.feedback_at.isoformat() if message.feedback_at else None
                }
            },
            status=status.HTTP_200_OK
        )
        
    except Message.DoesNotExist:
        return Response(
            {
                'success': False,
                'error': 'Message not found or you do not have permission to access it'
            },
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {
                'success': False,
                'error': f'Failed to submit feedback: {str(e)}'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


