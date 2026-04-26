from smtplib import SMTPAuthenticationError, SMTPException

from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Utilisateur
from .serializers import (
    ConnexionSerializer,
    ForgotPasswordSerializer,
    InscriptionSerializer,
    ResetPasswordSerializer,
    UtilisateurSerializer,
    VerifyEmailSerializer,
)
from .utils import is_code_valid, send_reset_password_email, send_verification_email


def _token_payload_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def _dev_verification_payload(user):
    if settings.EMAIL_BACKEND.endswith("console.EmailBackend"):
        return {
            "email_delivery": "console",
        }
    if settings.DEBUG:
        return {
            "email_delivery": "smtp",
        }
    return {}


def _email_delivery_failure_response(exc):
    if isinstance(exc, SMTPAuthenticationError):
        message = (
            "SMTP authentication failed. Check AUTH_EMAIL_HOST_USER and "
            "AUTH_EMAIL_HOST_PASSWORD in cv_service/.env."
        )
    elif isinstance(exc, OSError):
        message = "Could not connect to the SMTP server. Check the SMTP host, port, and network access."
    else:
        message = "Verification email could not be sent. Check the SMTP configuration and try again."

    payload = {
        "success": False,
        "message": message,
        "email_delivery": "smtp_error",
    }
    if settings.DEBUG:
        payload["error_type"] = exc.__class__.__name__
    return Response(payload, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = InscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        try:
            send_verification_email(user)
        except (SMTPException, OSError) as exc:
            return _email_delivery_failure_response(exc)

        return Response(
            {
                "success": True,
                "message": "Registration successful. Verify your email to continue.",
                "user": UtilisateurSerializer(user).data,
                **_dev_verification_payload(user),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ConnexionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {
                    "success": False,
                    "message": "Invalid email or password.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.email_verified:
            return Response(
                {
                    "success": False,
                    "message": "Please verify your email before logging in.",
                    "requires_verification": True,
                    "email": user.email,
                    **_dev_verification_payload(user),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        token_payload = _token_payload_for_user(user)
        return Response(
            {
                "success": True,
                "user": UtilisateurSerializer(user).data,
                **token_payload,
            },
            status=status.HTTP_200_OK,
        )


class ProfileView(APIView):
    def get(self, request):
        return Response(
            {
                "success": True,
                "user": UtilisateurSerializer(request.user).data,
            }
        )


class HealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"status": "healthy", "service": "auth-service"})


class SendVerificationCodeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = Utilisateur.objects.get(email=email)
        except Utilisateur.DoesNotExist:
            return Response(
                {"success": False, "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.email_verified:
            return Response(
                {"success": False, "message": "Email already verified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            send_verification_email(user)
        except (SMTPException, OSError) as exc:
            return _email_delivery_failure_response(exc)

        return Response(
            {
                "success": True,
                "message": "Verification code sent.",
                **_dev_verification_payload(user),
            },
            status=status.HTTP_200_OK,
        )


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = Utilisateur.objects.get(email=serializer.validated_data["email"])
        except Utilisateur.DoesNotExist:
            return Response(
                {"success": False, "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.verification_code != serializer.validated_data["code"]:
            return Response(
                {"success": False, "message": "Invalid verification code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not is_code_valid(user.verification_code_created_at):
            return Response(
                {"success": False, "message": "Verification code expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.email_verified = True
        user.verification_code = None
        user.verification_code_created_at = None
        user.save(update_fields=["email_verified", "verification_code", "verification_code_created_at"])
        token_payload = _token_payload_for_user(user)
        return Response(
            {
                "success": True,
                "message": "Email verified successfully.",
                "user": UtilisateurSerializer(user).data,
                **token_payload,
            },
            status=status.HTTP_200_OK,
        )


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = Utilisateur.objects.get(email=email)
        except Utilisateur.DoesNotExist:
            return Response(
                {"success": True, "message": "If the email exists, a reset code has been sent."},
                status=status.HTTP_200_OK,
            )

        try:
            send_reset_password_email(user)
        except (SMTPException, OSError) as exc:
            return _email_delivery_failure_response(exc)

        return Response(
            {"success": True, "message": "Password reset code sent."},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        try:
            user = Utilisateur.objects.get(email=payload["email"])
        except Utilisateur.DoesNotExist:
            return Response(
                {"success": False, "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.reset_password_code != payload["code"]:
            return Response(
                {"success": False, "message": "Invalid reset code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not is_code_valid(user.reset_password_code_created_at):
            return Response(
                {"success": False, "message": "Reset code expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(payload["new_password"])
        user.reset_password_code = None
        user.reset_password_code_created_at = None
        user.save(update_fields=["password", "reset_password_code", "reset_password_code_created_at"])
        return Response(
            {"success": True, "message": "Password reset successful."},
            status=status.HTTP_200_OK,
        )


InscriptionView = RegisterView
ConnexionView = LoginView
ProfilView = ProfileView
