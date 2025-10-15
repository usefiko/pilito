# Generated migration for adding Intercom conversation ID to SupportTicket

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('settings', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='supportticket',
            name='intercom_conversation_id',
            field=models.CharField(
                blank=True,
                help_text='Intercom Conversation ID for syncing support tickets',
                max_length=255,
                null=True,
                unique=True
            ),
        ),
    ]

