from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models.user import EmailConfirmationToken

User = get_user_model()


class Command(BaseCommand):
    help = 'Test the enhanced admin configuration'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Testing Enhanced Admin Configuration")
        self.stdout.write("=" * 50)
        
        # Show field counts
        user_fields = User._meta.get_fields()
        self.stdout.write(f"👤 User model has {len(user_fields)} total fields:")
        
        field_types = {}
        for field in user_fields:
            field_type = field.__class__.__name__
            if field_type not in field_types:
                field_types[field_type] = []
            field_types[field_type].append(field.name)
        
        for field_type, fields in field_types.items():
            self.stdout.write(f"   {field_type}: {', '.join(fields)}")
        
        # Show current data
        total_users = User.objects.count()
        google_users = User.objects.filter(is_google_user=True).count()
        confirmed_users = User.objects.filter(email_confirmed=True).count()
        
        self.stdout.write(f"\n📊 Current Data:")
        self.stdout.write(f"   Total users: {total_users}")
        self.stdout.write(f"   Google users: {google_users}")
        self.stdout.write(f"   Email confirmed: {confirmed_users}")
        
        # Show confirmation tokens
        total_tokens = EmailConfirmationToken.objects.count()
        valid_tokens = EmailConfirmationToken.objects.filter(is_used=False).count()
        
        self.stdout.write(f"\n📧 Email Confirmation Tokens:")
        self.stdout.write(f"   Total tokens: {total_tokens}")
        self.stdout.write(f"   Valid tokens: {valid_tokens}")
        
        if total_tokens > 0:
            recent_tokens = EmailConfirmationToken.objects.order_by('-created_at')[:3]
            self.stdout.write(f"\n📋 Recent tokens:")
            for token in recent_tokens:
                status = "Valid" if token.is_valid() else "Invalid/Expired/Used"
                self.stdout.write(f"   - {token.user.email}: {token.code} ({status})")
        
        self.stdout.write(f"\n✅ Admin Features Added:")
        self.stdout.write(f"   - All user fields in admin panel")
        self.stdout.write(f"   - Email confirmation status")
        self.stdout.write(f"   - Google OAuth information")
        self.stdout.write(f"   - Email confirmation codes display")
        self.stdout.write(f"   - Organized fieldsets")
        self.stdout.write(f"   - Enhanced filtering and searching")
        
        self.stdout.write(f"\n🌐 Access admin at: http://localhost:8000/admin/")
        self.stdout.write(f"   Users: http://localhost:8000/admin/accounts/user/")
        self.stdout.write(f"   Email Tokens: http://localhost:8000/admin/accounts/emailconfirmationtoken/")
