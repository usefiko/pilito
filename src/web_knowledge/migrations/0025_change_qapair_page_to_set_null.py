# Generated migration to change QAPair.page from CASCADE to SET_NULL
# So Q&A pairs are preserved when website/page is deleted

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('web_knowledge', '0023_product_external_id_product_external_source_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='qapair',
            name='page',
            field=models.ForeignKey(
                blank=True,
                help_text='Source page (if deleted, Q&A remains)',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='qa_pairs',
                to='web_knowledge.websitepage'
            ),
        ),
    ]

