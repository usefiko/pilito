#!/bin/bash
# Safe SSH Test Commands for Session Memory
# Run these commands one by one

echo "============================================"
echo "SESSION MEMORY TEST COMMANDS"
echo "============================================"

# Step 1: Check if services are running
echo -e "\n📍 STEP 1: Check Docker services"
echo "RUN: docker compose ps"

# Step 2: Upload test file
echo -e "\n📍 STEP 2: Upload test_session_memory.py to server"
echo "RUN (on your local machine):"
echo "scp test_session_memory.py ubuntu@YOUR_SERVER_IP:~/fiko-backend/"

# Step 3: Run test inside Django container
echo -e "\n📍 STEP 3: Run test (READ-ONLY - SAFE)"
echo "RUN: docker compose exec web python /app/test_session_memory.py"

# Step 4: Check recent logs
echo -e "\n📍 STEP 4: Check recent AI logs"
echo "RUN: docker compose logs web | grep -i 'session\|memory\|summary' | tail -50"

# Step 5: Manual test in Django shell (optional)
echo -e "\n📍 STEP 5: (OPTIONAL) Django shell test"
echo "RUN: docker compose exec web python manage.py shell"
echo "Then run:"
echo "from AI_model.models import SessionMemory"
echo "sessions = SessionMemory.objects.all().order_by('-last_updated')[:3]"
echo "for s in sessions: print(f'{s.session_id}: {s.summary[:100]}')"

echo -e "\n============================================"
echo "✅ ALL COMMANDS ARE SAFE (READ-ONLY)"
echo "============================================"
