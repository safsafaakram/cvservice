import shutil
import tempfile
from unittest.mock import patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from .models import CV
from .services.job_service import JobServiceError


def build_access_token():
    token = AccessToken()
    token["user_id"] = "integration-user"
    return str(token)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class CVServiceTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {build_access_token()}")

    def test_upload_rejects_missing_job(self):
        uploaded_file = SimpleUploadedFile(
            "resume.pdf",
            b"%PDF-1.4 test content",
            content_type="application/pdf",
        )

        with patch("cv_app.views.fetch_job", side_effect=JobServiceError("boom")):
            response = self.client.post(
                "/api/upload/",
                {
                    "candidate_name": "Jane Doe",
                    "email": "jane@example.com",
                    "job_id": "99",
                    "file": uploaded_file,
                },
                format="multipart",
            )

        self.assertEqual(response.status_code, 503)

    def test_upload_publishes_cv_message(self):
        uploaded_file = SimpleUploadedFile(
            "resume.pdf",
            b"%PDF-1.4 test content",
            content_type="application/pdf",
        )

        with patch("cv_app.views.fetch_job", return_value={"id": 1, "description": "Python"}), patch(
            "cv_app.views.extract_text",
            return_value="python django docker",
        ), patch("cv_app.views.publish_cv_for_scoring") as mock_publish:
            response = self.client.post(
                "/api/upload/",
                {
                    "candidate_name": "Jane Doe",
                    "email": "jane@example.com",
                    "job_id": "1",
                    "file": uploaded_file,
                },
                format="multipart",
            )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["status"], "processing")
        mock_publish.assert_called_once()

    def test_internal_score_update_requires_internal_token(self):
        cv = CV.objects.create(
            candidate_name="John Doe",
            email="john@example.com",
            job_id="1",
            file=SimpleUploadedFile(
                "resume.pdf",
                b"%PDF-1.4 test content",
                content_type="application/pdf",
            ),
        )

        response = self.client.patch(
            f"/api/internal/cv/{cv.cv_id}/score/",
            {"score": 0.91},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.patch(
            f"/api/internal/cv/{cv.cv_id}/score/",
            {"score": 0.91},
            format="json",
            HTTP_X_INTERNAL_TOKEN=settings.INTERNAL_API_TOKEN,
        )
        self.assertEqual(response.status_code, 200)

        cv.refresh_from_db()
        self.assertEqual(cv.score, 0.91)
