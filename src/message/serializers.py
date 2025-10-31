from rest_framework import serializers
from message.models import Conversation,Tag,Customer,Message


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
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True,
        help_text="List of tag IDs to assign to the customer. Example: [1, 2, 3]"
    )
    tag = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'username', 'phone_number', 'description', 
                 'profile_picture', 'email', 'tag', 'tag_ids']
        
    def validate_tag_ids(self, value):
        """Custom validation for tag_ids"""
        if value is None:
            return value
        
        # Handle string input (when using form-data)
        if isinstance(value, str):
            try:
                import json
                value = json.loads(value)
            except (json.JSONDecodeError, ValueError):
                raise serializers.ValidationError(
                    "tag_ids must be a valid JSON array of integers. "
                    "Example: [1, 2, 3] or \"[1, 2, 3]\" when using form-data"
                )
            
        # Ensure it's a list
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "tag_ids must be a list of integers. "
                "Example: [1, 2, 3] or \"[1, 2, 3]\" when using form-data"
            )
        
        # Validate each item is an integer
        for i, item in enumerate(value):
            if not isinstance(item, int):
                try:
                    value[i] = int(item)
                except (ValueError, TypeError):
                    raise serializers.ValidationError(
                        f"All tag IDs must be integers. Item at index {i} is not a valid integer: {item}"
                    )
        
        # Check for duplicates
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Duplicate tag IDs are not allowed")
        
        # Validate that all tag IDs exist
        if value:  # Only check if list is not empty
            existing_tags = Tag.objects.filter(id__in=value)
            if len(existing_tags) != len(value):
                existing_ids = set(existing_tags.values_list('id', flat=True))
                invalid_ids = set(value) - existing_ids
                raise serializers.ValidationError(f'Invalid tag IDs: {sorted(list(invalid_ids))}. Please provide valid tag IDs.')
        
        return value
    
    def get_tag(self, obj):
        """Filter out system tags (Instagram, Telegram, Whatsapp) from customer tags"""
        user_tags = obj.tag.exclude(name__in=["Telegram", "Whatsapp", "Instagram"])
        return TagSerializer(user_tags, many=True).data

    def update(self, instance, validated_data):
        # Extract tag_ids if provided
        tag_ids = validated_data.pop('tag_ids', None)
        
        # Update regular fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Handle tag updates
        if tag_ids is not None:
            # If empty list, preserve system tags and clear all user tags
            if not tag_ids:
                system_tags = instance.tag.filter(name__in=["Telegram", "Whatsapp", "Instagram"])
                instance.tag.set(system_tags)
            else:
                # Add system tags to the provided tag_ids to ensure they're kept
                system_tags = instance.tag.filter(name__in=["Telegram", "Whatsapp", "Instagram"])
                system_tag_ids = list(system_tags.values_list('id', flat=True))
                all_tag_ids = list(set(tag_ids + system_tag_ids))  # Combine and deduplicate
                instance.tag.set(all_tag_ids)
        
        instance.save()
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
        fields = ['id', 'content', 'type', 'customer', 'conversation_id', 'is_ai_response', 'is_answered', 'created_at', 'feedback', 'feedback_comment', 'feedback_at']


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
