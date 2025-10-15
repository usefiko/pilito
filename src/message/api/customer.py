from rest_framework.views import APIView
from rest_framework.response import Response
from message.serializers import ConversationSerializer,CustomerSerializer,CustomerUpdateSerializer
from rest_framework import status, filters
from message.models import Conversation,Customer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.http import HttpResponse
import csv
from io import StringIO
from django.utils import timezone


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 500


class CustomersListAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    serializer_class = CustomerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name','last_name','phone_number','description']
    ordering_fields = ['created_at','updated_at']
    filterset_fields = ['created_at','updated_at','source','email','tag__name']
    @swagger_auto_schema()
    def get(self, request, format=None):
        query = self.filter_queryset(Customer.objects.filter(conversations__user=self.request.user).distinct())
        page = self.paginate_queryset(query)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(query, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class CustomerItemAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerSerializer
    
    def _get_customer_and_check_permission(self, customer_id, user):
        """Get customer and check if user has permission to access it"""
        try:
            customer = Customer.objects.get(id=customer_id)
            # Check if user has any conversations with this customer
            if not customer.conversations.filter(user=user).exists():
                return None, Response(
                    {"error": "You don't have permission to access this customer"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            return customer, None
        except Customer.DoesNotExist:
            return None, Response(
                {"error": "Customer not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @swagger_auto_schema(
        operation_description="Get customer details",
        responses={
            200: CustomerSerializer,
            403: "Permission denied",
            404: "Customer not found"
        }
    )
    def get(self, request, *args, **kwargs):
        customer, error_response = self._get_customer_and_check_permission(
            self.kwargs["id"], request.user
        )
        if error_response:
            return error_response
            
        serializer = self.serializer_class(customer)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Update customer (full update)",
        request_body=CustomerUpdateSerializer,
        responses={
            200: CustomerSerializer,
            400: "Bad request",
            403: "Permission denied", 
            404: "Customer not found"
        }
    )
    def put(self, request, *args, **kwargs):
        customer, error_response = self._get_customer_and_check_permission(
            self.kwargs["id"], request.user
        )
        if error_response:
            return error_response
        
        serializer = CustomerUpdateSerializer(customer, data=request.data)
        if serializer.is_valid():
            updated_customer = serializer.save()
            
            # Send websocket notification about the customer update
            from message.websocket_utils import notify_customer_updated
            notify_customer_updated(updated_customer)
            
            response_serializer = CustomerSerializer(updated_customer)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Update customer (partial update)",
        request_body=CustomerUpdateSerializer,
        responses={
            200: CustomerSerializer,
            400: "Bad request",
            403: "Permission denied",
            404: "Customer not found"
        }
    )
    def patch(self, request, *args, **kwargs):
        customer, error_response = self._get_customer_and_check_permission(
            self.kwargs["id"], request.user
        )
        if error_response:
            return error_response
        
        serializer = CustomerUpdateSerializer(customer, data=request.data, partial=True)
        if serializer.is_valid():
            updated_customer = serializer.save()
            
            # Send websocket notification about the customer update
            from message.websocket_utils import notify_customer_updated
            notify_customer_updated(updated_customer)
            
            response_serializer = CustomerSerializer(updated_customer)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Delete customer and all related conversations and messages",
        responses={
            204: "Customer deleted successfully",
            403: "Permission denied",
            404: "Customer not found"
        }
    )
    def delete(self, request, *args, **kwargs):
        customer, error_response = self._get_customer_and_check_permission(
            self.kwargs["id"], request.user
        )
        if error_response:
            return error_response
        
        # Store customer ID and user ID for websocket notification
        customer_id = customer.id
        user_id = request.user.id
        
        # Delete the customer (this will cascade delete all related conversations and messages)
        customer.delete()
        
        # Send websocket notification about the deletion
        from message.websocket_utils import notify_customer_deleted
        notify_customer_deleted(customer_id, user_id)
        
        return Response(
            {"message": "Customer deleted successfully"}, 
            status=status.HTTP_204_NO_CONTENT
        )


class CustomerBulkDeleteAPIView(GenericAPIView):
    """API for bulk deleting customers based on IDs with filtering support"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name','last_name','phone_number','description']
    ordering_fields = ['created_at','updated_at']
    filterset_fields = ['created_at','updated_at','source','email','tag__name']
    
    @swagger_auto_schema(
        operation_description="Bulk delete customers by IDs with optional filtering",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'customer_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description='List of customer IDs to delete. If empty, all filtered customers will be deleted.'
                )
            },
            required=[]
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'deleted_count': openapi.Schema(type=openapi.TYPE_INTEGER)
                }
            ),
            400: "Bad request",
            403: "Permission denied"
        }
    )
    def post(self, request):
        customer_ids = request.data.get('customer_ids', [])
        
        # Start with base queryset filtered by user's customers
        queryset = Customer.objects.filter(conversations__user=request.user).distinct()
        
        # Apply filters (search, ordering, filterset)
        filtered_queryset = self.filter_queryset(queryset)
        
        # If specific IDs provided, filter further by those IDs
        if customer_ids:
            if not isinstance(customer_ids, list):
                return Response(
                    {"error": "customer_ids must be a list of integers"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate all IDs are integers
            try:
                customer_ids = [int(id) for id in customer_ids]
            except (ValueError, TypeError):
                return Response(
                    {"error": "All customer IDs must be valid integers"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            filtered_queryset = filtered_queryset.filter(id__in=customer_ids)
        
        # Count customers to be deleted
        delete_count = filtered_queryset.count()
        
        if delete_count == 0:
            return Response(
                {"message": "No customers found matching the criteria", "deleted_count": 0},
                status=status.HTTP_200_OK
            )
        
        # Store customer IDs and user ID for websocket notification
        deleted_customer_ids = list(filtered_queryset.values_list('id', flat=True))
        user_id = request.user.id
        
        # Perform bulk delete
        filtered_queryset.delete()
        
        # Send websocket notifications for each deleted customer
        from message.websocket_utils import notify_customer_deleted
        for customer_id in deleted_customer_ids:
            notify_customer_deleted(customer_id, user_id)
        
        return Response(
            {
                "message": f"Successfully deleted {delete_count} customer(s)",
                "deleted_count": delete_count
            },
            status=status.HTTP_200_OK
        )


class CustomerBulkExportAPIView(GenericAPIView):
    """API for bulk exporting customers to CSV based on IDs with filtering support"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name','last_name','phone_number','description']
    ordering_fields = ['created_at','updated_at']
    filterset_fields = ['created_at','updated_at','source','email','tag__name']
    
    @swagger_auto_schema(
        operation_description="Bulk export customers to CSV by IDs with optional filtering",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'customer_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description='List of customer IDs to export. If empty, all filtered customers will be exported.'
                )
            },
            required=[]
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_BINARY,
                description='CSV file download'
            ),
            400: "Bad request",
            403: "Permission denied"
        }
    )
    def post(self, request):
        customer_ids = request.data.get('customer_ids', [])
        
        # Start with base queryset filtered by user's customers
        queryset = Customer.objects.filter(conversations__user=request.user).distinct()
        
        # Apply filters (search, ordering, filterset)
        filtered_queryset = self.filter_queryset(queryset)
        
        # If specific IDs provided, filter further by those IDs
        if customer_ids:
            if not isinstance(customer_ids, list):
                return Response(
                    {"error": "customer_ids must be a list of integers"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate all IDs are integers
            try:
                customer_ids = [int(id) for id in customer_ids]
            except (ValueError, TypeError):
                return Response(
                    {"error": "All customer IDs must be valid integers"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            filtered_queryset = filtered_queryset.filter(id__in=customer_ids)
        
        # Prefetch related tags for efficiency
        customers = filtered_queryset.prefetch_related('tag').order_by('-created_at')
        
        if not customers.exists():
            return Response(
                {"error": "No customers found matching the criteria"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = [
            'ID', 'First Name', 'Last Name', 'Username', 'Email', 'Phone Number',
            'Description', 'Source', 'Source ID', 'Tags', 'Created At', 'Updated At'
        ]
        writer.writerow(headers)
        
        # Write customer data
        for customer in customers:
            # Get tags as comma-separated string
            tags = ', '.join([tag.name for tag in customer.tag.all()])
            
            row = [
                customer.id,
                customer.first_name or '',
                customer.last_name or '',
                customer.username or '',
                customer.email or '',
                customer.phone_number or '',
                customer.description or '',
                customer.source,
                customer.source_id or '',
                tags,
                customer.created_at.strftime('%Y-%m-%d %H:%M:%S') if customer.created_at else '',
                customer.updated_at.strftime('%Y-%m-%d %H:%M:%S') if customer.updated_at else ''
            ]
            writer.writerow(row)
        
        # Prepare response
        output.seek(0)
        csv_content = output.getvalue()
        output.close()
        
        # Create HTTP response with CSV
        response = HttpResponse(
            csv_content,
            content_type='text/csv'
        )
        
        # Generate filename with timestamp
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'customers_export_{timestamp}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response