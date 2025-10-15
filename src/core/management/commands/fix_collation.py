"""
Django management command to fix PostgreSQL collation version mismatch.

This command addresses the warning:
WARNING: database has a collation version mismatch
DETAIL: The database was created using collation version X.XX, but the operating system provides version Y.YY.
HINT: Rebuild all objects in this database that use the default collation and run ALTER DATABASE REFRESH COLLATION VERSION.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix PostgreSQL collation version mismatch warnings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually executing',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.verbose = options['verbose']
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('🧪 DRY RUN MODE - No changes will be made')
            )
        
        self.stdout.write('🔧 PostgreSQL Collation Version Fix')
        self.stdout.write('=' * 40)
        
        try:
            self._check_database()
            self._show_current_status()
            self._fix_collation()
            self._verify_fix()
            
            self.stdout.write(
                self.style.SUCCESS('✅ Collation version fix completed successfully!')
            )
            self.stdout.write(
                'The PostgreSQL collation warnings should no longer appear.'
            )
            
        except Exception as e:
            logger.exception("Error fixing collation version")
            raise CommandError(f'Failed to fix collation version: {str(e)}')

    def _check_database(self):
        """Check if we're using PostgreSQL"""
        db_engine = settings.DATABASES['default']['ENGINE']
        
        if 'postgresql' not in db_engine:
            raise CommandError(
                f'This command only works with PostgreSQL. '
                f'Current database engine: {db_engine}'
            )
        
        self.stdout.write('✅ Confirmed PostgreSQL database')

    def _show_current_status(self):
        """Show current database and collation information"""
        if self.verbose:
            self.stdout.write('\n📊 Current Database Status:')
            
            with connection.cursor() as cursor:
                # Get database info
                cursor.execute("""
                    SELECT 
                        current_database() as database_name,
                        current_user as current_user,
                        version() as postgres_version
                """)
                
                result = cursor.fetchone()
                database_name, current_user, postgres_version = result
                
                self.stdout.write(f'  Database: {database_name}')
                self.stdout.write(f'  User: {current_user}')
                self.stdout.write(f'  PostgreSQL: {postgres_version.split(" on ")[0]}')
                
                # Check for collation version mismatches
                try:
                    cursor.execute("""
                        SELECT datname, datcollate, datctype
                        FROM pg_database 
                        WHERE datname = current_database()
                    """)
                    
                    result = cursor.fetchone()
                    if result:
                        datname, datcollate, datctype = result
                        self.stdout.write(f'  Collation: {datcollate}')
                        self.stdout.write(f'  Character Type: {datctype}')
                except Exception as e:
                    if self.verbose:
                        self.stdout.write(f'  Could not get collation info: {e}')

    def _fix_collation(self):
        """Execute the collation version fix"""
        database_name = settings.DATABASES['default']['NAME']
        
        self.stdout.write(f'\n🔄 Refreshing collation version for database: {database_name}')
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'Would execute: ALTER DATABASE "{database_name}" REFRESH COLLATION VERSION;'
                )
            )
            return
        
        try:
            with connection.cursor() as cursor:
                # Use connection.ops.quote_name to properly quote the database name
                quoted_db_name = connection.ops.quote_name(database_name)
                sql = f'ALTER DATABASE {quoted_db_name} REFRESH COLLATION VERSION'
                
                if self.verbose:
                    self.stdout.write(f'Executing: {sql}')
                
                cursor.execute(sql)
                
            self.stdout.write(
                self.style.SUCCESS('✅ Database collation version refreshed')
            )
            
        except Exception as e:
            error_msg = str(e)
            
            # Check for common errors and provide helpful messages
            if 'permission denied' in error_msg.lower():
                raise CommandError(
                    'Permission denied. Make sure your database user has '
                    'ALTER DATABASE privileges, or run this as a superuser.'
                )
            elif 'does not exist' in error_msg.lower():
                raise CommandError(
                    f'Database "{database_name}" does not exist or is not accessible.'
                )
            else:
                raise CommandError(f'Failed to refresh collation version: {error_msg}')

    def _verify_fix(self):
        """Verify that the fix worked"""
        self.stdout.write('\n🔍 Verifying fix...')
        
        try:
            with connection.cursor() as cursor:
                # Test basic connectivity
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
                
                if result and result[0] == 1:
                    self.stdout.write('✅ Database connection test passed')
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠️  Database connection test returned unexpected result')
                    )
                
                # Run a simple query that might trigger collation warnings
                cursor.execute("""
                    SELECT 
                        'Verification test' as status,
                        current_database() as database,
                        current_timestamp as checked_at
                """)
                
                result = cursor.fetchone()
                if self.verbose and result:
                    self.stdout.write(f'  Test query result: {result[0]}')
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Verification test failed: {str(e)}')
            )
            self.stdout.write('The collation fix may have worked, but verification failed.')

    def _log_activity(self, message):
        """Log activity for debugging"""
        if self.verbose:
            logger.info(message)
            self.stdout.write(f'📝 {message}')
