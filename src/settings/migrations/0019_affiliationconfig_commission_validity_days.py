# Generated migration for AffiliationConfig - adding commission_validity_days

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('settings', '0018_affiliationconfig'),
    ]

    operations = [
        migrations.AddField(
            model_name='affiliationconfig',
            name='commission_validity_days',
            field=models.PositiveIntegerField(
                default=30,
                help_text='Number of days after registration during which payments qualify for commission (0 = unlimited)',
                verbose_name='Commission Validity (Days)'
            ),
        ),
    ]

