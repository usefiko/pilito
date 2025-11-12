# Generated merge migration to resolve conflict between 0019_remove, 0019_add_sale_price, 0020, and 0021

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web_knowledge', '0019_remove_product_unique_external_product_per_user_and_more'),
        ('web_knowledge', '0019_add_sale_price_to_product'),
        ('web_knowledge', '0020_product_external_id_product_external_source_and_more'),
        ('web_knowledge', '0021_add_wordpress_sync_fields'),
    ]

    operations = [
        # Empty merge migration - all migrations are already applied
        # This resolves the conflict where multiple migrations depend on different parents:
        # - 0019_remove depends on 0017
        # - 0020 depends on 0017
        # - 0019_add_sale_price depends on 0020
        # - 0021 depends on 0020
    ]

