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

