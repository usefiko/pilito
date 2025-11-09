#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from AI_model.models import IntentKeyword

total = IntentKeyword.objects.filter(user__isnull=True).count()
print(f'Total keywords: {total}')

contact = IntentKeyword.objects.filter(intent='contact', language='fa', user__isnull=True).count()
print(f'Contact (FA) keywords: {contact}')

important = ['ادرس', 'آدرس', 'ارسال', 'نحوه ارسال']
print('\nChecking important keywords:')
for word in important:
    exists = IntentKeyword.objects.filter(keyword=word, user__isnull=True).exists()
    status = 'OK' if exists else 'MISSING'
    print(f'  {word}: {status}')

if total < 100:
    print(f'\nWARNING: Only {total} keywords found. Need to re-import!')
else:
    print(f'\nOK: {total} keywords found')

