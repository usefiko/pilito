# Generated migration for parent-child chunk relationship

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('AI_model', '0005_rename_ai_usage_l_user_id_2a5e9d_idx_ai_usage_lo_user_id_a17394_idx_and_more'),
    ]

    operations = [
        # document_id already exists in production, skip it
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

