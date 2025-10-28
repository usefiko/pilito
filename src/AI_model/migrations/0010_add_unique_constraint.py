# Generated migration for preventing duplicate chunks
# Critical fix for race condition in concurrent chunking

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AI_model', '0009_add_parent_child_chunks'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='tenantknowledge',
            constraint=models.UniqueConstraint(
                fields=['user', 'source_id', 'chunk_type'],
                condition=models.Q(source_id__isnull=False),
                name='unique_chunk_per_source',
                violation_error_message='این صفحه قبلاً chunk شده است'
            ),
        ),
    ]

