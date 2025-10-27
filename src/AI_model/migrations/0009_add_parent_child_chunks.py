# Generated migration for parent-child chunk relationship

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('AI_model', '0008_auto_20241027_0000'),  # Update this to your latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='tenantknowledge',
            name='document_id',
            field=models.UUIDField(
                blank=True,
                null=True,
                help_text='Groups related chunks from same document'
            ),
        ),
        migrations.AddField(
            model_name='tenantknowledge',
            name='parent_chunk_id',
            field=models.UUIDField(
                blank=True,
                null=True,
                help_text='Reference to parent chunk (for child chunks)'
            ),
        ),
        migrations.AddField(
            model_name='tenantknowledge',
            name='chunk_index',
            field=models.IntegerField(
                default=0,
                help_text='Index of this chunk within document'
            ),
        ),
        migrations.AddIndex(
            model_name='tenantknowledge',
            index=models.Index(
                fields=['document_id'],
                name='ai_model_te_documen_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='tenantknowledge',
            index=models.Index(
                fields=['parent_chunk_id'],
                name='ai_model_te_parent_idx'
            ),
        ),
    ]

