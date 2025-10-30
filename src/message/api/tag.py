from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from message.serializers import TagSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, filters
from django_filters.rest_framework import DjangoFilterBackend
from message.models import Tag
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class TagsAPIView(GenericAPIView):
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']  # Search by tag name
    ordering_fields = ['name', 'created_at']  # Allow ordering by name or creation date
    ordering = ['-created_at']  # Default ordering (newest first)
    filterset_fields = ['created_at']  # Filter by creation date
    
    @swagger_auto_schema(
        operation_description="Get all tags created by the authenticated user with search and filter support",
        manual_parameters=[
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Search tags by name (case-insensitive partial match). Example: ?search=vip",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Order results by field. Use '-' for descending. Options: name, -name, created_at, -created_at. Example: ?ordering=name",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'created_at',
                openapi.IN_QUERY,
                description="Filter by creation date (exact match). Format: YYYY-MM-DD. Example: ?created_at=2024-01-15",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'name': openapi.Schema(type=openapi.TYPE_STRING),
                        'created_by': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                    }
                )
            ),
            400: "Bad request"
        }
    )
    def get(self, request, *args, **kwargs):
        try:
            # Get tags created by the user, excluding system tags
            queryset = Tag.objects.filter(
                created_by=request.user
            ).exclude(name__in=["Telegram", "Whatsapp", "Instagram"])
            
            # Apply filters (search, ordering, filterset)
            filtered_queryset = self.filter_queryset(queryset)
            
            serializer = self.serializer_class(filtered_queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Create new tag(s). Supports creating single tag, multiple tags, or tags from a list of names.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Tag name for single tag creation. Example: "VIP"'
                ),
                'names': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description='Array of tag names for bulk creation. Example: ["VIP", "Premium", "Active"]'
                )
            },
            example={
                "names": ["VIP", "Premium", "Enterprise"]
            }
        ),
        responses={
            201: TagSerializer(many=True),
            400: "Bad request - Invalid tag data"
        }
    )
    def post(self, request, *args, **kwargs):
        try:
            data = request.data

            # Support multiple input formats: list of objects, list of names, or single object
            if isinstance(data, dict) and "names" in data and isinstance(data["names"], list):
                prepared = [{"name": str(name).strip()} for name in data["names"] if str(name).strip()]
                if not prepared:
                    return Response({"detail": "No valid tag names provided."}, status=status.HTTP_400_BAD_REQUEST)
                serializer = self.serializer_class(data=prepared, many=True)
            elif isinstance(data, list):
                serializer = self.serializer_class(data=data, many=True)
            else:
                serializer = self.serializer_class(data=data)

            if serializer.is_valid():
                # Set created_by when creating new tags
                if isinstance(serializer.validated_data, list):
                    # For list of tags
                    tags = [Tag(created_by=request.user, **item) for item in serializer.validated_data]
                    Tag.objects.bulk_create(tags, ignore_conflicts=True)
                    return Response(TagSerializer(tags, many=True).data, status=status.HTTP_201_CREATED)
                else:
                    # For single tag
                    serializer.save(created_by=request.user)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class TagItemAPIView(APIView):
    """API for managing individual tags (get, update, delete)"""
    permission_classes = [IsAuthenticated]
    
    def _get_tag_and_check_permission(self, tag_id, user):
        """Get tag and check if user has permission to modify it"""
        try:
            tag = Tag.objects.get(id=tag_id)
            
            # Check if user is the owner
            if tag.created_by != user:
                return None, Response(
                    {"error": "You don't have permission to modify this tag"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Prevent modification of system tags
            if tag.name in ["Telegram", "Whatsapp", "Instagram"]:
                return None, Response(
                    {"error": "System tags cannot be modified or deleted"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            return tag, None
        except Tag.DoesNotExist:
            return None, Response(
                {"error": "Tag not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @swagger_auto_schema(
        operation_description="Get a specific tag by ID",
        responses={
            200: TagSerializer,
            403: "Permission denied",
            404: "Tag not found"
        }
    )
    def get(self, request, tag_id):
        """Get a specific tag"""
        tag, error_response = self._get_tag_and_check_permission(tag_id, request.user)
        if error_response:
            return error_response
        
        serializer = TagSerializer(tag)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Update a tag",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name'],
            properties={
                'name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='New tag name. Example: "VIP Plus"'
                )
            }
        ),
        responses={
            200: TagSerializer,
            400: "Bad request",
            403: "Permission denied",
            404: "Tag not found"
        }
    )
    def put(self, request, tag_id):
        """Update a tag"""
        tag, error_response = self._get_tag_and_check_permission(tag_id, request.user)
        if error_response:
            return error_response
        
        serializer = TagSerializer(tag, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Delete a tag",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'tag_name': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ),
            403: "Permission denied - Cannot delete system tags or tags owned by others",
            404: "Tag not found"
        }
    )
    def delete(self, request, tag_id):
        """Delete a tag"""
        tag, error_response = self._get_tag_and_check_permission(tag_id, request.user)
        if error_response:
            return error_response
        
        tag_name = tag.name
        tag.delete()
        
        return Response(
            {
                "message": f"Tag '{tag_name}' deleted successfully",
                "tag_name": tag_name
            }, 
            status=status.HTTP_200_OK
        )


class TagBulkDeleteAPIView(APIView):
    """API for bulk deleting tags"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Bulk delete tags by IDs",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['tag_ids'],
            properties={
                'tag_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description='List of tag IDs to delete. Example: [1, 2, 3]'
                )
            }
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'deleted_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'deleted_tags': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING)
                    ),
                    'skipped_tags': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING),
                        description='Tags that could not be deleted (system tags or not owned by user)'
                    )
                }
            ),
            400: "Bad request - Invalid tag IDs"
        }
    )
    def post(self, request):
        """Bulk delete tags by IDs"""
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
        
        # Get tags that exist and belong to the user
        tags = Tag.objects.filter(
            id__in=tag_ids,
            created_by=request.user
        )
        
        # Separate system tags and user tags
        system_tag_names = ["Telegram", "Whatsapp", "Instagram"]
        deletable_tags = tags.exclude(name__in=system_tag_names)
        system_tags = tags.filter(name__in=system_tag_names)
        
        # Track what was deleted and what was skipped
        deleted_tag_names = list(deletable_tags.values_list('name', flat=True))
        skipped_tag_names = list(system_tags.values_list('name', flat=True))
        
        # Check for tags that don't exist or don't belong to user
        existing_ids = set(tags.values_list('id', flat=True))
        missing_ids = set(tag_ids) - existing_ids
        if missing_ids:
            skipped_tag_names.append(f"Tag IDs not found or not owned: {list(missing_ids)}")
        
        # Delete the tags
        deleted_count = deletable_tags.delete()[0]
        
        response_data = {
            "message": f"Successfully deleted {deleted_count} tag(s)",
            "deleted_count": deleted_count,
            "deleted_tags": deleted_tag_names
        }
        
        if skipped_tag_names:
            response_data["skipped_tags"] = skipped_tag_names
        
        return Response(response_data, status=status.HTTP_200_OK)

