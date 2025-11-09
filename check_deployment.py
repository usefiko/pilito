#!/usr/bin/env python
"""Check if deployment includes latest changes"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

print('\n' + '='*80)
print('🔍 CHECKING DEPLOYMENT')
print('='*80)

# بررسی FAQ جدید
print('\n1️⃣ Checking FAQ chunking:')
from web_knowledge.models import QAPair
from AI_model.models import TenantKnowledge
from accounts.models import User

user = User.objects.get(email='y_motahedin@yahoo.com')

# جستجوی FAQ آدرس
address_faqs = QAPair.objects.filter(user=user).filter(
    question__icontains='ادرس'
).order_by('-created_at')

print(f'   Found {address_faqs.count()} FAQs with "ادرس"')

for faq in address_faqs:
    print(f'\n   Q: {faq.question}')
    print(f'   A: {faq.answer[:80]}...')
    print(f'   created_by_ai: {faq.created_by_ai}')
    print(f'   generation_status: {faq.generation_status}')
    
    # بررسی chunk
    chunk = TenantKnowledge.objects.filter(
        source_id=faq.id,
        chunk_type='faq'
    ).first()
    
    if chunk:
        print(f'   ✅ HAS CHUNK')
        print(f'      Priority: {chunk.metadata.get("priority", "N/A")}')
        print(f'      User corrected: {chunk.metadata.get("user_corrected", "N/A")}')
    else:
        print(f'   ❌ NO CHUNK - Need to create!')
        
        # Chunk کردن
        from AI_model.services.incremental_chunker import IncrementalChunker
        chunker = IncrementalChunker(user)
        try:
            result = chunker.chunk_qapair(faq)
            print(f'   ✅ CHUNKED NOW: {result}')
        except Exception as e:
            print(f'   ❌ CHUNK FAILED: {e}')

# بررسی code version
print('\n' + '='*80)
print('2️⃣ Checking code version:')
print('='*80)

# بررسی اینکه آیا تغییرات status_fa در کد هست
import inspect
import web_knowledge.tasks as tasks_module

source = inspect.getsource(tasks_module.generate_prompt_async_task)
if 'status_fa' in source:
    print('   ✅ status_fa FOUND in generate_prompt_async_task')
else:
    print('   ❌ status_fa NOT FOUND - old code is running!')

if 'gemini-2.0-flash-exp' in source:
    print('   ✅ gemini-2.0-flash-exp FOUND in task')
else:
    print('   ❌ Still using old model in task')

print('\n✅ Check complete!')

