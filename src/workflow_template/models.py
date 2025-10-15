import uuid
from django.db import models
from django.utils import timezone

class Language(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Language name")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = "Language"
        verbose_name_plural = "Languages"
        ordering = ['name']
    def __str__(self):
        return self.name


class Type(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=500, help_text="Type name")
    description = models.TextField(blank=True, help_text="Type description")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Type"
        verbose_name_plural = "Types"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=500, help_text="Tag name")
    description = models.TextField(blank=True, help_text="Tag description")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Template(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('popular', 'Popular'),
        ('none', 'None'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=500, help_text="Template name")
    description = models.TextField(blank=True, help_text="Template description")
    jsonfield = models.JSONField(
        default=dict,
        blank = True,
        help_text="Template configuration in JSON format"
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='templates',
        help_text="Template language"
    )
    type = models.ForeignKey(
        Type,
        on_delete=models.CASCADE,
        related_name='templates',
        help_text="Template type"
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.SET_NULL,
        related_name='templates',
        null=True,
        blank=True,
        help_text="Template tag"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='none',
        help_text="Template status (New, Popular, or None)"
    )
    cover_image = models.ImageField(
        upload_to='workflow_templates/covers/',
        null=True,
        blank=True,
        help_text="Cover image for the template"
    )
    is_active = models.BooleanField(default=True, help_text="Whether template is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Workflow Template"
        verbose_name_plural = "Workflow Templates"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['language', 'type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['tag']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.language.name} - {self.type.name})"