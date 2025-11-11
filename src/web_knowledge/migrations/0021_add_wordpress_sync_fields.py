from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web_knowledge', '0020_product_external_id_product_external_source_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='websitepage',
            name='source_type',
            field=models.CharField(
                choices=[('crawled', 'Crawled'), ('wordpress', 'WordPress Sync')],
                default='crawled',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='websitepage',
            name='wordpress_post_id',
            field=models.IntegerField(blank=True, help_text='WordPress Post ID if synced', null=True),
        ),
    ]

