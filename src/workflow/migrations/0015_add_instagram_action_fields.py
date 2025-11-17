# Generated manually for Instagram Comment → DM + Reply action fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0014_add_instagram_comment_filters'),
    ]

    operations = [
        migrations.AddField(
            model_name='actionnode',
            name='instagram_dm_mode',
            field=models.CharField(
                blank=True,
                choices=[('STATIC', 'Static Message'), ('PRODUCT', 'Product-based AI Message')],
                default='STATIC',
                help_text='DM mode: static template or AI-generated product message',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='actionnode',
            name='instagram_dm_text_template',
            field=models.TextField(
                blank=True,
                help_text='Template for static DM (supports {{username}}, {{comment_text}}, etc.)'
            ),
        ),
        migrations.AddField(
            model_name='actionnode',
            name='instagram_product_id',
            field=models.UUIDField(
                blank=True,
                null=True,
                help_text='Product ID for PRODUCT mode (AI will generate DM based on this product)'
            ),
        ),
        migrations.AddField(
            model_name='actionnode',
            name='instagram_public_reply_enabled',
            field=models.BooleanField(
                default=False,
                help_text='Whether to send a public reply to the comment'
            ),
        ),
        migrations.AddField(
            model_name='actionnode',
            name='instagram_public_reply_text',
            field=models.TextField(
                blank=True,
                help_text='Template for public reply (supports {{username}}, etc.)'
            ),
        ),
    ]

