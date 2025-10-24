# Generated manually for modular prompt system refactoring
# Similar to: OpenAI ChatGPT, Intercom Fin, Zendesk AI

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('settings', '0017_intercomtickettype_supportticket_intercom_ticket_id_and_more'),
    ]

    operations = [
        # Add new modular fields to GeneralSettings
        migrations.AddField(
            model_name='generalsettings',
            name='ai_role',
            field=models.TextField(
                default='You are an AI customer service assistant.',
                max_length=500,
                verbose_name='🤖 AI Role & Identity'
            ),
        ),
        migrations.AddField(
            model_name='generalsettings',
            name='language_rules',
            field=models.TextField(
                default="""Always reply in Persian (Farsi).
Convert Latin names to Persian equivalents (e.g., Omid → امید).
Use everyday Persian expressions, not formal sentences.""",
                max_length=1000,
                verbose_name='🌐 Language & Localization'
            ),
        ),
        migrations.AddField(
            model_name='generalsettings',
            name='tone_and_style',
            field=models.TextField(
                default="""Speak casually and emotionally, not like a brochure.
Write like a person chatting on Instagram.
Keep responses under 2 short lines.""",
                max_length=1000,
                verbose_name='💬 Tone & Style (لحن و سبک)'
            ),
        ),
        migrations.AddField(
            model_name='generalsettings',
            name='response_length',
            field=models.CharField(
                choices=[
                    ('concise', '🔹 Concise (1-2 جمله کوتاه)'),
                    ('moderate', '🔸 Moderate (2-4 جمله متوسط)'),
                    ('detailed', '🔶 Detailed (4+ جمله تفصیلی)'),
                ],
                default='concise',
                max_length=20,
                verbose_name='📏 Response Length (طول پاسخ)'
            ),
        ),
        migrations.AddField(
            model_name='generalsettings',
            name='response_guidelines',
            field=models.TextField(
                default="""Limit emojis to 1 per message.
Avoid long introductions — go straight to the point.
After each answer, add one short outcome phrase if possible.""",
                max_length=1000,
                verbose_name='📝 Response Guidelines (راهنمای پاسخ‌دهی)'
            ),
        ),
        migrations.AddField(
            model_name='generalsettings',
            name='greeting_rules',
            field=models.TextField(
                default="""Use customer's name ONLY in the FIRST message.
After that, use their name only if 3+ messages have passed.
NEVER say 'سلام' more than once in the same conversation.""",
                max_length=1000,
                verbose_name='👋 Greeting & Name Usage (احوالپرسی و استفاده از نام)'
            ),
        ),
        migrations.AddField(
            model_name='generalsettings',
            name='welcome_back_threshold_hours',
            field=models.IntegerField(
                default=12,
                verbose_name='⏰ Welcome Back Threshold (ساعت)'
            ),
        ),
        migrations.AddField(
            model_name='generalsettings',
            name='anti_hallucination_rules',
            field=models.TextField(
                default="""NEVER promise to send information if you don't have it RIGHT NOW.
NEVER say: "الان برات می‌فرستم" or "یه لحظه صبر کن"
If you don't have the information, be honest immediately.""",
                max_length=1000,
                verbose_name='🚨 Anti-Hallucination Rules (قوانین ضد توهم‌زایی)'
            ),
        ),
        migrations.AddField(
            model_name='generalsettings',
            name='knowledge_limitation_response',
            field=models.TextField(
                default='متاسفانه این اطلاعات الان در دسترس نیست، ولی می‌تونی از طریق {contact_method} بپرسی.',
                max_length=500,
                verbose_name='📢 Knowledge Limitation Response (پاسخ محدودیت دانش)'
            ),
        ),
        migrations.AddField(
            model_name='generalsettings',
            name='link_handling_rules',
            field=models.TextField(
                default="""Always include FULL URLs (e.g., https://example.com/pricing)
NEVER use placeholders like [link] or [URL]
If you don't have a link, say so honestly instead of making one up.""",
                max_length=500,
                verbose_name='🔗 Link & URL Handling (مدیریت لینک‌ها)'
            ),
        ),
        migrations.AddField(
            model_name='generalsettings',
            name='custom_instructions',
            field=models.TextField(
                blank=True,
                null=True,
                max_length=2000,
                verbose_name='⚡ Custom Instructions (دستورات سفارشی - اختیاری)'
            ),
        ),
        # Make auto_prompt nullable and mark as deprecated
        migrations.AlterField(
            model_name='generalsettings',
            name='auto_prompt',
            field=models.TextField(
                blank=True,
                default='''You are an AI customer service representative.
Respond to customer inquiries professionally and helpfully.
Always respond in the same language the customer uses.
Keep your responses clear and concise.

🔗 CRITICAL - Links & URLs:
- Always include FULL URLs (e.g., https://fiko.net/pricing)
- NEVER use placeholders like [link] or [URL]
- Write complete clickable links in your responses''',
                max_length=5000,
                null=True,
                verbose_name='⚠️ [DEPRECATED] Old Auto Prompt'
            ),
        ),
    ]

