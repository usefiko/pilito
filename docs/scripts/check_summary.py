#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
django.setup()

from AI_model.models import SessionMemory

# Get latest session
session = SessionMemory.objects.order_by('-last_updated').first()

if session:
    print("="*80)
    print(f"📊 Session: {session.conversation.id}")
    print(f"👤 User: {session.conversation.user.email if session.conversation.user else 'Anonymous'}")
    print(f"💬 Messages: {session.message_count}")
    print(f"📝 Summary Tokens: ~{len(session.cumulative_summary.split()) * 1.3:.0f}")
    print("="*80)
    print("\n📝 SUMMARY:")
    print(session.cumulative_summary)
    print("\n" + "="*80)
else:
    print("❌ No session found!")

