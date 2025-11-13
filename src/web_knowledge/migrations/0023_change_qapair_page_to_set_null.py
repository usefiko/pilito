# Generated manually for changing QAPair.page from CASCADE to SET_NULL

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('web_knowledge', '0022_merge_sale_price_and_wordpress_sync'),
    ]

    operations = [
        migrations.AlterField(
            model_name='qapair',
            name='page',
            field=models.ForeignKey(blank=True, help_text='Source page (if deleted, Q&A remains)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qa_pairs', to='web_knowledge.websitepage'),
        ),
    ]

