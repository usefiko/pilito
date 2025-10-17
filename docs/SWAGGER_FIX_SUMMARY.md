# Swagger API Documentation Fix

## Problem
The API documentation at `https://api.pilito.com/docs/` was failing with the following error:

```
drf_yasg.errors.SwaggerGenerationError: FileField is supported only in a formData Parameter or response Schema
```

## Root Cause
The issue was caused by `drf-yasg` (Django REST Framework YAML and Swagger Generation) attempting to auto-introspect serializers that contain `ListField` with `FileField` as a child. This pattern is used for multiple file uploads but doesn't conform to OpenAPI/Swagger specifications when automatically converted.

The problematic serializers were:
1. **SupportMessageSerializer** - used for sending messages to support tickets
2. **CreateSupportTicketSerializer** - used for creating new support tickets

Both serializers had fields like:
```python
uploaded_files = serializers.ListField(
    child=serializers.FileField(max_length=10000000, allow_empty_file=True),
    write_only=True,
    required=False,
    allow_empty=True
)
```

## Solution
The fix involved creating a **custom field inspector** for drf-yasg that can properly handle `ListField` with `FileField` children. This is the cleanest and most maintainable solution as it doesn't require modifying every view or serializer.

### Changes Made

#### 1. Created `/src/core/swagger_inspectors.py` (NEW FILE)

Created a custom field inspector class `MultipleFileFieldInspector` that:
- Detects when drf-yasg encounters a `ListField` with `FileField` child
- Converts it to a proper OpenAPI schema (array of binary strings)
- Prevents the SwaggerGenerationError from occurring

```python
class MultipleFileFieldInspector(FieldInspector):
    """
    Custom field inspector for handling ListField with FileField children.
    """
    
    def field_to_swagger_object(self, field, swagger_object_type, use_references, **kwargs):
        if isinstance(field, serializers.ListField) and isinstance(field.child, serializers.FileField):
            if swagger_object_type == openapi.Schema:
                return openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_STRING,
                        format=openapi.FORMAT_BINARY,
                        description="File upload"
                    ),
                    description=field.help_text or "Upload multiple files"
                )
            return NotHandled
        return NotHandled
```

#### 2. Updated `/src/core/urls.py`

Modified the drf-yasg schema configuration to use our custom inspector:
- Created `CustomOpenAPISchemaGenerator` class that extends `OpenAPISchemaGenerator`
- Overrode `get_field_inspectors()` to prepend our `MultipleFileFieldInspector`
- Updated `schema_view` to use `generator_class=CustomOpenAPISchemaGenerator`

This ensures our custom inspector is used for ALL schema generation across the entire API.

#### 3. Enhanced `/src/settings/support_views.py`

Added swagger documentation improvements:
- Added `request_body=None` to POST method decorators (prevents double inspection)
- Added `consumes=['multipart/form-data']` to specify content type
- Kept `manual_parameters` for explicit form field documentation

#### 4. Enhanced `/src/settings/serializers.py`

- Added `help_text` to file upload fields for better documentation
- Fields remain functional for actual API operations

## Technical Details

### How the Custom Inspector Works

1. **Field Detection**: During schema generation, drf-yasg calls our `MultipleFileFieldInspector.field_to_swagger_object()` method for each field in the serializer.

2. **Pattern Matching**: The inspector checks if the field is a `ListField` with a `FileField` child.

3. **Schema Conversion**: If matched, it returns an OpenAPI-compliant schema:
   ```yaml
   type: array
   items:
     type: string
     format: binary
   ```

4. **Fallback**: If not matched, it returns `NotHandled`, allowing other inspectors to process the field.

5. **Priority**: By prepending our inspector to the list (in `CustomOpenAPISchemaGenerator`), it's checked before the default inspectors that would throw the error.

### Why This Approach is Better

- **Automatic**: Works for ALL endpoints without manual intervention
- **Maintainable**: Single point of configuration
- **Non-intrusive**: Doesn't modify existing serializers or views
- **Extensible**: Easy to add support for other custom field types
- **Clean**: Separates Swagger/OpenAPI concerns from business logic

## Testing

To verify the fix:
1. Navigate to `https://api.pilito.com/docs/`
2. The Swagger UI should load without errors
3. The affected endpoints should show proper documentation:
   - `POST /api/support/tickets/` - Create support ticket
   - `POST /api/support/tickets/{ticket_id}/messages/` - Send message

## Future Recommendations

### For New File Upload Endpoints

The custom inspector now handles `ListField(child=FileField())` automatically! You can:

1. **Use the pattern freely in serializers**:
   ```python
   files = serializers.ListField(
       child=serializers.FileField(max_length=10000000, allow_empty_file=True),
       write_only=True,
       required=False,
       help_text="Upload multiple files"
   )
   ```

2. **Add proper view configuration**:
   - Use `parser_classes = [MultiPartParser, FormParser]`
   - The Swagger docs will be generated automatically!

3. **Optional: Add explicit swagger docs** (for better control):
   ```python
   @swagger_auto_schema(
       operation_description="Endpoint with file uploads",
       manual_parameters=[...],
       consumes=['multipart/form-data']
   )
   ```

### For Other Custom Field Types

If you encounter similar issues with other field combinations:

1. Create a new inspector in `/src/core/swagger_inspectors.py`
2. Add it to the `CustomOpenAPISchemaGenerator.get_field_inspectors()` method
3. The inspector should:
   - Detect the problematic field pattern
   - Return an OpenAPI-compliant schema
   - Return `NotHandled` if it doesn't match

## References
- [drf-yasg Documentation](https://drf-yasg.readthedocs.io/)
- [OpenAPI Specification - File Uploads](https://swagger.io/docs/specification/describing-request-body/file-upload/)

