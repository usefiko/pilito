# Generated manually for key_values field addition

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0012_workflownode_condition_ai_prompt_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='actionnode',
            name='key_values',
            field=models.JSONField(blank=True, default=list, help_text="Key-value pairs for CTA buttons (e.g., [['CTA:Title|https://url.com']])"),
        ),
        migrations.AddField(
            model_name='waitingnode',
            name='key_values',
            field=models.JSONField(blank=True, default=list, help_text="Key-value pairs for CTA buttons (e.g., [['CTA:Title|https://url.com']])"),
        ),
    ]

