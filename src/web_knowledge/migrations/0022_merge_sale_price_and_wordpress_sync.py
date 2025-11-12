# Generated merge migration to resolve conflict between 0019 and 0021

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web_knowledge', '0019_add_sale_price_to_product'),
        ('web_knowledge', '0021_add_wordpress_sync_fields'),
    ]

    operations = [
        # Empty merge migration - both migrations are already applied
        # This resolves the conflict where both 0019 and 0021 depend on different parents
    ]

