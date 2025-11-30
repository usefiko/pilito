# Generated migration for AffiliationConfig

from django.db import migrations, models
import django.core.exceptions


class Migration(migrations.Migration):

    dependencies = [
        ('settings', '0017_intercomtickettype_alter_generalsettings_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AffiliationConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('percentage', models.DecimalField(decimal_places=2, default=10.0, help_text='Percentage of payment to give as commission to referring user (e.g., 10 = 10%)', max_digits=5, verbose_name='Commission Percentage (%)')),
                ('is_active', models.BooleanField(default=True, help_text='Enable or disable the entire affiliate reward system', verbose_name='Affiliate System Active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': '🤝 Affiliation Configuration',
                'verbose_name_plural': '🤝 Affiliation Configuration',
            },
        ),
    ]

