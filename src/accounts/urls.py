from django.urls import path
from accounts.api import LoginAPIView,RegisterView,CompleteRegisterView,Refresh,RefreshAccess,Logout,Profile,ProfilePicture,ProfilePictureRemove,ChangePasswordAPIView,DeleteAccountAPIView,WizardCompleteAPIView,WizardCompleteForceAPIView,ForgetPasswordAPIView,ResetPasswordAPIView,GoogleOAuthLoginAPIView,GoogleOAuthCodeAPIView,GoogleOAuthAuthURLAPIView,GoogleOAuthTestAPIView,UserOverview,SendOTPAPIView,VerifyOTPAPIView,AddEmailSendCodeAPIView,AddEmailVerifyCodeAPIView,AddPhoneSendOTPAPIView,AddPhoneVerifyOTPAPIView,AffiliateInfoAPIView
from accounts.api.intercom import IntercomJWTView, IntercomConfigView, IntercomUserHashView, IntercomValidateJWTView
from accounts.api.email_confirmation import EmailConfirmationAPIView, ResendEmailConfirmationAPIView, EmailConfirmationStatusAPIView
from accounts.api.auth_status import AuthStatusAPIView, DashboardAccessAPIView

urlpatterns = [
    path("login", LoginAPIView.as_view(), name="login"),
    path('register', RegisterView.as_view(), name='register'),
    path('complete', CompleteRegisterView.as_view(), name='complete'),
    path("refresh", Refresh.as_view(), name="refresh"),
    path("refresh-access", RefreshAccess.as_view(), name="refresh-access"),
    path("logout", Logout.as_view(), name="logout"),
    path("profile", Profile.as_view(), name="profile"),
    path("overview", UserOverview.as_view(), name="overview"),
    path("profile-pic", ProfilePicture.as_view(), name="profile-pic"),
    path("profile-pic/remove", ProfilePictureRemove.as_view(), name="profile-pic-remove"),
    path("change-password", ChangePasswordAPIView.as_view(), name="change-password"),
    path("delete-account", DeleteAccountAPIView.as_view(), name="delete-account"),
    path("wizard-complete", WizardCompleteAPIView.as_view(), name="wizard-complete"),
    path("wizard-complete/force", WizardCompleteForceAPIView.as_view(), name="wizard-complete-force"),
    path("forget-password", ForgetPasswordAPIView.as_view(), name="forget-password"),
    path("reset-password", ResetPasswordAPIView.as_view(), name="reset-password"),
    # Google OAuth endpoints
    path("google/login", GoogleOAuthLoginAPIView.as_view(), name="google-oauth-login"),
    path("google/callback", GoogleOAuthCodeAPIView.as_view(), name="google-oauth-callback"),
    path("google/auth-url", GoogleOAuthAuthURLAPIView.as_view(), name="google-oauth-auth-url"),
    path("google/test", GoogleOAuthTestAPIView.as_view(), name="google-oauth-test"),
    
    # Intercom endpoints
    path("intercom/jwt", IntercomJWTView.as_view(), name="intercom-jwt"),
    path("intercom/config", IntercomConfigView.as_view(), name="intercom-config"),
    path("intercom/user-hash", IntercomUserHashView.as_view(), name="intercom-user-hash"),
    path("intercom/validate-jwt", IntercomValidateJWTView.as_view(), name="intercom-validate-jwt"),
    
    # Email confirmation endpoints
    path("email/confirm", EmailConfirmationAPIView.as_view(), name="email-confirm"),
    path("email/resend", ResendEmailConfirmationAPIView.as_view(), name="email-resend"),
    path("email/status", EmailConfirmationStatusAPIView.as_view(), name="email-status"),
    
    # Authentication debugging endpoints
    path("auth/status", AuthStatusAPIView.as_view(), name="auth-status"),
    path("auth/dashboard-test", DashboardAccessAPIView.as_view(), name="dashboard-test"),
    
    # OTP authentication endpoints
    path("otp", SendOTPAPIView.as_view(), name="send_otp"),
    path("otp/verify", VerifyOTPAPIView.as_view(), name="verify_otp"),
    
    # Account linking endpoints (authenticated)
    path("link/email", AddEmailSendCodeAPIView.as_view(), name="link-email-send"),
    path("link/email/verify", AddEmailVerifyCodeAPIView.as_view(), name="link-email-verify"),
    path("link/phone", AddPhoneSendOTPAPIView.as_view(), name="link-phone-send"),
    path("link/phone/verify", AddPhoneVerifyOTPAPIView.as_view(), name="link-phone-verify"),
    
    # Affiliate marketing endpoints
    path("affiliate", AffiliateInfoAPIView.as_view(), name="affiliate-info"),
]
