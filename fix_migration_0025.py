#!/usr/bin/env python3
"""
Fix migration 0025 conflict by removing it from database
Run this BEFORE Django loads to avoid migration conflicts
"""
import os
import sys

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')

# Setup Django
import django
django.setup()

from django.db import connection

def remove_migration_0025():
    """Remove migration 0025 from database"""
    try:
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM django_migrations WHERE app = 'web_knowledge' AND name = '0025_change_qapair_page_to_set_null';"
        )
        connection.commit()
        deleted = cursor.rowcount
        if deleted > 0:
            print(f"✅ Removed {deleted} migration 0025 record(s) from database")
        else:
            print("ℹ️ Migration 0025 not found in database (already removed)")
        return True
    except Exception as e:
        print(f"⚠️ Error removing migration 0025: {e}")
        return False

if __name__ == '__main__':
    success = remove_migration_0025()
    sys.exit(0 if success else 1)

