# Generated migration for adding affiliate_active field to User

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='affiliate_active',
            field=models.BooleanField(default=False, help_text='Enable or disable affiliate rewards for this user', verbose_name='Affiliate System Active'),
        ),
    ]

