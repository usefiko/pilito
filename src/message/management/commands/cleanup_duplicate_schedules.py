from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    help = 'Clean up duplicate CrontabSchedule entries and fix Instagram token refresh tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned up without actually deleting anything'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write('🔍 DRY RUN - No changes will be made')
        else:
            self.stdout.write('🧹 Cleaning up duplicate schedules...')
        
        # Clean up duplicate daily schedules (3 AM)
        daily_schedules = CrontabSchedule.objects.filter(
            minute='0',
            hour='3',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )
        
        if daily_schedules.count() > 1:
            self.stdout.write(f'📅 Found {daily_schedules.count()} duplicate daily schedules')
            
            if not dry_run:
                # Keep the first one, delete the rest
                keep_schedule = daily_schedules.first()
                deleted_count = daily_schedules.exclude(id=keep_schedule.id).count()
                daily_schedules.exclude(id=keep_schedule.id).delete()
                self.stdout.write(f'✅ Deleted {deleted_count} duplicate daily schedules')
            else:
                self.stdout.write(f'   Would delete {daily_schedules.count() - 1} duplicate daily schedules')
        else:
            self.stdout.write('✅ No duplicate daily schedules found')
        
        # Clean up duplicate emergency schedules (every 6 hours)
        emergency_schedules = CrontabSchedule.objects.filter(
            minute='0',
            hour='*/6',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )
        
        if emergency_schedules.count() > 1:
            self.stdout.write(f'🚨 Found {emergency_schedules.count()} duplicate emergency schedules')
            
            if not dry_run:
                # Keep the first one, delete the rest
                keep_schedule = emergency_schedules.first()
                deleted_count = emergency_schedules.exclude(id=keep_schedule.id).count()
                emergency_schedules.exclude(id=keep_schedule.id).delete()
                self.stdout.write(f'✅ Deleted {deleted_count} duplicate emergency schedules')
            else:
                self.stdout.write(f'   Would delete {emergency_schedules.count() - 1} duplicate emergency schedules')
        else:
            self.stdout.write('✅ No duplicate emergency schedules found')
        
        # Check and fix Instagram token refresh tasks
        self.stdout.write('\n📋 Checking Instagram token refresh tasks...')
        
        instagram_tasks = PeriodicTask.objects.filter(name__icontains='Instagram')
        self.stdout.write(f'Found {instagram_tasks.count()} Instagram token refresh tasks:')
        
        for task in instagram_tasks:
            status = "✅ Enabled" if task.enabled else "❌ Disabled"
            self.stdout.write(f'   • {task.name}: {status}')
            
            if not task.enabled and not dry_run:
                task.enabled = True
                task.save()
                self.stdout.write(f'     🔧 Enabled {task.name}')
        
        # Summary
        self.stdout.write('\n🎯 Summary:')
        
        daily_count = CrontabSchedule.objects.filter(
            minute='0', hour='3', day_of_week='*', day_of_month='*', month_of_year='*'
        ).count()
        
        emergency_count = CrontabSchedule.objects.filter(
            minute='0', hour='*/6', day_of_week='*', day_of_month='*', month_of_year='*'
        ).count()
        
        active_tasks = PeriodicTask.objects.filter(
            name__icontains='Instagram', enabled=True
        ).count()
        
        self.stdout.write(f'   📅 Daily schedules: {daily_count}')
        self.stdout.write(f'   🚨 Emergency schedules: {emergency_count}')
        self.stdout.write(f'   ⚡ Active Instagram tasks: {active_tasks}')
        
        if daily_count == 1 and emergency_count == 1 and active_tasks >= 2:
            self.stdout.write('\n🎉 Instagram token auto-refresh system is properly configured!')
        else:
            self.stdout.write('\n⚠️  Some issues may remain. Consider running setup_periodic_tasks command.')
            
        if dry_run:
            self.stdout.write('\n💡 Run without --dry-run to actually perform cleanup')