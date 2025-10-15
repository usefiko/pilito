from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class MessageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'message'

    def ready(self):
        """
        Auto-setup Instagram token refresh system on startup
        This ensures the system is always ready without manual intervention
        """
        # Import signals module to register @receiver decorators
        # This MUST be done before anything else to ensure signals are active
        try:
            import message.signals  # noqa: F401
            logger.info("✅ Message signals module imported and registered")
        except Exception as e:
            logger.error(f"❌ Failed to import message signals: {e}")
            # Continue anyway - don't break app startup
        
        # Connect message app signals for WebSocket notifications
        try:
            from message.signals import connect_message_signals
            connect_message_signals()
        except Exception as e:
            logger.error(f"Error connecting message signals: {e}")
        
        self.setup_automatic_token_refresh()

    def setup_automatic_token_refresh(self):
        """Setup automatic Instagram token refresh system"""
        try:
            # Only run in specific processes to avoid multiple executions
            import sys
            
            # Skip during migrations and other management commands except runserver/gunicorn
            if any(arg in sys.argv for arg in ['migrate', 'makemigrations', 'collectstatic', 'shell']):
                return
                
            # Skip during tests
            if 'test' in sys.argv:
                return
            
            # Delay database access to avoid Django warning
            from django.core.management import call_command
            import threading
            
            def delayed_setup():
                import time
                time.sleep(2)  # Wait for Django to fully initialize
                
                logger.info("🚀 Setting up automatic Instagram token refresh system...")
                
                try:
                    # Import here to avoid import issues during startup
                    from django_celery_beat.models import PeriodicTask, CrontabSchedule
                    import json
                    
                    # Check if database is ready
                    if not self._is_database_ready():
                        logger.warning("⚠️  Database not ready, skipping automatic setup")
                        return
                    
                    # Clean up any duplicate schedules first
                    self._cleanup_duplicate_schedules()
                    
                    # Get or create crontab for daily refresh at 3 AM
                    try:
                        daily_schedule = CrontabSchedule.objects.filter(
                            minute='0',
                            hour='3',
                            day_of_week='*',
                            day_of_month='*',
                            month_of_year='*',
                        ).first()
                        
                        if not daily_schedule:
                            daily_schedule = CrontabSchedule.objects.create(
                                minute='0',
                                hour='3',
                                day_of_week='*',
                                day_of_month='*',
                                month_of_year='*',
                            )
                    except Exception as e:
                        logger.error(f"Error creating daily schedule: {e}")
                        return
                    
                    # Get or create crontab for emergency refresh every 6 hours
                    try:
                        emergency_schedule = CrontabSchedule.objects.filter(
                            minute='0',
                            hour='*/6',
                            day_of_week='*',
                            day_of_month='*',
                            month_of_year='*',
                        ).first()
                        
                        if not emergency_schedule:
                            emergency_schedule = CrontabSchedule.objects.create(
                                minute='0',
                                hour='*/6',
                                day_of_week='*',
                                day_of_month='*',
                                month_of_year='*',
                            )
                    except Exception as e:
                        logger.error(f"Error creating emergency schedule: {e}")
                        return

                    # Create or update daily refresh task
                    daily_task, created = PeriodicTask.objects.get_or_create(
                        name='Instagram Token Daily Refresh',
                        defaults={
                            'crontab': daily_schedule,
                            'task': 'message.tasks.auto_refresh_instagram_tokens',
                            'args': json.dumps([15]),  # 15 days before expiry (more safety margin)
                            'enabled': True,
                        }
                    )
                    
                    if not created:
                        # Update existing task to ensure it's current
                        daily_task.crontab = daily_schedule
                        daily_task.task = 'message.tasks.auto_refresh_instagram_tokens'
                        daily_task.args = json.dumps([15])  # 15 days before expiry
                        daily_task.enabled = True
                        daily_task.save()

                    # Create or update emergency refresh task
                    emergency_task, created = PeriodicTask.objects.get_or_create(
                        name='Instagram Token Emergency Refresh',
                        defaults={
                            'crontab': emergency_schedule,
                            'task': 'message.tasks.auto_refresh_instagram_tokens',
                            'args': json.dumps([5]),  # 5 days before expiry (more safety)
                            'enabled': True,
                        }
                    )
                    
                    if not created:
                        # Update existing task to ensure it's current
                        emergency_task.crontab = emergency_schedule
                        emergency_task.task = 'message.tasks.auto_refresh_instagram_tokens'
                        emergency_task.args = json.dumps([5])  # 5 days before expiry
                        emergency_task.enabled = True
                        emergency_task.save()

                    logger.info("✅ Instagram token auto-refresh system ready!")
                    logger.info("📅 Daily refresh: Every day at 3:00 AM (15 days before expiry)")
                    logger.info("🚨 Emergency refresh: Every 6 hours (5 days before expiry)")
                    
                except Exception as e:
                    logger.error(f"❌ Error setting up automatic token refresh: {e}")
            
            # Run setup in background thread to avoid blocking app startup
            setup_thread = threading.Thread(target=delayed_setup, daemon=True)
            setup_thread.start()
            
        except Exception as e:
            logger.error(f"❌ Error initializing token refresh setup: {e}")
            # Don't raise the exception to avoid breaking app startup

    def _is_database_ready(self):
        """Check if database is ready and tables exist"""
        try:
            from django.db import connection
            from django.core.management.color import no_style
            
            # Check if required tables exist
            with connection.cursor() as cursor:
                # Check if django_celery_beat tables exist
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = 'django_celery_beat_periodictask'
                """)
                return cursor.fetchone()[0] > 0
                
        except Exception:
            return False

    def _cleanup_duplicate_schedules(self):
        """Clean up duplicate CrontabSchedule entries"""
        try:
            from django_celery_beat.models import CrontabSchedule
            
            # Find duplicate daily schedules (3 AM)
            daily_schedules = CrontabSchedule.objects.filter(
                minute='0',
                hour='3',
                day_of_week='*',
                day_of_month='*',
                month_of_year='*',
            )
            
            if daily_schedules.count() > 1:
                # Keep the first one, delete the rest
                keep_schedule = daily_schedules.first()
                daily_schedules.exclude(id=keep_schedule.id).delete()
                logger.info(f"🧹 Cleaned up {daily_schedules.count() - 1} duplicate daily schedules")
            
            # Find duplicate emergency schedules (every 6 hours)
            emergency_schedules = CrontabSchedule.objects.filter(
                minute='0',
                hour='*/6',
                day_of_week='*',
                day_of_month='*',
                month_of_year='*',
            )
            
            if emergency_schedules.count() > 1:
                # Keep the first one, delete the rest
                keep_schedule = emergency_schedules.first()
                emergency_schedules.exclude(id=keep_schedule.id).delete()
                logger.info(f"🧹 Cleaned up {emergency_schedules.count() - 1} duplicate emergency schedules")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not cleanup duplicate schedules: {e}")
