from django.contrib import admin
from django.utils.html import format_html
from .models import Language, Type, Tag, Template


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'language', 'type', 'tag', 'status', 'is_active', 'created_at'
    ]
    list_filter = [
        'is_active', 'language', 'type', 'tag', 'status', 'created_at'
    ]
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'cover_image_preview']
    filter_horizontal = []
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'language', 'type', 'tag', 'status')
        }),
        ('Media', {
            'fields': ('cover_image', 'cover_image_preview'),
            'description': 'Template cover image'
        }),
        ('Template Configuration', {
            'fields': ('jsonfield',),
            'description': 'JSON configuration for the workflow template'
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def cover_image_preview(self, obj):
        if obj.cover_image:
            return format_html('<img src="{}" style="max-height: 200px; max-width: 300px;" />', obj.cover_image.url)
        return "No image"
    cover_image_preview.short_description = "Cover Image Preview"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('language', 'type', 'tag')
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        return super().get_readonly_fields(request, obj)