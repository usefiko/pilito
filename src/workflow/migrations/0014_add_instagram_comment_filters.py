# Generated manually for Instagram comment filtering

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0013_alter_action_action_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='whennode',
            name='instagram_post_url',
            field=models.URLField(blank=True, help_text='Filter: Only trigger for comments on this specific post (optional). Leave empty for all posts.', null=True),
        ),
        migrations.AddField(
            model_name='whennode',
            name='instagram_media_type',
            field=models.CharField(blank=True, choices=[('all', 'All'), ('post', 'Post Only'), ('reel', 'Reel Only'), ('video', 'Video Only')], default='all', help_text='Filter: Type of Instagram media to monitor', max_length=20),
        ),
        migrations.AddField(
            model_name='whennode',
            name='comment_keywords',
            field=models.JSONField(blank=True, default=list, help_text='Filter: Only trigger if comment contains these keywords (case-insensitive)'),
        ),
    ]

