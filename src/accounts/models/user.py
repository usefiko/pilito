from django.contrib.auth.models import AbstractUser
from django.db import models
from accounts.models.user_manager import UserManager
from django.utils.safestring import mark_safe
from django.utils import timezone
import uuid
import random
import string

class User(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    HANDLER_CHOICES = [('Manual', 'Manual'), ('AI', 'AI')]

    first_name = models.CharField(max_length=250,null=True,blank=True)
    last_name = models.CharField(max_length=250,null=True,blank=True)
    username = models.CharField(max_length=250,unique=True)
    email = models.EmailField(max_length=250,unique=True)
    phone_number = models.CharField(max_length=100,unique=True,null=True,blank=True)
    description = models.TextField(max_length=1000,null=True,blank=True)
    profile_picture = models.ImageField(default="user_img/default.png",upload_to="user_img",blank=True,null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    age = models.PositiveIntegerField(blank=True,null=True)
    address = models.CharField(max_length=1000,null=True,blank=True)
    organisation = models.CharField(max_length=500,null=True,blank=True)
    state = models.CharField(max_length=250,null=True,blank=True)
    zip_code = models.CharField(max_length=250,null=True,blank=True)
    country = models.CharField(max_length=250,null=True,blank=True)
    language = models.CharField(max_length=250,null=True,blank=True)
    time_zone = models.CharField(max_length=250,null=True,blank=True)
    default_reply_handler = models.CharField(max_length=20, choices=HANDLER_CHOICES, default="AI")
    currency = models.CharField(max_length=250,null=True,blank=True)
    business_type = models.CharField(max_length=1000, null=True, blank=True)
    wizard_complete = models.BooleanField(default=False)
    # Google OAuth fields
    google_id = models.CharField(max_length=250, unique=True, null=True, blank=True)
    is_google_user = models.BooleanField(default=False)
    google_avatar_url = models.URLField(max_length=500, null=True, blank=True)
    # Email confirmation field
    email_confirmed = models.BooleanField(default=False)
    # Affiliate marketing fields
    invite_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    affiliate_active = models.BooleanField(
        default=False,
        verbose_name="Affiliate System Active",
        help_text="Enable or disable affiliate rewards for this user"
    )
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    def save(self, *args, **kwargs):
        if not self.invite_code:
            # Generate a unique 10-character invite code
            self.invite_code = self._generate_unique_invite_code()
        super().save(*args, **kwargs)
    
    def _generate_unique_invite_code(self):
        """Generate a unique invite code for the user"""
        while True:
            # Generate a random 10-character alphanumeric code
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            if not User.objects.filter(invite_code=code).exists():
                return code

    def __str__(self):
        return str(self.email) +' | '+ str(self.first_name) +' '+ str(self.last_name)
    def is_profile_fill(self):
        if self.email is not None and self.username is not None and self.first_name is not None and self.last_name is not None:
            return True
        else:
            return False
    def img_tag(self):
        if self.profile_picture:
            return mark_safe('<img src="{}" height="20"/>'.format(self.profile_picture.url))
    img_tag.short_description = 'profile'


class Plan(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    days = models.IntegerField(default=0)
    tokens = models.IntegerField(default=0)
    emails = models.IntegerField(default=0)
    updated_at = models.DateField(auto_now=True)
    def __str__(self):
        return str(self.user) + ' | days: '+ str(self.days) + ' | tokens: '+ str(self.tokens)


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Token expires in 1 hour
            self.expires_at = timezone.now() + timezone.timedelta(hours=1)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"Password reset token for {self.user.email}"


class EmailConfirmationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.code:
            # Generate 6-digit OTP
            self.code = ''.join(random.choices(string.digits, k=6))
        if not self.expires_at:
            # Token expires in 15 minutes
            self.expires_at = timezone.now() + timezone.timedelta(minutes=15)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"Email confirmation code for {self.user.email}"


class OTPToken(models.Model):
    """Model for storing OTP codes for phone number authentication"""
    phone_number = models.CharField(max_length=100)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)  # Track verification attempts
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number', '-created_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.code:
            # Generate 6-digit OTP
            self.code = ''.join(random.choices(string.digits, k=6))
        if not self.expires_at:
            # Token expires in 5 minutes (configurable via settings)
            from django.conf import settings
            expiry_seconds = getattr(settings, 'OTP_EXPIRY_TIME', 300)
            self.expires_at = timezone.now() + timezone.timedelta(seconds=expiry_seconds)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if OTP is valid (not used, not expired, attempts not exceeded)"""
        from django.conf import settings
        max_attempts = getattr(settings, 'OTP_MAX_ATTEMPTS', 3)
        return (
            not self.is_used 
            and timezone.now() < self.expires_at 
            and self.attempts < max_attempts
        )
    
    def increment_attempts(self):
        """Increment verification attempts"""
        self.attempts += 1
        self.save()
    
    def __str__(self):
        return f"OTP for {self.phone_number} - {'Used' if self.is_used else 'Active'}"

