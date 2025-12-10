from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import status, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from message.models import CustomerData, Customer
from message.serializers import (
    CustomerDataSerializer, 
    CustomerDataCreateSerializer, 
    CustomerDataUpdateSerializer
)


class CustomerDataListAPIView(GenericAPIView):
    """
    API for listing and creating CustomerData.
    Each user can create custom key-value data for any customer.
    Supports both text values and file uploads.
    
    For file uploads, use multipart/form-data content type.
    """
    serializer_class = CustomerDataSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['key', 'value']
    ordering_fields = ['key', 'created_at', 'updated_at']
    ordering = ['-created_at']
    filterset_fields = ['customer', 'key']

    @swagger_auto_schema(
        operation_description="Get all customer data created by the authenticated user. Returns both text values and file URLs.",
        manual_parameters=[
            openapi.Parameter(
                'customer',
                openapi.IN_QUERY,
                description="Filter by customer ID. Example: ?customer=1",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'key',
                openapi.IN_QUERY,
                description="Filter by key name. Example: ?key=birthday",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Search in key and value fields. Example: ?search=email",
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
            200: CustomerDataSerializer(many=True),
            400: "Bad request"
        }
    )
    def get(self, request, *args, **kwargs):
        """Get all customer data for the authenticated user"""
        try:
            queryset = CustomerData.objects.filter(user=request.user)
            filtered_queryset = self.filter_queryset(queryset)
            serializer = self.serializer_class(filtered_queryset, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="""Create new customer data (key-value pair and/or file for a customer).
        
**For text data:** Send JSON with customer, key, and value.
**For file upload:** Use multipart/form-data with customer, key, and file fields.
**For both:** Use multipart/form-data with all fields.""",
        manual_parameters=[
            openapi.Parameter(
                'customer',
                openapi.IN_FORM,
                description="Customer ID",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'key',
                openapi.IN_FORM,
                description="Data key name (e.g., 'contract', 'id_card', 'notes')",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'value',
                openapi.IN_FORM,
                description="Text value (optional if file is provided)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'file',
                openapi.IN_FORM,
                description="File attachment (optional if value is provided)",
                type=openapi.TYPE_FILE,
                required=False
            ),
        ],
        responses={
            201: CustomerDataSerializer,
            400: "Bad request - Invalid data or duplicate key"
        }
    )
    def post(self, request, *args, **kwargs):
        """Create new customer data with optional file upload"""
        try:
            serializer = CustomerDataCreateSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                customer_data = serializer.save(user=request.user)
                response_serializer = CustomerDataSerializer(customer_data, context={'request': request})
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class CustomerDataItemAPIView(APIView):
    """API for managing individual customer data items (get, update, delete).
    Supports file uploads using multipart/form-data."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def _get_customer_data(self, data_id, user):
        """Get customer data and check ownership"""
        try:
            customer_data = CustomerData.objects.get(id=data_id, user=user)
            return customer_data, None
        except CustomerData.DoesNotExist:
            return None, Response(
                {"error": "Customer data not found or you don't have permission to access it"},
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_description="Get a specific customer data by ID. Returns text value and file URL if available.",
        responses={
            200: CustomerDataSerializer,
            404: "Customer data not found"
        }
    )
    def get(self, request, data_id):
        """Get a specific customer data"""
        customer_data, error_response = self._get_customer_data(data_id, request.user)
        if error_response:
            return error_response
        
        serializer = CustomerDataSerializer(customer_data, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="""Update customer data. Supports partial updates.
        
**Update text value:** Send JSON or form-data with 'value' field.
**Update/replace file:** Use multipart/form-data with 'file' field.
**Remove file:** Send `remove_file: true` to delete the attached file.
**Update key:** Send 'key' field (note: duplicate key validation applies).""",
        manual_parameters=[
            openapi.Parameter(
                'key',
                openapi.IN_FORM,
                description="New key name (optional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'value',
                openapi.IN_FORM,
                description="New text value (optional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'file',
                openapi.IN_FORM,
                description="New file to upload/replace (optional)",
                type=openapi.TYPE_FILE,
                required=False
            ),
            openapi.Parameter(
                'remove_file',
                openapi.IN_FORM,
                description="Set to 'true' to remove the existing file without replacing",
                type=openapi.TYPE_BOOLEAN,
                required=False
            ),
        ],
        responses={
            200: CustomerDataSerializer,
            400: "Bad request",
            404: "Customer data not found"
        }
    )
    def put(self, request, data_id):
        """Update customer data with optional file upload/removal"""
        customer_data, error_response = self._get_customer_data(data_id, request.user)
        if error_response:
            return error_response
        
        serializer = CustomerDataUpdateSerializer(customer_data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Refresh from database to get updated file info
            customer_data.refresh_from_db()
            response_serializer = CustomerDataSerializer(customer_data, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete customer data. Also deletes any attached file.",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'deleted_key': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ),
            404: "Customer data not found"
        }
    )
    def delete(self, request, data_id):
        """Delete customer data and any attached file"""
        customer_data, error_response = self._get_customer_data(data_id, request.user)
        if error_response:
            return error_response
        
        key = customer_data.key
        # Delete file if exists
        if customer_data.file:
            customer_data.file.delete(save=False)
        customer_data.delete()
        
        return Response(
            {
                "message": f"Customer data '{key}' deleted successfully",
                "deleted_key": key
            },
            status=status.HTTP_200_OK
        )


class CustomerDataByCustomerAPIView(GenericAPIView):
    """
    API for getting all data for a specific customer.
    URL: /api/message/customer/<customer_id>/data/
    Returns both text values and file URLs.
    """
    serializer_class = CustomerDataSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['key', 'value']
    ordering_fields = ['key', 'created_at']
    ordering = ['-created_at']

    @swagger_auto_schema(
        operation_description="Get all custom data for a specific customer created by the authenticated user. Returns text values and file URLs.",
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
            200: CustomerDataSerializer(many=True),
            404: "Customer not found"
        }
    )
    def get(self, request, customer_id):
        """Get all data for a specific customer"""
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return Response(
                {"error": "Customer not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        queryset = CustomerData.objects.filter(customer=customer, user=request.user)
        filtered_queryset = self.filter_queryset(queryset)
        serializer = self.serializer_class(filtered_queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomerDataBulkDeleteAPIView(APIView):
    """API for bulk deleting customer data. Also deletes any attached files."""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Bulk delete customer data by IDs. Also deletes any attached files.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['data_ids'],
            properties={
                'data_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description='List of customer data IDs to delete. Example: [1, 2, 3]'
                )
            }
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'deleted_count': openapi.Schema(type=openapi.TYPE_INTEGER)
                }
            ),
            400: "Bad request"
        }
    )
    def post(self, request):
        """Bulk delete customer data by IDs"""
        data_ids = request.data.get('data_ids', [])
        
        if not isinstance(data_ids, list):
            return Response(
                {"error": "data_ids must be a list of integers"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not data_ids:
            return Response(
                {"error": "data_ids cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            data_ids = [int(data_id) for data_id in data_ids]
        except (ValueError, TypeError):
            return Response(
                {"error": "All data IDs must be valid integers"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get items to delete (to clean up files)
        items_to_delete = CustomerData.objects.filter(
            id__in=data_ids,
            user=request.user
        )
        
        # Delete files first
        for item in items_to_delete:
            if item.file:
                item.file.delete(save=False)
        
        # Now delete the records
        deleted_count = items_to_delete.delete()[0]
        
        return Response(
            {
                "message": f"Successfully deleted {deleted_count} customer data item(s)",
                "deleted_count": deleted_count
            },
            status=status.HTTP_200_OK
        )

