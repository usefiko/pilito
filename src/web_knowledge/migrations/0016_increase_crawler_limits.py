# Generated migration to increase crawler limits

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web_knowledge', '0007_product_billing_period_product_brand_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='websitesource',
            name='max_pages',
            field=models.PositiveIntegerField(default=200, help_text='Maximum number of pages to crawl'),
        ),
        migrations.AlterField(
            model_name='websitesource',
            name='crawl_depth',
            field=models.PositiveIntegerField(default=5, help_text='Maximum depth to crawl'),
        ),
    ]

