# Generated manually for AIUsageLog model
# Migration for detailed AI usage tracking

import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AI_model', '0003_intentrouting_intentkeyword_sessionmemory_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AIUsageLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('section', models.CharField(
                    choices=[
                        ('chat', 'Customer Chat'),
                        ('prompt_generation', 'Prompt Generation'),
                        ('marketing_workflow', 'Marketing Workflow'),
                        ('knowledge_qa', 'Knowledge Base Q&A'),
                        ('product_recommendation', 'Product Recommendation'),
                        ('rag_pipeline', 'RAG Pipeline'),
                        ('web_knowledge', 'Web Knowledge Processing'),
                        ('session_memory', 'Session Memory Summary'),
                        ('intent_detection', 'Intent Detection'),
                        ('embedding_generation', 'Embedding Generation'),
                        ('other', 'Other'),
                    ],
                    db_index=True,
                    help_text='Feature or module that used AI',
                    max_length=50
                )),
                ('prompt_tokens', models.IntegerField(default=0, help_text='Input tokens used')),
                ('completion_tokens', models.IntegerField(default=0, help_text='Output tokens used')),
                ('total_tokens', models.IntegerField(default=0, help_text='Total tokens used')),
                ('response_time_ms', models.IntegerField(default=0, help_text='Response time in milliseconds')),
                ('success', models.BooleanField(default=True, help_text='Whether the request was successful')),
                ('model_name', models.CharField(
                    blank=True,
                    default='gemini-1.5-flash',
                    help_text='AI model used (e.g., gemini-1.5-flash, gpt-4)',
                    max_length=100
                )),
                ('error_message', models.TextField(blank=True, help_text='Error details if request failed', null=True)),
                ('metadata', models.JSONField(
                    blank=True,
                    default=dict,
                    help_text='Additional context (conversation_id, message_id, etc.)'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('user', models.ForeignKey(
                    db_index=True,
                    help_text='User who triggered the AI request',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ai_usage_logs',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': '📝 AI Usage Log',
                'verbose_name_plural': '📝 AI Usage Logs',
                'db_table': 'ai_usage_log',
                'ordering': ['-created_at'],
            },
        ),
        # Add indexes for better query performance
        migrations.AddIndex(
            model_name='aiusagelog',
            index=models.Index(fields=['user', 'section', 'created_at'], name='ai_usage_l_user_id_2a5e9d_idx'),
        ),
        migrations.AddIndex(
            model_name='aiusagelog',
            index=models.Index(fields=['user', 'created_at'], name='ai_usage_l_user_id_f7c8a2_idx'),
        ),
        migrations.AddIndex(
            model_name='aiusagelog',
            index=models.Index(fields=['section', 'created_at'], name='ai_usage_l_section_8d3b1f_idx'),
        ),
        migrations.AddIndex(
            model_name='aiusagelog',
            index=models.Index(fields=['created_at'], name='ai_usage_l_created_2c4e5a_idx'),
        ),
        migrations.AddIndex(
            model_name='aiusagelog',
            index=models.Index(fields=['success'], name='ai_usage_l_success_9f6d3b_idx'),
        ),
    ]

