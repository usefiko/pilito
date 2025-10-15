from django.contrib import admin
from message.models import Conversation,Tag,Customer,Message

class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'created_at', 'status')
    list_filter = ("created_at", "status")
admin.site.register(Conversation, ConversationAdmin)

class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')
admin.site.register(Tag, TagAdmin)

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'source',  'created_at', 'id')
    list_filter = ("source", "created_at")
    search_fields = (
        'first_name', 'last_name', 'username', 'phone_number', 'email', 'source_id'
    )
admin.site.register(Customer, CustomerAdmin)

class MessageAdmin(admin.ModelAdmin):
    list_display = (
        'content_preview', 'customer', 'type', 'conversation', 
        'token_display', 'is_ai_response', 'is_answered', 
        'feedback', 'feedback_at', 'created_at', 'id'
    )
    list_filter = ("type", "conversation", "feedback", "created_at", "is_ai_response")
    search_fields = ('content', 'feedback_comment')
    readonly_fields = ('feedback_at', 'created_at', 'input_tokens', 'output_tokens', 'total_tokens')
    
    # Show token fields in detail view
    fieldsets = (
        ('Message Info', {
            'fields': ('conversation', 'customer', 'type', 'content', 'is_ai_response', 'is_answered')
        }),
        ('Token Usage (AI Only)', {
            'fields': ('input_tokens', 'output_tokens', 'total_tokens'),
            'classes': ('collapse',),
            'description': 'Token usage information for AI-generated messages'
        }),
        ('Feedback', {
            'fields': ('feedback', 'feedback_at', 'feedback_comment'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """Show first 50 chars of content"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
    
    def token_display(self, obj):
        """Display token usage in a readable format"""
        if obj.is_ai_response and obj.total_tokens:
            return f"🎯 {obj.total_tokens:,} (↓{obj.input_tokens:,} ↑{obj.output_tokens:,})"
        return "—"
    token_display.short_description = 'Tokens (In/Out)'
    
    def get_queryset(self, request):
        """Optimize queryset to reduce database queries"""
        qs = super().get_queryset(request)
        return qs.select_related('customer', 'conversation')
    
    # نمایش بهتر feedback تو admin
    def feedback_display(self, obj):
        if obj.feedback == 'positive':
            return "👍 Positive"
        elif obj.feedback == 'negative':
            return "👎 Negative"
        return "😐 No feedback"
    feedback_display.short_description = "Feedback Status"

admin.site.register(Message, MessageAdmin)