from django.shortcuts import render
from django.shortcuts import get_object_or_404
from settings.serializers import (
    SettingsSerializer, AIPromptsSerializer, 
    AIPromptsManualPromptSerializer, AIPromptsCreateUpdateSerializer,
    UpToProSerializer
)
from accounts.serializers import DefaultReplyHandlerSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from settings.models import Settings, AIPrompts, UpToPro
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

logger = logging.getLogger(__name__)

class PricesAPIView(APIView):
    serializer_class = SettingsSerializer
    permission_classes = [AllowAny]
    def get(self, *args, **kwargs):
        try:
            prices = Settings.objects.get(id=1)
            serializer = self.serializer_class(prices)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response("Prices not found or something went wrong, try again", status=status.HTTP_400_BAD_REQUEST)



class DefaultReplyHandlerAPIView(APIView):
    serializer_class = DefaultReplyHandlerSerializer
    permission_classes = [IsAuthenticated]
    def get(self, *args, **kwargs):
        serializer = self.serializer_class(self.request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def patch(self, *args, **kwargs):
        serializer = self.serializer_class(self.request.user, data=self.request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


class AIPromptsAPIView(APIView):
    """
    API for getting and updating user's AI prompts
    Automatically creates AIPrompts if user doesn't have them
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get user's AI prompts. Creates default prompts if user doesn't have them.",
        responses={
            200: AIPromptsSerializer,
            500: "Internal server error"
        }
    )
    def get(self, request):
        """Get or create AIPrompts for the authenticated user"""
        try:
            # Get or create AIPrompts for the user
            prompts, created = AIPrompts.get_or_create_for_user(request.user)
            
            if created:
                logger.info(f"Created new AIPrompts for user {request.user.username}")
            
            serializer = AIPromptsSerializer(prompts)
            return Response({
                'success': True,
                'data': serializer.data,
                'created': created
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting AI prompts for user {request.user.username}: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to get AI prompts'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        operation_description="Update user's AI prompts",
        request_body=AIPromptsCreateUpdateSerializer,
        responses={
            200: AIPromptsSerializer,
            400: "Bad request",
            500: "Internal server error"
        }
    )
    def patch(self, request):
        """Update AIPrompts for the authenticated user"""
        try:
            # Get or create AIPrompts for the user
            prompts, created = AIPrompts.get_or_create_for_user(request.user)
            
            serializer = AIPromptsCreateUpdateSerializer(prompts, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                
                # Return full data
                response_serializer = AIPromptsSerializer(prompts)
                return Response({
                    'success': True,
                    'data': response_serializer.data,
                    'message': 'AI prompts updated successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error updating AI prompts for user {request.user.username}: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to update AI prompts'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIPromptsManualPromptAPIView(APIView):
    """
    API specifically for getting and updating manual_prompt field
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get user's manual prompt. Creates default if user doesn't have AIPrompts.",
        responses={
            200: openapi.Response(
                description="Manual prompt data",
                examples={
                    "application/json": {
                        "success": True,
                        "manual_prompt": "You are a helpful customer service assistant...",
                        "created": False
                    }
                }
            ),
            500: "Internal server error"
        }
    )
    def get(self, request):
        """Get manual_prompt for the authenticated user"""
        try:
            # Get or create AIPrompts for the user
            prompts, created = AIPrompts.get_or_create_for_user(request.user)
            
            return Response({
                'success': True,
                'manual_prompt': prompts.manual_prompt,
                'created': created
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting manual prompt for user {request.user.username}: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to get manual prompt'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        operation_description="Update user's manual prompt",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'manual_prompt': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Manual prompt text'
                )
            },
            required=['manual_prompt']
        ),
        responses={
            200: openapi.Response(
                description="Manual prompt updated",
                examples={
                    "application/json": {
                        "success": True,
                        "manual_prompt": "Updated prompt text",
                        "message": "Manual prompt updated successfully"
                    }
                }
            ),
            400: "Bad request",
            500: "Internal server error"
        }
    )
    def patch(self, request):
        """Update manual_prompt for the authenticated user"""
        try:
            # Get or create AIPrompts for the user
            prompts, created = AIPrompts.get_or_create_for_user(request.user)
            
            serializer = AIPromptsManualPromptSerializer(prompts, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                
                return Response({
                    'success': True,
                    'manual_prompt': prompts.manual_prompt,
                    'message': 'Manual prompt updated successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error updating manual prompt for user {request.user.username}: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to update manual prompt'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LatestUpToProAPIView(APIView):
    """
    API endpoint to get the latest (most recent) UpToPro object
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get the latest UpToPro object based on creation date",
        responses={
            200: UpToProSerializer,
            404: "No UpToPro object found",
            500: "Internal server error"
        }
    )
    def get(self, request):
        """Get the most recent UpToPro object"""
        try:
            # Get the latest UpToPro object (ordered by -created_at in model Meta)
            latest_uptopro = UpToPro.objects.first()
            
            if not latest_uptopro:
                return Response({
                    'success': False,
                    'message': 'No UpToPro object found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = UpToProSerializer(latest_uptopro, context={'request': request})
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting latest UpToPro: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to get latest UpToPro'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
