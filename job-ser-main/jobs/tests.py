from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from .models import Job


def build_access_token():
    token = AccessToken()
    token["user_id"] = "integration-user"
    return str(token)


class JobServiceSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_job_creation_requires_jwt(self):
        response = self.client.post(
            "/api/jobs/",
            {"title": "Backend Engineer", "description": "Python and Django"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_job_creation_succeeds_with_jwt(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {build_access_token()}")
        response = self.client.post(
            "/api/jobs/",
            {"title": "Backend Engineer", "description": "Python and Django"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "Backend Engineer")

    def test_internal_job_endpoint_requires_internal_token(self):
        job = Job.objects.create(
            job_name="Platform Engineer",
            description="Messaging and APIs",
            company="",
            location="",
        )

        response = self.client.get(f"/api/internal/jobs/{job.id}/")
        self.assertEqual(response.status_code, 403)

        response = self.client.get(
            f"/api/internal/jobs/{job.id}/",
            HTTP_X_INTERNAL_TOKEN=settings.INTERNAL_API_TOKEN,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["description"], "Messaging and APIs")
