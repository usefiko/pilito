#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from AI_model.services.production_rag import ProductionRAG
from AI_model.services.token_budget_controller import TokenBudgetController

# Disable reranking for faster test
ProductionRAG.ENABLE_RERANKING = False

User = get_user_model()
user = User.objects.get(phone_number='+989158157440')

print('='*80)
print('🔍 تست کامل: بررسی جریان کامل')
print('='*80)

# 1. ProductionRAG
print('\n1️⃣ ProductionRAG:')
rag_result = ProductionRAG.retrieve_context(
    query='ادرستون', user=user, primary_source='faq',
    secondary_sources=['manual'], primary_budget=600,
    secondary_budget=200, routing_info=None
)

primary = rag_result.get('primary_context', [])
secondary = rag_result.get('secondary_context', [])

print(f'   Primary: {len(primary)}')
print(f'   Secondary: {len(secondary)}')
sys.stdout.flush()

# 2. Token Budget Controller
print('\n2️⃣ Token Budget Controller:')
components = {
    'system_prompt': 'Test system prompt',
    'bio_context': '',
    'customer_info': 'Test customer',
    'conversation': '',
    'primary_context': primary,
    'secondary_context': secondary,
    'user_query': 'ادرستون'
}

trimmed = TokenBudgetController.trim_to_budget(components)

print(f'   Primary after trim: {len(trimmed.get("primary_context", []))}')
print(f'   Secondary after trim: {len(trimmed.get("secondary_context", []))}')
sys.stdout.flush()

# 3. بررسی آدرس
if trimmed.get('secondary_context'):
    print('\n3️⃣ بررسی آدرس در secondary_context:')
    address_found = False
    for item in trimmed['secondary_context']:
        content = item.get('content', '')
        if 'مشهد' in content and 'فردوسی' in content:
            print('   ✅ آدرس پیدا شد!')
            print(f'   Preview: {content[:200]}...')
            address_found = True
            break
    
    if not address_found:
        print('   ❌ آدرس پیدا نشد')
        sys.stdout.flush()
else:
    print('\n3️⃣ ❌ secondary_context خالی است بعد از trim!')
    sys.stdout.flush()

print('\n✅ تست کامل شد!')
sys.stdout.flush()

