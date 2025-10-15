# Generated manually to handle existing openai_api_key field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('settings', '0014_uptopro_generalsettings_openai_api_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='generalsettings',
            name='openai_api_key',
            field=models.CharField(blank=True, help_text='OpenAI API key for multilingual embedding (text-embedding-3-large)', max_length=200, null=True),
        ),
    ]

