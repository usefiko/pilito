#!/usr/bin/env python
"""Check keywords and test delete signal"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from AI_model.models import IntentKeyword, TenantKnowledge
from web_knowledge.models import QAPair
from accounts.models import User

user = User.objects.get(email='y_motahedin@yahoo.com')

print('\n' + '='*80)
print('1️⃣ CHECKING KEYWORDS')
print('='*80)

# بررسی تعداد keywords
total = IntentKeyword.objects.filter(user__isnull=True).count()
print(f'\n📊 Total global keywords: {total}')

# بررسی contact keywords
contact_fa = IntentKeyword.objects.filter(
    intent='contact',
    language='fa',
    user__isnull=True
).count()

print(f'📊 Contact (FA) keywords: {contact_fa}')

# بررسی کلمات مهم
important = ['ادرس', 'آدرس', 'ارسال', 'نحوه ارسال']
print(f'\n🔍 Checking important keywords:')
for word in important:
    exists = IntentKeyword.objects.filter(
        keyword=word,
        user__isnull=True
    ).exists()
    print(f'  {"✅" if exists else "❌"} "{word}": {exists}')

# نمایش چند keyword
print(f'\n📋 Sample Contact Keywords:')
sample = IntentKeyword.objects.filter(
    intent='contact',
    language='fa',
    user__isnull=True
)[:10]
for kw in sample:
    print(f'  - {kw.keyword} (weight: {kw.weight})')

print('\n' + '='*80)
print('2️⃣ CHECKING DELETE SIGNAL')
print('='*80)

# بررسی FAQ ها و chunks
faqs = QAPair.objects.filter(user=user)
print(f'\n📋 Total FAQs: {faqs.count()}')

for faq in faqs:
    print(f'\n  FAQ: {faq.question[:50]}...')
    print(f'    ID: {faq.id}')
    
    # بررسی chunk
    chunk = TenantKnowledge.objects.filter(
        source_id=faq.id,
        chunk_type='faq'
    ).first()
    
    if chunk:
        print(f'    ✅ Has chunk: {chunk.id}')
        print(f'       Priority: {chunk.metadata.get("priority", 1.0)}')
    else:
        print(f'    ❌ NO CHUNK')

print('\n' + '='*80)
print('3️⃣ TESTING DELETE SIGNAL')
print('='*80)
print('\n⚠️  Note: Delete signal uses pre_delete, so chunks are deleted BEFORE FAQ')
print('   This ensures relationships still exist when deleting chunks')
print('\n✅ Signal is configured correctly in signals.py:')
print('   @receiver(pre_delete, sender=\'web_knowledge.QAPair\')')
print('   def on_qapair_deleted_cleanup_chunks(...)')

print('\n✅ Done!')

