from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from .models import Utilisateur


class AuthenticationFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_returns_verification_flow_without_tokens(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "new-user@example.com",
                "nom": "User",
                "prenom": "New",
                "role": "CANDIDAT",
                "telephone": "",
                "entreprise": "",
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        self.assertNotIn("verification_code", response.data)
        self.assertEqual(response.data["user"]["email"], "new-user@example.com")
        self.assertFalse(response.data["user"]["email_verified"])

        user = Utilisateur.objects.get(email="new-user@example.com")
        self.assertFalse(user.email_verified)
        self.assertIsNotNone(user.verification_code)
        self.assertIsNotNone(user.verification_code_created_at)

    def test_login_requires_verified_email(self):
        user = Utilisateur.objects.create_user(
            email="pending@example.com",
            nom="Pending",
            prenom="User",
            role="CANDIDAT",
            password="StrongPass123!",
        )
        user.verification_code = "654321"
        user.verification_code_created_at = timezone.now()
        user.save(update_fields=["verification_code", "verification_code_created_at"])

        response = self.client.post(
            "/api/auth/login/",
            {"email": "pending@example.com", "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
        self.assertTrue(response.data["requires_verification"])
        self.assertEqual(response.data["email"], "pending@example.com")
        self.assertNotIn("verification_code", response.data)

    def test_verify_email_marks_user_verified_and_returns_tokens(self):
        user = Utilisateur.objects.create_user(
            email="verify@example.com",
            nom="Verify",
            prenom="Case",
            role="RECRUTEUR",
            password="StrongPass123!",
        )
        user.verification_code = "123456"
        user.verification_code_created_at = timezone.now()
        user.save(
            update_fields=[
                "verification_code",
                "verification_code_created_at",
            ]
        )

        response = self.client.post(
            "/api/auth/verify-email/",
            {"email": "verify@example.com", "code": "123456"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(response.data["user"]["email_verified"])

        user.refresh_from_db()
        self.assertTrue(user.email_verified)
        self.assertIsNone(user.verification_code)
        self.assertIsNone(user.verification_code_created_at)

    def test_login_succeeds_after_email_is_verified(self):
        user = Utilisateur.objects.create_user(
            email="verified@example.com",
            nom="Verified",
            prenom="User",
            role="RECRUTEUR",
            password="StrongPass123!",
        )
        user.email_verified = True
        user.save(update_fields=["email_verified"])

        response = self.client.post(
            "/api/auth/login/",
            {"email": "verified@example.com", "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(response.data["user"]["email_verified"])
