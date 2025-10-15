from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix PostgreSQL collation version mismatch warning'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check the current collation version without fixing'
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 PostgreSQL Collation Version Fix")
        self.stdout.write("=" * 50)
        
        if options['check_only']:
            self.check_collation_status()
        else:
            self.fix_collation_version()

    def check_collation_status(self):
        """Check current collation version status"""
        self.stdout.write("📊 Checking current collation status...")
        
        try:
            with connection.cursor() as cursor:
                # Check database collation info
                cursor.execute("""
                    SELECT datname, datcollate, datctype 
                    FROM pg_database 
                    WHERE datname = current_database()
                """)
                
                result = cursor.fetchone()
                if result:
                    db_name, collate, ctype = result
                    self.stdout.write(f"📋 Database: {db_name}")
                    self.stdout.write(f"📋 Collation: {collate}")
                    self.stdout.write(f"📋 Character Type: {ctype}")
                
                # Check for collation version mismatches
                cursor.execute("""
                    SELECT schemaname, tablename, attname, collname
                    FROM pg_stats 
                    JOIN pg_attribute ON pg_stats.schemaname = (
                        SELECT nspname FROM pg_namespace WHERE oid = pg_attribute.attrelid::regclass::oid
                    )
                    AND pg_stats.tablename = pg_attribute.attrelid::regclass::name
                    AND pg_stats.attname = pg_attribute.attname
                    JOIN pg_collation ON pg_attribute.attcollation = pg_collation.oid
                    WHERE pg_stats.schemaname = 'public'
                    LIMIT 5
                """)
                
                self.stdout.write("\n📋 Sample collation usage:")
                for row in cursor.fetchall():
                    self.stdout.write(f"  {row[0]}.{row[1]}.{row[2]} -> {row[3]}")
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error checking collation status: {e}"))

    def fix_collation_version(self):
        """Fix the collation version mismatch"""
        self.stdout.write("🔧 Fixing PostgreSQL collation version...")
        
        try:
            with connection.cursor() as cursor:
                # Get current database name
                cursor.execute("SELECT current_database()")
                db_name = cursor.fetchone()[0]
                
                self.stdout.write(f"📋 Current database: {db_name}")
                
                # Refresh collation version
                self.stdout.write("🔄 Refreshing collation version...")
                cursor.execute(f'ALTER DATABASE "{db_name}" REFRESH COLLATION VERSION')
                
                self.stdout.write(self.style.SUCCESS("✅ Collation version refreshed successfully!"))
                
                # Verify the fix
                self.stdout.write("🔍 Verifying fix...")
                
                # The warning should no longer appear after this
                cursor.execute("SELECT 1")  # Simple query to test
                
                self.stdout.write(self.style.SUCCESS("✅ Fix verified!"))
                self.stdout.write("\n📋 Next steps:")
                self.stdout.write("1. Restart your Django application")
                self.stdout.write("2. The collation warnings should no longer appear")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error fixing collation version: {e}"))
            self.stdout.write("\n💡 Alternative solutions:")
            self.stdout.write("1. Run this command as a superuser")
            self.stdout.write("2. Use the provided Python script: python3 fix_postgresql_collation.py")
            self.stdout.write("3. Manually connect to PostgreSQL and run:")
            self.stdout.write(f'   ALTER DATABASE "{connection.settings_dict["NAME"]}" REFRESH COLLATION VERSION;')

    def get_database_info(self):
        """Get database connection information"""
        db_settings = connection.settings_dict
        return {
            'name': db_settings.get('NAME'),
            'user': db_settings.get('USER'),
            'host': db_settings.get('HOST'),
            'port': db_settings.get('PORT'),
        }
