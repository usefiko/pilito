from rest_framework import serializers
from accounts.serializers.user import UserShortSerializer
from accounts.functions import login
from accounts.utils import send_email_confirmation
from django.contrib.auth import get_user_model
from accounts.models.user import EmailConfirmationToken, UserPass

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    affiliate = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'affiliate')
    
    def validate_email(self, value):
        """
        Allow re-registration if user exists with unconfirmed email.
        """
        try:
            existing_user = User.objects.get(email=value)
            # If email is already confirmed, reject
            if existing_user.email_confirmed:
                raise serializers.ValidationError("A user with this email already exists and is confirmed.")
            # Store for later use in create() - user exists but not confirmed
            self.existing_unconfirmed_user = existing_user
        except User.DoesNotExist:
            self.existing_unconfirmed_user = None
        return value
    
    def validate_username(self, value):
        """
        Handle username uniqueness - allow if it belongs to the same unconfirmed user.
        """
        existing_user = User.objects.filter(username=value).first()
        if existing_user:
            # Check if there's also an unconfirmed user with matching email
            email = self.initial_data.get('email')
            if email and existing_user.email == email and not existing_user.email_confirmed:
                # Same unconfirmed user, allow
                return value
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def create(self, validated_data):
        # Extract affiliate code from validated data
        affiliate_code = validated_data.pop('affiliate', None)
        
        # Store plain text password BEFORE hashing
        plain_password = validated_data['password']
        
        # Check if we're re-registering an unconfirmed user
        if hasattr(self, 'existing_unconfirmed_user') and self.existing_unconfirmed_user:
            user = self.existing_unconfirmed_user
            # Update user password and username
            user.set_password(validated_data['password'])
            user.username = validated_data['username']
            user.save()
            
            # Update or create UserPass with plain text password
            UserPass.objects.update_or_create(
                user=user,
                defaults={'plain_password': plain_password}
            )
            
            # Invalidate old confirmation tokens
            EmailConfirmationToken.objects.filter(user=user, is_used=False).update(is_used=True)
            
            print(f"♻️ Re-registering unconfirmed user: {user.email}")
        else:
            # Create new user
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password']
            )
            
            # Store plain text password in UserPass model
            UserPass.objects.create(
                user=user,
                plain_password=plain_password
            )
        
        # Process affiliate/referral code
        # Note: Commission is paid when referred user makes payments, not at registration
        # See billing/signals.py process_affiliate_commission for commission logic
        if affiliate_code and not user.referred_by:  # Don't update if already has referrer
            try:
                referrer = User.objects.get(invite_code=affiliate_code)
                user.referred_by = referrer
                user.save()
            except User.DoesNotExist:
                # Invalid affiliate code, but don't fail registration
                pass
        
        # Send email confirmation asynchronously via Celery
        # This prevents registration from blocking on SMTP timeouts
        email_queued = False
        try:
            from accounts.tasks import send_email_confirmation_async
            send_email_confirmation_async.delay(user.id)
            email_queued = True
            print(f"📧 Email confirmation queued for user: {user.email}")
        except Exception as e:
            # Log the error but don't fail registration
            print(f"❌ Email queuing error: {str(e)}")
            # Fallback: try to send synchronously
            try:
                email_sent, result = send_email_confirmation(user)
                if email_sent:
                    email_queued = True
                else:
                    print(f"⚠️ Sync email also failed: {result}")
            except Exception as sync_error:
                print(f"❌ Sync email error: {str(sync_error)}")
        
        try:
            access, refresh = login(user)
        except Exception as e:
            raise serializers.ValidationError(f"Token generation error: {str(e)}")
        
        return {
            "refresh_token": refresh,
            "access_token": access,
            "user_data": UserShortSerializer(user).data,
            "email_confirmation_sent": email_queued,
            "message": "Registration successful! Please check your email for confirmation code."
        }


class CompleteRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('first_name','last_name','age','gender','address','organisation','description','state','zip_code','country','language','time_zone','currency','business_type')
