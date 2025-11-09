#!/usr/bin/env python
"""Test Keywords"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from AI_model.services.query_router import QueryRouter
from accounts.models import User

user = User.objects.get(email='y_motahedin@yahoo.com')

tests = [
    ('ادرس شما کجاست؟', 'contact'),
    ('نحوه ارسالتون چطوریه؟', 'contact'),
    ('ارسال دارید؟', 'contact'),
    ('قیمتش چنده؟', 'pricing'),
    ('چی دارین؟', 'product'),
]

print('\n' + '='*80)
print('🧪 TESTING INTENT CLASSIFICATION')
print('='*80)

passed = 0
failed = 0

for query, expected_intent in tests:
    result = QueryRouter.route_query(query, user)
    actual_intent = result['intent']
    confidence = result['confidence']
    keywords = result['keywords_matched'][:5]
    
    status = '✅' if actual_intent == expected_intent else '❌'
    if actual_intent == expected_intent:
        passed += 1
    else:
        failed += 1
    
    print(f'\n{status} Query: "{query}"')
    print(f'   Expected: {expected_intent}')
    print(f'   Actual: {actual_intent} (confidence: {confidence:.2f})')
    print(f'   Keywords: {keywords}')

print('\n' + '='*80)
print(f'📊 RESULTS: {passed} passed, {failed} failed')
print('='*80)

sys.exit(0 if failed == 0 else 1)

