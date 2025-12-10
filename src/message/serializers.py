from rest_framework import serializers
from message.models import Conversation,Tag,Customer,Message,CustomerData
import json


class FlexibleTagField(serializers.Field):
    """Custom field that accepts tag IDs as list, string, or null"""
    
    def to_internal_value(self, data):
        """Convert input data to list of integers"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 FlexibleTagField.to_internal_value called with: {data!r} (type: {type(data).__name__})")
        
        # Handle None/null explicitly - will clear tags
        if data is None or data == 'null':
            logger.info("✅ tag is None/null - returning [] (will clear tags)")
            return []
        
        # Handle empty string - will clear tags
        if data == '' or data == '[]':
            logger.info("✅ tag is empty - returning [] (will clear tags)")
            return []
        
        # If already a list, validate it
        if isinstance(data, list):
            logger.info(f"✅ tag is already a list: {data}")
            return self._validate_tag_list(data)
        
        # If string, try to parse as JSON
        if isinstance(data, str):
            data = data.strip()
            if data == '' or data == '[]':
                logger.info("✅ tag is empty string - returning [] (will clear tags)")
                return []
            try:
                parsed = json.loads(data)
                logger.info(f"✅ Parsed string to: {parsed}")
                if not isinstance(parsed, list):
                    logger.error(f"❌ Parsed value is not a list: {type(parsed).__name__}")
                    raise serializers.ValidationError(
                        "tag must be a valid JSON array of integers. "
                        "Example: [1, 2, 3]"
                    )
                return self._validate_tag_list(parsed)
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"❌ Failed to parse tag string: {data} - {e}")
                raise serializers.ValidationError(
                    "tag must be a valid JSON array of integers. "
                    "Example: [1, 2, 3] or \"[1, 2, 3]\" when using form-data"
                )
        
        # Unsupported type
        logger.error(f"❌ tag has unsupported type: {type(data).__name__}")
        raise serializers.ValidationError(
            f"tag must be a list of integers or null, got {type(data).__name__}"
        )
    
    def _validate_tag_list(self, value):
        """Validate list of tag IDs"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Handle empty list
        if len(value) == 0:
            logger.info("✅ tag is empty list - returning [] (will clear tags)")
            return []
        
        # Validate each item is an integer
        validated_ids = []
        for i, item in enumerate(value):
            if not isinstance(item, int):
                try:
                    validated_ids.append(int(item))
                except (ValueError, TypeError):
                    logger.error(f"❌ Invalid tag ID at index {i}: {item}")
                    raise serializers.ValidationError(
                        f"All tag IDs must be integers. Item at index {i} is not a valid integer: {item}"
                    )
            else:
                validated_ids.append(item)
        
        # Check for duplicates
        if len(validated_ids) != len(set(validated_ids)):
            logger.error(f"❌ Duplicate tag IDs found: {validated_ids}")
            raise serializers.ValidationError("Duplicate tag IDs are not allowed")
        
        # Validate that all tag IDs exist
        existing_tags = Tag.objects.filter(id__in=validated_ids)
        if len(existing_tags) != len(validated_ids):
            existing_ids = set(existing_tags.values_list('id', flat=True))
            invalid_ids = set(validated_ids) - existing_ids
            logger.error(f"❌ Invalid tag IDs: {sorted(list(invalid_ids))}")
            raise serializers.ValidationError(
                f'Invalid tag IDs: {sorted(list(invalid_ids))}. Please provide valid tag IDs.'
            )
        
        logger.info(f"✅ tag validated successfully: {validated_ids}")
        return validated_ids
    
    def to_representation(self, value):
        """Convert tag relation to list of tag details"""
        # This is handled in the serializer's to_representation method
        return value


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class CustomerSerializer(serializers.ModelSerializer):
    tag = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = '__all__'
    
    def get_tag(self, obj):
        """Filter out system tags (Instagram, Telegram, Whatsapp) from customer tags"""
        # Exclude system tags from display
        user_tags = obj.tag.exclude(name__in=["Telegram", "Whatsapp", "Instagram"])
        return TagSerializer(user_tags, many=True).data


class CustomerUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Customer with writable tag field"""
    # Sentinel value to distinguish between "not provided" and "explicitly null/empty"
    _TAG_NOT_PROVIDED = object()
    
    tag = FlexibleTagField(
        required=False,
        allow_null=True,
        help_text="List of tag IDs to assign to the customer. Example: [1, 2, 3]. Send empty array [] or null to clear all user tags."
    )
    
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'username', 'phone_number', 'description', 
                 'profile_picture', 'email', 'tag']
    
    def to_representation(self, instance):
        """Customize output representation to show tag details instead of IDs"""
        representation = super().to_representation(instance)
        # Replace tag IDs with tag objects (excluding system tags)
        user_tags = instance.tag.exclude(name__in=["Telegram", "Whatsapp", "Instagram"])
        representation['tag'] = TagSerializer(user_tags, many=True).data
        return representation

    def update(self, instance, validated_data):
        import logging
        logger = logging.getLogger(__name__)
        
        # Extract tag if provided (using sentinel to distinguish "not provided" from "null/empty")
        tag_ids = validated_data.pop('tag', self._TAG_NOT_PROVIDED)
        logger.info(f"🔄 Updating customer {instance.id} - tag from validated_data: {tag_ids}")
        
        # Update regular fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Handle tag updates - only if tag was explicitly provided in the request
        # Check if tag is NOT the sentinel value (meaning it was provided)
        if tag_ids is not self._TAG_NOT_PROVIDED:
            # Get system tags that should always be preserved
            system_tags = instance.tag.filter(name__in=["Telegram", "Whatsapp", "Instagram"])
            system_tag_ids = list(system_tags.values_list('id', flat=True))
            logger.info(f"🔄 System tag IDs to preserve: {system_tag_ids}")
            
            # If empty list (from null or []), clear all user tags but keep system tags
            if tag_ids is None or len(tag_ids) == 0:
                logger.info(f"🔄 Clearing all user tags (tag={tag_ids}), keeping only system tags: {system_tag_ids}")
                instance.tag.set(system_tag_ids)
            else:
                # Combine user-provided tags with system tags
                all_tag_ids = list(set(tag_ids + system_tag_ids))  # Combine and deduplicate
                logger.info(f"🔄 Setting tags: user_tags={tag_ids}, system_tags={system_tag_ids}, combined={all_tag_ids}")
                instance.tag.set(all_tag_ids)
        else:
            logger.info("🔄 tag not provided - keeping existing tags unchanged")
        
        instance.save()
        logger.info(f"✅ Customer {instance.id} saved successfully")
        return instance


class ConversationSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    class Meta:
        model = Conversation
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    conversation = ConversationSerializer(read_only=True)
    class Meta:
        model = Message
        fields = '__all__'


class MessageSupportAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'


# WebSocket-specific serializers for better performance
class WSCustomerSerializer(serializers.ModelSerializer):
    """Enhanced customer serializer for WebSocket messages with complete customer data"""
    tag = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'phone_number', 
                 'description', 'source', 'source_id', 'profile_picture', 'created_at', 
                 'updated_at', 'tag']
    
    def get_tag(self, obj):
        """Filter out system tags (Instagram, Telegram, Whatsapp) from customer tags"""
        user_tags = obj.tag.exclude(name__in=["Telegram", "Whatsapp", "Instagram"])
        return TagSerializer(user_tags, many=True).data


class WSConversationSerializer(serializers.ModelSerializer):
    """Lightweight conversation serializer for WebSocket"""
    customer = WSCustomerSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'status', 'customer', 'priority', 'source', 'is_active', 'created_at', 'updated_at', 'last_message', 'unread_count']
    
    def get_last_message(self, obj):
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return {
                'id': last_message.id,
                'content': last_message.content,
                'type': last_message.type,
                'created_at': last_message.created_at.isoformat() if last_message.created_at else None,
                'feedback': last_message.feedback,
                'feedback_comment': last_message.feedback_comment,
                'feedback_at': last_message.feedback_at.isoformat() if last_message.feedback_at else None
            }
        return None
    
    def get_unread_count(self, obj):
        return obj.messages.filter(type='customer', is_answered=False).count()


class WSMessageSerializer(serializers.ModelSerializer):
    """Lightweight message serializer for WebSocket"""
    customer = WSCustomerSerializer(read_only=True)
    conversation_id = serializers.CharField(source='conversation.id', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'content', 'type', 'customer', 'conversation_id', 'is_ai_response', 'is_answered', 
                 'created_at', 'feedback', 'feedback_comment', 'feedback_at', 'message_type', 'media_url', 
                 'media_file', 'processing_status', 'transcription']


class ChatMessageInputSerializer(serializers.Serializer):
    """Serializer for validating incoming chat messages"""
    content = serializers.CharField(max_length=1000)
    type = serializers.ChoiceField(choices=['support', 'marketing'], default='support')


class CustomerWithConversationSerializer(serializers.ModelSerializer):
    """Enhanced customer serializer including conversation data and tags for WebSocket"""
    conversations = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'phone_number', 
                 'source', 'source_id', 'profile_picture', 'created_at', 'updated_at', 
                 'conversations', 'tags']
    
    def get_tags(self, obj):
        """Get customer tags (excluding system tags: Instagram, Telegram, Whatsapp)"""
        # Filter out system tags from display
        user_tags = obj.tag.exclude(name__in=["Telegram", "Whatsapp", "Instagram"])
        return [{'id': tag.id, 'name': tag.name} for tag in user_tags]
    
    def get_conversations(self, obj):
        """Get conversations for this customer filtered by the current user"""
        user = self.context.get('user')
        if not user:
            return []
        
        conversations = obj.conversations.filter(user=user).order_by('-updated_at')
        conversation_data = []
        
        for conversation in conversations:
            # Get last message
            last_message = conversation.messages.order_by('-created_at').first()
            last_message_data = None
            if last_message:
                last_message_data = {
                    'id': last_message.id,
                    'content': last_message.content,
                    'type': last_message.type,
                    'is_ai_response': getattr(last_message, 'is_ai_response', False),
                    'created_at': last_message.created_at.isoformat() if last_message.created_at else None,
                    'feedback': last_message.feedback,
                    'feedback_comment': last_message.feedback_comment,
                    'feedback_at': last_message.feedback_at.isoformat() if last_message.feedback_at else None
                }
            
            # Get unread count
            unread_count = conversation.messages.filter(type='customer', is_answered=False).count()
            
            conversation_data.append({
                'id': conversation.id,
                'title': conversation.title,
                'status': conversation.status,
                'source': conversation.source,
                'priority': conversation.priority,
                'is_active': conversation.is_active,
                'created_at': conversation.created_at.isoformat() if conversation.created_at else None,
                'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else None,
                'last_message': last_message_data,
                'unread_count': unread_count
            })
        
        return conversation_data


class CustomerDataSerializer(serializers.ModelSerializer):
    """Serializer for CustomerData model - supports both text values and file attachments"""
    customer_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomerData
        fields = [
            'id', 'customer', 'user', 'key', 'value', 
            'file', 'file_url', 'file_name',
            'customer_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_customer_name(self, obj):
        """Get customer display name"""
        return str(obj.customer)
    
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


class CustomerDataCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating CustomerData - supports both text and file uploads"""
    class Meta:
        model = CustomerData
        fields = ['customer', 'key', 'value', 'file']
        extra_kwargs = {
            'value': {'required': False, 'allow_blank': True},
            'file': {'required': False, 'allow_null': True}
        }
    
    def validate(self, data):
        """Check if the key already exists for this customer and user"""
        user = self.context['request'].user
        customer = data.get('customer')
        key = data.get('key')
        
        if CustomerData.objects.filter(customer=customer, user=user, key=key).exists():
            raise serializers.ValidationError({
                'key': f"A data field with key '{key}' already exists for this customer. Use PUT to update it."
            })
        
        # Ensure at least value or file is provided
        value = data.get('value', '')
        file = data.get('file')
        if not value and not file:
            raise serializers.ValidationError({
                'non_field_errors': "Either 'value' (text) or 'file' must be provided."
            })
        
        return data


class CustomerDataUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating CustomerData - supports partial updates for text and file"""
    remove_file = serializers.BooleanField(required=False, write_only=True, default=False)
    
    class Meta:
        model = CustomerData
        fields = ['key', 'value', 'file', 'remove_file']
        extra_kwargs = {
            'key': {'required': False},
            'value': {'required': False, 'allow_blank': True},
            'file': {'required': False, 'allow_null': True}
        }
    
    def update(self, instance, validated_data):
        """Handle file removal and updates"""
        remove_file = validated_data.pop('remove_file', False)
        
        # If remove_file is True, delete the existing file
        if remove_file and instance.file:
            instance.file.delete(save=False)
            instance.file = None
        
        return super().update(instance, validated_data)
