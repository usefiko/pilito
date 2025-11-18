# Placeholder migration to prevent Django from auto-generating 0026
# The columns external_id and external_source already exist (added in 0020 and 0023)
# This migration does nothing but marks the state as up-to-date

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web_knowledge', '0025_product_external_id_product_external_source_and_more'),
    ]

    operations = [
        # No operations needed - columns already exist
        # This migration exists only to prevent Django from auto-generating it
    ]

