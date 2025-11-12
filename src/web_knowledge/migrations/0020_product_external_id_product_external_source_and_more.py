# Generated migration for WooCommerce integration
# This migration exists in the database as 0020_product_external_id_product_external_source_and_more

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web_knowledge', '0017_add_image_to_product'),
    ]

    operations = [
        # Add external_id field
        migrations.AddField(
            model_name='product',
            name='external_id',
            field=models.CharField(
                max_length=100,
                blank=True,
                null=True,
                db_index=True,
                help_text='External product ID (e.g., woo_414, shopify_789)'
            ),
        ),
        
        # Add external_source field
        migrations.AddField(
            model_name='product',
            name='external_source',
            field=models.CharField(
                max_length=20,
                blank=True,
                choices=[
                    ('woocommerce', 'WooCommerce'),
                    ('shopify', 'Shopify'),
                    ('manual', 'Manual'),
                ],
                default='manual',
                help_text='Source of the product'
            ),
        ),
        
        # Add unique constraint for external products
        migrations.AddConstraint(
            model_name='product',
            constraint=models.UniqueConstraint(
                fields=['user', 'external_id'],
                condition=models.Q(external_id__isnull=False),
                name='unique_external_product_per_user',
                violation_error_message='این محصول خارجی قبلاً برای این کاربر وجود دارد'
            ),
        ),
        
        # Add index for external_source queries
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['user', 'external_source', 'is_active'], name='idx_product_external'),
        ),
    ]

