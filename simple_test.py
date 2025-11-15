#!/usr/bin/env python
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from AI_model.services.production_rag import ProductionRAG

# Disable reranking
ProductionRAG.ENABLE_RERANKING = False

User = get_user_model()
user = User.objects.get(phone_number='+989158157440')

result = ProductionRAG.retrieve_context(
    query='ادرستون', user=user, primary_source='faq',
    secondary_sources=['manual'], primary_budget=600,
    secondary_budget=200, routing_info=None
)

p = result.get('primary_context', [])
s = result.get('secondary_context', [])

print(f'Primary: {len(p)}, Secondary: {len(s)}')

if s:
    for i, chunk in enumerate(s[:3]):
        content = chunk.get('content', '')
        has_addr = 'مشهد' in content and 'فردوسی' in content
        print(f'{i+1}. Addr: {"YES" if has_addr else "NO"}, Len: {len(content)}')
        if has_addr:
            print(f'   Found: {content[:100]}')
else:
    print('Secondary is EMPTY!')

