#!/bin/bash

# Script to update static files after changing logo or other assets
# This handles all the caching layers

echo "🔄 Updating Static Files and Clearing Caches"
echo "============================================="
echo ""

# Check if we're in Docker or local environment
if [ -f "docker-compose.yml" ]; then
    DOCKER_MODE=true
    echo "📦 Detected Docker environment"
else
    DOCKER_MODE=false
    echo "💻 Detected local environment"
fi

# Step 1: Remove old collected static files
echo "1️⃣  Removing old collected static files..."
if [ "$DOCKER_MODE" = true ]; then
    docker-compose exec web rm -rf /app/staticfiles/email_assets/
    echo "   ✅ Old static files removed from container"
else
    cd src
    rm -rf staticfiles/email_assets/
    echo "   ✅ Old static files removed"
fi
echo ""

# Step 2: Run collectstatic
echo "2️⃣  Collecting new static files..."
if [ "$DOCKER_MODE" = true ]; then
    docker-compose exec web python manage.py collectstatic --noinput
else
    cd src
    python manage.py collectstatic --noinput
fi
echo "   ✅ Static files collected"
echo ""

# Step 3: Restart Django application
echo "3️⃣  Restarting Django application..."
if [ "$DOCKER_MODE" = true ]; then
    if command -v docker service >/dev/null 2>&1 && docker service ls 2>/dev/null | grep -q pilito_web; then
        echo "   Detected Docker Swarm..."
        docker service update --force pilito_web
        echo "   ✅ Django service restarted"
    else
        echo "   Detected Docker Compose..."
        docker-compose restart web
        echo "   ✅ Django container restarted"
    fi
else
    echo "   ⚠️  Please manually restart your Django development server"
fi
echo ""

# Step 4: Test if new image is accessible
echo "4️⃣  Testing image accessibility..."
sleep 3

# Get the modification time of the logo file
if [ -f "src/static/email_assets/logo.png" ]; then
    LOGO_MOD_TIME=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" src/static/email_assets/logo.png 2>/dev/null || stat -c "%y" src/static/email_assets/logo.png 2>/dev/null | cut -d'.' -f1)
    echo "   📅 Logo file last modified: $LOGO_MOD_TIME"
fi

# Test URL accessibility
TEST_URL="https://api.pilito.com/static/email_assets/logo.png?v=2"
echo "   🔗 Testing URL: $TEST_URL"

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$TEST_URL" 2>/dev/null || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    echo "   ✅ New logo is accessible (HTTP $HTTP_STATUS)"
else
    echo "   ⚠️  Could not verify accessibility (HTTP $HTTP_STATUS)"
    echo "   💡 Make sure your Django server is running and accessible"
fi
echo ""

# Instructions
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Static files updated successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📧 NEW EMAILS will show the updated logo with ?v=2"
echo ""
echo "⚠️  IMPORTANT:"
echo "   - Gmail caches images for 24-48 hours"
echo "   - Old emails will still show cached logo"
echo "   - NEW emails will show the updated logo"
echo "   - Test by sending a NEW email"
echo ""
echo "🧪 To test:"
echo "   1. Send a password reset or confirmation email"
echo "   2. Check the NEW email in a fresh inbox"
echo "   3. The logo should be updated in the NEW email"
echo ""
echo "💡 If you still see the old logo:"
echo "   - Make sure you're checking a NEWLY sent email"
echo "   - Clear your browser cache"
echo "   - Check in a different email client"
echo "   - Wait for Gmail's cache to expire (24-48 hours)"
echo ""
echo "🔧 Need to change version number?"
echo "   - Edit src/templates/emails/*.html"
echo "   - Change ?v=2 to ?v=3 (increment the number)"
echo "   - Run this script again"

