from rest_framework import serializers
from settings.models import Settings,TelegramChannel,InstagramChannel,AIPrompts,SupportTicket,SupportMessage,SupportMessageAttachment,UpToPro,AIBehaviorSettings,BusinessPrompt,BusinessPromptData

class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        #fields = '__all__'
        exclude = ['id']


class TelegramChannelSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = TelegramChannel
        fields = '__all__'
        
    def get_profile_picture_url(self, obj):
        """Return the full URL for the profile picture"""
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            return obj.profile_picture.url
        return None


class InstagramChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstagramChannel
        fields = '__all__'


class AIPromptsSerializer(serializers.ModelSerializer):
    """Serializer for AIPrompts model"""
    user_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = AIPrompts
        fields = ['id', 'user', 'user_name', 'manual_prompt', 
                 'knowledge_source', 'product_service', 'question_answer', 
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'user_name', 'created_at', 'updated_at']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username


class AIPromptsManualPromptSerializer(serializers.ModelSerializer):
    """Simple serializer for getting/updating only manual_prompt"""
    
    class Meta:
        model = AIPrompts
        fields = ['manual_prompt']


class AIPromptsCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating AIPrompts without user field"""
    
    class Meta:
        model = AIPrompts
        fields = ['manual_prompt', 'knowledge_source', 
                 'product_service', 'question_answer']


class SupportMessageAttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SupportMessageAttachment
        fields = ['id', 'file', 'file_url', 'original_filename', 'file_size', 'file_type', 'uploaded_at']
        read_only_fields = ['id', 'file_url', 'original_filename', 'file_size', 'file_type', 'uploaded_at']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class SupportMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    attachments = SupportMessageAttachmentSerializer(many=True, read_only=True)
    uploaded_files = serializers.ListField(
        child=serializers.FileField(max_length=10000000, allow_empty_file=True),
        write_only=True,
        required=False,
        allow_empty=True,
        help_text="Upload multiple files (use multipart/form-data)"
    )
    # Alternative field names for frontend compatibility
    attachments_upload = serializers.ListField(
        child=serializers.FileField(max_length=10000000, allow_empty_file=True),
        write_only=True,
        required=False,
        allow_empty=True,
        help_text="Upload multiple files (use multipart/form-data)"
    )
    files = serializers.ListField(
        child=serializers.FileField(max_length=10000000, allow_empty_file=True),
        write_only=True,
        required=False,
        allow_empty=True,
        help_text="Upload multiple files (use multipart/form-data)"
    )
    
    class Meta:
        model = SupportMessage
        fields = ['id', 'content', 'is_from_support', 'sender', 'sender_name', 'attachments', 'uploaded_files', 'attachments_upload', 'files', 'created_at']
        read_only_fields = ['id', 'created_at', 'sender_name', 'attachments']
    
    def get_sender_name(self, obj):
        if obj.is_from_support:
            return "Support Team"
        elif obj.sender:
            return f"{obj.sender.first_name} {obj.sender.last_name}".strip() or obj.sender.email
        return "Customer"
    
    def create(self, validated_data):
        # Check for files under different field names
        uploaded_files = (
            validated_data.pop('uploaded_files', []) or
            validated_data.pop('attachments_upload', []) or
            validated_data.pop('files', [])
        )
        message = super().create(validated_data)
        
        # Create attachments for uploaded files
        for file in uploaded_files:
            # Skip empty files
            if not file or file.size == 0:
                continue
                
            try:
                SupportMessageAttachment.objects.create(
                    message=message,
                    file=file
                )
            except Exception as e:
                # Log the error but don't fail the message creation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to create attachment for message {message.id}: {str(e)}")
                continue
        
        return message


class SupportTicketSerializer(serializers.ModelSerializer):
    messages = SupportMessageSerializer(many=True, read_only=True)
    user_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    department_display = serializers.CharField(source='get_department_display', read_only=True)
    message_count = serializers.SerializerMethodField()
    last_message_at = serializers.SerializerMethodField()
    
    class Meta:
        model = SupportTicket
        fields = ['id', 'title', 'user', 'user_name', 'department', 'department_display', 'status', 'status_display', 'created_at', 'updated_at', 'messages', 'message_count', 'last_message_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_name', 'status_display', 'department_display', 'message_count', 'last_message_at']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
    
    def get_message_count(self, obj):
        return obj.messages.count()
    
    def get_last_message_at(self, obj):
        last_message = obj.messages.last()
        return last_message.created_at if last_message else obj.created_at


class SupportTicketListSerializer(serializers.ModelSerializer):
    """Simplified serializer for ticket list view"""
    user_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    department_display = serializers.CharField(source='get_department_display', read_only=True)
    message_count = serializers.SerializerMethodField()
    last_message_at = serializers.SerializerMethodField()
    
    class Meta:
        model = SupportTicket
        fields = ['id', 'title', 'user_name', 'department', 'department_display', 'status', 'status_display', 'created_at', 'updated_at', 'message_count', 'last_message_at']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
    
    def get_message_count(self, obj):
        return obj.messages.count()
    
    def get_last_message_at(self, obj):
        last_message = obj.messages.last()
        return last_message.created_at if last_message else obj.created_at


class CreateSupportTicketSerializer(serializers.ModelSerializer):
    initial_message = serializers.CharField(write_only=True)
    initial_attachments = serializers.ListField(
        child=serializers.FileField(max_length=10000000, allow_empty_file=True),
        write_only=True,
        required=False,
        allow_empty=True,
        help_text="Upload multiple files (use multipart/form-data)"
    )
    
    class Meta:
        model = SupportTicket
        fields = ['title', 'department', 'initial_message', 'initial_attachments']
    
    def create(self, validated_data):
        initial_message = validated_data.pop('initial_message')
        initial_attachments = validated_data.pop('initial_attachments', [])
        user = self.context['request'].user
        ticket = SupportTicket.objects.create(user=user, **validated_data)
        
        # Create initial message
        message = SupportMessage.objects.create(
            ticket=ticket,
            content=initial_message,
            is_from_support=False,
            sender=user
        )
        
        # Create attachments for initial message
        for file in initial_attachments:
            # Skip empty files
            if not file or file.size == 0:
                continue
                
            try:
                SupportMessageAttachment.objects.create(
                    message=message,
                    file=file
                )
            except Exception as e:
                # Log the error but don't fail the ticket creation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to create initial attachment for ticket {ticket.id}: {str(e)}")
                continue
        
        return ticket


class UpToProSerializer(serializers.ModelSerializer):
    """Serializer for UpToPro model"""
    profileimage_url = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = UpToPro
        fields = ['id', 'rate', 'signedup', 'comment', 'name', 'profileimage', 'profileimage_url', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'profileimage_url']
    
    def get_profileimage_url(self, obj):
        """Return the full URL for the profile image"""
        if obj.profileimage:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profileimage.url)
            return obj.profileimage.url
        return None


class AIBehaviorSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for AI Behavior Settings
    
    Provides frontend with choices and validation for AI behavior customization.
    User field is read-only as it's automatically set to the request user.
    """
    
    # Display labels for choices (for frontend dropdowns)
    tone_display = serializers.CharField(source='get_tone_display', read_only=True)
    emoji_usage_display = serializers.CharField(source='get_emoji_usage_display', read_only=True)
    response_length_display = serializers.CharField(source='get_response_length_display', read_only=True)
    
    # Choices lists for frontend
    tone_choices = serializers.SerializerMethodField()
    emoji_usage_choices = serializers.SerializerMethodField()
    response_length_choices = serializers.SerializerMethodField()
    
    # Estimated token usage for monitoring
    estimated_token_usage = serializers.SerializerMethodField()
    
    class Meta:
        model = AIBehaviorSettings
        fields = [
            'id',
            # Persona
            'tone',
            'tone_display',
            'tone_choices',
            'emoji_usage',
            'emoji_usage_display',
            'emoji_usage_choices',
            'response_length',
            'response_length_display',
            'response_length_choices',
            # Behavior
            'use_customer_name',
            'use_bio_context',
            # Sales
            'persuasive_selling_enabled',
            'persuasive_cta_text',
            # Response Rules
            'unknown_fallback_text',
            'custom_instructions',
            # Metadata
            'created_at',
            'updated_at',
            'estimated_token_usage',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_tone_choices(self, obj):
        """Return tone choices for dropdown"""
        return [{'value': k, 'label': v} for k, v in AIBehaviorSettings.TONE_CHOICES]
    
    def get_emoji_usage_choices(self, obj):
        """Return emoji usage choices for dropdown"""
        return [{'value': k, 'label': v} for k, v in AIBehaviorSettings.EMOJI_CHOICES]
    
    def get_response_length_choices(self, obj):
        """Return response length choices for dropdown"""
        return [{'value': k, 'label': v} for k, v in AIBehaviorSettings.LENGTH_CHOICES]
    
    def get_estimated_token_usage(self, obj):
        """
        Estimate token usage for monitoring
        Persian: ~0.25 token per character (approximate)
        """
        cta_tokens = len(obj.persuasive_cta_text or '') * 0.25
        fallback_tokens = len(obj.unknown_fallback_text or '') * 0.25
        custom_tokens = len(obj.custom_instructions or '') * 0.25
        base_tokens = 30  # For flags (TONE, EMOJI, etc.)
        
        total = int(base_tokens + cta_tokens + fallback_tokens + custom_tokens)
        
        return {
            'total': total,
            'max_allowed': 200,  # We allocated 200 tokens for behavior settings
            'percentage': min(100, int((total / 200) * 100)),
            'breakdown': {
                'base_flags': int(base_tokens),
                'cta_text': int(cta_tokens),
                'fallback_text': int(fallback_tokens),
                'custom_instructions': int(custom_tokens),
            }
        }
    
    def validate_persuasive_cta_text(self, value):
        """Validate CTA text length"""
        if value and len(value) > 300:
            raise serializers.ValidationError(
                "متن CTA نباید بیشتر از 300 کاراکتر باشد. "
                f"طول فعلی: {len(value)} کاراکتر"
            )
        return value
    
    def validate_unknown_fallback_text(self, value):
        """Validate fallback text length"""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "متن fallback نمی‌تواند خالی باشد. "
                "یک پیام پیش‌فرض برای زمانی که AI جواب ندارد را وارد کنید."
            )
        if len(value) > 500:
            raise serializers.ValidationError(
                "متن fallback نباید بیشتر از 500 کاراکتر باشد. "
                f"طول فعلی: {len(value)} کاراکتر"
            )
        return value
    
    def validate_custom_instructions(self, value):
        """Validate custom instructions length"""
        if value and len(value) > 1000:
            raise serializers.ValidationError(
                "دستورات اضافی نباید بیشتر از 1000 کاراکتر باشد. "
                f"طول فعلی: {len(value)} کاراکتر"
            )
        return value


# =============================================
# BUSINESS PROMPT DATA SERIALIZERS
# =============================================

class BusinessPromptDataSerializer(serializers.ModelSerializer):
    """Serializer for BusinessPromptData model - supports text values and file attachments"""
    business_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    
    class Meta:
        model = BusinessPromptData
        fields = [
            'id', 'business', 'business_name', 'key', 'value',
            'file', 'file_url', 'file_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_business_name(self, obj):
        """Get BusinessPrompt name"""
        return obj.business.name
    
    def get_file_url(self, obj):
        """Get full URL for the file"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_file_name(self, obj):
        """Get file name"""
        return obj.file_name


class BusinessPromptSerializer(serializers.ModelSerializer):
    """Serializer for BusinessPrompt with its associated data"""
    prompt_data = BusinessPromptDataSerializer(many=True, read_only=True)
    
    class Meta:
        model = BusinessPrompt
        fields = [
            'id', 'name', 'prompt', 'ai_answer_prompt',
            'prompt_data', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BusinessPromptListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for BusinessPrompt list view"""
    data_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BusinessPrompt
        fields = ['id', 'name', 'data_count', 'created_at', 'updated_at']
    
    def get_data_count(self, obj):
        """Count of associated data items"""
        return obj.prompt_data.count()