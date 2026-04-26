import json
import logging

from django.db.models import F
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CV
from .permissions import HasInternalAPIToken
from .producers.cv_producer import RabbitMQPublishError, publish_cv_for_scoring
from .serializers import CVSerializer, CVUploadSerializer
from .services.job_service import JobNotFoundError, JobServiceError, fetch_job
from .services.pdf_service import PDFExtractionError, extract_text


logger = logging.getLogger(__name__)


class CVUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CVUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            fetch_job(serializer.validated_data["job_id"])
        except JobNotFoundError:
            return Response(
                {"detail": "The selected job does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except JobServiceError:
            return Response(
                {"detail": "Job validation is currently unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        cv = serializer.save()

        try:
            cv.extracted_text = extract_text(cv.file.path)
            cv.save(update_fields=["extracted_text"])
        except PDFExtractionError as exc:
            cv.file.delete(save=False)
            cv.delete()
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            publish_cv_for_scoring(
                cv_id=cv.cv_id,
                cv_text=cv.extracted_text,
                job_id=cv.job_id,
            )
        except RabbitMQPublishError:
            logger.exception(
                json.dumps(
                    {
                        "event": "cv_scoring_publish_failed",
                        "cv_id": cv.cv_id,
                        "job_id": cv.job_id,
                    }
                )
            )
            return Response(
                {
                    "cv_id": cv.cv_id,
                    "status": "queue_unavailable",
                    "detail": "CV was saved, but RabbitMQ could not be reached.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        logger.info(
            json.dumps(
                {
                    "event": "cv_upload_accepted",
                    "cv_id": cv.cv_id,
                    "job_id": cv.job_id,
                    "candidate_email": cv.email,
                }
            )
        )
        return Response(
            {
                "cv_id": cv.cv_id,
                "status": "processing",
            },
            status=status.HTTP_202_ACCEPTED,
        )


class CVJobRankingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        cvs = CV.objects.filter(job_id=job_id).order_by(
            F("score").desc(nulls_last=True),
            "-created_at",
        )
        serializer = CVSerializer(cvs, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobRankingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        try:
            job = fetch_job(job_id)
        except JobNotFoundError:
            return Response(
                {"detail": "Job not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except JobServiceError:
            return Response(
                {"detail": "Job details are currently unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        cvs = CV.objects.filter(job_id=job_id).order_by(
            F("score").desc(nulls_last=True),
            "-created_at",
        )
        serialized_cvs = CVSerializer(cvs, many=True, context={"request": request}).data
        rankings = [
            {
                "rank": index,
                **cv_payload,
            }
            for index, cv_payload in enumerate(serialized_cvs, start=1)
        ]
        return Response(
            {
                "job": job,
                "cvs": rankings,
            },
            status=status.HTTP_200_OK,
        )


class CVInternalScoreUpdateView(APIView):
    permission_classes = [HasInternalAPIToken]

    def patch(self, request, cv_id):
        try:
            cv = CV.objects.get(cv_id=cv_id)
        except CV.DoesNotExist:
            return Response(
                {"detail": "CV not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        score = request.data.get("score")
        if score is None:
            return Response(
                {"detail": "Score is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            cv.score = float(score)
        except (TypeError, ValueError):
            return Response(
                {"detail": "Score must be numeric."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cv.save(update_fields=["score"])
        logger.info(
            json.dumps(
                {
                    "event": "cv_score_updated",
                    "cv_id": cv.cv_id,
                    "job_id": cv.job_id,
                    "score": cv.score,
                }
            )
        )
        return Response({"detail": "Score updated."}, status=status.HTTP_200_OK)
