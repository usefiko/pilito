from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Max
from django.utils import timezone
from settings.models import SupportTicket, SupportMessage
from settings.serializers import (
    SupportTicketSerializer,
    SupportTicketListSerializer,
    CreateSupportTicketSerializer,
    SupportMessageSerializer
)
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi



class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 500


class SupportTicketListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List all tickets for the authenticated user
    POST: Create a new support ticket
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # Support file uploads
    pagination_class = CustomPagination
    
    def get_queryset(self):
        user = self.request.user
        # Regular users only see their own tickets
        # Staff users see all tickets only if they use the admin endpoints
        return SupportTicket.objects.filter(user=user).prefetch_related('messages__attachments', 'messages__sender')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateSupportTicketSerializer
        return SupportTicketListSerializer
    
    @swagger_auto_schema(
        operation_description="Create a new support ticket with optional file attachments",
        request_body=None,  # Don't introspect serializer, use manual_parameters instead
        manual_parameters=[
            openapi.Parameter('title', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description='Ticket title'),
            openapi.Parameter('department', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description='Department (technical, billing, general)'),
            openapi.Parameter('initial_message', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description='Initial message content'),
            openapi.Parameter('initial_attachments', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description='File attachments (multiple allowed)'),
        ],
        consumes=['multipart/form-data'],
        responses={201: SupportTicketSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        # User is already set in the serializer's create method
        serializer.save()


class SupportTicketDetailAPIView(generics.RetrieveUpdateAPIView):
    """
    GET: Retrieve ticket details with all messages
    PATCH: Update ticket (status, etc.)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SupportTicketSerializer
    
    def get_queryset(self):
        user = self.request.user
        # Users can only access their own tickets
        return SupportTicket.objects.filter(user=user).prefetch_related('messages__attachments', 'messages__sender')
    
    def get_object(self):
        ticket_id = self.kwargs.get('pk')
        return get_object_or_404(self.get_queryset(), id=ticket_id)


class SupportTicketCloseAPIView(APIView):
    """
    POST: Close a support ticket
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk, *args, **kwargs):
        user = request.user
        
        if user.is_staff:
            ticket = get_object_or_404(SupportTicket, id=pk)
        else:
            ticket = get_object_or_404(SupportTicket, id=pk, user=user)
        
        if ticket.status == 'closed':
            return Response({'detail': 'Ticket is already closed.'}, status=status.HTTP_400_BAD_REQUEST)
        
        ticket.status = 'closed'
        ticket.save()
        
        # Add a system message indicating the ticket was closed
        SupportMessage.objects.create(
            ticket=ticket,
            content=f"Ticket closed by {'Support Team' if user.is_staff else 'Customer'}.",
            is_from_support=user.is_staff,
            sender=user
        )
        
        serializer = SupportTicketSerializer(ticket, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class SupportMessageListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List all messages for a specific ticket
    POST: Send a new message to a ticket
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SupportMessageSerializer
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = CustomPagination
    
    def get_queryset(self):
        ticket_id = self.kwargs.get('ticket_id')
        user = self.request.user
        
        # Verify user has access to this ticket
        if user.is_staff:
            ticket = get_object_or_404(SupportTicket, id=ticket_id)
        else:
            ticket = get_object_or_404(SupportTicket, id=ticket_id, user=user)
        
        return SupportMessage.objects.filter(ticket=ticket).select_related('sender').prefetch_related('attachments').order_by('-created_at')
    
    @swagger_auto_schema(
        operation_description="Send a new message to a ticket with optional file attachments",
        request_body=None,  # Don't introspect serializer, use manual_parameters instead
        manual_parameters=[
            openapi.Parameter('content', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description='Message content'),
            openapi.Parameter('uploaded_files', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description='File attachments (multiple allowed)'),
            openapi.Parameter('files', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description='Alternative field for file attachments'),
        ],
        consumes=['multipart/form-data'],
        responses={201: SupportMessageSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        ticket_id = self.kwargs.get('ticket_id')
        user = self.request.user
        
        # Verify user has access to this ticket
        if user.is_staff:
            ticket = get_object_or_404(SupportTicket, id=ticket_id)
        else:
            ticket = get_object_or_404(SupportTicket, id=ticket_id, user=user)
        
        # Check if ticket is closed
        if ticket.status == 'closed':
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': 'Cannot send messages to a closed ticket.'})
        
        # Determine if this is from support
        is_from_support = user.is_staff
        
        # Save the message
        message = serializer.save(
            ticket=ticket,
            is_from_support=is_from_support,
            sender=user
        )
        
        # Update ticket status based on who sent the message
        if is_from_support:
            ticket.status = 'support_response'
        else:
            ticket.status = 'customer_reply'
        
        ticket.updated_at = timezone.now()
        ticket.save()


class SupportStaffTicketListAPIView(generics.ListAPIView):
    """
    GET: List all tickets for staff members (admin view)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SupportTicketListSerializer
    pagination_class = CustomPagination
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only staff members can access this endpoint.")
        
        # Staff can see all tickets
        return SupportTicket.objects.all().prefetch_related('messages__attachments', 'messages__sender')


class SupportStatsAPIView(APIView):
    """
    GET: Get support statistics (for admin dashboard)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # Only staff can access stats
        if not request.user.is_staff:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        
        total_tickets = SupportTicket.objects.count()
        open_tickets = SupportTicket.objects.filter(status__in=['open', 'under_review', 'support_response', 'customer_reply']).count()
        closed_tickets = SupportTicket.objects.filter(status='closed').count()
        
        # Status breakdown
        status_counts = SupportTicket.objects.values('status').annotate(count=Count('id'))
        
        # Recent tickets (last 7 days)
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        recent_tickets = SupportTicket.objects.filter(created_at__gte=week_ago).count()
        
        stats = {
            'total_tickets': total_tickets,
            'open_tickets': open_tickets,
            'closed_tickets': closed_tickets,
            'recent_tickets': recent_tickets,
            'status_breakdown': {item['status']: item['count'] for item in status_counts}
        }
        
        return Response(stats, status=status.HTTP_200_OK) 