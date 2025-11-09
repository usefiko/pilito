#!/usr/bin/env python
"""Chunk missing FAQs and add priority system"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from web_knowledge.models import QAPair
from AI_model.models import TenantKnowledge
from AI_model.services.incremental_chunker import IncrementalChunker
from accounts.models import User

user = User.objects.get(email='y_motahedin@yahoo.com')

# پیدا کردن FAQs بدون chunk
all_faqs = QAPair.objects.filter(user=user)
chunked_faq_ids = set(
    TenantKnowledge.objects.filter(
        user=user,
        chunk_type='faq',
        source_id__isnull=False
    ).values_list('source_id', flat=True)
)

missing_faq_ids = [faq.id for faq in all_faqs if faq.id not in chunked_faq_ids]

print(f'\n📊 Stats:')
print(f'  Total FAQs: {all_faqs.count()}')
print(f'  Chunked FAQs: {len(chunked_faq_ids)}')
print(f'  Missing chunks: {len(missing_faq_ids)}')

if missing_faq_ids:
    print(f'\n🔧 Chunking missing FAQs...')
    chunker = IncrementalChunker(user)
    
    for faq_id in missing_faq_ids:
        faq = QAPair.objects.get(id=faq_id)
        print(f'\n  Chunking: {faq.question[:50]}...')
        
        try:
            result = chunker.chunk_qapair(faq)
            print(f'  ✅ Success: {result}')
        except Exception as e:
            print(f'  ❌ Error: {e}')

# بررسی نتیجه
final_count = TenantKnowledge.objects.filter(
    user=user,
    chunk_type='faq'
).count()

print(f'\n📊 Final Stats:')
print(f'  Total FAQ chunks: {final_count}')

# نمایش chunks
print(f'\n📦 FAQ Chunks:')
chunks = TenantKnowledge.objects.filter(
    user=user,
    chunk_type='faq'
).order_by('-created_at')

for chunk in chunks:
    print(f'\n  Title: {chunk.section_title}')
    print(f'  Text: {chunk.full_text[:100]}...')
    
    # بررسی metadata برای priority
    if 'user_corrected' in chunk.metadata:
        print(f'  🌟 USER CORRECTED (priority: {chunk.metadata.get("priority", 1.0)})')

print(f'\n✅ Done!')

