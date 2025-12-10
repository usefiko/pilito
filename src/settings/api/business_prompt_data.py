from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from settings.models import BusinessPrompt, BusinessPromptData
from settings.serializers import (
    BusinessPromptSerializer,
    BusinessPromptListSerializer,
    BusinessPromptDataSerializer
)


class BusinessPromptListAPIView(GenericAPIView):
    """
    API for listing all BusinessPrompts.
    Public read-only access.
    """
    serializer_class = BusinessPromptListSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-updated_at']

    @swagger_auto_schema(
        operation_description="Get all BusinessPrompts with their data count",
        manual_parameters=[
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Search by name. Example: ?search=sales",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Order results. Options: name, -name, created_at, -created_at. Example: ?ordering=-created_at",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: BusinessPromptListSerializer(many=True),
            400: "Bad request"
        }
    )
    def get(self, request, *args, **kwargs):
        """Get all BusinessPrompts"""
        try:
            queryset = BusinessPrompt.objects.all()
            filtered_queryset = self.filter_queryset(queryset)
            serializer = self.serializer_class(filtered_queryset, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class BusinessPromptDetailAPIView(APIView):
    """
    API for getting a single BusinessPrompt with all its data.
    Public read-only access.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Get a BusinessPrompt with all its associated data",
        responses={
            200: BusinessPromptSerializer,
            404: "BusinessPrompt not found"
        }
    )
    def get(self, request, business_id):
        """Get a BusinessPrompt with all its data"""
        try:
            business = BusinessPrompt.objects.prefetch_related('prompt_data').get(id=business_id)
        except BusinessPrompt.DoesNotExist:
            return Response(
                {"error": "BusinessPrompt not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = BusinessPromptSerializer(business, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class BusinessPromptDataListAPIView(GenericAPIView):
    """
    API for listing all BusinessPromptData.
    Public read-only access.
    """
    serializer_class = BusinessPromptDataSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['key', 'value']
    ordering_fields = ['key', 'created_at', 'updated_at']
    ordering = ['-created_at']
    filterset_fields = ['business', 'key']

    @swagger_auto_schema(
        operation_description="Get all BusinessPromptData entries",
        manual_parameters=[
            openapi.Parameter(
                'business',
                openapi.IN_QUERY,
                description="Filter by BusinessPrompt ID. Example: ?business=1",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'key',
                openapi.IN_QUERY,
                description="Filter by key name. Example: ?key=logo",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Search in key and value fields. Example: ?search=config",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Order results. Options: key, -key, created_at, -created_at. Example: ?ordering=-created_at",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: BusinessPromptDataSerializer(many=True),
            400: "Bad request"
        }
    )
    def get(self, request, *args, **kwargs):
        """Get all BusinessPromptData"""
        try:
            queryset = BusinessPromptData.objects.select_related('business').all()
            filtered_queryset = self.filter_queryset(queryset)
            serializer = self.serializer_class(filtered_queryset, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class BusinessPromptDataItemAPIView(APIView):
    """
    API for getting a single BusinessPromptData entry.
    Public read-only access.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Get a specific BusinessPromptData by ID",
        responses={
            200: BusinessPromptDataSerializer,
            404: "BusinessPromptData not found"
        }
    )
    def get(self, request, data_id):
        """Get a specific BusinessPromptData"""
        try:
            data = BusinessPromptData.objects.select_related('business').get(id=data_id)
        except BusinessPromptData.DoesNotExist:
            return Response(
                {"error": "BusinessPromptData not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = BusinessPromptDataSerializer(data, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class BusinessPromptDataByBusinessAPIView(GenericAPIView):
    """
    API for getting all data for a specific BusinessPrompt.
    URL: /api/settings/business-prompt/{business_id}/data/
    Public read-only access.
    """
    serializer_class = BusinessPromptDataSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['key', 'value']
    ordering_fields = ['key', 'created_at']
    ordering = ['-created_at']

    @swagger_auto_schema(
        operation_description="Get all data entries for a specific BusinessPrompt",
        manual_parameters=[
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Search in key and value fields",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Order results. Options: key, -key, created_at, -created_at",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: BusinessPromptDataSerializer(many=True),
            404: "BusinessPrompt not found"
        }
    )
    def get(self, request, business_id):
        """Get all data for a specific BusinessPrompt"""
        try:
            business = BusinessPrompt.objects.get(id=business_id)
        except BusinessPrompt.DoesNotExist:
            return Response(
                {"error": "BusinessPrompt not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        queryset = BusinessPromptData.objects.filter(business=business)
        filtered_queryset = self.filter_queryset(queryset)
        serializer = self.serializer_class(filtered_queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class BusinessPromptDataByKeyAPIView(APIView):
    """
    API for getting a specific data entry by BusinessPrompt ID and key.
    URL: /api/settings/business-prompt/{business_id}/data/{key}/
    Public read-only access.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Get a specific data entry by BusinessPrompt ID and key name",
        responses={
            200: BusinessPromptDataSerializer,
            404: "Data not found"
        }
    )
    def get(self, request, business_id, key):
        """Get a specific data entry by business and key"""
        try:
            data = BusinessPromptData.objects.select_related('business').get(
                business_id=business_id,
                key=key
            )
        except BusinessPromptData.DoesNotExist:
            return Response(
                {"error": f"Data with key '{key}' not found for this BusinessPrompt"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = BusinessPromptDataSerializer(data, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

