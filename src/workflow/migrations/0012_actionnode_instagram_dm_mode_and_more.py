# Placeholder migration for Instagram DM mode
# This migration exists in the database but was missing from files
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0011_alter_whennode_channels_alter_whennode_keywords_and_more'),
    ]

    operations = [
        # Empty - fields already exist in database
    ]

