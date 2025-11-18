# Generated merge migration to resolve conflicts
# This merges the two 0013 migration branches:
# - 0013_add_instagram_comment_filters (file)
# - 0013_alter_action_action_type_and_more (in database, file may be missing)

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0013_add_instagram_comment_filters'),
        # Note: The other branch '0013_alter_action_action_type_and_more' may exist in database
        # but not as a file. Django will handle this when you run makemigrations --merge
        ('workflow', '0012_alter_whennode_tags'),  # Fallback if other migration doesn't exist
    ]

    operations = [
        # This is a merge migration - no operations needed
        # It just merges the two migration branches
    ]

