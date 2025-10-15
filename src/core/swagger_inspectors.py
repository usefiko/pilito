"""
Custom Swagger/OpenAPI inspectors for drf-yasg to handle special field types.
"""

from drf_yasg import openapi
from drf_yasg.inspectors import FieldInspector, NotHandled
from rest_framework import serializers


class MultipleFileFieldInspector(FieldInspector):
    """
    Custom field inspector for handling ListField with FileField children.
    
    This fixes the issue where drf-yasg cannot automatically convert
    ListField(child=FileField()) to OpenAPI schema.
    """
    
    def field_to_swagger_object(self, field, swagger_object_type, use_references, **kwargs):
        """
        Convert a ListField containing FileField to a Swagger object.
        
        This method is called by drf-yasg when it encounters a field during schema generation.
        """
        SwaggerType, ChildSwaggerType = self._get_partial_types(field, swagger_object_type, use_references, **kwargs)
        
        # Check if this is a ListField with FileField child
        if isinstance(field, serializers.ListField):
            # Check if the child is a FileField
            if hasattr(field, 'child') and isinstance(field.child, (serializers.FileField, serializers.ImageField)):
                # For response schema or request body schema
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
                # For form parameters (multipart/form-data)
                elif swagger_object_type == openapi.Parameter:
                    # Return a single parameter that accepts multiple files
                    # In OpenAPI 2.0 (Swagger), arrays of files in form data are represented
                    # as a single parameter with type=file
                    return openapi.Parameter(
                        name=field.field_name or 'files',
                        in_=openapi.IN_FORM,
                        type=openapi.TYPE_FILE,
                        required=field.required,
                        description=field.help_text or "Upload multiple files"
                    )
                else:
                    # For any other type, return a generic schema to prevent errors
                    # This ensures we don't fall through to the default inspector
                    return openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BINARY)
                    )
        
        # Not our field type, let other inspectors handle it
        return NotHandled

