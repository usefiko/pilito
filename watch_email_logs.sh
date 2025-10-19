#!/bin/bash

# Script to watch email-related logs in real-time

echo "========================================"
echo "📧 Watching Email Logs in Real-time"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Watch the Django log file for email-related entries
tail -f /Users/omidataei/Documents/GitHub/pilito2/Untitled/src/logs/django.log | grep --line-buffered -i -E "email|smtp|mail|password reset|confirmation|✅|❌|⚠️|🔐|📧|⏱️|🔌|🔥"

