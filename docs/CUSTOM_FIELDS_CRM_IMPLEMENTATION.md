# 🎯 Custom Fields & Mini CRM Implementation Guide

## 📋 فهرست مطالب
1. [Overview](#overview)
2. [Architecture Design](#architecture-design)
3. [Database Schema](#database-schema)
4. [Implementation Plan](#implementation-plan)
5. [CRM Features Suggestions](#crm-features-suggestions)
6. [Best Practices](#best-practices)
7. [Migration Strategy](#migration-strategy)

---

## 🎯 Overview

### هدف
تبدیل پلتفرم به یک **Mini CRM ساده و کاربردی** که کاربران عادی بتوانند بدون پیچیدگی از آن استفاده کنند.

### اصول طراحی
- ✅ **سادگی**: UI/UX ساده و intuitive
- ✅ **انعطاف‌پذیری**: Custom Fields برای هر صنعت
- ✅ **Performance**: بهینه برای 200K+ Customer
- ✅ **Scalability**: قابلیت رشد بدون مشکل

### تفاوت با CRM های پیچیده
| ویژگی | CRM های پیچیده | این پلتفرم |
|-------|----------------|------------|
| Setup Time | 2-3 ساعت | 5 دقیقه |
| Learning Curve | بالا | پایین |
| Customization | پیچیده | ساده (Form Builder) |
| Price | گران | مقرون به صرفه |

---

## 🏗️ Architecture Design

### رویکرد: Pre-defined Fields + Mapping

**چرا این رویکرد؟**
- ✅ Performance عالی (بدون JOIN)
- ✅ Query ساده
- ✅ Migration یکباره
- ✅ Type Safety (EmailField, DateField, etc.)

### ساختار کلی

```
┌─────────────────────────────────────────┐
│         Customer Model                  │
│  - Existing fields (first_name, etc.)   │
│  - Pre-defined custom fields (90)       │
│  - Extra fields (JSONField fallback)    │
└─────────────────────────────────────────┘
                    ▲
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼────────┐    ┌─────────▼──────────┐
│ Field Mapping  │    │ Industry Template │
│ (User-defined) │    │ (Admin-defined)   │
└────────────────┘    └───────────────────┘
```

---

## 💾 Database Schema

### 1. Customer Model Extension

```python
class Customer(models.Model):
    # ========== Existing Fields ==========
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=250, null=True, blank=True)
    description = models.TextField(max_length=1000, null=True, blank=True)
    # ... other existing fields ...
    
    # ========== Pre-defined Custom Fields ==========
    # Text Fields (30 fields)
    custom_text_1 = models.CharField(max_length=500, null=True, blank=True, db_index=True)
    custom_text_2 = models.CharField(max_length=500, null=True, blank=True, db_index=True)
    # ... تا custom_text_30
    
    # Number Fields (15 fields)
    custom_number_1 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True, db_index=True)
    custom_number_2 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True, db_index=True)
    # ... تا custom_number_15
    
    # Date Fields (10 fields)
    custom_date_1 = models.DateField(null=True, blank=True, db_index=True)
    custom_date_2 = models.DateField(null=True, blank=True, db_index=True)
    # ... تا custom_date_10
    
    # Boolean Fields (10 fields)
    custom_boolean_1 = models.BooleanField(null=True, blank=True, db_index=True)
    custom_boolean_2 = models.BooleanField(null=True, blank=True, db_index=True)
    # ... تا custom_boolean_10
    
    # Email Fields (5 fields)
    custom_email_1 = models.EmailField(null=True, blank=True, db_index=True)
    custom_email_2 = models.EmailField(null=True, blank=True, db_index=True)
    # ... تا custom_email_5
    
    # Phone Fields (5 fields)
    custom_phone_1 = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    custom_phone_2 = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    # ... تا custom_phone_5
    
    # URL Fields (5 fields)
    custom_url_1 = models.URLField(null=True, blank=True)
    custom_url_2 = models.URLField(null=True, blank=True)
    # ... تا custom_url_5
    
    # Select/Choice Fields (10 fields) - stored as CharField
    custom_select_1 = models.CharField(max_length=200, null=True, blank=True, db_index=True)
    custom_select_2 = models.CharField(max_length=200, null=True, blank=True, db_index=True)
    # ... تا custom_select_10
    
    # ========== Fallback for Extra Fields ==========
    custom_fields_extra = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Additional custom fields beyond 90 pre-defined fields"
    )
    
    # ========== CRM Metadata ==========
    crm_score = models.IntegerField(
        default=0,
        help_text="CRM score based on engagement, purchases, etc."
    )
    last_contacted_at = models.DateTimeField(null=True, blank=True)
    total_interactions = models.IntegerField(default=0)
    total_purchases = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    class Meta:
        indexes = [
            # Indexes for common queries
            models.Index(fields=['crm_score']),
            models.Index(fields=['last_contacted_at']),
            models.Index(fields=['total_interactions']),
        ]
```

**Total Pre-defined Fields: 90**
- 30 Text
- 15 Number
- 10 Date
- 10 Boolean
- 5 Email
- 5 Phone
- 5 URL
- 10 Select

### 2. CustomerFieldMapping Model

```python
class CustomerFieldMapping(models.Model):
    """
    هر User (Tenant) فیلدهای خودش رو تعریف می‌کنه و به یکی از pre-defined fields map می‌کنه
    """
    FIELD_TYPE_CHOICES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('boolean', 'Boolean (Yes/No)'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('url', 'URL'),
        ('select', 'Select (Dropdown)'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='customer_field_mappings',
        db_index=True
    )
    
    # Field Definition
    field_key = models.SlugField(
        max_length=100,
        help_text="Unique key for this field (e.g., 'birth_date', 'company_name')"
    )
    field_label = models.CharField(
        max_length=200,
        help_text="Display label (e.g., 'تاریخ تولد', 'نام شرکت')"
    )
    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPE_CHOICES,
        help_text="Type of field"
    )
    
    # Mapping to Pre-defined Field
    mapped_field_name = models.CharField(
        max_length=50,
        unique=True,  # هر فیلد فقط یک بار استفاده میشه
        help_text="Name of pre-defined field (e.g., 'custom_text_1', 'custom_date_5')"
    )
    
    # Configuration
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order")
    
    # Validation Rules
    validation_rules = models.JSONField(
        default=dict,
        help_text="Validation rules: {'min': 0, 'max': 100, 'pattern': '...', 'options': [...]}"
    )
    
    # Select Options (for select type)
    select_options = models.JSONField(
        default=list,
        null=True,
        blank=True,
        help_text="Options for select field: ['Option 1', 'Option 2', ...]"
    )
    
    # Metadata
    help_text = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Help text shown to users"
    )
    placeholder = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Placeholder text"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [('user', 'field_key')]
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['field_type']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.field_label} ({self.field_key})"
    
    def clean(self):
        """Validate mapping"""
        # Check if mapped_field_name is valid
        valid_fields = self._get_valid_field_names()
        if self.mapped_field_name not in valid_fields:
            raise ValidationError(f"Invalid mapped_field_name: {self.mapped_field_name}")
        
        # Check field type matches
        expected_prefix = f"custom_{self.field_type}_"
        if not self.mapped_field_name.startswith(expected_prefix):
            raise ValidationError(f"Field type mismatch: {self.field_type} != {self.mapped_field_name}")
    
    @staticmethod
    def _get_valid_field_names():
        """Get all valid pre-defined field names"""
        fields = []
        for i in range(1, 31):  # text 1-30
            fields.append(f"custom_text_{i}")
        for i in range(1, 16):  # number 1-15
            fields.append(f"custom_number_{i}")
        for i in range(1, 11):  # date 1-10, boolean 1-10, select 1-10
            fields.append(f"custom_date_{i}")
            fields.append(f"custom_boolean_{i}")
            fields.append(f"custom_select_{i}")
        for i in range(1, 6):  # email 1-5, phone 1-5, url 1-5
            fields.append(f"custom_email_{i}")
            fields.append(f"custom_phone_{i}")
            fields.append(f"custom_url_{i}")
        return fields
```

### 3. IndustryFieldTemplate Model

```python
class IndustryFieldTemplate(models.Model):
    """
    فیلدهای پیش‌فرض برای هر Industry (توسط Admin تنظیم می‌شه)
    """
    INDUSTRY_CHOICES = [
        ('retail', 'Retail'),
        ('ecommerce', 'E-commerce'),
        ('restaurant', 'Restaurant'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('technology', 'Technology'),
        ('finance', 'Finance'),
        ('real_estate', 'Real Estate'),
        ('travel', 'Travel & Tourism'),
        ('beauty', 'Beauty & Wellness'),
        ('fitness', 'Fitness & Sports'),
        ('automotive', 'Automotive'),
        ('consulting', 'Consulting'),
        ('legal', 'Legal Services'),
        ('nonprofit', 'Non-profit'),
        ('manufacturing', 'Manufacturing'),
        ('agriculture', 'Agriculture'),
        ('entertainment', 'Entertainment'),
        ('media', 'Media & Publishing'),
        ('other', 'Other'),
    ]
    
    industry = models.CharField(
        max_length=50,
        choices=INDUSTRY_CHOICES,
        db_index=True
    )
    
    field_key = models.SlugField(max_length=100)
    field_label = models.CharField(max_length=200)
    field_type = models.CharField(max_length=20, choices=CustomerFieldMapping.FIELD_TYPE_CHOICES)
    
    is_required = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    validation_rules = models.JSONField(default=dict)
    select_options = models.JSONField(default=list, null=True, blank=True)
    help_text = models.CharField(max_length=500, null=True, blank=True)
    placeholder = models.CharField(max_length=200, null=True, blank=True)
    
    is_system = models.BooleanField(
        default=True,
        help_text="System fields cannot be deleted by users"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [('industry', 'field_key')]
        ordering = ['industry', 'order']
    
    def __str__(self):
        return f"{self.get_industry_display()} - {self.field_label}"
```

### 4. CustomerFieldValue Helper Model (Optional - برای History)

```python
class CustomerFieldHistory(models.Model):
    """
    تاریخچه تغییرات فیلدهای Customer (Optional - برای Audit)
    """
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='field_history')
    field_mapping = models.ForeignKey(CustomerFieldMapping, on_delete=models.CASCADE)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField()
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    change_reason = models.CharField(max_length=500, null=True, blank=True)
    
    class Meta:
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['customer', 'changed_at']),
        ]
```

---

## 🔧 Implementation Plan

### Phase 1: Database & Models (Week 1)

#### Step 1.1: Create Migration for Customer Fields
```python
# src/message/migrations/XXXX_add_customer_custom_fields.py

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('message', 'XXXX_previous_migration'),
    ]

    operations = [
        # Add text fields (30)
        migrations.AddField(
            model_name='customer',
            name='custom_text_1',
            field=models.CharField(blank=True, db_index=True, max_length=500, null=True),
        ),
        # ... تا custom_text_30
        
        # Add number fields (15)
        migrations.AddField(
            model_name='customer',
            name='custom_number_1',
            field=models.DecimalField(blank=True, db_index=True, decimal_places=2, max_digits=20, null=True),
        ),
        # ... تا custom_number_15
        
        # Add date fields (10)
        migrations.AddField(
            model_name='customer',
            name='custom_date_1',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
        # ... تا custom_date_10
        
        # Add boolean fields (10)
        migrations.AddField(
            model_name='customer',
            name='custom_boolean_1',
            field=models.BooleanField(blank=True, db_index=True, null=True),
        ),
        # ... تا custom_boolean_10
        
        # Add email fields (5)
        migrations.AddField(
            model_name='customer',
            name='custom_email_1',
            field=models.EmailField(blank=True, db_index=True, max_length=254, null=True),
        ),
        # ... تا custom_email_5
        
        # Add phone fields (5)
        migrations.AddField(
            model_name='customer',
            name='custom_phone_1',
            field=models.CharField(blank=True, db_index=True, max_length=20, null=True),
        ),
        # ... تا custom_phone_5
        
        # Add URL fields (5)
        migrations.AddField(
            model_name='customer',
            name='custom_url_1',
            field=models.URLField(blank=True, null=True),
        ),
        # ... تا custom_url_5
        
        # Add select fields (10)
        migrations.AddField(
            model_name='customer',
            name='custom_select_1',
            field=models.CharField(blank=True, db_index=True, max_length=200, null=True),
        ),
        # ... تا custom_select_10
        
        # Add extra fields JSONField
        migrations.AddField(
            model_name='customer',
            name='custom_fields_extra',
            field=models.JSONField(blank=True, default=dict, help_text='Additional custom fields beyond 90 pre-defined fields', null=True),
        ),
        
        # Add CRM metadata fields
        migrations.AddField(
            model_name='customer',
            name='crm_score',
            field=models.IntegerField(default=0, help_text='CRM score based on engagement, purchases, etc.'),
        ),
        migrations.AddField(
            model_name='customer',
            name='last_contacted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='total_interactions',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='customer',
            name='total_purchases',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='customer',
            name='total_spent',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=20),
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='customer',
            index=models.Index(fields=['crm_score'], name='message_cust_crm_sc_idx'),
        ),
        migrations.AddIndex(
            model_name='customer',
            index=models.Index(fields=['last_contacted_at'], name='message_cust_last_co_idx'),
        ),
    ]
```

#### Step 1.2: Create CustomerFieldMapping Model
```python
# src/message/models.py - اضافه کردن مدل‌های جدید
```

#### Step 1.3: Create IndustryFieldTemplate Model
```python
# src/message/models.py - اضافه کردن IndustryFieldTemplate
```

### Phase 2: Services & Utilities (Week 1-2)

#### Step 2.1: CustomerFieldService
```python
# src/message/services/customer_field_service.py

from django.db import models
from message.models import Customer, CustomerFieldMapping

class CustomerFieldService:
    """
    Service for managing customer custom fields
    """
    
    @staticmethod
    def get_customer_field_value(customer: Customer, field_key: str, user: User):
        """
        Get value of a custom field for a customer
        """
        try:
            mapping = CustomerFieldMapping.objects.get(
                user=user,
                field_key=field_key,
                is_active=True
            )
            return getattr(customer, mapping.mapped_field_name, None)
        except CustomerFieldMapping.DoesNotExist:
            # Check extra fields
            if customer.custom_fields_extra and field_key in customer.custom_fields_extra:
                return customer.custom_fields_extra[field_key]
            return None
    
    @staticmethod
    def set_customer_field_value(customer: Customer, field_key: str, value: Any, user: User):
        """
        Set value of a custom field for a customer
        """
        try:
            mapping = CustomerFieldMapping.objects.get(
                user=user,
                field_key=field_key,
                is_active=True
            )
            
            # Validate value based on field type
            validated_value = CustomerFieldService._validate_value(mapping, value)
            
            # Set value
            setattr(customer, mapping.mapped_field_name, validated_value)
            customer.save(update_fields=[mapping.mapped_field_name])
            
            # Log history (optional)
            CustomerFieldHistory.objects.create(
                customer=customer,
                field_mapping=mapping,
                new_value=str(validated_value),
                changed_by=user
            )
            
            return True
        except CustomerFieldMapping.DoesNotExist:
            # Save to extra fields
            if not customer.custom_fields_extra:
                customer.custom_fields_extra = {}
            customer.custom_fields_extra[field_key] = value
            customer.save(update_fields=['custom_fields_extra'])
            return True
    
    @staticmethod
    def _validate_value(mapping: CustomerFieldMapping, value: Any):
        """
        Validate value based on field type and rules
        """
        field_type = mapping.field_type
        rules = mapping.validation_rules or {}
        
        if field_type == 'number':
            value = float(value)
            if 'min' in rules and value < rules['min']:
                raise ValidationError(f"Value must be >= {rules['min']}")
            if 'max' in rules and value > rules['max']:
                raise ValidationError(f"Value must be <= {rules['max']}")
        
        elif field_type == 'date':
            if isinstance(value, str):
                from datetime import datetime
                value = datetime.strptime(value, '%Y-%m-%d').date()
        
        elif field_type == 'boolean':
            if isinstance(value, str):
                value = value.lower() in ['true', '1', 'yes', 'y']
        
        elif field_type == 'select':
            if mapping.select_options and value not in mapping.select_options:
                raise ValidationError(f"Value must be one of: {mapping.select_options}")
        
        elif field_type == 'email':
            from django.core.validators import validate_email
            validate_email(value)
        
        elif field_type == 'phone':
            # Basic phone validation
            import re
            if not re.match(r'^\+?[\d\s\-\(\)]+$', str(value)):
                raise ValidationError("Invalid phone number format")
        
        return value
    
    @staticmethod
    def get_all_customer_fields(customer: Customer, user: User) -> Dict[str, Any]:
        """
        Get all custom field values for a customer
        """
        mappings = CustomerFieldMapping.objects.filter(
            user=user,
            is_active=True
        ).order_by('order')
        
        fields = {}
        for mapping in mappings:
            value = CustomerFieldService.get_customer_field_value(customer, mapping.field_key, user)
            fields[mapping.field_key] = {
                'label': mapping.field_label,
                'type': mapping.field_type,
                'value': value,
                'is_required': mapping.is_required,
            }
        
        return fields
    
    @staticmethod
    def create_field_mapping(user: User, field_key: str, field_label: str, 
                            field_type: str, **kwargs) -> CustomerFieldMapping:
        """
        Create a new field mapping for a user
        """
        # Check limit (90 fields)
        active_count = CustomerFieldMapping.objects.filter(
            user=user,
            is_active=True
        ).count()
        
        if active_count >= 90:
            raise ValidationError("حداکثر 90 فیلد می‌توانید ایجاد کنید. لطفاً یک فیلد را حذف کنید یا از Enterprise Plan استفاده کنید.")
        
        # Find available field
        available_field = CustomerFieldService._find_available_field(user, field_type)
        if not available_field:
            raise ValidationError(f"هیچ فیلد {field_type} خالی موجود نیست. لطفاً یک فیلد را حذف کنید.")
        
        # Create mapping
        mapping = CustomerFieldMapping.objects.create(
            user=user,
            field_key=field_key,
            field_label=field_label,
            field_type=field_type,
            mapped_field_name=available_field,
            is_required=kwargs.get('is_required', False),
            order=kwargs.get('order', active_count + 1),
            validation_rules=kwargs.get('validation_rules', {}),
            select_options=kwargs.get('select_options', []),
            help_text=kwargs.get('help_text'),
            placeholder=kwargs.get('placeholder'),
        )
        
        return mapping
    
    @staticmethod
    def _find_available_field(user: User, field_type: str) -> Optional[str]:
        """
        Find an available pre-defined field for the given type
        """
        used_fields = set(
            CustomerFieldMapping.objects.filter(
                user=user,
                is_active=True
            ).values_list('mapped_field_name', flat=True)
        )
        
        # Get all fields of this type
        prefix = f"custom_{field_type}_"
        all_fields = CustomerFieldMapping._get_valid_field_names()
        type_fields = [f for f in all_fields if f.startswith(prefix)]
        
        # Find first unused field
        for field in type_fields:
            if field not in used_fields:
                return field
        
        return None
```

#### Step 2.2: Industry Template Service
```python
# src/message/services/industry_template_service.py

class IndustryTemplateService:
    """
    Service for managing industry field templates
    """
    
    @staticmethod
    def apply_industry_template_to_user(user: User, industry: str):
        """
        Apply industry template fields to a user
        """
        templates = IndustryFieldTemplate.objects.filter(
            industry=industry
        ).order_by('order')
        
        created_count = 0
        for template in templates:
            try:
                CustomerFieldService.create_field_mapping(
                    user=user,
                    field_key=template.field_key,
                    field_label=template.field_label,
                    field_type=template.field_type,
                    is_required=template.is_required,
                    validation_rules=template.validation_rules,
                    select_options=template.select_options,
                    help_text=template.help_text,
                    placeholder=template.placeholder,
                )
                created_count += 1
            except ValidationError as e:
                logger.warning(f"Failed to create field {template.field_key} for user {user.id}: {e}")
        
        return created_count
```

### Phase 3: API Endpoints (Week 2)

#### Step 3.1: Field Mapping API
```python
# src/message/api/customer_fields.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from message.models import CustomerFieldMapping, IndustryFieldTemplate
from message.services.customer_field_service import CustomerFieldService
from message.services.industry_template_service import IndustryTemplateService

class CustomerFieldMappingViewSet(viewsets.ModelViewSet):
    """
    API for managing customer field mappings
    """
    serializer_class = CustomerFieldMappingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CustomerFieldMapping.objects.filter(
            user=self.request.user,
            is_active=True
        ).order_by('order')
    
    @action(detail=False, methods=['post'])
    def create_field(self, request):
        """
        Create a new custom field
        """
        serializer = CreateFieldMappingSerializer(data=request.data)
        if serializer.is_valid():
            try:
                mapping = CustomerFieldService.create_field_mapping(
                    user=request.user,
                    **serializer.validated_data
                )
                return Response(
                    CustomerFieldMappingSerializer(mapping).data,
                    status=status.HTTP_201_CREATED
                )
            except ValidationError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def apply_industry_template(self, request):
        """
        Apply industry template to current user
        """
        industry = request.data.get('industry')
        if not industry:
            return Response(
                {'error': 'Industry is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        count = IndustryTemplateService.apply_industry_template_to_user(
            request.user,
            industry
        )
        
        return Response({
            'message': f'{count} fields created from industry template',
            'fields_created': count
        })
```

#### Step 3.2: Customer Field Values API
```python
# src/message/api/customer.py - اضافه کردن endpoint جدید

@action(detail=True, methods=['get', 'patch'])
def custom_fields(self, request, pk=None):
    """
    Get/Update custom fields for a customer
    """
    customer = self.get_object()
    
    if request.method == 'GET':
        fields = CustomerFieldService.get_all_customer_fields(customer, request.user)
        return Response(fields)
    
    elif request.method == 'PATCH':
        # Update multiple fields
        updates = request.data
        for field_key, value in updates.items():
            try:
                CustomerFieldService.set_customer_field_value(
                    customer, field_key, value, request.user
                )
            except ValidationError as e:
                return Response(
                    {'error': f'Invalid value for {field_key}: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response({'message': 'Fields updated successfully'})
```

### Phase 4: Waiting Node Integration (Week 2-3)

#### Step 4.1: Extend WaitingNode Model
```python
# src/workflow/models.py - WaitingNode

class WaitingNode(WorkflowNode):
    # ... existing fields ...
    
    # ✅ NEW: Save to Customer Field
    save_to_customer_field = models.ForeignKey(
        CustomerFieldMapping,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Save user response to this customer custom field",
        related_name='waiting_nodes'
    )
    
    # Alternative: Direct field key (if mapping doesn't exist yet)
    customer_field_key = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Key of custom field to save response to (alternative to save_to_customer_field)"
    )
```

#### Step 4.2: Update Node Execution Service
```python
# src/workflow/services/node_execution_service.py

def process_user_response(self, waiting_node, response_text, context, execution):
    # ... existing validation and storage ...
    
    # ✅ Save to Customer Profile if configured
    if waiting_node.save_to_customer_field:
        customer = self._get_customer_from_context(context)
        user = self._get_user_from_context(context)
        
        try:
            CustomerFieldService.set_customer_field_value(
                customer=customer,
                field_key=waiting_node.save_to_customer_field.field_key,
                value=response_text,
                user=user
            )
            logger.info(f"✅ Saved response to customer field: {waiting_node.save_to_customer_field.field_key}")
        except Exception as e:
            logger.error(f"Failed to save to customer field: {e}")
    
    elif waiting_node.customer_field_key:
        # Fallback: use field key directly
        customer = self._get_customer_from_context(context)
        user = self._get_user_from_context(context)
        
        try:
            CustomerFieldService.set_customer_field_value(
                customer=customer,
                field_key=waiting_node.customer_field_key,
                value=response_text,
                user=user
            )
        except Exception as e:
            logger.error(f"Failed to save to customer field: {e}")
```

### Phase 5: Frontend Form Builder (Week 3-4)

#### UI Components Needed:
1. **Field List View**: نمایش لیست فیلدهای تعریف شده
2. **Field Form**: فرم ساخت/ویرایش فیلد
3. **Form Builder**: Drag & Drop form builder
4. **Customer Profile View**: نمایش فیلدهای Customer با مقادیر
5. **Customer Profile Edit**: ویرایش فیلدهای Customer

---

## 🚀 CRM Features Suggestions

### 1. Customer Scoring System
```python
class CustomerScoringService:
    """
    Calculate CRM score based on:
    - Engagement (messages, responses)
    - Purchases (if integrated)
    - Last contact date
    - Custom field completeness
    """
    
    @staticmethod
    def calculate_crm_score(customer: Customer, user: User) -> int:
        score = 0
        
        # Engagement score (0-40)
        score += min(customer.total_interactions * 2, 40)
        
        # Recency score (0-30)
        if customer.last_contacted_at:
            days_ago = (timezone.now() - customer.last_contacted_at).days
            score += max(30 - days_ago, 0)
        
        # Purchase score (0-20)
        score += min(customer.total_purchases * 5, 20)
        
        # Completeness score (0-10)
        fields = CustomerFieldService.get_all_customer_fields(customer, user)
        filled_count = sum(1 for f in fields.values() if f['value'])
        total_count = len(fields)
        if total_count > 0:
            score += int((filled_count / total_count) * 10)
        
        return min(score, 100)  # Max 100
```

### 2. Customer Segmentation
```python
class CustomerSegment(models.Model):
    """
    Customer segments (e.g., VIP, Regular, Inactive)
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    conditions = models.JSONField(
        help_text="Conditions: {'crm_score__gte': 80, 'total_purchases__gte': 5}"
    )
    color = models.CharField(max_length=7, default="#000000")
    order = models.IntegerField(default=0)
    
    def get_customers(self):
        """Get customers matching this segment"""
        from django.db.models import Q
        conditions = Q()
        for key, value in self.conditions.items():
            conditions &= Q(**{key: value})
        return Customer.objects.filter(conditions)
```

### 3. Activity Timeline
```python
class CustomerActivity(models.Model):
    """
    Timeline of customer activities
    """
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50)  # 'message', 'purchase', 'field_update', etc.
    description = models.TextField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
```

### 4. Smart Tags (Auto-tagging)
```python
class SmartTagRule(models.Model):
    """
    Auto-tagging rules based on custom fields
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    condition = models.JSONField(
        help_text="{'custom_text_1__icontains': 'VIP', 'crm_score__gte': 80}"
    )
    
    def apply_to_customers(self):
        """Auto-tag customers matching condition"""
        # Implementation
```

### 5. Customer Notes & Tasks
```python
class CustomerNote(models.Model):
    """
    Notes and tasks for customers
    """
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='notes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.TextField()
    is_task = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### 6. Export/Import
```python
class CustomerExportService:
    """
    Export customers with custom fields to CSV/Excel
    """
    @staticmethod
    def export_to_csv(user: User, customers: QuerySet) -> BytesIO:
        # Implementation
```

### 7. Bulk Actions
```python
class BulkActionService:
    """
    Bulk update custom fields, tags, etc.
    """
    @staticmethod
    def bulk_update_fields(customers: QuerySet, field_key: str, value: Any):
        # Implementation
```

### 8. Customer Merge
```python
class CustomerMergeService:
    """
    Merge duplicate customers
    """
    @staticmethod
    def merge_customers(source: Customer, target: Customer):
        # Implementation
```

---

## 📊 Best Practices

### 1. Performance Optimization

#### Indexing Strategy
```python
# Index frequently queried fields
class Meta:
    indexes = [
        models.Index(fields=['crm_score']),
        models.Index(fields=['last_contacted_at']),
        models.Index(fields=['custom_text_1']),  # Most used fields
        models.Index(fields=['custom_date_1']),
    ]
```

#### Query Optimization
```python
# ✅ Good: Use select_related/prefetch_related
customers = Customer.objects.select_related('user').prefetch_related('field_mappings')

# ❌ Bad: N+1 queries
for customer in customers:
    fields = customer.field_mappings.all()  # N queries!
```

### 2. Data Validation

```python
# Always validate before saving
def validate_customer_field(customer, field_key, value, user):
    mapping = CustomerFieldMapping.objects.get(user=user, field_key=field_key)
    
    # Type validation
    if mapping.field_type == 'number' and not isinstance(value, (int, float)):
        raise ValidationError("Value must be a number")
    
    # Required validation
    if mapping.is_required and not value:
        raise ValidationError(f"{mapping.field_label} is required")
    
    # Custom validation rules
    rules = mapping.validation_rules
    if 'min' in rules and value < rules['min']:
        raise ValidationError(f"Value must be >= {rules['min']}")
```

### 3. UI/UX Guidelines

#### Form Builder
- Drag & Drop interface
- Live preview
- Field validation preview
- Mobile responsive

#### Customer Profile
- Tabbed interface (Basic Info, Custom Fields, Activity, Notes)
- Quick edit mode
- Bulk edit support
- Export button

### 4. Security

```python
# Always check user ownership
def get_customer_fields(user, customer):
    # Verify customer belongs to user
    if not Conversation.objects.filter(user=user, customer=customer).exists():
        raise PermissionDenied("Customer does not belong to this user")
    
    return CustomerFieldService.get_all_customer_fields(customer, user)
```

---

## 🔄 Migration Strategy

### Step 1: Pre-migration
```bash
# Backup database
pg_dump pilito_db > backup_before_custom_fields.sql

# Test on staging
python manage.py migrate --dry-run
```

### Step 2: Migration
```bash
# Run migration
python manage.py migrate message

# Verify
python manage.py shell
>>> from message.models import Customer
>>> Customer._meta.get_field('custom_text_1')
```

### Step 3: Post-migration
```bash
# Create default industry templates
python manage.py create_industry_templates

# Verify data integrity
python manage.py verify_customer_fields
```

### Rollback Plan
```bash
# If something goes wrong
python manage.py migrate message XXXX_previous_migration
```

---

## 📝 Example Industry Templates

### Retail Industry
```python
templates = [
    {'field_key': 'birth_date', 'field_label': 'تاریخ تولد', 'field_type': 'date'},
    {'field_key': 'loyalty_points', 'field_label': 'امتیاز وفاداری', 'field_type': 'number'},
    {'field_key': 'favorite_category', 'field_label': 'دسته‌بندی مورد علاقه', 'field_type': 'select', 'options': ['لباس', 'کفش', 'اکسسوری']},
    {'field_key': 'last_purchase_date', 'field_label': 'تاریخ آخرین خرید', 'field_type': 'date'},
    {'field_key': 'is_vip', 'field_label': 'مشتری VIP', 'field_type': 'boolean'},
]
```

### Healthcare Industry
```python
templates = [
    {'field_key': 'medical_id', 'field_label': 'کد ملی/پزشکی', 'field_type': 'text'},
    {'field_key': 'insurance_type', 'field_label': 'نوع بیمه', 'field_type': 'select', 'options': ['تامین اجتماعی', 'خدمات درمانی', 'خصوصی']},
    {'field_key': 'last_visit_date', 'field_label': 'تاریخ آخرین ویزیت', 'field_type': 'date'},
    {'field_key': 'chronic_conditions', 'field_label': 'بیماری‌های مزمن', 'field_type': 'text'},
]
```

---

## 🎯 Success Metrics

### Technical Metrics
- Query performance: < 100ms for customer list with fields
- Migration time: < 5 minutes for 200K customers
- Storage overhead: < 50MB for 200K customers

### User Metrics
- Field creation time: < 30 seconds
- Customer profile load: < 500ms
- Form builder usability: > 80% success rate

---

## 🚨 Potential Issues & Solutions

### Issue 1: Field Limit Reached
**Solution**: 
- Show clear message: "حداکثر 90 فیلد. لطفاً یک فیلد را حذف کنید."
- Offer upgrade to Enterprise (unlimited fields with JSONField fallback)

### Issue 2: Performance with Many Fields
**Solution**:
- Use database indexes
- Implement field-level caching
- Lazy load fields in UI

### Issue 3: Data Migration
**Solution**:
- Provide migration script for existing data
- Support CSV import/export

---

## 📚 Additional Resources

### Related Files
- `src/message/models.py` - Customer model
- `src/message/services/customer_field_service.py` - Field service
- `src/workflow/models.py` - WaitingNode integration
- `src/message/api/customer_fields.py` - API endpoints

### Testing
- Unit tests for field validation
- Integration tests for API
- Performance tests for 200K+ customers

---

## ✅ Checklist

### Phase 1: Database
- [ ] Create migration for 90 custom fields
- [ ] Create CustomerFieldMapping model
- [ ] Create IndustryFieldTemplate model
- [ ] Add indexes
- [ ] Test migration on staging

### Phase 2: Backend
- [ ] Create CustomerFieldService
- [ ] Create IndustryTemplateService
- [ ] Create API endpoints
- [ ] Integrate with WaitingNode
- [ ] Add validation logic

### Phase 3: Frontend
- [ ] Field list view
- [ ] Field form (create/edit)
- [ ] Form builder UI
- [ ] Customer profile view
- [ ] Customer profile edit

### Phase 4: CRM Features
- [ ] CRM scoring
- [ ] Customer segmentation
- [ ] Activity timeline
- [ ] Notes & tasks
- [ ] Export/Import

### Phase 5: Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] Performance tests
- [ ] User acceptance testing

---

**نویسنده**: AI Assistant  
**تاریخ**: 2025-01-18  
**نسخه**: 1.0



