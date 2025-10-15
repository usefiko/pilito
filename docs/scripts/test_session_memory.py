"""
Test script for Session Memory V1 (Fixed) and V2 (Multi-tier)
Safe to run - only reads and displays session memory status
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.production')
django.setup()

from AI_model.models import SessionMemory
from AI_model.services.session_memory_manager import SessionMemoryManager
from AI_model.services.session_memory_manager_v2 import SessionMemoryManagerV2
from django.contrib.auth import get_user_model

User = get_user_model()

def test_session_memory():
    """Test Session Memory system"""
    print("\n" + "="*80)
    print("🧪 SESSION MEMORY TEST - SAFE READ-ONLY MODE")
    print("="*80 + "\n")
    
    # Get recent sessions
    sessions = SessionMemory.objects.all().order_by('-last_updated')[:5]
    
    if not sessions:
        print("❌ No sessions found in database")
        return
    
    print(f"✅ Found {sessions.count()} recent sessions\n")
    
    for idx, session in enumerate(sessions, 1):
        print(f"\n{'─'*80}")
        print(f"📝 SESSION {idx}")
        print(f"{'─'*80}")
        print(f"Session ID: {session.session_id}")
        print(f"User: {session.user.email if session.user else 'Anonymous'}")
        print(f"Created: {session.created_at}")
        print(f"Last Updated: {session.last_updated}")
        print(f"Message Count: {session.message_count}")
        print(f"Total Tokens: {session.total_tokens}")
        print(f"\n📄 CURRENT SUMMARY:")
        print(f"{session.summary}")
        
        # Test V1 Manager
        print(f"\n🔧 TESTING V1 (SessionMemoryManager)...")
        try:
            manager_v1 = SessionMemoryManager(session.session_id, session.user)
            context_v1 = manager_v1.get_conversation_context()
            print(f"✅ V1 Context Length: {len(context_v1)} chars")
            print(f"V1 Context Preview: {context_v1[:200]}...")
        except Exception as e:
            print(f"❌ V1 Error: {str(e)}")
        
        # Test V2 Manager
        print(f"\n🔧 TESTING V2 (SessionMemoryManagerV2)...")
        try:
            manager_v2 = SessionMemoryManagerV2(session.session_id, session.user)
            context_v2 = manager_v2.get_conversation_context()
            print(f"✅ V2 Context Length: {len(context_v2)} chars")
            print(f"V2 Context Preview: {context_v2[:200]}...")
        except Exception as e:
            print(f"❌ V2 Error: {str(e)}")
    
    print(f"\n{'='*80}")
    print("✅ TEST COMPLETED - NO CHANGES MADE TO DATABASE")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    test_session_memory()
