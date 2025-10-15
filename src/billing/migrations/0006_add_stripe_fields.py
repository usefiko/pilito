# Generated migration to add Stripe fields to plans

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0005_create_free_trial_plan'),
    ]

    operations = [
        migrations.AddField(
            model_name='tokenplan',
            name='stripe_product_id',
            field=models.CharField(max_length=255, null=True, blank=True, help_text='Stripe Product ID'),
        ),
        migrations.AddField(
            model_name='tokenplan',
            name='stripe_price_id',
            field=models.CharField(max_length=255, null=True, blank=True, help_text='Stripe Price ID'),
        ),
        migrations.AddField(
            model_name='fullplan',
            name='stripe_product_id',
            field=models.CharField(max_length=255, null=True, blank=True, help_text='Stripe Product ID'),
        ),
        migrations.AddField(
            model_name='fullplan',
            name='stripe_price_id',
            field=models.CharField(max_length=255, null=True, blank=True, help_text='Stripe Price ID'),
        ),
    ]

