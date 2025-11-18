# Merge migration to resolve conflict between 0012 and 0014
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0012_alter_whennode_tags'),
        ('workflow', '0012_actionnode_instagram_dm_mode_and_more'),
    ]

    operations = [
        # This is a merge migration - no operations needed
    ]

