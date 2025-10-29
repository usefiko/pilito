from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from message.models import Customer, Tag
from message.serializers import TagSerializer


class CustomerTagsAPIView(APIView):
    """
    API for managing tags on a specific customer
    GET: Get all tags for a customer
    POST: Add tags to a customer (without removing existing ones)
    PUT: Replace all customer tags with new tags
    DELETE: Remove specific tags from a customer
    """
    permission_classes = [IsAuthenticated]
    
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
        operation_description="Get all tags for a specific customer",
        manual_parameters=[
            openapi.Parameter(
                'customer_id',
                openapi.IN_PATH,
                description="Customer ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'customer_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'tags': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        )
                    )
                }
            ),
            403: "Permission denied",
            404: "Customer not found"
        }
    )
    def get(self, request, customer_id):
        """Get all tags for a specific customer"""
        customer, error_response = self._get_customer_and_check_permission(customer_id, request.user)
        if error_response:
            return error_response
        
        # Exclude system tags (Instagram, Telegram, Whatsapp)
        tags = customer.tag.exclude(name__in=["Telegram", "Whatsapp", "Instagram"]).order_by('name')
        serializer = TagSerializer(tags, many=True)
        
        return Response({
            'customer_id': customer.id,
            'tags': serializer.data
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Add tags to a customer (keeps existing tags)",
        manual_parameters=[
            openapi.Parameter(
                'customer_id',
                openapi.IN_PATH,
                description="Customer ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['tag_ids'],
            properties={
                'tag_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description='List of tag IDs to add to the customer. Example: [1, 2, 3]'
                )
            }
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'customer_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'tags': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        )
                    )
                }
            ),
            400: "Bad request - Invalid tag IDs",
            403: "Permission denied",
            404: "Customer not found"
        }
    )
    def post(self, request, customer_id):
        """Add tags to a customer (without removing existing tags)"""
        customer, error_response = self._get_customer_and_check_permission(customer_id, request.user)
        if error_response:
            return error_response
        
        tag_ids = request.data.get('tag_ids', [])
        
        if not isinstance(tag_ids, list):
            return Response(
                {"error": "tag_ids must be a list of integers"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not tag_ids:
            return Response(
                {"error": "tag_ids cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate all IDs are integers
        try:
            tag_ids = [int(tag_id) for tag_id in tag_ids]
        except (ValueError, TypeError):
            return Response(
                {"error": "All tag IDs must be valid integers"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if all tags exist
        tags = Tag.objects.filter(id__in=tag_ids)
        if len(tags) != len(tag_ids):
            existing_ids = set(tags.values_list('id', flat=True))
            invalid_ids = set(tag_ids) - existing_ids
            return Response(
                {"error": f"Invalid tag IDs: {sorted(list(invalid_ids))}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add tags to customer (keeps existing tags)
        customer.tag.add(*tags)
        
        # Send websocket notification
        from message.websocket_utils import notify_customer_updated
        notify_customer_updated(customer)
        
        # Get updated tags (excluding system tags)
        updated_tags = customer.tag.exclude(name__in=["Telegram", "Whatsapp", "Instagram"]).order_by('name')
        serializer = TagSerializer(updated_tags, many=True)
        
        return Response({
            'message': f'Successfully added {len(tags)} tag(s) to customer',
            'customer_id': customer.id,
            'tags': serializer.data
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Replace all customer tags with new tags",
        manual_parameters=[
            openapi.Parameter(
                'customer_id',
                openapi.IN_PATH,
                description="Customer ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['tag_ids'],
            properties={
                'tag_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description='List of tag IDs to set for the customer (replaces all existing tags). Use empty array [] to remove all tags. Example: [1, 2, 3]'
                )
            }
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'customer_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'tags': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        )
                    )
                }
            ),
            400: "Bad request - Invalid tag IDs",
            403: "Permission denied",
            404: "Customer not found"
        }
    )
    def put(self, request, customer_id):
        """Replace all customer tags with new tags"""
        customer, error_response = self._get_customer_and_check_permission(customer_id, request.user)
        if error_response:
            return error_response
        
        tag_ids = request.data.get('tag_ids', None)
        
        if tag_ids is None:
            return Response(
                {"error": "tag_ids is required. Use empty array [] to remove all tags"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(tag_ids, list):
            return Response(
                {"error": "tag_ids must be a list of integers"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If empty list, clear all tags
        if not tag_ids:
            # Keep system tags (Instagram, Telegram, Whatsapp)
            system_tags = customer.tag.filter(name__in=["Telegram", "Whatsapp", "Instagram"])
            customer.tag.set(system_tags)
            
            # Send websocket notification
            from message.websocket_utils import notify_customer_updated
            notify_customer_updated(customer)
            
            return Response({
                'message': 'Successfully removed all tags from customer',
                'customer_id': customer.id,
                'tags': []
            }, status=status.HTTP_200_OK)
        
        # Validate all IDs are integers
        try:
            tag_ids = [int(tag_id) for tag_id in tag_ids]
        except (ValueError, TypeError):
            return Response(
                {"error": "All tag IDs must be valid integers"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if all tags exist
        tags = Tag.objects.filter(id__in=tag_ids)
        if len(tags) != len(tag_ids):
            existing_ids = set(tags.values_list('id', flat=True))
            invalid_ids = set(tag_ids) - existing_ids
            return Response(
                {"error": f"Invalid tag IDs: {sorted(list(invalid_ids))}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Keep system tags and add new tags
        system_tags = customer.tag.filter(name__in=["Telegram", "Whatsapp", "Instagram"])
        all_tags = list(tags) + list(system_tags)
        customer.tag.set(all_tags)
        
        # Send websocket notification
        from message.websocket_utils import notify_customer_updated
        notify_customer_updated(customer)
        
        # Get updated tags (excluding system tags)
        updated_tags = customer.tag.exclude(name__in=["Telegram", "Whatsapp", "Instagram"]).order_by('name')
        serializer = TagSerializer(updated_tags, many=True)
        
        return Response({
            'message': f'Successfully replaced customer tags with {len(tags)} tag(s)',
            'customer_id': customer.id,
            'tags': serializer.data
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Remove specific tags from a customer",
        manual_parameters=[
            openapi.Parameter(
                'customer_id',
                openapi.IN_PATH,
                description="Customer ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['tag_ids'],
            properties={
                'tag_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description='List of tag IDs to remove from the customer. Example: [1, 2, 3]'
                )
            }
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'customer_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'tags': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        )
                    )
                }
            ),
            400: "Bad request - Invalid tag IDs",
            403: "Permission denied",
            404: "Customer not found"
        }
    )
    def delete(self, request, customer_id):
        """Remove specific tags from a customer"""
        customer, error_response = self._get_customer_and_check_permission(customer_id, request.user)
        if error_response:
            return error_response
        
        tag_ids = request.data.get('tag_ids', [])
        
        if not isinstance(tag_ids, list):
            return Response(
                {"error": "tag_ids must be a list of integers"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not tag_ids:
            return Response(
                {"error": "tag_ids cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate all IDs are integers
        try:
            tag_ids = [int(tag_id) for tag_id in tag_ids]
        except (ValueError, TypeError):
            return Response(
                {"error": "All tag IDs must be valid integers"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if all tags exist
        tags = Tag.objects.filter(id__in=tag_ids)
        if len(tags) != len(tag_ids):
            existing_ids = set(tags.values_list('id', flat=True))
            invalid_ids = set(tag_ids) - existing_ids
            return Response(
                {"error": f"Invalid tag IDs: {sorted(list(invalid_ids))}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Don't allow removing system tags
        system_tags_to_remove = tags.filter(name__in=["Telegram", "Whatsapp", "Instagram"])
        if system_tags_to_remove.exists():
            return Response(
                {"error": "Cannot remove system tags (Telegram, Whatsapp, Instagram)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove tags from customer
        customer.tag.remove(*tags)
        
        # Send websocket notification
        from message.websocket_utils import notify_customer_updated
        notify_customer_updated(customer)
        
        # Get updated tags (excluding system tags)
        updated_tags = customer.tag.exclude(name__in=["Telegram", "Whatsapp", "Instagram"]).order_by('name')
        serializer = TagSerializer(updated_tags, many=True)
        
        return Response({
            'message': f'Successfully removed {len(tags)} tag(s) from customer',
            'customer_id': customer.id,
            'tags': serializer.data
        }, status=status.HTTP_200_OK)


class CustomerSingleTagAPIView(APIView):
    """
    API for managing a single tag on a customer
    POST: Add a single tag to customer
    DELETE: Remove a single tag from customer
    """
    permission_classes = [IsAuthenticated]
    
    def _get_customer_and_check_permission(self, customer_id, user):
        """Get customer and check if user has permission to access it"""
        try:
            customer = Customer.objects.get(id=customer_id)
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
        operation_description="Add a single tag to a customer",
        manual_parameters=[
            openapi.Parameter(
                'customer_id',
                openapi.IN_PATH,
                description="Customer ID",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'tag_id',
                openapi.IN_PATH,
                description="Tag ID to add",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'customer_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'tag': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'name': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    )
                }
            ),
            400: "Tag already exists on customer",
            403: "Permission denied",
            404: "Customer or tag not found"
        }
    )
    def post(self, request, customer_id, tag_id):
        """Add a single tag to customer"""
        customer, error_response = self._get_customer_and_check_permission(customer_id, request.user)
        if error_response:
            return error_response
        
        # Get tag
        try:
            tag = Tag.objects.get(id=tag_id)
        except Tag.DoesNotExist:
            return Response(
                {"error": f"Tag with ID {tag_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if tag already exists
        if customer.tag.filter(id=tag_id).exists():
            return Response(
                {"error": f"Tag '{tag.name}' already exists on this customer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add tag
        customer.tag.add(tag)
        
        # Send websocket notification
        from message.websocket_utils import notify_customer_updated
        notify_customer_updated(customer)
        
        serializer = TagSerializer(tag)
        return Response({
            'message': f'Successfully added tag "{tag.name}" to customer',
            'customer_id': customer.id,
            'tag': serializer.data
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Remove a single tag from a customer",
        manual_parameters=[
            openapi.Parameter(
                'customer_id',
                openapi.IN_PATH,
                description="Customer ID",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'tag_id',
                openapi.IN_PATH,
                description="Tag ID to remove",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'customer_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                }
            ),
            400: "Cannot remove system tag or tag not on customer",
            403: "Permission denied",
            404: "Customer or tag not found"
        }
    )
    def delete(self, request, customer_id, tag_id):
        """Remove a single tag from customer"""
        customer, error_response = self._get_customer_and_check_permission(customer_id, request.user)
        if error_response:
            return error_response
        
        # Get tag
        try:
            tag = Tag.objects.get(id=tag_id)
        except Tag.DoesNotExist:
            return Response(
                {"error": f"Tag with ID {tag_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if it's a system tag
        if tag.name in ["Telegram", "Whatsapp", "Instagram"]:
            return Response(
                {"error": "Cannot remove system tags (Telegram, Whatsapp, Instagram)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if tag exists on customer
        if not customer.tag.filter(id=tag_id).exists():
            return Response(
                {"error": f"Tag '{tag.name}' does not exist on this customer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove tag
        customer.tag.remove(tag)
        
        # Send websocket notification
        from message.websocket_utils import notify_customer_updated
        notify_customer_updated(customer)
        
        return Response({
            'message': f'Successfully removed tag "{tag.name}" from customer',
            'customer_id': customer.id,
        }, status=status.HTTP_200_OK)

