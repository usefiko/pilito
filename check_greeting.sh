#!/bin/bash
# این script رو تو سرور بزن تا greeting rules رو ببینیم

docker exec django_app python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from settings.models import GeneralSettings

settings = GeneralSettings.get_settings()
print('='*80)
print('📝 Current Greeting Rules:')
print('='*80)
print(settings.greeting_rules)
print()
print('='*80)
print('📝 Welcome Back Threshold:')
print('='*80)
print(f'{settings.welcome_back_threshold_hours} hours')
"
