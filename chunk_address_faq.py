#!/usr/bin/env python
"""Chunk the address FAQ"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from web_knowledge.models import QAPair
from AI_model.services.incremental_chunker import IncrementalChunker
from accounts.models import User
from AI_model.models import TenantKnowledge

user = User.objects.get(email='y_motahedin@yahoo.com')

# پیدا کردن FAQ آدرس
faq = QAPair.objects.filter(user=user).filter(
    question__icontains='ادرستون'
).order_by('-created_at').first()

if faq:
    print(f'Found FAQ: {faq.question}')
    print(f'Answer: {faq.answer}')
    print(f'created_by_ai: {faq.created_by_ai}')
    
    # بررسی chunk
    existing_chunk = TenantKnowledge.objects.filter(
        source_id=faq.id,
        chunk_type='faq'
    ).first()
    
    if existing_chunk:
        print(f'\n✅ Already has chunk')
        print(f'   Priority: {existing_chunk.metadata.get("priority", 1.0)}')
    else:
        print(f'\n❌ No chunk found. Creating...')
        chunker = IncrementalChunker(user)
        try:
            result = chunker.chunk_qapair(faq)
            print(f'✅ Chunked successfully: {result}')
            
            # بررسی chunk جدید
            new_chunk = TenantKnowledge.objects.filter(
                source_id=faq.id,
                chunk_type='faq'
            ).first()
            
            if new_chunk:
                print(f'\n✅ Chunk created:')
                print(f'   Title: {new_chunk.section_title}')
                print(f'   Priority: {new_chunk.metadata.get("priority", 1.0)}')
                print(f'   User corrected: {new_chunk.metadata.get("user_corrected", False)}')
        except Exception as e:
            print(f'❌ Error: {e}')
            import traceback
            traceback.print_exc()
else:
    print('No FAQ found')

