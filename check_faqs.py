#!/usr/bin/env python
"""Check FAQ chunks"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from web_knowledge.models import QAPair
from AI_model.models import TenantKnowledge
from accounts.models import User
from django.db.models import Q

user = User.objects.get(email='y_motahedin@yahoo.com')

# بررسی FAQ ها
print('\n' + '='*80)
print('📋 RECENT FAQ PAIRS')
print('='*80)
faqs = QAPair.objects.filter(user=user).order_by('-created_at')[:5]
for i, faq in enumerate(faqs, 1):
    print(f'\n{i}. Q: {faq.question}')
    print(f'   A: {faq.answer[:100]}...')
    print(f'   Created by AI: {faq.created_by_ai}')
    print(f'   ID: {faq.id}')

# بررسی chunks
print('\n' + '='*80)
print('📦 RECENT FAQ CHUNKS')
print('='*80)
chunks = TenantKnowledge.objects.filter(
    user=user,
    chunk_type='faq'
).order_by('-created_at')[:5]

for i, chunk in enumerate(chunks, 1):
    print(f'\n{i}. Title: {chunk.section_title}')
    print(f'   Text: {chunk.full_text[:100]}...')
    print(f'   Source ID: {chunk.source_id}')
    print(f'   Created: {chunk.created_at}')

# جستجوی کلمه 'ادرس'
print('\n' + '='*80)
print('🔍 FAQS WITH "ادرس/آدرس"')
print('='*80)
address_faqs = QAPair.objects.filter(user=user).filter(
    Q(question__icontains='ادرس') | Q(question__icontains='آدرس') |
    Q(answer__icontains='ادرس') | Q(answer__icontains='آدرس')
)
print(f'Found: {address_faqs.count()} FAQs')

for faq in address_faqs:
    print(f'\nQ: {faq.question}')
    print(f'A: {faq.answer}')
    
    # آیا chunk شده؟
    chunk = TenantKnowledge.objects.filter(
        source_id=faq.id,
        chunk_type='faq'
    ).first()
    
    if chunk:
        print(f'✅ Has chunk (created: {chunk.created_at})')
    else:
        print(f'❌ NO CHUNK! Need to create chunk for FAQ {faq.id}')

print('\n' + '='*80)
print(f'📊 STATS')
print('='*80)
print(f'Total FAQs: {QAPair.objects.filter(user=user).count()}')
print(f'Total FAQ chunks: {TenantKnowledge.objects.filter(user=user, chunk_type="faq").count()}')
print(f'FAQs without chunks: {QAPair.objects.filter(user=user).exclude(id__in=TenantKnowledge.objects.filter(user=user, chunk_type="faq").values("source_id")).count()}')

