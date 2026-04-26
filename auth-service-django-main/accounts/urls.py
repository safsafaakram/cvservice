from django.urls import path

from . import views


app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("health/", views.HealthCheckView.as_view(), name="health"),
    path(
        "send-verification-code/",
        views.SendVerificationCodeView.as_view(),
        name="send_verification_code",
    ),
    path("verify-email/", views.VerifyEmailView.as_view(), name="verify_email"),
    path(
        "forgot-password/",
        views.ForgotPasswordView.as_view(),
        name="forgot_password",
    ),
    path(
        "reset-password/",
        views.ResetPasswordView.as_view(),
        name="reset_password",
    ),
    path("inscription/", views.RegisterView.as_view(), name="inscription"),
    path("connexion/", views.LoginView.as_view(), name="connexion"),
    path("profil/", views.ProfileView.as_view(), name="profil"),
]
