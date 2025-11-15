#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from AI_model.services.production_rag import ProductionRAG

User = get_user_model()
user = User.objects.get(phone_number='+989158157440')

print('Testing address search...')
sys.stdout.flush()

rag_result = ProductionRAG.retrieve_context(
    query='ادرستون', user=user, primary_source='faq',
    secondary_sources=['manual'], primary_budget=600,
    secondary_budget=200, routing_info=None
)

secondary = rag_result.get('secondary_context', [])
print(f'Secondary chunks: {len(secondary)}')
sys.stdout.flush()

if secondary:
    for chunk in secondary[:2]:
        content = chunk.get('content', '')
        if 'مشهد' in content and 'فردوسی' in content:
            print('✅ آدرس پیدا شد')
            sys.stdout.flush()
            break
    else:
        print('❌ آدرس پیدا نشد')
        sys.stdout.flush()
else:
    print('❌ Secondary chunks خالی است')
    sys.stdout.flush()

