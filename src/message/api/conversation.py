from rest_framework.views import APIView
from rest_framework.response import Response
from message.serializers import ConversationSerializer
from rest_framework import status, filters
from message.models import Conversation
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 500

class FullUserConversationsAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    serializer_class = ConversationSerializer
    #queryset = Conversation.objects.filter(user=self.request.user)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title',]
    ordering_fields = ['created_at','updated_at','priority']
    filterset_fields = ['created_at','updated_at','priority','status','is_active','source']
    @swagger_auto_schema()
    def get(self, request, format=None):
        query = self.filter_queryset(Conversation.objects.filter(user=self.request.user))
        page = self.paginate_queryset(query)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(query, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class UserConversationsAPIView(APIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    def get(self, *args, **kwargs):
        try:
            conv = Conversation.objects.filter(user=self.request.user)
            serializer = self.serializer_class(conv, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(f"Error: {str(e)}", status=status.HTTP_400_BAD_REQUEST)



class ConversationItemAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer
    
    def _get_conversation_and_check_permission(self, conversation_id, user):
        """Get conversation and check if user has permission to access it"""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            # Check if user owns this conversation
            if conversation.user != user:
                return None, Response(
                    {"error": "You don't have permission to access this conversation"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            return conversation, None
        except Conversation.DoesNotExist:
            return None, Response(
                {"error": "Conversation not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @swagger_auto_schema(
        operation_description="Get conversation details",
        responses={
            200: ConversationSerializer,
            403: "Permission denied",
            404: "Conversation not found"
        }
    )
    def get(self, request, *args, **kwargs):
        conversation, error_response = self._get_conversation_and_check_permission(
            self.kwargs["id"], request.user
        )
        if error_response:
            return error_response
            
        serializer = self.serializer_class(conversation)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Delete conversation and all related messages",
        responses={
            204: "Conversation deleted successfully",
            403: "Permission denied",
            404: "Conversation not found"
        }
    )
    def delete(self, request, *args, **kwargs):
        conversation, error_response = self._get_conversation_and_check_permission(
            self.kwargs["id"], request.user
        )
        if error_response:
            return error_response
        
        # Store conversation ID and user ID for websocket notification
        conversation_id = conversation.id
        user_id = request.user.id
        
        # Delete the conversation (this will cascade delete all related messages)
        conversation.delete()
        
        # Send websocket notification about the deletion
        from message.websocket_utils import notify_conversation_deleted
        notify_conversation_deleted(conversation_id, user_id)
        
        return Response(
            {"message": "Conversation deleted successfully"}, 
            status=status.HTTP_204_NO_CONTENT
        )


class ActivateAllUserConversationsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Activate all conversations of the authenticated user (set status to 'active')",
        responses={
            200: openapi.Response(
                description="All conversations activated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'updated_count': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            400: "Bad request"
        }
    )
    def post(self, request, *args, **kwargs):
        try:
            # Get all conversations of the authenticated user
            conversations = Conversation.objects.filter(user=request.user)
            
            # Update all conversations to status='active'
            updated_count = conversations.update(status='active')
            
            return Response(
                {
                    "message": f"Successfully activated {updated_count} conversation(s)",
                    "updated_count": updated_count
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )


class DisableAllUserConversationsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Disable all AI conversations of the authenticated user (set status to 'support_active' to disable AI)",
        responses={
            200: openapi.Response(
                description="All conversations disabled for AI successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'updated_count': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            400: "Bad request"
        }
    )
    def post(self, request, *args, **kwargs):
        try:
            # Get all conversations of the authenticated user
            conversations = Conversation.objects.filter(user=request.user)
            
            # Update all conversations to status='support_active' (disables AI)
            updated_count = conversations.update(status='support_active')
            
            return Response(
                {
                    "message": f"Successfully disabled AI for {updated_count} conversation(s)",
                    "updated_count": updated_count
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )