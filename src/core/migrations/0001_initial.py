# Generated manually for core app
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ProxySetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='نام پروکسی (مثلاً: Main Proxy)', max_length=50, unique=True)),
                ('http_proxy', models.CharField(help_text='آدرس پروکسی HTTP به فرمت: http://user:pass@ip:port', max_length=255)),
                ('https_proxy', models.CharField(help_text='آدرس پروکسی HTTPS به فرمت: http://user:pass@ip:port', max_length=255)),
                ('fallback_http_proxy', models.CharField(blank=True, help_text='پروکسی پشتیبان HTTP (اختیاری)', max_length=255, null=True)),
                ('fallback_https_proxy', models.CharField(blank=True, help_text='پروکسی پشتیبان HTTPS (اختیاری)', max_length=255, null=True)),
                ('is_active', models.BooleanField(default=True, help_text='فقط یک پروکسی باید فعال باشد')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'تنظیمات پروکسی',
                'verbose_name_plural': 'تنظیمات پروکسی\u200cها',
                'ordering': ['-is_active', '-updated_at'],
            },
        ),
    ]

