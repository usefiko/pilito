#!/bin/bash
# Quick reference guide for subscription management
# This script helps manage subscriptions safely after the deactivation fix

echo "🔧 Fiko Subscription Management Commands"
echo "========================================"
echo ""

echo "📊 1. CHECK SUBSCRIPTION STATUS (Dry Run - Safe)"
echo "   Command: python src/manage.py check_subscription_status --dry-run"
echo "   Purpose: See what subscriptions would be deactivated without making changes"
echo ""

echo "⚠️  2. CHECK LOW TOKENS (Warning Only)"
echo "   Command: python src/manage.py check_subscription_status --dry-run --warn-threshold 200"
echo "   Purpose: Find users running low on tokens (below 200)"
echo ""

echo "✅ 3. DEACTIVATE EXPIRED SUBSCRIPTIONS ONLY (Safe)"
echo "   Command: python src/manage.py check_subscription_status"
echo "   Purpose: Deactivate only subscriptions where end_date has passed"
echo ""

echo "⚡ 4. DEACTIVATE ZERO-TOKEN SUBSCRIPTIONS (Use Carefully)"
echo "   Command: python src/manage.py check_subscription_status --deactivate-zero-tokens"
echo "   Purpose: Deactivate subscriptions with 0 tokens remaining"
echo "   Warning: Only use this if you're sure users should be deactivated"
echo ""

echo "📅 5. RECOMMENDED CRON JOB"
echo "   Add to crontab:"
echo "   0 2 * * * cd /path/to/Fiko-Backend && source venv/bin/activate && python src/manage.py check_subscription_status"
echo "   This checks daily at 2 AM and deactivates only date-expired subscriptions"
echo ""

echo "🔍 6. MONITOR LOGS"
echo "   Command: tail -f src/logs/django.log | grep -i subscription"
echo "   Purpose: Watch subscription-related events in real-time"
echo ""

echo "💡 QUICK START"
echo "   1. First, do a dry run: python src/manage.py check_subscription_status --dry-run"
echo "   2. Review the output carefully"
echo "   3. If looks good, run: python src/manage.py check_subscription_status"
echo "   4. Set up daily cron job for automatic checks"
echo ""

# Ask if user wants to run a command
read -p "Do you want to run a dry-run check now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "$(dirname "$0")"
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        python src/manage.py check_subscription_status --dry-run
    else
        echo "❌ Virtual environment not found. Please activate it manually and run:"
        echo "   python src/manage.py check_subscription_status --dry-run"
    fi
fi

