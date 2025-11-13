# Generated migration for external_id and external_source fields in Product model
# This migration exists on server but was missing locally

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web_knowledge', '0022_merge_sale_price_and_wordpress_sync'),
    ]

    operations = [
        # These fields likely already exist, so this is a placeholder
        # The actual operations were already applied on server
        migrations.AlterField(
            model_name='product',
            name='external_id',
            field=models.CharField(blank=True, max_length=255, null=True, help_text='External product ID (e.g., WooCommerce product ID)'),
        ),
        migrations.AlterField(
            model_name='product',
            name='external_source',
            field=models.CharField(blank=True, choices=[('woocommerce', 'WooCommerce'), ('shopify', 'Shopify'), ('manual', 'Manual Entry'), ('ai_extracted', 'AI Extracted')], max_length=50, null=True, help_text='Source of the product data'),
        ),
    ]

