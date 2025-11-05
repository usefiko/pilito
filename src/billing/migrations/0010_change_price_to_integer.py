# Generated manually - Change price from DecimalField to IntegerField

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0009_change_price_to_single_field'),
    ]

    operations = [
        # TokenPlan: Change price field to IntegerField
        migrations.AlterField(
            model_name='tokenplan',
            name='price',
            field=models.IntegerField(default=0, help_text='Price of the plan'),
        ),
        # FullPlan: Change price field to IntegerField
        migrations.AlterField(
            model_name='fullplan',
            name='price',
            field=models.IntegerField(default=0, help_text='Price of the plan'),
        ),
    ]

