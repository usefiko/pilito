#!/usr/bin/env python3
"""
PostgreSQL Collation Version Fix Script
This script fixes the collation version mismatch warning in PostgreSQL
"""

import subprocess
import sys
import os


def run_command(command, description):
    """Run a command and return the result"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} failed")
            print(f"Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False


def fix_collation_docker():
    """Fix collation version in Docker environment"""
    print("🔍 Fixing PostgreSQL collation version in Docker...")
    
    # Check if containers are running
    print("\n1️⃣ Checking Docker containers...")
    if not run_command("docker compose ps | grep postgres_db", "Check PostgreSQL container"):
        print("❌ PostgreSQL container not found. Make sure Docker Compose is running.")
        return False
    
    # Connect to PostgreSQL and fix collation
    print("\n2️⃣ Fixing collation version...")
    
    # First, check current collation version
    check_cmd = '''docker compose exec db psql -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-postgres} -c "SELECT datname, datcollate, datctype FROM pg_database WHERE datname = 'FikoDB';"'''
    run_command(check_cmd, "Check current database collation")
    
    # Fix the collation version
    fix_cmd = '''docker compose exec db psql -U ${POSTGRES_USER:-postgres} -d FikoDB -c "ALTER DATABASE \\"FikoDB\\" REFRESH COLLATION VERSION;"'''
    
    if run_command(fix_cmd, "Refresh collation version"):
        print("✅ PostgreSQL collation version fixed!")
        return True
    else:
        print("❌ Failed to fix collation version")
        return False


def fix_collation_alternative():
    """Alternative method using Docker Compose environment variables"""
    print("\n🔄 Trying alternative method...")
    
    # Get environment variables from Docker Compose
    env_vars = {
        'POSTGRES_USER': 'postgres',
        'POSTGRES_DB': 'FikoDB'
    }
    
    # Try to get actual values from Docker Compose
    try:
        result = subprocess.run(
            "docker compose config | grep -E 'POSTGRES_USER|POSTGRES_DB'", 
            shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'POSTGRES_USER:' in line:
                    env_vars['POSTGRES_USER'] = line.split(':')[1].strip()
                elif 'POSTGRES_DB:' in line:
                    env_vars['POSTGRES_DB'] = line.split(':')[1].strip()
    except:
        pass
    
    print(f"Using POSTGRES_USER: {env_vars['POSTGRES_USER']}")
    print(f"Using POSTGRES_DB: {env_vars['POSTGRES_DB']}")
    
    # Fix collation with proper environment variables
    fix_cmd = f'''docker compose exec db psql -U {env_vars['POSTGRES_USER']} -d {env_vars['POSTGRES_DB']} -c "ALTER DATABASE \\"{env_vars['POSTGRES_DB']}\\" REFRESH COLLATION VERSION;"'''
    
    return run_command(fix_cmd, "Refresh collation version (alternative method)")


def main():
    print("🛠️  PostgreSQL Collation Version Fix")
    print("=" * 50)
    
    # Method 1: Standard fix
    if fix_collation_docker():
        print("\n🎉 Collation version fixed successfully!")
        print("The warning messages should now disappear from your logs.")
    else:
        print("\n⚠️  Standard method failed, trying alternative...")
        if fix_collation_alternative():
            print("\n🎉 Collation version fixed with alternative method!")
        else:
            print("\n❌ Both methods failed. Manual intervention required.")
            print("\n📋 Manual fix steps:")
            print("1. Connect to PostgreSQL container:")
            print("   docker compose exec db bash")
            print("2. Connect to PostgreSQL:")
            print("   psql -U $POSTGRES_USER -d FikoDB")
            print("3. Run the fix command:")
            print('   ALTER DATABASE "FikoDB" REFRESH COLLATION VERSION;')
            print("4. Exit PostgreSQL and container:")
            print("   \\q")
            print("   exit")
    
    print("\n🔄 Restart your Django containers to see clean logs:")
    print("docker compose restart web")


if __name__ == "__main__":
    main()
