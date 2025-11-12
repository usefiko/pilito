# Generated manually for adding sale_price field to Product model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web_knowledge', '0020_product_external_id_product_external_source_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='sale_price',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Sale price (final price after discount, used for manual entry)',
                max_digits=10,
                null=True
            ),
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Current price (used by AI extraction, keep null for manual entry)',
                max_digits=10,
                null=True
            ),
        ),
    ]

