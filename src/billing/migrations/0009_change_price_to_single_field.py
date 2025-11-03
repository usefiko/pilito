# Generated manually - Consolidate price fields to single price field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0008_subscription_queued_full_plan_and_more'),
    ]

    operations = [
        # TokenPlan: Add single price field
        migrations.AddField(
            model_name='tokenplan',
            name='price',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Price of the plan',
                max_digits=10
            ),
        ),
        # FullPlan: Add single price field
        migrations.AddField(
            model_name='fullplan',
            name='price',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Price of the plan',
                max_digits=10
            ),
        ),
        # TokenPlan: Remove old price fields
        migrations.RemoveField(
            model_name='tokenplan',
            name='price_en',
        ),
        migrations.RemoveField(
            model_name='tokenplan',
            name='price_tr',
        ),
        migrations.RemoveField(
            model_name='tokenplan',
            name='price_ar',
        ),
        # FullPlan: Remove old price fields
        migrations.RemoveField(
            model_name='fullplan',
            name='price_en',
        ),
        migrations.RemoveField(
            model_name='fullplan',
            name='price_tr',
        ),
        migrations.RemoveField(
            model_name='fullplan',
            name='price_ar',
        ),
        # Update model ordering for TokenPlan
        migrations.AlterModelOptions(
            name='tokenplan',
            options={'ordering': ['price']},
        ),
        # Update model ordering for FullPlan
        migrations.AlterModelOptions(
            name='fullplan',
            options={'ordering': ['is_yearly', 'price']},
        ),
    ]

