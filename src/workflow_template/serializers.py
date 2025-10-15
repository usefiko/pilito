from rest_framework import serializers
from .models import Language, Type, Tag, Template

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'name', 'is_active', 'created_at', 'updated_at']


class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'updated_at']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'updated_at']


class TemplateSerializer(serializers.ModelSerializer):
    language = LanguageSerializer(read_only=True)
    language_id = serializers.UUIDField(write_only=True)
    type = TypeSerializer(read_only=True)
    type_id = serializers.UUIDField(write_only=True)
    tag = TagSerializer(read_only=True)
    tag_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Template
        fields = [
            'id', 'name', 'description', 'jsonfield', 'language', 'language_id',
            'type', 'type_id', 'tag', 'tag_id', 'status', 'cover_image',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_language_id(self, value):
        try:
            Language.objects.get(id=value, is_active=True)
        except Language.DoesNotExist:
            raise serializers.ValidationError("Invalid language ID or language is not active.")
        return value
    
    def validate_type_id(self, value):
        try:
            Type.objects.get(id=value, is_active=True)
        except Type.DoesNotExist:
            raise serializers.ValidationError("Invalid type ID or type is not active.")
        return value
    
    def validate_tag_id(self, value):
        if value is None:
            return value
        try:
            Tag.objects.get(id=value, is_active=True)
        except Tag.DoesNotExist:
            raise serializers.ValidationError("Invalid tag ID or tag is not active.")
        return value
    
    def create(self, validated_data):
        language_id = validated_data.pop('language_id')
        type_id = validated_data.pop('type_id')
        tag_id = validated_data.pop('tag_id', None)
        
        validated_data['language_id'] = language_id
        validated_data['type_id'] = type_id
        if tag_id is not None:
            validated_data['tag_id'] = tag_id
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        language_id = validated_data.pop('language_id', None)
        type_id = validated_data.pop('type_id', None)
        tag_id = validated_data.pop('tag_id', None)
        
        if language_id is not None:
            validated_data['language_id'] = language_id
        if type_id is not None:
            validated_data['type_id'] = type_id
        if 'tag_id' in validated_data or tag_id is not None:
            validated_data['tag_id'] = tag_id
        
        return super().update(instance, validated_data)


class TemplateListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for template list views
    """
    language_name = serializers.CharField(source='language.name', read_only=True)
    type_name = serializers.CharField(source='type.name', read_only=True)
    tag_name = serializers.CharField(source='tag.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Template
        fields = [
            'id', 'name', 'description', 'language_name', 'type_name', 'tag_name',
            'status', 'cover_image', 'is_active', 'created_at'
        ]