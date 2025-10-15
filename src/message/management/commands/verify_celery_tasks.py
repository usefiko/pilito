from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from django.utils import timezone
import json


class Command(BaseCommand):
    help = 'Verify Celery periodic tasks are properly configured for Instagram token refresh'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Checking Celery periodic task configuration...\n')

        # Check if required schedules exist
        self.stdout.write('📅 Checking crontab schedules:')
        
        # Check daily schedule (3 AM)
        daily_schedule = CrontabSchedule.objects.filter(
            minute='0',
            hour='3',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        ).first()

        if daily_schedule:
            self.stdout.write(self.style.SUCCESS('   ✅ Daily schedule (3 AM) exists'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ Daily schedule (3 AM) missing'))

        # Check emergency schedule (every 6 hours)
        emergency_schedule = CrontabSchedule.objects.filter(
            minute='0',
            hour='*/6',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        ).first()

        if emergency_schedule:
            self.stdout.write(self.style.SUCCESS('   ✅ Emergency schedule (every 6 hours) exists'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ Emergency schedule (every 6 hours) missing'))

        # Check periodic tasks
        self.stdout.write('\n📋 Checking periodic tasks:')
        
        daily_task = PeriodicTask.objects.filter(
            name='Instagram Token Daily Refresh'
        ).first()

        if daily_task:
            args = json.loads(daily_task.args) if daily_task.args else []
            self.stdout.write(self.style.SUCCESS(f'   ✅ Daily refresh task exists'))
            self.stdout.write(f'      - Task: {daily_task.task}')
            self.stdout.write(f'      - Args: {args} (days before expiry)')
            self.stdout.write(f'      - Enabled: {daily_task.enabled}')
            self.stdout.write(f'      - Last run: {daily_task.last_run_at or "Never"}')
        else:
            self.stdout.write(self.style.ERROR('   ❌ Daily refresh task missing'))

        emergency_task = PeriodicTask.objects.filter(
            name='Instagram Token Emergency Refresh'
        ).first()

        if emergency_task:
            args = json.loads(emergency_task.args) if emergency_task.args else []
            self.stdout.write(self.style.SUCCESS(f'   ✅ Emergency refresh task exists'))
            self.stdout.write(f'      - Task: {emergency_task.task}')
            self.stdout.write(f'      - Args: {args} (days before expiry)')
            self.stdout.write(f'      - Enabled: {emergency_task.enabled}')
            self.stdout.write(f'      - Last run: {emergency_task.last_run_at or "Never"}')
        else:
            self.stdout.write(self.style.ERROR('   ❌ Emergency refresh task missing'))

        # Check for any other Instagram token tasks
        other_tasks = PeriodicTask.objects.filter(
            task__icontains='instagram_token'
        ).exclude(
            name__in=['Instagram Token Daily Refresh', 'Instagram Token Emergency Refresh']
        )

        if other_tasks:
            self.stdout.write('\n🔍 Other Instagram token tasks found:')
            for task in other_tasks:
                self.stdout.write(f'   - {task.name}: {task.task} (enabled: {task.enabled})')

        # Summary and recommendations
        self.stdout.write('\n' + '='*50)
        self.stdout.write('📊 SUMMARY:')

        issues = []
        if not daily_schedule:
            issues.append('Daily schedule missing')
        if not emergency_schedule:
            issues.append('Emergency schedule missing')
        if not daily_task:
            issues.append('Daily refresh task missing')
        if not emergency_task:
            issues.append('Emergency refresh task missing')
        if daily_task and not daily_task.enabled:
            issues.append('Daily refresh task disabled')
        if emergency_task and not emergency_task.enabled:
            issues.append('Emergency refresh task disabled')

        if issues:
            self.stdout.write(self.style.ERROR('🚨 ISSUES FOUND:'))
            for issue in issues:
                self.stdout.write(f'   - {issue}')
            
            self.stdout.write('\n💡 RECOMMENDATIONS:')
            self.stdout.write('   1. Restart the Django application to trigger setup_periodic_tasks()')
            self.stdout.write('   2. Check celery worker is running: celery -A core worker --loglevel=info')
            self.stdout.write('   3. Check celery beat is running: celery -A core beat --loglevel=info')
            self.stdout.write('   4. Run: python manage.py cleanup_duplicate_schedules')
        else:
            self.stdout.write(self.style.SUCCESS('✅ All periodic tasks are properly configured!'))
            
            self.stdout.write('\n💡 To test tasks manually:')
            self.stdout.write('   - python manage.py auto_refresh_instagram_tokens')
            self.stdout.write('   - python manage.py check_instagram_tokens')

        # Current time info
        now = timezone.now()
        self.stdout.write(f'\n⏰ Current time: {now}')
        if daily_schedule:
            self.stdout.write(f'📅 Next daily refresh: Tomorrow at 3:00 AM')
        if emergency_schedule:
            next_emergency = now.replace(minute=0, second=0, microsecond=0)
            if now.hour >= 18:
                next_emergency = next_emergency.replace(hour=0) + timezone.timedelta(days=1)
            elif now.hour >= 12:
                next_emergency = next_emergency.replace(hour=18)
            elif now.hour >= 6:
                next_emergency = next_emergency.replace(hour=12)
            else:
                next_emergency = next_emergency.replace(hour=6)
            self.stdout.write(f'🚨 Next emergency refresh: {next_emergency}')