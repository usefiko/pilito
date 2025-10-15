from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json


class Command(BaseCommand):
    help = 'Setup periodic tasks for automatic Instagram token refresh'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Setting up automatic Instagram token refresh schedule...')
        
        try:
            # Create crontab for daily refresh at 3 AM
            daily_schedule, created = CrontabSchedule.objects.get_or_create(
                minute='0',
                hour='3',
                day_of_week='*',
                day_of_month='*',
                month_of_year='*',
            )
            
            if created:
                self.stdout.write('✅ Created daily schedule (3 AM)')
            else:
                self.stdout.write('📋 Daily schedule already exists')

            # Create crontab for emergency refresh every 6 hours
            emergency_schedule, created = CrontabSchedule.objects.get_or_create(
                minute='0',
                hour='*/6',
                day_of_week='*',
                day_of_month='*',
                month_of_year='*',
            )
            
            if created:
                self.stdout.write('✅ Created emergency schedule (every 6 hours)')
            else:
                self.stdout.write('📋 Emergency schedule already exists')

            # Create daily refresh task
            daily_task, created = PeriodicTask.objects.get_or_create(
                name='Instagram Token Daily Refresh',
                defaults={
                    'crontab': daily_schedule,
                    'task': 'message.tasks.auto_refresh_instagram_tokens',
                    'args': json.dumps([7]),  # 7 days before expiry
                    'enabled': True,
                }
            )
            
            if created:
                self.stdout.write('✅ Created daily refresh task')
            else:
                self.stdout.write('📋 Daily refresh task already exists')
                # Update existing task
                daily_task.crontab = daily_schedule
                daily_task.task = 'message.tasks.auto_refresh_instagram_tokens'
                daily_task.args = json.dumps([7])
                daily_task.enabled = True
                daily_task.save()
                self.stdout.write('🔄 Updated daily refresh task')

            # Create emergency refresh task
            emergency_task, created = PeriodicTask.objects.get_or_create(
                name='Instagram Token Emergency Refresh',
                defaults={
                    'crontab': emergency_schedule,
                    'task': 'message.tasks.auto_refresh_instagram_tokens',
                    'args': json.dumps([1]),  # 1 day before expiry
                    'enabled': True,
                }
            )
            
            if created:
                self.stdout.write('✅ Created emergency refresh task')
            else:
                self.stdout.write('📋 Emergency refresh task already exists')
                # Update existing task
                emergency_task.crontab = emergency_schedule
                emergency_task.task = 'message.tasks.auto_refresh_instagram_tokens'
                emergency_task.args = json.dumps([1])
                emergency_task.enabled = True
                emergency_task.save()
                self.stdout.write('🔄 Updated emergency refresh task')

            # Summary
            self.stdout.write('\n🎉 Periodic tasks setup completed!')
            self.stdout.write('📅 Daily Refresh: Every day at 3:00 AM (7 days before expiry)')
            self.stdout.write('🚨 Emergency Refresh: Every 6 hours (1 day before expiry)')
            
            # List all tasks
            self.stdout.write('\n📋 Current periodic tasks:')
            for task in PeriodicTask.objects.filter(name__icontains='Instagram'):
                status = "✅ Enabled" if task.enabled else "❌ Disabled"
                self.stdout.write(f'   • {task.name}: {status}')

        except Exception as e:
            self.stdout.write(f'❌ Error setting up periodic tasks: {e}')
            raise