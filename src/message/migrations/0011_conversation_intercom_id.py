# Generated migration for adding Intercom integration fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('message', '0010_customer_bio_customer_persona_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='intercom_conversation_id',
            field=models.CharField(
                max_length=255,
                null=True,
                blank=True,
                help_text='Intercom conversation ID for syncing'
            ),
        ),
        migrations.AddField(
            model_name='conversation',
            name='sync_to_intercom',
            field=models.BooleanField(
                default=False,
                help_text='Whether to sync this conversation to Intercom'
            ),
        ),
        migrations.AddField(
            model_name='message',
            name='intercom_message_id',
            field=models.CharField(
                max_length=255,
                null=True,
                blank=True,
                help_text='Intercom message ID for syncing'
            ),
        ),
    ]

