from accounts.api.login import LoginAPIView
from accounts.api.register import RegisterView,CompleteRegisterView
from accounts.api.refresh import Refresh
from accounts.api.refresh_access import RefreshAccess
from accounts.api.logout import Logout
from accounts.api.profile import Profile,ProfilePicture,ProfilePictureRemove,UserOverview
from accounts.api.change_password import ChangePasswordAPIView
from accounts.api.wizard_complete import WizardCompleteAPIView
from accounts.api.delete_account import DeleteAccountAPIView
from accounts.api.forget_password import ForgetPasswordAPIView, ResetPasswordAPIView
from accounts.api.google_oauth import GoogleOAuthLoginAPIView, GoogleOAuthCodeAPIView, GoogleOAuthAuthURLAPIView, GoogleOAuthTestAPIView
from accounts.api.otp import SendOTPAPIView, VerifyOTPAPIView
from accounts.api.linking import AddEmailSendCodeAPIView, AddEmailVerifyCodeAPIView, AddPhoneSendOTPAPIView, AddPhoneVerifyOTPAPIView